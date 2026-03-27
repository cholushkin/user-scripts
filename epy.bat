@echo off

REM -------------------------
REM CONFIG (EDIT HERE)
REM -------------------------
set ENV_NAME=dev

REM -------------------------
REM SETUP
REM -------------------------

chcp 65001 >nul

REM activate conda environment
call C:\Users\Maxim\miniconda3\Scripts\activate.bat %ENV_NAME%

echo Python path:
where python

echo Running user script under conda environment: %ENV_NAME%

REM run script with all passed args
python %*

pause