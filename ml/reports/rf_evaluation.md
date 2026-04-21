# Random Forest Evaluation Report

Dataset rows used: 188
Train rows: 150
Test rows: 38

Macro F1: 0.9195
AUC-ROC (OVR): 0.9926

## Classification Report

```
              precision    recall  f1-score   support

         LOW     1.0000    1.0000    1.0000        13
    MODERATE     0.9091    0.8333    0.8696        12
        HIGH     0.8571    0.9231    0.8889        13

    accuracy                         0.9211        38
   macro avg     0.9221    0.9188    0.9195        38
weighted avg     0.9224    0.9211    0.9208        38

```

## Confusion Matrix

|                 |   Pred LOW |   Pred MODERATE |   Pred HIGH |
|:----------------|-----------:|----------------:|------------:|
| Actual LOW      |         13 |               0 |           0 |
| Actual MODERATE |          0 |              10 |           2 |
| Actual HIGH     |          0 |               1 |          12 |

## Feature Importances

| feature             |   importance |
|:--------------------|-------------:|
| struggle_index      |  0.293502    |
| p90_elapsed_time    |  0.156617    |
| avg_elapsed_time    |  0.0977006   |
| time_pressure_index |  0.0971527   |
| median_elapsed_time |  0.0796776   |
| pace_ratio          |  0.0630999   |
| n_interactions      |  0.0542733   |
| error_burden        |  0.0486001   |
| wrong_streak_max    |  0.046635    |
| std_elapsed_time    |  0.0232774   |
| consistency_index   |  0.0217189   |
| elapsed_range_proxy |  0.00959937  |
| long_response_rate  |  0.00814511  |
| retry_rate          |  7.52302e-07 |
| efficiency_score    |  0           |
| retry_burden        |  0           |
| accuracy            |  0           |
| incorrect_rate      |  0           |
| accuracy_pct        |  0           |
