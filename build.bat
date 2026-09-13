@echo off
REM Builds BleachAutoFarm.exe locally. Run this on Windows, inside the repo folder.

python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller --noconfirm build_exe.spec

echo.
echo ============================================
echo Build complete: dist\BleachAutoFarm.exe
echo ============================================
pause
