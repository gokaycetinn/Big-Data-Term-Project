from pyspark.sql import SparkSession

def load_and_combine_data(spark):
    """
    Reads three different CSV files and merges them into a single Spark DataFrame.
    """
    print("Loading dataset 1...")
    df1 = spark.read.csv('data/online_retail.csv', header=True, inferSchema=True)
    print(f"Dataset 1 loaded: {df1.count()} records")
    
    print("Loading dataset 2...")
    df2 = spark.read.csv('data/online_retail_2009-2010.csv', header=True, inferSchema=True)
    print(f"Dataset 2 loaded: {df2.count()} records")
    
    print("Loading dataset 3...")
    df3 = spark.read.csv('data/online_retail_2010-2011.csv', header=True, inferSchema=True)
    print(f"Dataset 3 loaded: {df3.count()} records")
    
    print("Combining datasets...")
    combined_df = df1.union(df2).union(df3)
    print(f"Total records after combining: {combined_df.count()}")
    return combined_df