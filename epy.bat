@echo off
chcp 65001 >nul

set BACKEND=micromamba
set ENV=dev

echo Running %~nx1 under [%BACKEND%:%ENV%]

if /i "%BACKEND%"=="micromamba" (
    set MAMBA_ROOT_PREFIX=C:\micromamba\root
    C:\micromamba\micromamba.exe run -n %ENV% python %*
) else (
    call C:\Users\cholu\miniconda3\Scripts\activate.bat %ENV%
    python %*
)

pause