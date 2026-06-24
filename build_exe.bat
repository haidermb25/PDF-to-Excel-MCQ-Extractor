@echo off
echo Building COMPTIA Parser executable...
echo.

pip install -r requirements.txt pyinstaller -q
if errorlevel 1 (
    echo Failed to install dependencies.
    exit /b 1
)

python -m PyInstaller --noconfirm "COMPTIA Parser.spec"
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo.
echo ============================================
echo  Build complete!
echo  EXE location: dist\COMPTIA Parser.exe
echo ============================================
echo.
echo Send the file "dist\COMPTIA Parser.exe" to your client.
echo No Python installation required on their machine.
pause
