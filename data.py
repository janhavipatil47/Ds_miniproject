import pandas as pd
import os

folder_path = "fitbit_data"

all_files = os.listdir(folder_path)

step_files = []
calorie_files = []

for file in all_files:
    if "step" in file.lower():
        step_files.append(os.path.join(folder_path, file))
    elif "calorie" in file.lower():
        calorie_files.append(os.path.join(folder_path, file))
steps_df = pd.concat([pd.read_csv(f) for f in step_files], ignore_index=True)
calories_df = pd.concat([pd.read_csv(f) for f in calorie_files], ignore_index=True)
print(steps_df.columns)
print(calories_df.columns)
steps_df = steps_df.rename(columns={
    "timestamp": "datetime",
    "steps": "Steps"
})

calories_df = calories_df.rename(columns={
    "timestamp": "datetime",
    "calories": "Calories"
})
steps_df["datetime"] = pd.to_datetime(steps_df["datetime"])
calories_df["datetime"] = pd.to_datetime(calories_df["datetime"])

steps_df["date"] = steps_df["datetime"].dt.date
calories_df["date"] = calories_df["datetime"].dt.date
merged_df = pd.merge(
    steps_df[["date", "Steps"]],
    calories_df[["date", "Calories"]],
    on="date",
    how="inner"
)
daily_df = merged_df.groupby("date").agg({
    "Steps": "sum",
    "Calories": "sum"
}).reset_index()
daily_df["ActivityScore"] = daily_df["Steps"] * 0.1
daily_df["Sedentary"] = 1440 - daily_df["ActivityScore"]
daily_df = daily_df[[
    "Steps", "Calories", "ActivityScore", "Sedentary"
]]
kaggle_df = pd.read_csv("dailyActivity_merged.csv")

kaggle_df = kaggle_df.rename(columns={
    "TotalSteps": "Steps",
    "Calories": "Calories",
    "VeryActiveMinutes": "VeryActive",
    "FairlyActiveMinutes": "Moderate",
    "LightlyActiveMinutes": "Light",
    "SedentaryMinutes": "Sedentary"
})

kaggle_df["ActivityScore"] = (
    kaggle_df["VeryActive"] +
    kaggle_df["Moderate"] +
    kaggle_df["Light"]
)

kaggle_df = kaggle_df[[
    "Steps", "Calories", "ActivityScore", "Sedentary"
]]


final_df = pd.concat([kaggle_df, daily_df], ignore_index=True)
final_df.to_csv("final_combined_data.csv", index=False)
print("Final dataset ready!")
