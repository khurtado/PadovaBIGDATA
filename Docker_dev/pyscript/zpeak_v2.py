import os
from pyspark.sql.functions import lit,udf,rand
from samples import *
from math import *
from pyspark.sql.types import *
from pyspark.sql import SparkSession
#import matplotlib
#matplotlib.use('Agg')
#import matplotlib.pyplot as plt                                                                                                                                        
import histogrammar.sparksql
import histogrammar as hg
import numpy as np

from pyspark.ml.linalg import Vectors,VectorUDT
from pyspark.ml.feature import StringIndexer,StandardScaler,VectorAssembler
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

from keras.models import Sequential
from keras.layers.core import Dense,Dropout,Activation

from distkeras.transformers import LabelIndexTransformer
from distkeras.predictors import ModelPredictor
from distkeras.evaluators import *
from distkeras.trainers import SingleTrainer

#Method
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
    
    default_=(False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
    """                                                    
    Z->mm candidate from arbitrary muon selection:
      N(mu) >= 2                                                
      pT > 30, 10  
      abs(eta) < 2.4, 2.4 
      mediumId muon                                                  
      opposite charge                                                     
    """
    
    if len(pt)<2:
        return default_

    #Identify muon candidate                                                                                                                                                      
    leadingIdx=None
    trailingIdx=None

    for idx in range(len(pt)):
        if leadingIdx == None:
            if pt[idx]>30 and abs(eta[idx])<2.4 and mediumid[idx]:
                leadingIdx = idx
        elif trailingIdx == None:
            if pt[idx]>10 and abs(eta[idx])<2.4 and mediumid[idx]:
                trailingIdx = idx
        else:
            if pt[idx]>10 and abs(eta[idx])<2.4 and mediumid[idx]:
                return default_

    if leadingIdx!=None and trailingIdx!=None and charge[leadingIdx]!=charge[trailingIdx]:
        dimuon_=(True,)+invMass(
            pt[leadingIdx], pt[trailingIdx],
            eta[leadingIdx], eta[trailingIdx],
            phi[leadingIdx], phi[trailingIdx],
            mass[leadingIdx], mass[trailingIdx]
        ) + (
            pt[leadingIdx], pt[trailingIdx],
            eta[leadingIdx], eta[trailingIdx],
            phi[leadingIdx], phi[trailingIdx]
        )

        return dimuon_
    else:
        return default_

def evaluate(model):
    global test_set
    
    metric_name = "f1"
    evaluator = MulticlassClassificationEvaluator(metricName=metric_name, predictionCol="prediction_index", labelCol="index_label")
    # Clear the prediction column from the testset.
    test_set1 = test_set.select("scaled_features", "label", "index_label")
    # Apply a prediction from a trained model.
    predictor = ModelPredictor(keras_model=trained_model, features_col="scaled_features")
    test_set1 = predictor.predict(test_set1)
    # Transform the prediction vector to an indexed label.
    index_transformer = LabelIndexTransformer(output_dim=nb_classes)
    test_set1 = index_transformer.transform(test_set1)
    # Store the F1 score of the SingleTrainer.
    score = evaluator.evaluate(test_set1)

    return score

def evaluate_accuracy(model, test_set, features="scaled_features"):
    evaluator = AccuracyEvaluator(prediction_col="prediction_index", label_col="index_label")
    predictor = ModelPredictor(keras_model=trained_model, features_col=features)
    transformer = LabelIndexTransformer(output_dim=nb_classes)
    test_set2 = test_set.select(features, "index_label")
    test_set2 = predictor.predict(test_set2)
    test_set2 = transformer.transform(test_set2)
    score = evaluator.evaluate(test_set2)

    return score


if __name__ == "__main__":
    
    spark=SparkSession.builder.appName('ZpeakSpark').getOrCreate()
    sc=spark
    sc0=spark.sparkContext

    #Metric start
    ##Collect StageMetrics
    stageMetrics = sc0._jvm.ch.cern.sparkmeasure.StageMetrics(spark._jsparkSession)
    stageMetrics.begin()

    ##Collect TaskMetrics
    taskMetrics = sc0._jvm.ch.cern.sparkmeasure.TaskMetrics(spark._jsparkSession, False)
    ###Verbal report
    #taskMetrics.begin()
    ###Save for later analysis
    TM = taskMetrics.createTaskMetricsDF("PerfTaskMetrics")

    DFList=[]
    for s in samples:
        print 'Loading {0} sample from EOS file'.format(s)
        dsPath="root://eospublic.cern.ch//eos/opstest/cmspd-bigdata/"+samples[s]['filename']
        tempDF=sc.read.format("org.dianahep.sparkroot").option("tree", "Events").load(dsPath).withColumn("pseudoweight", lit(samples[s]['weight'])).withColumn("sample", lit(s))

        DFList.append(tempDF)

    columns=[
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
        ### JET
        'Jet_pt',
        'Jet_eta',
        'Jet_phi',
        'Jet_mass',
        'Jet_bReg',
        ### Weight
        'pseudoweight',
    ]
    DF=DFList[0].select(columns)
    for df_ in DFList[1:]:
        DF=DF.union(df_.select(columns))
    #DF=DF.cache()
    #print 'Partitions: {}'.format(DF.rdd.getNumPartitions())

    ### Data scheme
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
        StructField("pt1", FloatType(), False),   # leading mu pT                                                                              
        StructField("pt2", FloatType(), False),   # sub-leading mu pT
        StructField("eta1", FloatType(), False),  # leading mu eta
        StructField("eta2", FloatType(), False),  # sub-leading mu eta
        StructField("phi1", FloatType(), False),  # leading mu phi
        StructField("phi2", FloatType(), False),  # sub-leading mu phi          
    ])

    dijetSchema = StructType([
        StructField("mass", FloatType(), False),     # Dijet mass                                                                                         
        StructField("pt", FloatType(), False),       # Dijet pt
        StructField("eta", FloatType(), False),      # Dijet eta                                                                
        StructField("phi", FloatType(), False),      # Dijet phi                  
        StructField("dPhi", FloatType(), False),     # DeltaPhi(jet1,jet2)
        StructField("dR", FloatType(), False),       # DeltaR(jet1,jet2)
        StructField("dEta", FloatType(), False),     # DeltaEta(jet1,jet2)                                                                          
    ])

    dimuonUDF=udf(dimuonCandidate, dimuonSchema)
    DeltaRZJJUDF = udf(deltaR, FloatType())
    dijetUDF = udf(invMass, dijetSchema)
    
    DF=DF.withColumn('Dimuon', dimuonUDF("Muon_pt",
                                         "Muon_eta",
                                         "Muon_phi",
                                         "Muon_mass",
                                         "Muon_charge",
                                         "Muon_mediumId")
                     )

    DF=DF.withColumn('Dijet', dijetUDF ( DF["Jet_pt"][0],
                                       DF["Jet_pt"][1],
                                       DF["Jet_eta"][0],
                                       DF["Jet_eta"][1],
                                       DF["Jet_phi"][0],
                                       DF["Jet_phi"][1],
                                       DF["Jet_mass"][0],
                                       DF["Jet_mass"][1]
                                     )
                  )
    DF = DF.withColumn('DeltaRZjj', DeltaRZJJUDF( 'Dimuon.eta', 'Dimuon.phi', 'Dijet.eta', 'Dijet.phi' ) )
    
    DF=DF.filter("Dimuon.mass>70").filter("Dimuon.mass<110")
    DF = DF.filter('Muon_pt[0] > 40').filter('Muon_pt[1] > 40')
    
    hg.sparksql.addMethods(DF)

    plots = hg.UntypedLabel(
    # 1d histograms 
        LeadMuPt       = hg.Bin(20, 0, 500,    DF['Dimuon.pt1'], hg.Sum(DF['pseudoweight'])),
        LeadMuEta      = hg.Bin(48, -2.4, 2.4, DF['Dimuon.eta1'], hg.Sum(DF['pseudoweight'])),
        SubLeadMuPt    = hg.Bin(20, 0, 500,    DF['Dimuon.pt2'], hg.Sum(DF['pseudoweight'])),
        SubLeadMuEta   = hg.Bin(48, -2.4, 2.4, DF['Dimuon.eta2'], hg.Sum(DF['pseudoweight'])),
        ZInvMass      = hg.Bin(80, 70, 110,   DF['Dimuon.mass'], hg.Sum(DF['pseudoweight'])),
        ZDeltaR       = hg.Bin(20, 0, 3,      DF['Dimuon.dPhi'], hg.Sum(DF['pseudoweight'])),
        ZDeltaPhi     = hg.Bin(10, 0, 3,      DF['Dimuon.dR'], hg.Sum(DF['pseudoweight'])),
        
        LeadJetPt       = hg.Bin(20, 0, 500,    DF['Jet_pt'][0], hg.Sum(DF['pseudoweight'])),
        LeadJetEta      = hg.Bin(48, -2.4, 2.4, DF['Jet_eta'][0], hg.Sum(DF['pseudoweight'])),
        SubLeadJetPt    = hg.Bin(20, 0, 500,    DF['Jet_pt'][1], hg.Sum(DF['pseudoweight'])),
        SubLeadJetEta   = hg.Bin(48, -2.4, 2.4, DF['Jet_eta'][1], hg.Sum(DF['pseudoweight'])),
        JJInvMass      = hg.Bin(80, 70, 110,   DF['Dijet.mass'], hg.Sum(DF['pseudoweight'])),
        JJDeltaR       = hg.Bin(20, 0, 3,      DF['Dijet.dPhi'], hg.Sum(DF['pseudoweight'])),
        JJDeltaPhi     = hg.Bin(10, 0, 3,      DF['Dijet.dR'], hg.Sum(DF['pseudoweight'])),
        ZJJDeltaR       = hg.Bin(20, 0, 3,      DF['DeltaRZjj'], hg.Sum(DF['pseudoweight'])),
        
    )

    bulkHisto=hg.Categorize(quantity = DF['sample'], value = plots)
    bulkHisto.fillsparksql(df=DF)

#    for VARIABLE, num in zip(['ZInvMass','ZDeltaR','ZDeltaPhi','JJInvMass','JJDeltaR','JJDeltaPhi','ZJJDeltaR'],
#                         ['331','332','333','334','335','336','337']
#                        ):

#        fig = plt.figure(num=None, figsize=(20, 10), dpi=80, facecolor='w', edgecolor='k')

#        plotVals = {}
#        plt.subplot(num)

#        for k in bulkHisto.bins:
#            if k == 'SingleMuon':
#                continue

#            aHisto = bulkHisto(k)(VARIABLE)
#            nBins    = len(aHisto.values)
#            edges    = np.linspace(aHisto.low, aHisto.high, nBins + 1)
#            width    = (aHisto.high - aHisto.low) / nBins

#            plotVals[k] = [x.sum for x in bulkHisto(k)(VARIABLE).values]
#            plt.bar(edges[:-1], plotVals[k], width=width, label=k, color=samples[k]['color'], edgecolor=samples[k]['color'], fill=True)

#        xdata   = np.linspace(aHisto.low+0.5*width, aHisto.high+0.5*width, nBins)
#        ydata   = [x.sum*4 for x in bulkHisto('SingleMuon')(VARIABLE).values]
#        yerror  = [x**0.5 for x in ydata]

#        plt.errorbar(xdata, ydata, fmt='ko', label="Data", xerr=width/2, yerr=yerror, ecolor='black')
#        plt.xlabel('%s' %VARIABLE)
#        plt.ylabel('Events / %s GeV' %width)
#        plt.yscale('log')
#        plt.legend(loc='upper right', fontsize='x-large', prop={'size': 10})
#        plt.savefig('/'+VARIABLE+'.pdf')
    
#        os.system('hdfs dfs -put /%s.pdf hdfs://10.64.22.72:9000/%s.pdf' %(VARIABLE , VARIABLE) )
#        os.system('hdfs dfs -put /%s.pdf hdfs://10.64.22.72:9000/%s.pdf' %(VARIABLE , VARIABLE) )

#    stageMetrics.end()
#    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++'
#    print 'PRINT STAGE METRICS: REPORT'
#    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++'
#    #stageMetrics.printReport()
#    #print '++++++++++++++++++++++++++++++++++++++++++++++++++++++'
#    #print 'PRINT STAGE METRICS: ACCUMULABLES'
#    #print '++++++++++++++++++++++++++++++++++++++++++++++++++++++'
#    #stageMetrics.printAccumulables()
#    #print '++++++++++++++++++++++++++++++++++++++++++++++++++++++'
#    #metricsDF = stageMetrics.createTaskMetricsDF()
#    #stageMetrics.saveData(metricsDF, "myPerfTaskMetrics1")

    #Task Metrics
    #taskMetrics.end()
    #taskMetrics.printReport()

    TM.show()
    TM=TM.collect()
    taskMetrics.saveData(TM, "taskmetrics_test1", "json")
    os.system('hdfs dfs -put /taskmetrics_test1 hdfs://10.64.22.72:9000/taskmetrics_test1')
    print ' ++Run "hdfs dfs -copyToLocal hdfs://10.64.22.72:9000/<PATH-TO-FILE> ." to retrieve your file from hdfs ++'
    os.system('ls .')
    #os.system('ls /taskmetrics_test1')
    #os.system('cat /taskmetrics_test1/_SUCCESS')
    #sc.stop()

    vectorizer = udf(lambda x: Vectors.dense(x), VectorUDT())

    nFeatures = vectorizer(
        array(
            'Dimuon.mass','Dimuon.dPhi','Dimuon.dR','Dijet.mass','Dijet.dPhi','Dijet.dR','DeltaRZjj'
        )
    )

    pseudodata = DF.withColumn( "features" , nFeatures ).select("features","sample")
    pseudodata = pseudodata.where( (col('sample') == "DYJetsToLL") | (col('sample') == "ZH") )
    dataset = pseudodata.selectExpr("features as features", "sample as label").orderBy(rand())

    num_workers = num_executors * num_cores

    #print("Number of desired executors: " + `num_executors`)
    #print("Number of desired cores / executor: " + `num_cores`)
    #print("Total number of workers: " + `num_workers`)

    string_indexer = StringIndexer(inputCol="label", outputCol="index_label")
    fitted_indexer = string_indexer.fit(dataset)
    indexed_df = fitted_indexer.transform(dataset)

    scaler = StandardScaler(inputCol="features", outputCol="scaled_features", withStd=True, withMean=True)
    fitted_scaler = scaler.fit(indexed_df)
    scaled_df = fitted_scaler.transform(indexed_df)

    nb_features = len(scaled_df.select("features").take(1)[0]["features"])
    nb_classes = len(scaled_df.select("label").take(1)[0]["label"])

    #print("Number of features: " + str(nb_features))
    #print("Number of classes: " + str(nb_classes))

    (training_set, test_set) = scaled_df.randomSplit([0.7, 0.3])

    test_set = test_set.repartition(num_workers)
    training_set = training_set.repartition(num_workers)

    DF.unpersist()

    training_set.cache()
    test_set.cache()

    num_test_set = test_set.count()
    num_training_set = training_set.count()

    print("Number of testset instances: " + str(num_test_set))
    print("Number of trainingset instances: " + str(num_training_set))
    print("Total number of instances: " + str(num_test_set + num_training_set))

    model = Sequential()
    model.add(Dense(500, input_shape=(nb_features,)))
    model.add(Activation('relu'))
    model.add(Dropout(0.4))
    model.add(Dense(500))
    model.add(Activation('relu'))
    model.add(Dropout(0.6))
    model.add(Dense(500))
    model.add(Activation('relu'))
    model.add(Dense(nb_classes))
    model.add(Activation('softmax'))
    model.summary()

    optimizer = 'adagrad'
    loss = 'categorical_crossentropy'
    results = {}
    time_spent = {}

    trainer = SingleTrainer(keras_model=model, loss=loss, worker_optimizer=optimizer,
                        features_col="scaled_features", num_epoch=1, batch_size=64)
    trained_model = trainer.train(training_set)

    dt = trainer.get_training_time()
    print("Time spent (SingleTrainer): " + `dt` + " seconds.")
    score = evaluate(trained_model)
    print("F1 (SingleTrainer): " + `score`)
    accuracy = evaluate_accuracy(trained_model,test_set)
    print("Accuracy: " + `accuracy`)
    results['single'] = score
    time_spent['single'] = dt

    sc.stop()
