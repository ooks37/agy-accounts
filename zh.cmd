@echo off
chcp 65001 >nul
if exist "%~dp0scripts\account_manager.py" (
    python -u "%~dp0scripts\account_manager.py" %*
) else if exist "%~dp0account_manager.py" (
    python -u "%~dp0account_manager.py" %*
) else if exist "%USERPROFILE%\.gemini\config\plugins\agy-accounts\scripts\account_manager.py" (
    python -u "%USERPROFILE%\.gemini\config\plugins\agy-accounts\scripts\account_manager.py" %*
) else (
    python -u "account_manager.py" %*
)
