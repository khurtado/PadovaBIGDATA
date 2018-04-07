
# coding: utf-8

# # Setting up Spark
# 
# Start a pySpark session including Diana-Hep spark-root and histogrammar APIs
#from IPython import get_ipython
# In[17]:

#.master('spark://10.64.22.90:5050')
#get_ipython().magic(u'reset')
import pyspark.sql
from pyspark.conf import SparkConf
session = pyspark.sql.SparkSession.builder.appName('Demo').config('spark.jars.packages','org.diana-hep:spark-root_2.11:0.1.16,org.diana-hep:histogrammar-sparksql_2.11:1.0.4')     .config('spark.driver.extraClassPath','/opt/hadoop/share/hadoop/common/lib/EOSfs.jar')     .config('spark.executor.extraClassPath','/opt/hadoop/share/hadoop/common/lib/EOSfs.jar')     .getOrCreate()
#sqlContext= pyspark.sql.SparkSession().builder.config(conf=SparkConf())
#sqlContext= pyspark.sql.SparkSession.builder.master('mesos://10.64.22.90:5050').config(conf=SparkConf()).getOrCreate()
print 'SparkSQL sesssion created'

sqlContext=session
# # Loading root files stored remotely on EOS via xrootd
# 
# Loading root files (NanoAOD CMS format) from CERN public EOS area via xrootd.
# Trees are read using the spark-root

# In[18]:


from pyspark.sql.functions import lit
from samples import *

DFList = [] 

for s in samples:
    print 'Loading {0} sample from EOS file'.format(s) 
    dsPath = "root://eospublic.cern.ch//eos/opstest/cmspd-bigdata/"+samples[s]['filename']    
    tempDF = sqlContext.read                 .format("org.dianahep.sparkroot")                 .option("tree", "Events")                 .load(dsPath)                .withColumn("sample", lit(s))                
    DFList.append(tempDF)


# # Access DataFrame content
# 
# Get list of columns in the DataFrame ("branches" of the equivalent ROOT TTree).

# In[19]:


DFList[0].printSchema()


# # Data reduction
# 
# Subsets of interesting attributes can be selected via 'select' operations on the DataFrames (equivalent to "pruning" steps in ROOT-based frameworks).
# 
# All datasets can be joint into a single DataFrame (e.g. collecting data from various samples).

# In[20]:


columns = [
    ### MUON
    'Muon_pt',
    'Muon_eta',
    'Muon_phi',
    'Muon_mass',
    'Muon_charge',
    'Muon_mediumId',
    'Muon_softId',
    'Muon_tightId',
    'nMuon',
    ### SAMPLE
    'sample',
]

# Select columns from dataframe
DF = DFList[0].select(columns)
DF.printSchema()

# Merge all dataset into a single dataframe
for df_ in DFList[1:]:
    DF = DF.union(df_.select(columns))

print 'Partitions: {}'.format(DF.rdd.getNumPartitions())


# # Data selection
# 
# Selection of events based on features is obtained via a 'filter' operation.
# 
# Number of entries is obtained by 'count'.

# In[21]:


print 'total number of events in the DataFrame  = ', DF.count()
print 'events in the DataFrame with \"nMuon > 0\" = ', DF.filter('nMuon > 0').count()


# # Caching - 1
# 
# Dataframes can be cached into memory, shared across the Spark cluster nodes, for a faster access.
# 
# Caching takes some time...

# In[22]:


DF = DF.cache()


# # Caching - 2
# 
# ... but ensures fast data-handling operations afterwards.

# In[23]:


print 'total number of events in the DataFrame  = ', DF.count()
print 'events in the DataFrame with \"nMuon > 0\" = ', DF.filter('nMuon > 0').count()


# # Data inspection
# 
# 
# Events can be inspected with 'show' (as in TTree.Show() ), also concatenating 'select' and 'filter'.

# In[24]:


DF.filter(DF['sample'] == 'DYJetsToLL')  .select('sample','nMuon','Muon_pt','Muon_eta','Muon_phi','Muon_charge')  .show(5)


# # Create derivate quantities and structures - 1
# 
# User defined functions can be used for transformations evalueted row by row to compute derived quantity, such as invaraint mass of two physics objects involving multiple column.
# The return value is added as a new column in the output DataFrame.
# 
# Dimuon candidate structure is created as an example.

# In[28]:


from math import *
from pyspark.sql.types import *

dimuonSchema = StructType([
    StructField("pass", BooleanType(), False),   # True if filled / False if default(empty) 
    #
    StructField("mass", FloatType(), False),     # Dimuon mass
    StructField("pt", FloatType(), False),       # Dimuon pt
    StructField("eta", FloatType(), False),      # Dimuon eta
    StructField("phi", FloatType(), False),      # Dimuon phi
    StructField("dPhi", FloatType(), False),     # DeltaPhi(mu1,mu2)
    StructField("dR", FloatType(), False),       # DeltaR(mu1,mu2)
    StructField("dEta", FloatType(), False),     # DeltaEta(mu1,mu2)
    #
    StructField("mu1_pt", FloatType(), False),   # leading mu pT 
    StructField("mu2_pt", FloatType(), False),   # sub-leading mu pT 
    StructField("mu1_eta", FloatType(), False),  # leading mu eta
    StructField("mu2_eta", FloatType(), False),  # sub-leading mu eta
    StructField("mu1_phi", FloatType(), False),  # leading mu phi
    StructField("mu2_phi", FloatType(), False),  # sub-leading mu phi
])

def binaryWeight(pt):
    for idx in range(len(pt)):
        if pt[idx]>50:
            return 0.
        else:
            return 1.

def deltaPhi(phi1,phi2):
    ## Catch if being called with two objects
    if type(phi1) != float and type(phi1) != int:
        phi1 = phi1.phi
    if type(phi2) != float and type(phi2) != int:
        phi2 = phi2.phi
    ## Otherwise
    dphi = (phi1-phi2)
    while dphi >  pi: dphi -= 2*pi
    while dphi < -pi: dphi += 2*pi
    return dphi

def deltaR(eta1,phi1,eta2=None,phi2=None):
    ## catch if called with objects
    if eta2 == None:
        return deltaR(eta1.eta,eta1.phi,phi1.eta,phi1.phi)
    ## otherwise
    return hypot(eta1-eta2, deltaPhi(phi1,phi2))

def invMass(pt1, pt2, eta1, eta2, phi1, phi2, mass1, mass2):
    #
    theta1 = 2.0*atan(exp(-eta1))
    px1    = pt1 * cos(phi1)
    py1    = pt1 * sin(phi1)
    pz1    = pt1 / tan(theta1)
    E1     = sqrt(px1**2 + py1**2 + pz1**2 + mass1**2)

    theta2 = 2.0*atan(exp(-eta2))
    px2    = pt2 * cos(phi2)
    py2    = pt2 * sin(phi2)
    pz2    = pt2 / tan(theta2)
    E2     = sqrt(px2**2 + py2**2 + pz2**2 + mass2**2)

    themass  = sqrt((E1 + E2)**2 - (px1 + px2)**2 - (py1 + py2)**2 - (pz1 + pz2)**2)
    thept    = sqrt((px1 + px2)**2 + (py1 + py2)**2)
    thetheta = atan( thept / (pz1 + pz2) )        
    theeta   = 0.5*log( (sqrt((px1 + px2)**2 + (py1 + py2)**2 + (pz1 + pz2)**2)+(pz1 + pz2))/(sqrt((px1 + px2)**2 + (py1 + py2)**2 + (pz1 + pz2)**2)-(pz1 + pz2)) )
    thephi   = asin((py1 + py2)/thept)

    delPhi = deltaPhi(phi1,phi2)
    delR   = deltaR(eta1,phi1,eta2,phi2)
    delEta = eta1-eta2

    return (themass, thept, theeta, thephi, delPhi, delR, delEta)

def dimuonCandidate(pt, eta, phi, mass, charge, mediumid):
    # default class implementation   
    default_ = (False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
    """
    Z->mm candidate from arbitrary muon selection:
      N(mu) >= 2
      pT > 30, 10
      abs(eta) < 2.4, 2.4
      mediumId muon
      opposite charge
    """
    
    if len(pt) < 2:
        return default_
    
    #Identify muon candidate
    leadingIdx = None
    trailingIdx = None
 
    for idx in range(len(pt)):
        if leadingIdx == None:
            if pt[idx] > 30 and abs(eta[idx]) < 2.4 and mediumid[idx]:
                leadingIdx = idx
        elif trailingIdx == None:
            if pt[idx] > 10 and abs(eta[idx]) < 2.4 and mediumid[idx]:
                trailingIdx = idx
        else:
            if pt[idx] > 10 and abs(eta[idx]) < 2.4 and mediumid[idx]:
                return default_

    if leadingIdx != None and trailingIdx != None and charge[leadingIdx] != charge[trailingIdx]:            
        # Candidate found
        dimuon_   = (True,) +                     invMass(pt[leadingIdx], pt[trailingIdx],
                            eta[leadingIdx], eta[trailingIdx],
                            phi[leadingIdx], phi[trailingIdx],
                            mass[leadingIdx], mass[trailingIdx]) + \
                    (pt[leadingIdx], pt[trailingIdx],
                     eta[leadingIdx], eta[trailingIdx],
                     phi[leadingIdx], phi[trailingIdx])
                
        return dimuon_
    else:
        return default_    


# # Create derivate quantities and structures - 2
# 
# And a generic function filling the candidate structure can be defined.

# # Create derivate quantities and structures - 3
# 
# Finally, a dimuon candidate structure can be appended to the DataFrame as an additional column

# In[29]:


from pyspark.sql.functions import udf
dimuonUDF = udf(dimuonCandidate, dimuonSchema)
biweightUDF = udf(binaryWeight, FloatType())

DF = DF.withColumn('Dimuon', dimuonUDF ("Muon_pt",
                                        "Muon_eta",
                                        "Muon_phi",
                                        "Muon_mass",
                                        "Muon_charge",
                                        "Muon_mediumId")
                  )

DF = DF.withColumn('pseudoweight', biweightUDF("Muon_pt"))

DF.where('Dimuon.pass == True').select('Dimuon').show(3)
DF.where('Dimuon.pass == True').select('pseudoweight').show(3)


# In[33]:


DF.where('Dimuon.pass == True').where('Muon_pt[0] > 40').select('pseudoweight','Muon_pt').show(20)


# # Get statistics info about the data
# 
# Exploit pySparkSql functions to get statistical insights on the DataFrame

# In[34]:


from pyspark.sql.functions import *

print 'Number of events, pre-selection level'

DF.groupBy("sample").count().show()

print 'Number of events, Dimuon invariant mass in [70-110] GeV'

DF.where( (col("Dimuon.mass") > 70) & (col("Dimuon.mass") < 110) ).groupBy("sample").count().show()

print 'Mean of Dimuon mass, evaluated in [70-110] GeV range'

DF.where( (col("Dimuon.mass") > 70) & (col("Dimuon.mass") < 110) ).groupBy('sample').mean('Dimuon.mass').show()

print 'Description of Dimuon mass features for SingleMuon dataset only, evaluated in [70-110] GeV range'

DF.where( (col("Dimuon.mass") > 70) & (col("Dimuon.mass") < 110) & (DF["sample"] == "SingleMuon") ).describe('Dimuon.mass').show()


# # Plotting the Zpeak mass

# In[45]:


# Load libraries, and append histogrammar functionalities to dataframe
import matplotlib.pyplot as plt
#get_ipython().magic(u'matplotlib inline')
import histogrammar as hg
import histogrammar.sparksql
import numpy as np

DF = DF.where( (col("Dimuon.mass") > 70) & (col("Dimuon.mass") < 110) )

hg.sparksql.addMethods(DF)

plots = hg.UntypedLabel(
    # 1d histograms
    LeadPtW      = hg.Bin(50, 30, 180,   DF['Dimuon.mu1_pt'], hg.Sum(DF['pseudoweight'])),
    LeadPt       = hg.Bin(50, 30, 180,   DF['Dimuon.mu1_pt']),
    LeadPtEta    = hg.Bin(48, -2.4, 2.4, DF['Dimuon.mu1_eta']),
    SubLeadPt    = hg.Bin(100, 0, 200,   DF['Dimuon.mu2_pt']),
    SubLeadPtEta = hg.Bin(48, -2.4, 2.4, DF['Dimuon.mu2_eta']),
    InvMass      = hg.Bin(80, 70, 110,   DF['Dimuon.mass']),
    DeltaR       = hg.Bin(50, 0, 5,      DF['Dimuon.dPhi']),
    DeltaPhi     = hg.Bin(64, -3.2, 3.2, DF['Dimuon.dR']),
)

# Make a set of histograms, categorized per-sample
bulkHisto = hg.Categorize(quantity = DF['sample'], value = plots)

# Fill from spark
bulkHisto.fillsparksql(df=DF)


# In[36]:


VARIABLE = 'InvMass'

fig = plt.figure(num=None, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')

aHisto   = bulkHisto("SingleMuon")(VARIABLE)
nBins    = len(aHisto.values)
edges    = np.linspace(aHisto.low, aHisto.high, nBins + 1)
width    = (aHisto.high - aHisto.low) / nBins

plotVals = {}
for k in bulkHisto.bins:
    if k == 'SingleMuon':
        continue
    plotVals[k] = [x.toJson()['data']*0.19 for x in bulkHisto(k)(VARIABLE).values]
    plt.bar(edges[:-1], plotVals[k], width=width, label=k, color=samples[k]['color'], edgecolor=samples[k]['color'], fill=True)
    
xdata   = np.linspace(aHisto.low+0.5*width, aHisto.high+0.5*width, nBins)    
ydata   = [x.toJson()['data'] for x in bulkHisto('SingleMuon')(VARIABLE).values]
yerror  = [x**0.5 for x in ydata]

plt.errorbar(xdata, ydata, fmt='ko', label="Data", xerr=width/2, yerr=yerror, ecolor='black')

plt.xlabel('Dimuon invariant mass m($\mu\mu$) (GeV)')
plt.ylabel('Events / 0.5 GeV')
plt.legend(loc='upper right', fontsize='x-large', )


# # Plotting with pseudoweight

# In[46]:


VARIABLE = 'LeadPtW'

fig = plt.figure(num=None, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')

aHisto   = bulkHisto("SingleMuon")(VARIABLE)
nBins    = len(aHisto.values)
edges    = np.linspace(aHisto.low, aHisto.high, nBins + 1)
width    = (aHisto.high - aHisto.low) / nBins

plotVals = {}
for k in bulkHisto.bins:
    if k == 'SingleMuon':
        continue
    plotVals[k] = [x.sum*0.19 for x in bulkHisto(k)(VARIABLE).values]
    plt.bar(edges[:-1], plotVals[k], width=width, label=k, color=samples[k]['color'], edgecolor=samples[k]['color'], fill=True)
    
xdata   = np.linspace(aHisto.low+0.5*width, aHisto.high+0.5*width, nBins)    
ydata   = [x.sum for x in bulkHisto('SingleMuon')(VARIABLE).values]
yerror  = [x**0.5 for x in ydata]

plt.errorbar(xdata, ydata, fmt='ko', label="Data", xerr=width/2, yerr=yerror, ecolor='black')

plt.xlabel('Leading Muon pt (GeV)')
plt.ylabel('Events / 0.5 GeV')
plt.legend(loc='upper right', fontsize='x-large', )


# In[56]:


VARIABLE = 'LeadPt'

fig = plt.figure(num=None, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')

aHisto   = bulkHisto("SingleMuon")(VARIABLE)
nBins    = len(aHisto.values)
edges    = np.linspace(aHisto.low, aHisto.high, nBins + 1)
width    = (aHisto.high - aHisto.low) / nBins

plotVals = {}
for k in bulkHisto.bins:
    if k == 'SingleMuon':
        continue
    plotVals[k] = [x.toJson()['data']*0.19 for x in bulkHisto(k)(VARIABLE).values]
    plt.bar(edges[:-1], plotVals[k], width=width, label=k, color=samples[k]['color'], edgecolor=samples[k]['color'], fill=True)
    
xdata   = np.linspace(aHisto.low+0.5*width, aHisto.high+0.5*width, nBins)    
ydata   = [x.toJson()['data'] for x in bulkHisto('SingleMuon')(VARIABLE).values]
yerror  = [x**0.5 for x in ydata]

plt.errorbar(xdata, ydata, fmt='ko', label="Data", xerr=width/2, yerr=yerror, ecolor='black')

plt.xlabel('Leading Muon pt (GeV)')
plt.ylabel('Events / 0.5 GeV')
plt.legend(loc='upper right', fontsize='x-large', )
plt.savefig('foo.png')
plt.show()

# In[63]:


#for x in bulkHisto('DYJetsToLL')('LeadPtW').values :
#    print x.sum
#print '==================='
#for x in bulkHisto('DYJetsToLL')('LeadPt').values:
#    print x.toJson()['data']


# In[53]:


#print bulkHisto('DYJetsToLL')('LeadPtW').values

