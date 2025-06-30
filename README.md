# 🛒 Online Retail Product Recommendation System

This project implements a scalable big data system for processing and analyzing online retail sales data. It utilizes modern big data frameworks like **Apache Spark**, **Apache Kafka**, and **MongoDB** to build a real-time recommendation engine.

## 📌 Project Overview

- 🔍 Analyze and process large-scale retail transaction datasets
- ⚙️ Stream real-time data using Kafka and Spark Structured Streaming
- 🧠 Generate personalized product recommendations using machine learning (ALS)
- 🌐 Provide a user-friendly web interface for data visualization and interaction

## 🧱 System Architecture

### ✅ Apache Spark
- Distributed in-memory processing of CSV datasets
- Used Spark SQL, Spark Streaming, and MLlib (ALS collaborative filtering)
- Optimized with DataFrames, caching, and parallel execution

### ✅ Apache Kafka
- Handles real-time event streaming of retail transactions
- Structured streaming integration with Spark
- Provides fault-tolerant and scalable ingestion

### ✅ MongoDB
- Stores cleaned data and ALS-based recommendations
- Fast query access with indexed document collections
- Integrated with Flask web app for dynamic retrieval

## 🔄 Data Pipeline

1. **Ingestion**: Load and validate multiple CSV datasets  
2. **Cleaning**: Remove nulls, handle date/format errors, and normalize data  
3. **Transformation**: Feature engineering and schema optimization  
4. **Streaming**: Kafka to Spark Structured Streaming to MongoDB  
5. **Recommendation**: ALS model training and real-time suggestion generation  

## 🌐 Web Application

- Built using **Flask** with **Plotly** for data visualization
- REST API serves recommendation results
- Responsive design with interactive charts and user-based suggestions

## 📈 Performance Highlights

- Real-time ingestion & processing of high-volume data
- Scalable ALS model with cold-start handling
- Low-latency recommendations with high prediction accuracy
- Optimized MongoDB queries and throughput

## 🚀 Key Technologies

- Apache Spark (SQL, MLlib, Streaming)
- Apache Kafka
- MongoDB
- Flask (Python)
- Plotly

## 🧠 Authors

- Hasan Emre Usta — `202111301`  
- Gökay Çetinakdoğan — `202111050`  
(CENG 476 - Big Data, Spring 2025)

---

> This project demonstrates the integration of modern big data tools to solve a real-world problem in retail analytics using distributed computing and machine learning.
