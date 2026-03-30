@echo off
REM Amazon ESCI verisiyle accuracy olcumu (V1, V2, V3, V4)
REM Onceden: python scripts/load_amazon_esci.py --n_queries 1000
echo Accuracy eval basliyor...
python scripts/run_accuracy_eval.py --max_rows 50 --prompts v1 v2 v3 v4
pause
