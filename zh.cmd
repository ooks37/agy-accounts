@echo off
chcp 65001 >nul
python "%~dp0.agents\skills\zh\scripts\account_manager.py" %*
