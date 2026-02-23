@echo off
cd /d "%~dp0"
echo Running environment setup for Radbot...

powershell -NoProfile -ExecutionPolicy Bypass -File setup_env.ps1
