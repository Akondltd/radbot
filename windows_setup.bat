@echo off
cd /d "%~dp0"
echo Running environment setup for Akond Rad Bot...

powershell -NoProfile -ExecutionPolicy Bypass -File setup_env.ps1
