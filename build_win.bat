@echo off
chcp 65001 >nul
cd /d %~dp0
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller -w -F -n 窝哥报价系统 --add-data "templates/quote_template.xlsx;templates" --add-data "logo.png;." main.py
echo.
echo 打包完成：dist\窝哥报价系统.exe
echo 如需预置物料数据，把 woge.db 复制到 exe 同目录即可
pause
