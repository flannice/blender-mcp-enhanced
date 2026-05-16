# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Blender MCP Enhanced is a Model Context Protocol server that enables AI assistants (Claude/Trae IDE) to control Blender 3D modeling software through natural language commands.

## Architecture

```
┌─────────────┐     stdio MCP      ┌─────────────┐
│  Trae IDE   │ ◄──────────────►  │  server.py  │
│  (MCP Client)│                  │             │
└─────────────┘                   └──────┬──────┘
                                          │
                         TCP:9876         │ subprocess
                                          ▼
                                   ┌─────────────┐
                                   │ Blender     │
                                   │ (background)│
                                   └─────────────┘
                                          ▲
                                          │ socket
                                   ┌──────┴──────┐
                                   │ blender_    │
                                   │ mcp_addon.py│
                                   └─────────────┘
```

**Two connection paths:**
1. **MCP stdio** - Direct communication with Trae IDE (primary)
2. **TCP:9876** - Via Blender addon as intermediate client

## Running the Server

```bash
python server.py
```
Or use `start_mcp.bat`

The server must be configured in `.vscode/mcp.json` with correct Blender path.

## Key Files

- `server.py` - MCP server (stdio) + TCP server (9876), executes Blender via subprocess
- `blender_commands.py` - Generates Blender Python scripts for each operation
- `blender_mcp_addon.py` - Blender plugin that connects to TCP:9876
- `tools.json` - MCP tool definitions (15 tools across creation, editing, materials, lighting, file I/O)

## Important Configurations

**Blender path** in `server.py` line 13:
```python
BLENDER_PATH = r"E:\Chat\Trae-CN-IDE\Claude+Blender\blender-mcp-enhanced\blender-4.2.0-windows-x64\blender-4.2.0-windows-x64\blender.exe"
```
Must be updated to actual Blender installation path before use.

**MCP server config** in `.vscode/mcp.json` - Points to `server.py` location.

## MCP Protocol

- Protocol version: `2024-11-05`
- Methods: `initialize`, `tools/list`, `tools/call`, `ping`
- Communication: JSON-RPC 2.0 over stdio

## Blender Execution Model

Commands are executed by:
1. Writing Python script to temp file
2. Running `blender.exe --background --python <script>`
3. Capturing stdout/stderr
4. Returning results via MCP response