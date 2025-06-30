from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import plotly.express as px
import pandas as pd

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
recommendation_collection = client["retail_db"]["recommendations"]
itemmap_collection = client["retail_db"]["retail_data"]
description_collection = client["retail_db"]["products"]  

# Updated logic to fetch product details from retail_data collection
@app.route("/", methods=["GET", "POST"])
def index():
    recommendations = []
    customer_id = None

    if request.method == "POST":
        customer_id = int(request.form["customer_id"])
        recs = recommendation_collection.find({"customer_id": customer_id})

        for r in recs:
            stock_code = r.get("stock_code")
            predicted = round(r.get("predicted_rating", 0), 2)

            # Fetch product details from retail_data collection
            product_doc = itemmap_collection.find_one({"StockCode": stock_code})
            description = product_doc["Description"] if product_doc else "N/A"
            price = product_doc["UnitPrice"] if product_doc else "N/A"
            country = product_doc["Country"] if product_doc else "N/A"

            recommendations.append({
                "StockCode": stock_code,
                "Description": description,
                "UnitPrice": price,
                "Country": country,
                "PredictedRating": predicted
            })

    return render_template("index.html", recommendations=recommendations, customer_id=customer_id)

if __name__ == "__main__":
    app.run(debug=True)
