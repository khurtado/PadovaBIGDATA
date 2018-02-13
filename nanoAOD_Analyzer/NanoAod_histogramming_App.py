#Spark Context declaration
from pyspark.sql import SparkSession
import pyspark.sql.functions
from histogrammar import *
import histogrammar.sparksql

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

spark = SparkSession.builder \
    .master(
        "spark://10.64.22.66:7077"
    ) \
    .appName(# Name of your application in the dashboard/UI
             "NanoAod_histogramming"
            ) \
    .config(# Tell Spark to load some extra libraries from Maven (the Java repository)
            'spark.jars.packages',
            'org.diana-hep:spark-root_2.11:0.1.13,org.diana-hep:histogrammar-sparksql_2.11:1.0.4',
            ) \
    .config('spark.cores.max',3
            ) \
    .getOrCreate()
#plt.ioff()
#read NanoAod from hdfs and define a dataframe
df = spark.read.format("org.dianahep.sparkroot").load(
    #"hdfs:///user/shoh/SingleMuonRun2016H-03Feb2017_ver2-v1_NANO.root"
"hdfs://10.64.22.72:9000/SingleMuonRun2016H-03Feb2017_ver2-v1_NANO.root"
)
#trim the dataframe into interesting variable
Event1 = df.select("RawMET_pt","Electron_pt","nElectron")
#Event selection
Event1.filter(Event1.RawMET_pt>=150).filter(Event1.nElectron==1).filter(Event1.Electron_pt[0]>=30)
#declaration of histogram
histogrammar.sparksql.addMethods(Event1)
histogrammar.sparksql.addMethods(df)
hist = df.Bin(100, 0, 100, Event1['RawMET_pt'])
#%matplotlib inline
hist.plot.matplotlib(name="test")
#plt.draw()
plt.show()
plt.savefig('nanoRawMET_pt.png')
#plt.plot(hist)
