import os
from pyspark.sql.functions import lit, array, col, udf, rand
from samples import *
from math import *
from pyspark.sql.types import *
from pyspark.sql import SparkSession
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                                                                                                                        
import histogrammar.sparksql
import histogrammar as hg
import numpy as np

from pyspark.ml.linalg import Vectors, VectorUDT
from pyspark.ml.feature import StringIndexer
from pyspark.ml.feature import StandardScaler

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

from distkeras.transformers import LabelIndexTransformer
from distkeras.predictors import ModelPredictor
from distkeras.evaluators import *

from distkeras.trainers import SingleTrainer
from distkeras.trainers import AEASGD
from distkeras.trainers import DOWNPOUR

from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation


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


if __name__ == "__main__":
    
    spark=SparkSession.builder.appName('ZpeakSpark').getOrCreate()
    sc=spark
    #sc0=spark.sparkContext

    #Metric start
    ##Collect StageMetrics
    #stageMetrics = sc0._jvm.ch.cern.sparkmeasure.StageMetrics(spark._jsparkSession)
    #stageMetrics.begin()

    ##Collect TaskMetrics
    #taskMetrics = sc0._jvm.ch.cern.sparkmeasure.TaskMetrics(spark._jsparkSession, False)
    ###Verbal report
    #taskMetrics.begin()
    ###Save for later analysis
    #TM = taskMetrics.createTaskMetricsDF("PerfTaskMetrics")

    DFList=[]
    for s in samples:
        print 'Loading {0} sample from EOS file'.format(s)
        dsPath="root://eospublic.cern.ch//eos/opstest/cmspd-bigdata/"+samples[s]['filename']
        tempDF=sc.read.format("org.dianahep.sparkroot").option("tree", "Events").load(dsPath).withColumn("sample", lit(s))
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
    ]
    DF=DFList[0].select(columns)
    for df_ in DFList[1:]:
        DF=DF.union(df_.select(columns))
    DF=DF.cache()
    #print 'total number of events in the DataFrame  = ', DF.count()
    #print 'events in the DataFrame with \"nMuon > 0\" = ', DF.filter('nMuon > 0').count()
    #DF.filter(DF['sample'] == 'DYJetsToLL').select('sample','nMuon','Muon_pt','Muon_eta','Muon_phi','Muon_charge').show(5)
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

    dimuonUDF=udf(dimuonCandidate, dimuonSchema)
    biweightUDF=udf(binaryWeight, FloatType())

    DF=DF.withColumn('Dimuon', dimuonUDF("Muon_pt",
                                         "Muon_eta",
                                         "Muon_phi",
                                         "Muon_mass",
                                         "Muon_charge",
                                         "Muon_mediumId")
                     )
    
    DF=DF.withColumn('pseudoweight',biweightUDF("Muon_pt"))
    #DF.where('Dimuon.pass == True').select('Dimuon').show(3)
    #DF.where('Dimuon.pass == True').select('pseudoweight').show(3)
    #DF.where('Dimuon.pass == True').where('Muon_pt[0] > 40').select('pseudoweight','Muon_pt').show(20)
    
    #DF=DF.where( (col("Dimuon.mass") > 70) & (col("Dimuon.mass") < 110) )
    DF=DF.filter("Dimuon.mass>70").filter("Dimuon.mass<110")
    hg.sparksql.addMethods(DF)
    print hg
    plots=hg.UntypedLabel(
        # 1d histograms                                                                                                                                                               
        LeadPtW      = hg.Bin(50, 30, 180,   DF['Dimuon.mu1_pt']),
        LeadPt       = hg.Bin(50, 30, 180,   DF['Dimuon.mu1_pt']),
        LeadPtEta    = hg.Bin(48, -2.4, 2.4, DF['Dimuon.mu1_eta']),
        SubLeadPt    = hg.Bin(100, 0, 200,   DF['Dimuon.mu2_pt']),
        SubLeadPtEta = hg.Bin(48, -2.4, 2.4, DF['Dimuon.mu2_eta']),
        InvMass      = hg.Bin(80, 70, 110,   DF['Dimuon.mass']),
        DeltaR       = hg.Bin(50, 0, 5,      DF['Dimuon.dPhi']),
        DeltaPhi     = hg.Bin(64, -3.2, 3.2, DF['Dimuon.dR']),
    )
    bulkHisto=hg.Categorize(quantity = DF['sample'], value = plots)
    bulkHisto.fillsparksql(df=DF)

    fig = plt.figure(num=None, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')

    for VARIABLE in ['InvMass']: #'LeadPtW','LeadPt'
        aHisto   = bulkHisto("SingleMuon")('%s' %VARIABLE)
        nBins    = len(aHisto.values)
        edges    = np.linspace(aHisto.low, aHisto.high, nBins + 1)
        width    = (aHisto.high - aHisto.low) / nBins
        plotVals = {}
        for k in ['DYJetsToLL','ZZ','TT','WW','WZ']:
            plotVals[k] = [x.toJson()['data']*0.19 for x in bulkHisto(k)('%s' %VARIABLE).values]
            plt.bar(edges[:-1], plotVals[k], width=width, label=k, color=samples[k]['color'], edgecolor=samples[k]['color'], fill=True, log=True)

        xdata   = np.linspace(aHisto.low+0.5*width, aHisto.high+0.5*width, nBins)
        ydata   = [x.toJson()['data'] for x in bulkHisto('SingleMuon')('%s' %VARIABLE).values]
        yerror  = [x**0.5 for x in ydata]

        plt.errorbar(xdata, ydata, fmt='ko', label="Data", xerr=width/2, yerr=yerror, ecolor='black')
        
        plt.xlabel('Dimuon invariant mass m($\mu\mu$) (GeV)')
        plt.ylabel('Events / 0.5 GeV')
        plt.legend(loc='upper right', fontsize='x-large', )
        plt.savefig(VARIABLE+'.pdf')    
        os.system('hdfs dfs -put '+VARIABLE+'.pdf hdfs://10.64.22.72:9000/LeadPtW.pdf')

    print "plot save to hdfs://10.64.22.72:9000/"

    #stageMetrics.end()
    #print '++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    #print 'PRINT STAGE METRICS: REPORT'
    #print '++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    #stageMetrics.printReport()
    #print '++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    #print 'PRINT STAGE METRICS: ACCUMULABLES'
    #print '++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    #stageMetrics.printAccumulables()
    #print '++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    #metricsDF = stageMetrics.createTaskMetricsDF()
    #stageMetrics.saveData(metricsDF, "myPerfTaskMetrics1")

    #Task Metrics
    #taskMetrics.end()
    #taskMetrics.printReport()

    #TM.show()
    #TM=TM.collect()
    #taskMetrics.saveData(TM, "taskmetrics_test1", "json")
    #os.system('hdfs dfs -put /taskmetrics_test1 hdfs://10.64.22.72:9000/taskmetrics_test1')
    #print ' ++Run "hdfs dfs -copyToLocal hdfs://10.64.22.72:9000/<PATH-TO-FILE> ." to retrieve your file from hdfs ++'
    os.system('ls .')
    os.system('hdfs dfs -ls hdfs://10.64.22.72:9000/')
    #os.system('ls /taskmetrics_test1')
    #os.system('cat /taskmetrics_test1/_SUCCESS')
    
    vectorizer = udf(lambda x: Vectors.dense(x), VectorUDT())

    ##Construct Desire Features:
    #nFeatures = vectorizer(
    #    array(
    #        'Dimuon.mass',
    #        'Dimuon.dPhi',
    #        'Dimuon.dR'
    #        'Dijet.mass',
    #        'Dijet.dPhi',
    #        'Dijet.dR',
    #        'DeltaRZjj'
    #    )
    #)

    nFeatures = vectorizer( array('Dimuon.mass','Dimuon.dPhi','Dimuon.dR') ) 

    pseudodata = DF.withColumn( "features" , nFeatures ).select("features","sample")

    #background mix with signal
    pseudodata = pseudodata.where( (col('sample') == "DYJetsToLL") | (col('sample') == "ZH") )
    #Rename sample to Label
    dataset = pseudodata.selectExpr("features as features", "sample as label").orderBy(rand())

    string_indexer = StringIndexer(inputCol="label", outputCol="index_label")
    fitted_indexer = string_indexer.fit(dataset)
    indexed_df = fitted_indexer.transform(dataset)
    
    scaler = StandardScaler(inputCol="features", outputCol="scaled_features", withStd=True, withMean=True)
    fitted_scaler = scaler.fit(indexed_df)
    scaled_df = fitted_scaler.transform(indexed_df)
    print("The result of indexing and scaling. Each transformation adds new columns to the data frame:")
    scaled_df.show(10)

    nb_features = len(scaled_df.select("features").take(1)[0]["features"])
    nb_classes = len(scaled_df.select("label").take(1)[0]["label"])
    #nb_classes = 1

    print("Number of features: " + str(nb_features))
    print("Number of classes: " + str(nb_classes))

    (training_set, test_set) = scaled_df.randomSplit([0.7, 0.3])

    test_set = test_set.repartition(5)
    training_set = training_set.repartition(5)

    ##release DF
    #DF.unpersist()

    training_set.cache()
    test_set.cache()

    num_test_set = test_set.count()
    num_training_set = training_set.count()

    print("Number of testset instances: " + str(num_test_set))
    print("Number of trainingset instances: " + str(num_training_set))
    print("Total number of instances: " + str(num_test_set + num_training_set))


    model = Sequential()
    model.add(Dense(100, input_shape=(nb_features,)))
    model.add(Activation('relu'))
    model.add(Dropout(0.4))
    model.add(Dense(100))
    model.add(Activation('relu'))
    model.add(Dropout(0.6))
    model.add(Dense(100))
    model.add(Activation('relu'))
    model.add(Dense(nb_classes))
    model.add(Activation('softmax'))
    model.summary()

    optimizer = 'adagrad'
    loss = 'categorical_crossentropy'

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

    results = {}
    time_spent = {}

    #singleTrainer
    #trainer = SingleTrainer(keras_model=model, loss=loss, worker_optimizer=optimizer, 
    #                    features_col="scaled_features", num_epoch=1, batch_size=64)
    #trained_model = trainer.train(training_set)

    ## Fetch the training time.
    #dt = trainer.get_training_time()
    #print("Time spent (SingleTrainer): " + `dt` + " seconds.")

    ## Evaluate the model.
    #score = evaluate(trained_model)
    #print("F1 (SingleTrainer): " + `score`)

    ## Evaluate Accuracy
    #accuracy = evaluate_accuracy(trained_model,test_set)
    #print("Accuracy: " + `accuracy`)

    ## Store the training metrics.
    #results['single'] = score
    #time_spent['single'] = dt

    #Model Training and evaluation: Asynchronous EASGD
    trainer = AEASGD(keras_model=model, worker_optimizer=optimizer, loss=loss, num_workers=5, batch_size=64,
                 features_col="scaled_features", num_epoch=1, communication_window=32, 
                 rho=5.0, learning_rate=0.1)
    trainer.set_parallelism_factor(1)

    #try:
    trained_model = trainer.train(training_set)
    #except KeyboardInterrupt as e:
    #   trainer.parameter_server.stop()

    # Fetch the training time.
    dt = trainer.get_training_time()
    print("Time spent (AEASGD): " + `dt` + " seconds.")

    # Evaluate the model.
    score = evaluate(trained_model)
    print("F1 (AEASGD): " + `score`)

    # Store the training metrics.
    results['aeasgd'] = score
    time_spent['aeasgd'] = dt

    #Model Training and evaluation: DOWNPOUR
    trainer = DOWNPOUR(keras_model=model, worker_optimizer=optimizer, loss=loss, num_workers=5,
                   batch_size=64, communication_window=5, learning_rate=0.1, num_epoch=1,
                   features_col="scaled_features")
    trainer.set_parallelism_factor(1)
    try:
        trained_model = trainer.train(training_set)
    except KeyboardInterrupt as e:
        trainer.parameter_server.stop()

    #Fetch the training time.
    dt = trainer.get_training_time()
    print("Time spent (DOWNPOUR): " + `dt` + " seconds.")

    # Evaluate the model.
    score = evaluate(trained_model)
    print("F1 (DOWNPOUR): " + `score`)
    
    # Store the training metrics.
    results['downpour'] = score
    time_spent['downpour'] = dt

    # Plot the time.
    fig = plt.figure()
    st = fig.suptitle("Lower is better.", fontsize="x-small")

    plt.bar(range(len(time_spent)), time_spent.values(), align='center')
    plt.xticks(range(len(time_spent)), time_spent.keys())
    plt.xlabel("Optimizers")
    plt.ylabel("Seconds")
    plt.ylim([0, 7000])
    #plt.show()
    plt.savefig('compareModelTime.pdf')

    # Plot the statistical performanc of the optimizers.
    fig = plt.figure()
    st = fig.suptitle("Higer is better.", fontsize="x-small")
    
    plt.bar(range(len(results)), results.values(), align='center')
    plt.xticks(range(len(results)), results.keys())
    plt.xlabel("Optimizers")
    plt.ylabel("F1")
    plt.ylim([0.83,0.85])
    #plt.show()
    plt.savefig('compareModelF1.pdf')

    sc.stop()


    
    #os.system('hdfs dfs -put /LeadPt.pdf hdfs://10.64.22.72:9000/LeadPt.pdf')
