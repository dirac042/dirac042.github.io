@echo off
rem updateblog.cmd — Windows 용 실행 래퍼 (PowerShell / cmd 에서:  .\updateblog.cmd  또는 더블클릭)
rem 실제 작업은 updateblog.py 가 합니다.  옵션:  --serve  --dry-run  --no-build  --posts <폴더> --images <폴더>
chcp 65001 >nul
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0updateblog.py" %*
) else (
  python "%~dp0updateblog.py" %*
)
if errorlevel 1 pause
