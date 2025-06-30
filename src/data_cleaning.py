from pyspark.sql.functions import col, to_timestamp

def clean_data(df):
    """
    Cleans the DataFrame by removing nulls, fixing errors, and filtering out negative values. Also adds new columns.
    """
    initial_count = df.count()
    print(f"\nStarting data cleaning...")
    print(f"Initial record count: {initial_count}")
    
    # Remove rows with any null values
    df = df.dropna()
    after_null_count = df.count()
    print(f"Records after removing nulls: {after_null_count} (removed {initial_count - after_null_count} records)")
    
    # Convert InvoiceDate to timestamp (sometimes the format can be tricky)
    print("Converting InvoiceDate to timestamp...")
    df = df.withColumn("InvoiceDate", to_timestamp("InvoiceDate", "M/d/yyyy H:mm"))
    
    # Filter out rows where quantity or price is negative
    df = df.filter((col("Quantity") > 0) & (col("UnitPrice") > 0))
    after_filter_count = df.count()
    print(f"Records after removing negative values: {after_filter_count} (removed {after_null_count - after_filter_count} records)")
    
    # Add a column for the total amount spent on each row
    print("Calculating total amounts...")
    df = df.withColumn("TotalAmount", col("Quantity") * col("UnitPrice"))
    
    print(f"Data cleaning completed. Final record count: {df.count()}")
    return df