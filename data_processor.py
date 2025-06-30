from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, count, avg
from pyspark.sql.types import *
from kafka import KafkaProducer, KafkaConsumer
import json
from pymongo import MongoClient
import time
from datetime import datetime
import socket
import sys
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
import os
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import StringIndexer
import numpy as np
from src.data_ingestion import load_and_combine_data
from src.data_cleaning import clean_data
from src.recommendation import prepare_data_for_als, train_als_model, generate_recommendations, store_recommendations
from src.streaming import stream_to_kafka, write_stream_to_mongodb
from src.config import *

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("OnlineRetailAnalysis") \
    .config("spark.mongodb.output.uri", MONGODB_URI + MONGODB_DB) \
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:3.0.1") \
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_DIR) \
    .config("spark.hadoop.fs.defaultFS", "file:///") \
    .config("spark.executor.memory", "4g") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.cores", "2") \
    .config("spark.default.parallelism", "50") \
    .config("spark.sql.shuffle.partitions", "50") \
    .config("spark.memory.fraction", "0.8") \
    .config("spark.memory.storageFraction", "0.3") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.kryoserializer.buffer.max", "512m") \
    .config("spark.dynamicAllocation.enabled", "true") \
    .config("spark.shuffle.service.enabled", "true") \
    .config("spark.dynamicAllocation.minExecutors", "1") \
    .config("spark.dynamicAllocation.maxExecutors", "2") \
    .config("spark.dynamicAllocation.executorIdleTimeout", "60s") \
    .config("spark.dynamicAllocation.cachedExecutorIdleTimeout", "120s") \
    .getOrCreate()

# Set log level to WARN to reduce noise but keep important warnings
spark.sparkContext.setLogLevel("WARN")

# MongoDB connection
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'retail_data'

def create_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

def stream_to_kafka(df, producer=None):
    total_records = df.count()
    print(f"\nStarting Kafka streaming for {total_records} records...")
    df.selectExpr(
        "CAST(InvoiceNo AS STRING) AS key",
        "to_json(struct(*)) AS value"
    ).write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("topic", KAFKA_TOPIC) \
        .save()
    print("Bulk data transfer to Kafka completed!")

def write_stream_to_mongodb():
    print("\nStarting Spark Structured Streaming from Kafka to MongoDB...")
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .option("maxOffsetsPerTrigger", "100000") \
        .load()

    from pyspark.sql.functions import from_json, schema_of_json
    sample_json = '{"InvoiceNo": "1", "StockCode": "A", "Description": "desc", "Quantity": 1, "InvoiceDate": "2020-01-01 00:00:00", "UnitPrice": 1.0, "CustomerID": "12345", "Country": "UK", "TotalAmount": 1.0}'
    sample_schema = schema_of_json(sample_json)
    json_df = kafka_df.selectExpr("CAST(value AS STRING) as json") \
        .select(from_json("json", sample_schema).alias("data")).select("data.*")

    records_processed = 0
    def write_to_mongo(batch_df, batch_id):
        nonlocal records_processed
        batch_count = batch_df.count()
        records_processed += batch_count
        print(f"Processing batch {batch_id}: {batch_count} records (Total processed: {records_processed})")
        
        # Optimize MongoDB write
        batch_df.coalesce(10).write \
            .format("mongo") \
            .option("uri", "mongodb://localhost:27017/retail_db.retail_data") \
            .option("spark.mongodb.keep.alive", "true") \
            .option("spark.mongodb.connection.keep.alive.ms", "100000") \
            .mode("append") \
            .save()

    query = json_df.writeStream \
        .foreachBatch(write_to_mongo) \
        .outputMode("append") \
        .option("checkpointLocation", "checkpoint") \
        .trigger(processingTime='5 seconds') \
        .start()

    print("Streaming started. Waiting for data to be written to MongoDB...")
    query.awaitTermination()

def main():
    try:
        # Create checkpoint directory if it doesn't exist
        if not os.path.exists(CHECKPOINT_DIR):
            os.makedirs(CHECKPOINT_DIR)
        
        # Load and combine data with caching
        print("Loading and combining data...")
        df = load_and_combine_data(spark)
        df.cache()  # Cache the dataframe for multiple operations
        
        # Clean data
        print("Cleaning data...")
        df = clean_data(df)
        df.cache()  # Cache cleaned data
        
        # Prepare data for ALS with optimized partitioning
        df_ratings, df_indexed = prepare_data_for_als(df)
        df_ratings = df_ratings.repartition(200)  # Optimize partitioning for ALS
        df_ratings.cache()
        
        # Train ALS model with optimized parameters
        als_model = train_als_model(df_ratings)
        
        # Generate recommendations in batches
        recommendations = generate_recommendations(als_model, df_ratings)
        
        # Store recommendations in MongoDB with optimized batch size
        recommendations_collection = db[MONGODB_RECOMMENDATION_COLLECTION]
        store_recommendations(recommendations, df_indexed, recommendations_collection)
        
        # Stream data to Kafka with optimized batch size
        # Sadece ilk seferde veya veri güncellendiğinde bu satırı aç
        stream_to_kafka(df)
        
        # Spark Structured Streaming: Kafka -> MongoDB
        print("Starting streaming from Kafka to MongoDB...")
        write_stream_to_mongodb()
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        # Clean up
        spark.stop()
        mongo_client.close()

if __name__ == "__main__":
    main() 