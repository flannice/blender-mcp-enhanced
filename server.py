"""
Blender MCP Server - Controls running Blender via addon TCP connection
"""

import sys
import json
import socket
import threading
import subprocess
import os
import tempfile

BLENDER_PATH = r"D:\Software\blender\blender-4.2.0-windows-x64\blender.exe"
PORT = 9876

PROTOCOL_VERSION = "2024-11-05"

# Global: connected Blender client
blender_client = None
blender_client_lock = threading.Lock()


def execute_blender_direct(script):
    """Execute script in running Blender via addon, or fallback to background"""
    with blender_client_lock:
        if blender_client is not None:
            try:
                # Send script to connected Blender addon
                cmd = {"type": "script", "script": script}
                blender_client.sendall(json.dumps(cmd).encode('utf-8'))
                
                # Wait for response
                blender_client.settimeout(30.0)
                data = blender_client.recv(4096)
                result = json.loads(data.decode('utf-8'))
                if result.get("status") == "ok":
                    return result.get("output", "")
            except:
                pass
    
    # Fallback: run in background Blender
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write('import bpy\n')
            f.write(script)
            temp_script = f.name

        cmd = [BLENDER_PATH, "--background", "--python", temp_script]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=30)
        try:
            os.unlink(temp_script)
        except:
            pass

        if result.returncode != 0:
            return f"ERROR: {result.stderr}"
        return result.stdout
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {str(e)}"


def handle_tool(tool_name, args):
    if tool_name == "check_blender_connection":
        with blender_client_lock:
            if blender_client is not None:
                return {"content": [{"type": "text", "text": "✅ Blender connected (via addon)"}]}
        
        result = execute_blender_direct("print('BLENDER_OK')")
        if "BLENDER_OK" in result:
            return {"content": [{"type": "text", "text": "✅ Blender connected (background mode)"}]}
        return {"content": [{"type": "text", "text": "❌ Error: " + result}]}

    elif tool_name == "create_primitive":
        prim_type = args.get("type", "cube")
        name = args.get("name", "Primitive")

        type_map = {
            "cube": "primitive_cube_add(size=2, location=(0,0,0))",
            "sphere": "primitive_uv_sphere_add(radius=1, location=(0,0,0))",
        }

        op = type_map.get(prim_type, type_map["cube"])
        script = f"""
{op}
obj = bpy.context.active_object
obj.name = '{name}'
print('CREATED: ' + obj.name)
"""
        result = execute_blender_direct(script)
        return {"content": [{"type": "text", "text": result}]}

    elif tool_name == "add_light":
        script = """
bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
light = bpy.context.active_object
light.data.energy = 1000
print('LIGHT_ADDED')
"""
        result = execute_blender_direct(script)
        return {"content": [{"type": "text", "text": result}]}

    elif tool_name == "add_camera":
        script = """
bpy.ops.object.camera_add(location=(0, -5, 3))
camera = bpy.context.active_object
bpy.context.scene.camera = camera
print('CAMERA_ADDED')
"""
        result = execute_blender_direct(script)
        return {"content": [{"type": "text", "text": result}]}

    elif tool_name == "delete_objects":
        script = """
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
print('DELETED')
"""
        result = execute_blender_direct(script)
        return {"content": [{"type": "text", "text": result}]}

    return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}


def handle_mcp_request(request):
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    try:
        # Handle notifications (no id, no response needed)
        if req_id is None:
            return None

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "blender-mcp", "version": "1.0.0"}
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "check_blender_connection",
                            "description": "Check Blender connection",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        },
                        {
                            "name": "create_primitive",
                            "description": "Create primitive object",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "description": "Primitive type (cube or sphere)",
                                        "default": "cube"
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "Object name",
                                        "default": "Primitive"
                                    }
                                },
                                "required": []
                            }
                        },
                        {
                            "name": "add_light",
                            "description": "Add a light source",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        },
                        {
                            "name": "add_camera",
                            "description": "Add a camera",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        },
                        {
                            "name": "delete_objects",
                            "description": "Delete all objects",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    ]
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = handle_tool(tool_name, arguments)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": "pong"}

        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}

    except Exception as e:
        if req_id is not None:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}
        return None


def run_tcp():
    """TCP server - accepts connection from Blender addon"""
    global blender_client
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', PORT))
        server.listen(5)

        while True:
            client, addr = server.accept()
            with blender_client_lock:
                if blender_client is not None:
                    try:
                        blender_client.close()
                    except:
                        pass
                blender_client = client
    except:
        pass


if __name__ == "__main__":
    # Start TCP server in background
    tcp_thread = threading.Thread(target=run_tcp, daemon=True)
    tcp_thread.start()

    # MCP stdio server (for Trae IDE)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_mcp_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except:
            pass
