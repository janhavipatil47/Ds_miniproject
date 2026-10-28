import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report
import joblib


df = pd.read_csv("final_combined_data.csv")


df = df[df["Steps"] > 0]
df = df[df["Calories"] > 0]
df = df[df["Steps"] >= 500]
df = df[df["Steps"] <= 30000]
df = df[df["Sedentary"] <= 1440]

print("After cleaning:", df.shape)


def label_fitness(row):
    if row["Steps"] < 5000 and row["Sedentary"] > 1000:
        return "Low"
    elif row["Steps"] < 10000:
        return "Medium"
    else:
        return "High"

df["FitnessLevel"] = df.apply(label_fitness, axis=1)

print("\nClass Distribution:")
print(df["FitnessLevel"].value_counts())


X = df[["Calories", "ActivityScore", "Sedentary"]]
y = df["FitnessLevel"]


scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)


X_cluster = df[["Steps", "Calories", "ActivityScore", "Sedentary"]]

scaler_cluster = StandardScaler()
X_cluster_scaled = scaler_cluster.fit_transform(X_cluster)

kmeans = KMeans(n_clusters=3, random_state=42)
df["Cluster"] = kmeans.fit_predict(X_cluster_scaled)

cluster_means = df.groupby("Cluster")[["Steps", "Sedentary"]].mean()

print("\nCluster Means:")
print(cluster_means)

sorted_clusters = cluster_means.sort_values(by="Steps").index.tolist()

cluster_mapping = {
    sorted_clusters[0]: "Sedentary",
    sorted_clusters[1]: "Moderate",
    sorted_clusters[2]: "Active"
}

df["ClusterLabel"] = df["Cluster"].map(cluster_mapping)

print("\nCluster Label Distribution:")
print(df["ClusterLabel"].value_counts())

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)


model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

gb_model = GradientBoostingClassifier(random_state=42)
gb_model.fit(X_train, y_train)


rf_accuracy = model.score(X_test, y_test)
print("\nRandom Forest Accuracy:", rf_accuracy)

gb_accuracy = gb_model.score(X_test, y_test)
print("Gradient Boosting Accuracy:", gb_accuracy)

print("\nModel Comparison:")
print("Random Forest Accuracy:", rf_accuracy)
print("Gradient Boosting Accuracy:", gb_accuracy)


y_pred = model.predict(X_test)
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

gb_pred = gb_model.predict(X_test)
print("\nGradient Boosting Classification Report:")
print(classification_report(y_test, gb_pred))


importance = pd.Series(model.feature_importances_, index=X.columns)
print("\nFeature Importance:")
print(importance.sort_values(ascending=False))

gb_importance = pd.Series(gb_model.feature_importances_, index=X.columns)
print("\nGradient Boosting Feature Importance:")
print(gb_importance.sort_values(ascending=False))


joblib.dump(model, "rf_model.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(kmeans, "kmeans.pkl")
joblib.dump(scaler_cluster, "cluster_scaler.pkl")
joblib.dump(cluster_mapping, "cluster_mapping.pkl")
joblib.dump(gb_model, "gb_model.pkl")

print("\n Model + KMeans saved!")