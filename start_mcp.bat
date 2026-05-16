@echo off
cd /d "%~dp0"

echo Starting Blender MCP Server...
"D:\Software\blender\blender-4.2.0-windows-x64\4.2\python\bin\python.exe" server.py
echo Server stopped
pause