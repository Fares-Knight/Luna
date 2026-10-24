@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Environnement Python local absent. Suivez la preparation dans README.md.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m luna
if errorlevel 1 (
    echo Le jeu a rencontre une erreur.
    pause
    exit /b 1
)
exit /b 0
