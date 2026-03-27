@echo off

chcp 65001 >nul

call C:\Users\Maxim\miniconda3\Scripts\activate.bat dev

echo Python path:
where python
echo Running user script under conda dev evironment

python %*
pause