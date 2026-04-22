## Dataset Setup

This project uses the EdNet-KT1 dataset.

### Required files

Place the following files in the specified directories:

ml/data/raw/KT1/
- u1.csv
- u10.csv
- u100.csv

ml/data/raw/
- questions.csv

### How to run

python src/ednet_merge.py  
python src/ednet_stage1.py  
python src/feature_engineering.py  
python src/retrain.py  