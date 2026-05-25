@echo off
chcp 65001 >nul

REM -------------------------
REM CONFIG
REM -------------------------
set BACKEND=conda
set ENV=dev

echo Running %~nx1 under [%BACKEND%:%ENV%]

echo CLI params:
echo   %*
echo.

REM -------------------------
REM BACKENDS
REM -------------------------

if /i "%BACKEND%"=="micromamba" (

	where micromamba >nul 2>nul
	if %errorlevel%==0 (
		micromamba run -n %ENV% python %*
	) else (
        echo [ERR] micromamba not found
    )

) else if /i "%BACKEND%"=="conda" (

    if exist "C:\Users\Maxim\miniconda3\Scripts\activate.bat" (
        call C:\Users\Maxim\miniconda3\Scripts\activate.bat %ENV%
        python %*
    ) else (
        echo [ERR] conda not found
    )

) else if /i "%BACKEND%"=="default" (

    python %*

) else (

    echo [ERR] BACKEND "%BACKEND%" not supported

)

pause