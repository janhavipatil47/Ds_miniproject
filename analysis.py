"""Reproducible FitSense data-science pipeline.

The public Fitbit daily activity file is used as the primary source because it
contains participant identifiers and dates needed for quality checks.  The
rule-based fitness label is intentionally documented as an analytical target,
not a clinical outcome.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    silhouette_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import make_scorer


ROOT = Path(__file__).resolve().parent
SOURCE_FILE = ROOT / "dailyActivity_merged.csv"
NUMERIC_FEATURES = [
    "Calories",
    "TotalDistance",
    "VeryActiveMinutes",
    "FairlyActiveMinutes",
    "LightlyActiveMinutes",
    "SedentaryMinutes",
]
CLUSTER_FEATURES = ["TotalSteps", "Calories", "ActivityScore", "SedentaryMinutes"]


def load_and_clean_data(source_file: Path = SOURCE_FILE) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not source_file.exists():
        raise FileNotFoundError(f"Dataset not found: {source_file}")
    raw = pd.read_csv(source_file)
    required = {"Id", "ActivityDate", "TotalSteps", "Calories", *NUMERIC_FEATURES[1:]}
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")

    frame = raw.copy()
    before = len(frame)
    frame["ActivityDate"] = pd.to_datetime(frame["ActivityDate"], errors="coerce")
    numeric_columns = [column for column in frame.columns if column not in {"Id", "ActivityDate"}]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    invalid_rows = int(frame[["ActivityDate", "TotalSteps", "Calories"]].isna().any(axis=1).sum())
    frame = frame.dropna(subset=["ActivityDate", "TotalSteps", "Calories"])
    duplicate_rows = int(frame.duplicated(subset=["Id", "ActivityDate"]).sum())
    frame = frame.drop_duplicates(subset=["Id", "ActivityDate"]).copy()
    non_positive_rows = int(((frame["TotalSteps"] < 0) | (frame["Calories"] <= 0)).sum())
    frame = frame[(frame["TotalSteps"] >= 0) & (frame["Calories"] > 0)].copy()

    frame["ActivityScore"] = (
        frame["VeryActiveMinutes"] + frame["FairlyActiveMinutes"] + frame["LightlyActiveMinutes"]
    )
    frame["FitnessLevel"] = np.select(
        [
            (frame["TotalSteps"] < 5000) & (frame["SedentaryMinutes"] > 1000),
            frame["TotalSteps"] < 10000,
        ],
        ["Low", "Medium"],
        default="High",
    )
    frame["FitnessLevel"] = pd.Categorical(frame["FitnessLevel"], categories=["Low", "Medium", "High"])
    quality = {
        "source": source_file.name,
        "raw_records": before,
        "valid_records": int(len(frame)),
        "invalid_records": invalid_rows + non_positive_rows,
        "duplicate_records": duplicate_rows,
        "missing_values": {key: int(value) for key, value in raw.isna().sum().items() if value},
        "label_definition": "Low: steps < 5,000 and sedentary minutes > 1,000; Medium: steps < 10,000; otherwise High.",
    }
    return frame, quality


def _model_pipeline(model: Any) -> Pipeline:
    return Pipeline(
        [
            (
                "preprocess",
                ColumnTransformer(
                    [("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), NUMERIC_FEATURES)],
                    remainder="drop",
                ),
            ),
            ("model", model),
        ]
    )


def evaluate_models(frame: pd.DataFrame) -> dict[str, Any]:
    X = frame[NUMERIC_FEATURES]
    y = frame["FitnessLevel"].astype(str)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=42),
        "SVM": SVC(kernel="rbf", random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=250, random_state=42, class_weight="balanced"),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
        "MLP": MLPClassifier(hidden_layer_sizes=(32,), max_iter=1000, early_stopping=True, random_state=42),
    }
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rows: list[dict[str, Any]] = []
    fitted: dict[str, Pipeline] = {}
    for name, estimator in models.items():
        pipeline = _model_pipeline(estimator)
        scores = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=splitter,
            scoring={
                "accuracy": "accuracy",
                "precision_macro": make_scorer(precision_score, average="macro", zero_division=0),
                "recall_macro": make_scorer(recall_score, average="macro", zero_division=0),
                "f1_macro": make_scorer(f1_score, average="macro", zero_division=0),
            },
        )
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        fitted[name] = pipeline
        rows.append(
            {
                "model": name,
                "cv_accuracy_mean": float(scores["test_accuracy"].mean()),
                "cv_accuracy_std": float(scores["test_accuracy"].std()),
                "cv_macro_f1_mean": float(scores["test_f1_macro"].mean()),
                "test_accuracy": float(accuracy_score(y_test, predictions)),
                "test_precision_macro": float(precision_score(y_test, predictions, average="macro", zero_division=0)),
                "test_recall_macro": float(recall_score(y_test, predictions, average="macro", zero_division=0)),
                "test_macro_f1": float(f1_score(y_test, predictions, average="macro", zero_division=0)),
            }
        )
    rows.sort(key=lambda row: row["cv_macro_f1_mean"], reverse=True)
    selected_name = rows[0]["model"]
    selected_predictions = fitted[selected_name].predict(X_test)
    labels = ["Low", "Medium", "High"]
    matrix = confusion_matrix(y_test, selected_predictions, labels=labels)
    return {
        "comparison": rows,
        "selected_model": selected_name,
        "confusion_matrix": {"labels": labels, "values": matrix.tolist()},
        "test_records": int(len(y_test)),
        "target_caveat": "FitnessLevel is generated from activity thresholds, so scores measure rule reproduction rather than clinical prediction.",
    }


def clustering(frame: pd.DataFrame) -> dict[str, Any]:
    values = StandardScaler().fit_transform(frame[CLUSTER_FEATURES])
    candidates = []
    for k in range(2, 7):
        model = KMeans(n_clusters=k, n_init=20, random_state=42)
        labels = model.fit_predict(values)
        candidates.append({"k": k, "inertia": float(model.inertia_), "silhouette": float(silhouette_score(values, labels))})
    best = max(candidates, key=lambda item: item["silhouette"])
    model = KMeans(n_clusters=best["k"], n_init=20, random_state=42)
    labels = model.fit_predict(values)
    coordinates = PCA(n_components=2, random_state=42).fit_transform(values)
    profiles = frame.assign(Cluster=labels).groupby("Cluster")[CLUSTER_FEATURES].mean().round(2)
    return {
        "scores": candidates,
        "selected_k": int(best["k"]),
        "points": [
            {"x": float(point[0]), "y": float(point[1]), "cluster": int(label)}
            for point, label in zip(coordinates, labels)
        ],
        "profiles": [
            {"cluster": int(index), **{key: float(value) for key, value in row.items()}}
            for index, row in profiles.iterrows()
        ],
        "interpretation": "Clusters are exploratory activity profiles and are not medically validated categories.",
    }


def statistical_test(frame: pd.DataFrame) -> dict[str, Any]:
    low = frame.loc[frame["FitnessLevel"] == "Low", "TotalSteps"]
    high = frame.loc[frame["FitnessLevel"] == "High", "TotalSteps"]
    if low.empty or high.empty:
        return {"available": False, "reason": "Both Low and High groups are required."}
    statistic, p_value = mannwhitneyu(low, high, alternative="two-sided")
    pooled = np.sqrt((low.var(ddof=1) + high.var(ddof=1)) / 2)
    effect_size = float((high.mean() - low.mean()) / pooled) if pooled else 0.0
    return {
        "available": True,
        "test": "Mann–Whitney U",
        "null_hypothesis": "Low and High groups have the same step-count distribution.",
        "alternative": "The step-count distributions differ between groups.",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "effect_size": effect_size,
        "low_mean_steps": float(low.mean()),
        "high_mean_steps": float(high.mean()),
        "interpretation": "This is an association test on observational records; it does not establish causation.",
    }


def run_analysis() -> dict[str, Any]:
    frame, quality = load_and_clean_data()
    descriptive = frame[["TotalSteps", "Calories", "ActivityScore", "SedentaryMinutes"]].describe().round(2)
    correlations = frame[["TotalSteps", "Calories", "ActivityScore", "SedentaryMinutes"]].corr().round(3)
    model_results = evaluate_models(frame)
    cluster_results = clustering(frame)
    label_counts = frame["FitnessLevel"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
    trends = (
        frame.groupby("ActivityDate", as_index=False)[["TotalSteps", "Calories", "ActivityScore", "SedentaryMinutes"]]
        .mean()
        .sort_values("ActivityDate")
    )
    return {
        "quality": quality,
        "descriptive_statistics": json.loads(descriptive.to_json()),
        "correlations": json.loads(correlations.to_json()),
        "label_distribution": {key: int(value) for key, value in label_counts.items()},
        "trend": [
            {"date": row["ActivityDate"].strftime("%Y-%m-%d"), **{key: round(float(row[key]), 2) for key in ["TotalSteps", "Calories", "ActivityScore", "SedentaryMinutes"]}}
            for _, row in trends.iterrows()
        ],
        "statistical_test": statistical_test(frame),
        "models": model_results,
        "clustering": cluster_results,
        "limitations": [
            "The public Fitbit sample is observational and may not represent all users.",
            "Fitness labels are deterministic thresholds derived from the same activity domain.",
            "Repeated records from participants mean a participant-grouped validation split would be preferable for deployment.",
            "The application provides wellness-oriented insights, not diagnosis or medical advice.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(run_analysis(), indent=2))
