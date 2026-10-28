# FitSense

FitSense is a React/Vite and Flask wellness application backed by a reproducible Fitbit activity analysis.

## Setup

### Backend

From the project directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe backend\app.py
```

The API runs at `http://127.0.0.1:5000`. The `/analytics` endpoint computes and returns the academic analysis from `dailyActivity_merged.csv`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if the Flask API is hosted elsewhere.

## Analysis deliverables

Run the shared pipeline from the project directory:

```powershell
.\.venv\Scripts\python.exe analysis.py
```

Open [FitSense_Data_Analysis.ipynb](./FitSense_Data_Analysis.ipynb) in Jupyter for the executable notebook. The [project report](./FitSense_Project_Report.md) and [presentation outline](./FitSense_Presentation.md) document the method and limitations.

## Data and interpretation

The source is the public Fitbit daily activity sample in `dailyActivity_merged.csv`. The generated fitness label is based on transparent steps/sedentary thresholds. It is an analytical target, not a clinically validated outcome. Cluster labels are exploratory profiles, and all recommendations are wellness-oriented rather than medical advice.

## Verification

```powershell
cd frontend
npm run lint
npm run build
```
