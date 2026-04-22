# XGBoost Evaluation Report

Training rows used: 188

Unique users: 187

Train split rows: 150

Test split rows: 38

Train users: 149

Test users: 38

Macro F1: 0.9475

AUC-ROC (OVR): 0.9855

## Best Optuna Parameters

```json
{
  "n_estimators": 231,
  "max_depth": 7,
  "learning_rate": 0.016020256374242915,
  "subsample": 0.9797695913447781,
  "colsample_bytree": 0.9292103792681419,
  "min_child_weight": 6,
  "gamma": 2.3340446988016046,
  "reg_alpha": 2.2422946495762632,
  "reg_lambda": 1.7005101001006604
}
```

## Classification Report

```
              precision    recall  f1-score   support

         LOW     1.0000    0.9286    0.9630        14
    MODERATE     0.8571    1.0000    0.9231        12
        HIGH     1.0000    0.9167    0.9565        12

    accuracy                         0.9474        38
   macro avg     0.9524    0.9484    0.9475        38
weighted avg     0.9549    0.9474    0.9483        38

```
