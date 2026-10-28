# FitSense: Daily Activity Analysis and Wellness Dashboard

## Abstract

FitSense combines a public Fitbit daily activity sample with a React/Flask wellness dashboard. This project cleans and profiles activity records, tests group differences, compares five supervised classifiers using leakage-safe cross-validation, and explores activity profiles with K-Means and PCA. The application presents computed results while clearly separating descriptive evidence from model estimates and recommendations.

## Introduction and problem statement

People often have activity data but lack concise, decision-oriented feedback. FitSense addresses this by turning steps, calories, active minutes, and sedentary time into understandable trends and exploratory activity profiles. It does not diagnose disease or make causal health claims.

## Objectives

- Acquire and validate the supplied public Fitbit daily activity data.
- Clean, transform, describe, and visualize the records.
- Test whether step-count distributions differ between threshold-defined groups.
- Compare Logistic Regression, SVM, Random Forest, Gradient Boosting, and MLP.
- Explore clusters using an elbow/silhouette comparison and PCA.
- Deliver a reproducible notebook and connected analytics dashboard.

## Dataset and source

The primary source is `dailyActivity_merged.csv`, a public Fitbit daily activity sample distributed through the Kaggle Fitbit Fitness Tracker dataset. The file contains participant identifiers, dates, steps, distances, activity minutes, sedentary minutes, and calories. The analysis reports the exact record counts at runtime rather than embedding fabricated figures.

## Methodology and architecture

`analysis.py` is the single source of truth for cleaning, feature engineering, statistical testing, model evaluation, and clustering. Flask exposes its JSON result at `/analytics`; the React `DataScienceDashboard` renders the response. Existing authentication, profile, daily-entry, and trend flows remain intact.

## Data cleaning and EDA

Dates and numeric columns are coerced and validated. Duplicate participant-date records and invalid non-positive calorie records are removed. `ActivityScore` is engineered as the sum of very active, fairly active, and lightly active minutes. The notebook includes step distribution, correlation heatmap, boxplots, steps/calories scatter, label distribution, and activity/sedentary scatter views.

The `FitnessLevel` target is a deterministic analytical label: Low means fewer than 5,000 steps and more than 1,000 sedentary minutes; Medium means fewer than 10,000 steps; otherwise High. It is not independently verified health status.

## Statistical analysis

The notebook computes a two-sided Mann–Whitney U test comparing step-count distributions for the Low and High threshold groups. It reports the statistic, p-value, pooled-standard-deviation effect size, group means, and an interpretation. This is an observational association test, not a causal test.

## Machine learning methodology and validation

The supervised task reproduces the threshold label for analytical comparison. Each candidate model is wrapped in a scikit-learn `Pipeline` containing median imputation and standardization. A stratified five-fold cross-validation is run on the training partition, followed by a held-out test evaluation. Reported metrics include accuracy, macro precision, macro recall, macro F1, cross-validation mean, and cross-validation variability. A confusion matrix is returned for the selected model.

Because the target is derived from activity variables and the dataset contains repeated participant observations, performance must not be interpreted as clinical validity. A participant-grouped split would be preferred for a deployment dataset.

## Unsupervised learning

K-Means is evaluated for k=2 through k=6 using inertia and silhouette score. The best silhouette configuration is projected into two PCA dimensions. Cluster profiles retain original units for interpretation. Clusters are exploratory activity profiles, not medical categories.

## Results and error analysis

The verified run used 457 raw rows and retained 452 valid records (5 invalid rows removed). The threshold labels were Low=119, Medium=206, and High=127. Gradient Boosting had the strongest cross-validated macro F1 (0.9733, standard deviation of accuracy 0.0175); its held-out macro F1 was 0.9266. Random Forest had a higher held-out macro F1 (0.9480), illustrating why both cross-validation and held-out evaluation are reported. The Mann–Whitney U statistic was 0 with p < 0.001 and effect size 4.36; this is expected to be strongly separated because the label definition itself uses step thresholds.

Run `python analysis.py` or execute the notebook to regenerate the current numeric results. The dashboard reads those same results from `/analytics`, avoiding hardcoded scores. Error analysis is represented by the selected model's confusion matrix and the comparison between cross-validation and held-out test metrics. Limitations include label construction, class balance, sample representativeness, repeated participants, and observational measurement quality.

## Ethical considerations and limitations

The application should not expose private user data, infer medical conditions, or present recommendations as medical advice. Public Fitbit records may not generalize to other populations. Threshold labels encode assumptions and can reproduce those assumptions very accurately without proving health outcomes.

## Conclusion and future scope

FitSense now provides a reproducible analytical foundation and a functional dashboard. Future work should add participant-grouped or chronological validation where appropriate, confidence intervals, external validation labels, accessibility testing, and authenticated analytics access.

## References

1. Fitbit Fitness Tracker Data, public Kaggle dataset, `dailyActivity_merged.csv`.
2. Pedregosa et al. (2011), “Scikit-learn: Machine Learning in Python,” *Journal of Machine Learning Research*, 12, 2825–2830.
3. Lloyd (1982), “Least squares quantization in PCM,” *IEEE Transactions on Information Theory*.
