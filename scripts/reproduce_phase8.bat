@echo off
REM ==============================================================================
REM scripts/reproduce_phase8.bat
REM SupeRR Intelligence — End-to-End Phase 8 Reproduction Pipeline (Windows)
REM ==============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo ========================================================================
echo SUPERR INTELLIGENCE — END-TO-END PHASE 8 REPRODUCTION PIPELINE
echo ========================================================================

echo [Step 1/6] Verifying Python Environment...
python scripts\check_environment.py
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Environment verification returned non-zero.
)

set ZIP_PATH=%1
if "%ZIP_PATH%"=="" (
    if exist "6af458274c1e8_data_pack.zip" set ZIP_PATH=6af458274c1e8_data_pack.zip
    if exist "D:\Download\6af458274c1e8_data_pack.zip" set ZIP_PATH=D:\Download\6af458274c1e8_data_pack.zip
    if exist "..\6af458274c1e8_data_pack.zip" set ZIP_PATH=..\6af458274c1e8_data_pack.zip
)

if "%ZIP_PATH%"=="" (
    echo ERROR: Raw data pack archive not found!
    echo Usage: scripts\reproduce_phase8.bat path\to\6af458274c1e8_data_pack.zip
    exit /b 1
)

if not exist "%ZIP_PATH%" (
    echo ERROR: Specified data pack archive "%ZIP_PATH%" does not exist!
    exit /b 1
)
echo [Step 2/6] Using Data Pack: %ZIP_PATH%

echo [Step 3/6] Running Phase 1 Data Ingestion...
python supeRR_phase1_pipeline.py --zip "%ZIP_PATH%" --out output
if %ERRORLEVEL% neq 0 (
    echo ERROR in Phase 1 pipeline execution.
    exit /b 1
)

echo [Step 4/6] Running Phase 2 ML Analytical Generators...
set PYTHONPATH=.
echo   -^> Running Pressure Validation Generator...
python ml\phase2\pressure_validation.py
if %ERRORLEVEL% neq 0 exit /b 1

echo   -^> Running Model Evaluation Generator...
python ml\phase2\model_evaluation.py
if %ERRORLEVEL% neq 0 exit /b 1

echo   -^> Running WPA Evaluation Generator...
python ml\phase2\wpa_evaluation.py
if %ERRORLEVEL% neq 0 exit /b 1

echo [Step 5/6] Running Phase 8 Official Selection Engine...
python scripts\execute_phase8_analysis.py
if %ERRORLEVEL% neq 0 exit /b 1

echo [Step 6/6] Verifying Cryptographic Manifest and Submission Safety...
python scripts\verify_manifest.py
if %ERRORLEVEL% neq 0 exit /b 1

python scripts\verify_submission.py
if %ERRORLEVEL% neq 0 exit /b 1

echo ========================================================================
echo PHASE 8 REPRODUCTION COMPLETE ^& FULLY VERIFIED.
echo ========================================================================
