# FitSense presentation outline

## Slide 1 — Title and overview
FitSense: reproducible daily activity analysis and a decision-oriented wellness dashboard.

## Slide 2 — Problem and objectives
Explain the need to translate activity logs into trends, comparisons, and cautious recommendations.

## Slide 3 — Dataset and acquisition
Describe the public Fitbit daily activity file, its fields, participant/date grain, and source.

## Slide 4 — Cleaning and exploratory analysis
Show the quality summary, missing/duplicate handling, step distribution, correlation heatmap, and outlier boxplots.

## Slide 5 — Statistical analysis
State the Low-versus-High step-count hypothesis, Mann–Whitney U method, p-value/effect size from the executed notebook, and the non-causal interpretation.

## Slide 6 — Supervised learning
Compare Logistic Regression, SVM, Random Forest, Gradient Boosting, and MLP using stratified five-fold cross-validation and a held-out test set.

## Slide 7 — Clustering and PCA
Show inertia/silhouette values for k=2–6, the selected PCA projection, and original-unit cluster profiles.

## Slide 8 — Results and error analysis
Present the selected model, macro F1, confusion matrix, CV/test gap, class balance, and the fact that the target is rule-generated.

## Slide 9 — Dashboard demonstration
Demonstrate the activity entry/trend view and the live Data Science Analytics section connected to `/analytics`.

## Slide 10 — Limitations and future scope
Cover observational data, representativeness, repeated participants, non-clinical labels, privacy, grouped validation, and external validation.
