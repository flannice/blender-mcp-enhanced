bl_info = {
    "name": "Blender MCP Enhanced",
    "author": "Claude + Trae IDE",
    "version": (1, 0, 8),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > MCP",
    "description": "Blender MCP - TCP Client",
    "category": "Development",
}

import bpy
import socket
import json


PORT = 9876


def mcp_send(tool: str, params: dict = None) -> dict:
    if params is None:
        params = {}

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(180)  # 3 minute timeout for Blender
        sock.connect(('127.0.0.1', PORT))

        # Send command immediately
        command = {"tool": tool, "params": params}
        sock.sendall(json.dumps(command).encode('utf-8'))

        # Wait for single response
        sock.settimeout(60)
        response = b''
        chunk = sock.recv(4096)
        response += chunk

        sock.close()

        return json.loads(response.decode('utf-8'))

    except socket.timeout:
        return {"status": "error", "message": "Timeout - server not responding"}
    except ConnectionRefusedError:
        return {"status": "error", "message": "Connection refused - server not running"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


class MCP_OT_ping(bpy.types.Operator):
    bl_idname = "mcp.ping"
    bl_label = "Ping"

    def execute(self, context):
        result = mcp_send("ping")
        if result.get("status") == "ok":
            self.report({'INFO'}, "MCP OK")
        else:
            self.report({'ERROR'}, result.get("message", "Failed"))
        return {'FINISHED'}


class MCP_OT_cube(bpy.types.Operator):
    bl_idname = "mcp.cube"
    bl_label = "Cube"

    def execute(self, context):
        result = mcp_send("create_primitive", {"type": "cube", "name": "Cube"})
        if result.get("status") == "ok":
            self.report({'INFO'}, "Created")
        else:
            self.report({'ERROR'}, result.get("message", "Failed"))
        return {'FINISHED'}


class MCP_OT_sphere(bpy.types.Operator):
    bl_idname = "mcp.sphere"
    bl_label = "Sphere"

    def execute(self, context):
        result = mcp_send("create_primitive", {"type": "sphere", "name": "Sphere"})
        if result.get("status") == "ok":
            self.report({'INFO'}, "Created")
        else:
            self.report({'ERROR'}, result.get("message", "Failed"))
        return {'FINISHED'}


class MCP_OT_light(bpy.types.Operator):
    bl_idname = "mcp.light"
    bl_label = "Sun"

    def execute(self, context):
        result = mcp_send("add_light", {"type": "SUN"})
        if result.get("status") == "ok":
            self.report({'INFO'}, "Added")
        else:
            self.report({'ERROR'}, result.get("message", "Failed"))
        return {'FINISHED'}


class MCP_OT_camera(bpy.types.Operator):
    bl_idname = "mcp.camera"
    bl_label = "Camera"

    def execute(self, context):
        result = mcp_send("add_camera")
        if result.get("status") == "ok":
            self.report({'INFO'}, "Added")
        else:
            self.report({'ERROR'}, result.get("message", "Failed"))
        return {'FINISHED'}


class MCP_OT_delete(bpy.types.Operator):
    bl_idname = "mcp.delete"
    bl_label = "Delete"

    def execute(self, context):
        result = mcp_send("delete_all")
        if result.get("status") == "ok":
            self.report({'INFO'}, "Deleted")
        else:
            self.report({'ERROR'}, result.get("message", "Failed"))
        return {'FINISHED'}


class MCP_PT_panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "MCP_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MCP'

    def draw(self, context):
        layout = self.layout

        layout.box().label(text="MCP Control", icon='WORLD')
        layout.operator("mcp.ping", text="Ping", icon='PLAY')

        layout.box().label(text="Primitives", icon='MESH_CUBE')
        layout.operator("mcp.cube", text="Cube", icon='CUBE')
        layout.operator("mcp.sphere", text="Sphere", icon='SPHERE')

        layout.box().label(text="Scene", icon='SCENE_DATA')
        layout.operator("mcp.delete", text="Delete All", icon='X')

        layout.box().label(text="Camera/Light", icon='LIGHT')
        layout.operator("mcp.light", text="Sun", icon='LIGHT_SUN')
        layout.operator("mcp.camera", text="Camera", icon='CAMERA_STEREO')


classes = (
    MCP_OT_ping, MCP_OT_cube, MCP_OT_sphere,
    MCP_OT_light, MCP_OT_camera, MCP_OT_delete,
    MCP_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("[MCP] Loaded")


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()