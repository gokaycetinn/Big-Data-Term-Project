from pyspark.sql.functions import from_json, schema_of_json

def stream_to_kafka(df, kafka_bootstrap_servers, kafka_topic):
    total_records = df.count()
    print(f"\nStarting Kafka streaming for {total_records} records...")
    df.selectExpr(
        "CAST(InvoiceNo AS STRING) AS key",
        "to_json(struct(*)) AS value"
    ).write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("topic", kafka_topic) \
        .save()
    print("Bulk data transfer to Kafka completed!")

def write_stream_to_mongodb(spark, kafka_bootstrap_servers, kafka_topic, mongo_uri, checkpoint_dir):
    print("\nStarting Spark Structured Streaming from Kafka to MongoDB...")
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", kafka_topic) \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()

    # I created a sample JSON to get the schema for parsing Kafka messages
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
        batch_df.write \
            .format("mongo") \
            .option("uri", mongo_uri) \
            .mode("append") \
            .save()

    query = json_df.writeStream \
        .foreachBatch(write_to_mongo) \
        .outputMode("append") \
        .option("checkpointLocation", checkpoint_dir) \
        .start()

    print("Streaming started. Waiting for data to be written to MongoDB...")
    query.awaitTermination()