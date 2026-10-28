import joblib
import numpy as np
import pandas as pd

# -------------------------------
# LOAD MODELS
# -------------------------------
model = joblib.load("rf_model.pkl")
scaler = joblib.load("scaler.pkl")
kmeans = joblib.load("kmeans.pkl")
cluster_scaler = joblib.load("cluster_scaler.pkl")
cluster_mapping = joblib.load("cluster_mapping.pkl")


def get_recommendations(steps, calories, activity, sedentary):
    
    
    X = pd.DataFrame(
        [[calories, activity, sedentary]],
        columns=["Calories", "ActivityScore", "Sedentary"],
    )
    X_scaled = scaler.transform(X)
    X_cluster = pd.DataFrame(
        [[steps, calories, activity, sedentary]],
        columns=["Steps", "Calories", "ActivityScore", "Sedentary"],
    )
    X_cluster_scaled = cluster_scaler.transform(X_cluster)
    
    fitness = model.predict(X_scaled)[0]
    cluster = int(kmeans.predict(X_cluster_scaled)[0])
    cluster_type = cluster_mapping.get(cluster, "Unknown")

    if steps >= 8000:
        cluster_type = "Active"
    elif steps >= 5000:
        cluster_type = "Moderate"
    else:
        cluster_type = "Sedentary"
    
    recommendations = []

   
    if fitness == "Low":
        recommendations.append("Increase daily steps to at least 6000–8000")
        recommendations.append("Reduce sedentary time (take breaks every hour)")
        recommendations.append("Start with light exercises like walking")

    elif fitness == "Medium":
        recommendations.append("Maintain 8000–10000 steps daily")
        recommendations.append("Add moderate workouts like jogging or cycling")
        recommendations.append("Improve consistency in activity")

    else:  
        recommendations.append("Great job! Maintain your activity level")
        recommendations.append("Include strength training or HIIT workouts")
        recommendations.append("Ensure proper recovery and sleep")

   
    if cluster_type == "Sedentary":
        recommendations.append("You are in a sedentary group—reduce sitting time")
    
    elif cluster_type == "Moderate":
        recommendations.append("You are moderately active—push a bit more for better fitness")
    
    elif cluster_type == "Active":
        recommendations.append("You are in an active group—focus on performance improvement")

   
    if steps < 5000:
        recommendations.append("Your step count is low—try short walks during the day")

    if sedentary > 1000:
        recommendations.append("High sedentary time detected—stand/stretch frequently")

    if activity < 150:
        recommendations.append("Increase active minutes for better health benefits")

    return {
        "fitness_level": fitness,
        "cluster": cluster_type,
        "cluster_type": cluster_type,
        "recommendations": recommendations
    }
result = get_recommendations(
    steps=3000,
    calories=1800,
    activity=120,
    sedentary=1200
)

print(result)