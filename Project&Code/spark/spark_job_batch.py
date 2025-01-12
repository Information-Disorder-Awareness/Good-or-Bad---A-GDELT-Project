from pyspark.sql import SparkSession, functions
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType
from datetime import datetime, timedelta
import os
import time

def update_views():
    df = spark.read \
        .format("mongo") \
        .load()

    #max_date=df.select(functions.max("SQLDATE")).first()[0]
    today=int(datetime.now().date().strftime("%Y%m%d"))

    #most_mentioned_view = df.filter(((df["SQLDATE"] == today) | (df["SQLDATE"] == yesterday)))\
    most_mentioned_view = df.filter(((df["SQLDATE"] == today) | (df["SQLDATE"] == today-1)))\
    .select("EventCode","AvgTone","NumMentions","ActionGeo_CountryCode", "ActionGeo_Lat","ActionGeo_Long","CAMEOCodeDescription","SOURCEURL","GoldsteinScale", "SQLDATE", 
            "Actor1Name", "Actor2Name") \
    .dropDuplicates()

    #best_events_view = df.filter((df["GoldsteinScale"] >= 5) & ((df["SQLDATE"] == today) | (df["SQLDATE"] == yesterday))) \
    best_events_view = df.filter((df["GoldsteinScale"] >= 5)&(df["AvgTone"]>0) & ((df["SQLDATE"] == today) | (df["SQLDATE"] == today-1))) \
    .select("EventCode","AvgTone","NumMentions","ActionGeo_CountryCode", "ActionGeo_Lat","ActionGeo_Long","CAMEOCodeDescription","SOURCEURL","GoldsteinScale", "SQLDATE",
            "Actor1Name", "Actor2Name")\
    .dropDuplicates()

    #worst_events_view = df.filter((df["GoldsteinScale"] <= -5) & ((df["SQLDATE"] == today) | (df["SQLDATE"] == yesterday))) \
    worst_events_view = df.filter((df["GoldsteinScale"] <= -5)&(df["AvgTone"]<0) & ((df["SQLDATE"] == today) | (df["SQLDATE"] == today-1))) \
    .select("EventCode","AvgTone","NumMentions", "ActionGeo_CountryCode","ActionGeo_Lat","ActionGeo_Long","CAMEOCodeDescription","SOURCEURL","GoldsteinScale", "SQLDATE",
            "Actor1Name", "Actor2Name")\
    .dropDuplicates()

    if most_mentioned_view.count()==0:
        raise Exception("NoData")

    most_mentioned_view.write \
        .format("mongo") \
        .mode("overwrite") \
        .option("collection", "most_mentioned_view") \
        .save()

    best_events_view.write \
        .format("mongo") \
        .mode("overwrite") \
        .option("collection", "best_events_view") \
        .save()

    worst_events_view.write \
        .format("mongo") \
        .mode("overwrite") \
        .option("collection", "worst_events_view") \
        .save()

while True:
    master = os.getenv("SPARK_MASTER", "spark://spark-master:7077")
    spark = SparkSession.builder \
        .appName("MongoDBBatchViewJob") \
        .master(master) \
        .config("spark.mongodb.input.uri", "mongodb://mongodb:27017/gdelt_db.gdelt_events") \
        .config("spark.mongodb.output.uri", "mongodb://mongodb:27017/gdelt_batch_views") \
        .config("spark.cores.max", "4") \
        .config("spark.executor.memory", "2gb") \
        .config("spark.scheduler.mode", "FAIR") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("ERROR")
    try:
        update_views()
        print("Viste aggiornate in MongoDB")
        spark.stop()
        time.sleep(900)
    except Exception as e:
        print(f"Errore durante l'aggiornamento delle viste :\n {e}")
        print("Attendo l'arrivo dei dati...")
        spark.stop()
        time.sleep(60)
    
    
