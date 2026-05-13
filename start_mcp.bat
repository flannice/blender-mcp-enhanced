@echo off
cd /d "%~dp0"

echo Starting Blender MCP Server...
python server.py
echo Server stopped
pause