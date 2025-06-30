from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import StringIndexer
from pyspark.sql.functions import col, count
from datetime import datetime

def prepare_data_for_als(df):
    print("\nPreparing data for ALS model...")
    # I select the columns I need and make sure there are no duplicates
    df_indexed = df.select(
        "CustomerID",
        "StockCode",
        "Quantity"
    ).distinct().cache()
    
    # I use StringIndexer to convert string IDs to numeric indices
    user_indexer = StringIndexer(inputCol="CustomerID", outputCol="user_idx")
    item_indexer = StringIndexer(inputCol="StockCode", outputCol="item_idx")
    
    df_indexed = user_indexer.fit(df_indexed).transform(df_indexed)
    df_indexed = item_indexer.fit(df_indexed).transform(df_indexed)
    
    # I group by user and item to get the number of times each user bought each item
    df_ratings = df_indexed.groupBy("user_idx", "item_idx") \
        .agg(count("Quantity").alias("rating")) \
        .filter(col("rating") > 0)
    
    return df_ratings, df_indexed

def train_als_model(df_ratings):
    print("\nTraining ALS model...")
    train, test = df_ratings.randomSplit([0.8, 0.2], seed=42)
    
    als = ALS(
        maxIter=10,
        regParam=0.01,
        alpha=0.01,
        userCol="user_idx",
        itemCol="item_idx",
        ratingCol="rating",
        coldStartStrategy="drop",
        nonnegative=True,
        numUserBlocks=50,
        numItemBlocks=50,
        implicitPrefs=False,
        rank=20
    )
    
    model = als.fit(train)
    predictions = model.transform(test)
    
    evaluator = RegressionEvaluator(
        metricName="rmse",
        labelCol="rating",
        predictionCol="prediction"
    )
    rmse = evaluator.evaluate(predictions)
    print(f"Root-mean-square error = {rmse}")
    return model

def generate_recommendations(model, df_ratings, n_recommendations=10):
    print("\nGenerating recommendations...")
    users = df_ratings.select("user_idx").distinct()
    
    recommendations = model.recommendForUserSubset(users, n_recommendations)
    return recommendations

def store_recommendations(recommendations, df_indexed, collection):
    print("\nStoring recommendations in MongoDB...")
    # I create lookup tables to map indices back to original IDs
    user_lookup = df_indexed.select("user_idx", "CustomerID").distinct().collect()
    item_lookup = df_indexed.select("item_idx", "StockCode").distinct().collect()
    
    user_map = {row.user_idx: row.CustomerID for row in user_lookup}
    item_map = {row.item_idx: row.StockCode for row in item_lookup}
    
    batch_size = 500
    recommendations_list = []
    
    for row in recommendations.collect():
        user_id = user_map.get(row.user_idx)
        if user_id:
            for rec in row.recommendations:
                item_id = item_map.get(rec.item_idx)
                if item_id:
                    recommendations_list.append({
                        "customer_id": user_id,
                        "stock_code": item_id,
                        "predicted_rating": float(rec.rating),
                        "timestamp": datetime.now()
                    })
                    
                    if len(recommendations_list) >= batch_size:
                        collection.insert_many(recommendations_list)
                        recommendations_list = []
    
    if recommendations_list:
        collection.insert_many(recommendations_list)
    
    print(f"Stored recommendations for {len(user_map)} users")