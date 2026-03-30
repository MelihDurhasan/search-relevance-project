@echo off
cd /d "%~dp0"
python scripts\generate_1000_queries.py -n 500
pause
