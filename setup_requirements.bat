@echo off
title Installing Folder Sorter Requirements...
echo.
echo  --------------------------------------------------
echo   Installing needed libraries for Cable...
echo  --------------------------------------------------
echo.

python -m pip install rich watchdog pystray pillow

echo.
echo  --------------------------------------------------
echo   Finished! You can now run the script.
echo  --------------------------------------------------
echo.
pause

