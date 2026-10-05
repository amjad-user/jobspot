@echo off
rem =====================================================
rem  JobSpot - double-click this file to start JobSpot.
rem
rem  The first time, it gets everything ready (1-2 minutes):
rem    1. checks that Python is installed
rem    2. makes a private Python folder for JobSpot (.venv)
rem    3. installs what JobSpot needs
rem    4. makes the settings file (.env)
rem  Then it starts JobSpot and opens it in your browser.
rem =====================================================
setlocal
title JobSpot
rem Work in the folder this file is in (also when the path has spaces)
cd /d "%~dp0"

echo.
echo   Starting JobSpot...
echo.

rem ---------- 1. Find Python ----------
rem "py" is the Python launcher for Windows. If it is missing, we try "python".
set "PYTHON="
py -3 --version >nul 2>&1 && set "PYTHON=py -3"
if not defined PYTHON (
    python --version >nul 2>&1 && set "PYTHON=python"
)
if not defined PYTHON goto no_python

rem JobSpot needs Python 3.10 or newer
%PYTHON% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto old_python

rem ---------- 2. Make the private Python folder (only the first time) ----------
if not exist ".venv\Scripts\python.exe" (
    echo   First start: getting JobSpot ready. This takes a minute or two...
    echo.
    %PYTHON% -m venv .venv
    if errorlevel 1 goto venv_failed
)

rem ---------- 3. Install what JobSpot needs (first time, or after an update) ----------
rem We keep a copy of requirements.txt in .venv. If the two files are different,
rem something changed, so we install again.
fc /b "requirements.txt" ".venv\installed-requirements.txt" >nul 2>&1
if errorlevel 1 (
    echo   Installing what JobSpot needs. Please wait...
    ".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt
    if errorlevel 1 goto install_failed
    copy /y "requirements.txt" ".venv\installed-requirements.txt" >nul
)

rem ---------- 4. Settings file (only the first time) ----------
if not exist ".env" (
    copy ".env.example" ".env" >nul
)

rem ---------- 5. Start JobSpot ----------
rem -u = show messages right away
".venv\Scripts\python.exe" -u -m backend.launcher
if errorlevel 1 goto start_failed
goto done


rem ---------- Friendly messages when something is missing ----------
:no_python
echo   JobSpot needs Python, but Python is not installed on this computer.
echo.
echo   1. We now open the Python download page for you.
echo   2. Download and install Python. IMPORTANT: tick the box
echo      "Add python.exe to PATH" at the bottom of the first screen.
echo   3. Then double-click start.bat again.
echo.
start "" "https://www.python.org/downloads/"
pause
exit /b 1

:old_python
echo   JobSpot needs a newer Python (version 3.10 or newer).
echo   Please install the newest Python from https://www.python.org/downloads/
echo   and then double-click start.bat again.
echo.
pause
exit /b 1

:venv_failed
echo   JobSpot could not get ready (making the .venv folder did not work).
echo   Please delete the ".venv" folder inside the JobSpot folder and try again.
echo.
pause
exit /b 1

:install_failed
echo.
echo   JobSpot could not download what it needs.
echo   Please check your internet connection and try again.
echo   If it still does not work, delete the ".venv" folder and try again.
echo.
pause
exit /b 1

:start_failed
echo.
echo   JobSpot stopped because of a problem. See the message above.
echo.
pause
exit /b 1

:done
endlocal
