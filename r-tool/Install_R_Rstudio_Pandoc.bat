@echo off
setlocal

set "RSTUDIO_VERSION=RStudio-2024.04.1-748.exe"
set "R_VERSION=R-4.4.0-win.exe"
set "PANDOC_VERSION=pandoc-3.2.1-windows-x86_64.msi"
set "INSTALL_DIR=%~dp0"

echo Checking for RStudio installer...
if exist "%INSTALL_DIR%%RSTUDIO_VERSION%" (
    echo RStudio installer found.
) else (
    echo RStudio installer not found. Please download %RSTUDIO_VERSION% and place it in the same directory as this script.
    pause
    exit /b
)

echo Checking for R installer...
if exist "%INSTALL_DIR%%R_VERSION%" (
    echo R installer found.
) else (
    echo R installer not found. Please download %R_VERSION% and place it in the same directory as this script.
    pause
    exit /b
)

echo Checking for Pandoc installer...
if exist "%INSTALL_DIR%%PANDOC_VERSION%" (
    echo Pandoc installer found.
) else (
    echo Pandoc installer not found. Please download %PANDOC_VERSION% and place it in the same directory as this script.
    pause
    exit /b
)

echo Installing R...
start /wait "" "%INSTALL_DIR%%R_VERSION%" /SILENT

echo Installing RStudio...
start /wait "" "%INSTALL_DIR%%RSTUDIO_VERSION%" /SILENT

echo Installing Pandoc...
start /wait msiexec /i "%INSTALL_DIR%%PANDOC_VERSION%" /quiet /norestart

echo Installation complete.

echo Setting up environment variable for Rscript...

REM Set the Rscript.exe path directly
set "RSCRIPT_PATH=C:\Program Files\R\R-4.4.0\bin\Rscript.exe"

REM Check if Rscript.exe exists at the specified path
if exist "%RSCRIPT_PATH%" (
    echo Rscript.exe found.
    setx RSCRIPT_PATH "%RSCRIPT_PATH%" /M
    echo Environment variable 'RSCRIPT_PATH' set to: %RSCRIPT_PATH%
) else (
    echo Rscript.exe not found at: %RSCRIPT_PATH%
)

pause
