@echo off
cd /d "%~dp0"
Rscript -e "shiny::runApp('app.R', launch.browser = TRUE)"
pause
