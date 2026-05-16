bl_info = {
    "name": "Blender MCP Enhanced",
    "author": "Claude + Trae IDE",
    "version": (1, 0, 8),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > MCP",
    "description": "Blender MCP - Connect to Claude",
    "category": "Development",
}

import bpy
import socket
import json
import threading
import sys
from io import StringIO

PORT = 9876
connected = False
client_socket = None
running = False


class CapturePrint(StringIO):
    def __init__(self):
        super().__init__()
        self.old_stdout = sys.stdout
    
    def write(self, data):
        self.old_stdout.write(data)
        super().write(data)
    
    def __enter__(self):
        sys.stdout = self
        return self
    
    def __exit__(self, *args):
        sys.stdout = self.old_stdout


def mcp_loop():
    global client_socket, connected, running
    running = True
    
    while running:
        try:
            if not connected:
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.settimeout(5.0)
                    client_socket.connect(('127.0.0.1', PORT))
                    connected = True
                except:
                    bpy.app.timers.register(lambda: None, first_interval=2.0)
                    continue
            
            # Wait for command from server
            try:
                client_socket.settimeout(1.0)
                data = client_socket.recv(4096)
                if not data:
                    connected = False
                    continue
                
                cmd = json.loads(data.decode('utf-8'))
                
                if cmd.get("type") == "script":
                    script = cmd.get("script", "")
                    
                    # Execute the script and capture output
                    output = ""
                    try:
                        with CapturePrint() as cap:
                            exec(script)
                        output = cap.getvalue()
                    except Exception as e:
                        output = f"ERROR: {str(e)}"
                    
                    # Send response
                    response = {"status": "ok", "output": output}
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
            
            except socket.timeout:
                continue
            except json.JSONDecodeError:
                continue
                
        except Exception as e:
            connected = False
            try:
                if client_socket:
                    client_socket.close()
            except:
                pass
            bpy.app.timers.register(lambda: None, first_interval=2.0)


class MCP_OT_connect(bpy.types.Operator):
    bl_idname = "mcp.connect"
    bl_label = "Connect to MCP"
    
    def execute(self, context):
        thread = threading.Thread(target=mcp_loop, daemon=True)
        thread.start()
        self.report({'INFO'}, "Connecting...")
        return {'FINISHED'}


class MCP_OT_disconnect(bpy.types.Operator):
    bl_idname = "mcp.disconnect"
    bl_label = "Disconnect"
    
    def execute(self, context):
        global running, connected
        running = False
        connected = False
        try:
            if client_socket:
                client_socket.close()
        except:
            pass
        self.report({'INFO'}, "Disconnected")
        return {'FINISHED'}


class MCP_PT_panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "MCP_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MCP'
    
    def draw(self, context):
        layout = self.layout
        
        if connected:
            layout.label(text="✅ Connected to MCP", icon='CHECKMARK')
            layout.operator("mcp.disconnect", icon='X')
        else:
            layout.label(text="❌ Disconnected", icon='ERROR')
            layout.operator("mcp.connect", icon='PLUGIN')


classes = [
    MCP_OT_connect,
    MCP_OT_disconnect,
    MCP_PT_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
