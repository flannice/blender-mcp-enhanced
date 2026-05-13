"""
Blender命令封装模块
将MCP工具调用转换为Blender Python脚本
"""

import json
from typing import Dict, Any, Optional


def create_primitive(params: Dict) -> str:
    """创建基本几何体"""
    prim_type = params.get("type", "cube")
    name = params.get("name", f"Primitive_{prim_type}")
    location = params.get("location", [0, 0, 0])
    size = params.get("size", [2, 2, 2])

    location_str = f"[{location[0]}, {location[1]}, {location[2]}]"

    type_map = {
        "cube": "bpy.ops.mesh.primitive_cube_add(size=2, location={loc})",
        "sphere": "bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location={loc})",
        "cylinder": "bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location={loc})",
        "cone": "bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location={loc})",
        "plane": "bpy.ops.mesh.primitive_plane_add(size=2, location={loc})",
        "torus": "bpy.ops.mesh.primitive_torus_add(location={loc})"
    }

    op = type_map.get(prim_type, type_map["cube"])
    script = f"""
import bpy
{op.format(loc=location_str)}
obj = bpy.context.active_object
obj.name = "{name}"
if {size[0]} != 2 or {size[1]} != 2 or {size[2]} != 2:
    obj.scale = [{size[0]}, {size[1]}, {size[2]}]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
print(f"SUCCESS: 创建{{obj.name}} 类型={prim_type} 位置={location}")
"""

    if "size" in params:
        script = f"""
import bpy
{op.format(loc=location_str)}
obj = bpy.context.active_object
obj.name = "{name}"
obj.scale = [{size[0]}, {size[1]}, {size[2]}]
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
print(f"SUCCESS: 创建{{obj.name}} 类型={prim_type} 尺寸={size}")
"""
    else:
        script = f"""
import bpy
{op.format(loc=location_str)}
obj = bpy.context.active_object
obj.name = "{name}"
print(f"SUCCESS: 创建{{obj.name}} 类型={prim_type} 位置={location}")
"""

    return script


def transform_object(params: Dict) -> str:
    """移动、旋转、缩放物体"""
    name = params.get("name", "")
    if not name:
        return 'print("ERROR: 未指定物体名称")'

    location = params.get("location")
    rotation = params.get("rotation")
    scale = params.get("scale")
    mode = params.get("mode", "global")

    ops = []
    if location:
        ops.append(f"obj.location = [{location[0]}, {location[1]}, {location[2]}]")
    if rotation:
        ops.append(f"obj.rotation_euler = [{rotation[0]}, {rotation[1]}, {rotation[2]}]")
    if scale:
        ops.append(f"obj.scale = [{scale[0]}, {scale[1]}, {scale[2]}]")

    transform_ops = "; ".join(ops)

    script = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj is None:
    print("ERROR: 物体 {name} 不存在")
else:
    bpy.context.view_layer.objects.active = obj
    {transform_ops}
    bpy.ops.object.transform_apply(location={location is not None}, rotation={rotation is not None}, scale={scale is not None})
    print(f"SUCCESS: 变换 {{obj.name}} 位置={obj.location} 旋转={{obj.rotation_euler}} 缩放={{obj.scale}}")
"""
    return script


def edit_mesh(params: Dict) -> str:
    """编辑网格"""
    name = params.get("name", "")
    operation = params.get("operation", "")
    edit_params = params.get("params", {})

    if not name or not operation:
        return 'print("ERROR: 未指定物体或操作类型")'

    script = f"""
import bpy
import math
obj = bpy.data.objects.get("{name}")
if obj is None:
    print("ERROR: 物体 {name} 不存在")
else:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
"""

    if operation == "extrude":
        direction = edit_params.get("direction", [0, 0, 1])
        distance = edit_params.get("distance", 1)
        script += f"""
    bpy.ops.mesh.extrude_vertices_move({{
        'transform': ({direction[0]}, {direction[1]}, {direction[2]}),
        'distance': {distance}
    }})
    print(f"SUCCESS: 挤出顶点 距离={distance}")
"""

    elif operation == "bevel":
        amount = edit_params.get("amount", 0.1)
        segments = edit_params.get("segments", 4)
        script += f"""
    bpy.ops.mesh.bevel(offset={amount}, segments={segments})
    print(f"SUCCESS: 倒角 宽度={amount} 段数={segments}")
"""

    elif operation == "subdivide":
        cuts = edit_params.get("cuts", 1)
        script += f"""
    bpy.ops.mesh.subdivide(number_cuts={cuts})
    print(f"SUCCESS: 细分 切割数={cuts}")
"""

    elif operation == "knife":
        script += f"""
    bpy.ops.mesh.knife_tool()
    print("SUCCESS: 刀切工具已激活")
"""

    elif operation == "weld_vertices":
        threshold = edit_params.get("threshold", 0.01)
        script += f"""
    bpy.ops.mesh.weld_verts(threshold={threshold})
    print(f"SUCCESS: 焊接顶点 阈值={threshold}")
"""

    script += """
    bpy.ops.object.mode_set(mode='OBJECT')
"""
    return script


def boolean_operation(params: Dict) -> str:
    """布尔运算"""
    operation = params.get("operation", "")
    object1 = params.get("object1", "")
    object2 = params.get("object2", "")
    result_name = params.get("result_name", "Boolean_Result")

    if not all([operation, object1, object2]):
        return 'print("ERROR: 缺少必要参数")'

    bool_map = {
        "union": "UNION",
        "difference": "DIFFERENCE",
        "intersect": "INTERSECT"
    }
    bool_type = bool_map.get(operation, "UNION")

    script = f"""
import bpy
obj1 = bpy.data.objects.get("{object1}")
obj2 = bpy.data.objects.get("{object2}")
if obj1 is None or obj2 is None:
    print("ERROR: 物体不存在")
else:
    bpy.context.view_layer.objects.active = obj1
    bool_mod = obj1.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.operation = '{bool_type}'
    bool_mod.object = obj2
    bpy.ops.object.modifier_apply(modifier="Boolean")
    obj1.name = "{result_name}"
    print(f"SUCCESS: 布尔运算 {{obj1.name}} 类型={operation}")
"""
    return script


def duplicate_object(params: Dict) -> str:
    """复制物体"""
    name = params.get("name", "")
    mode = params.get("mode", "single")
    count = params.get("count", 1)
    offset = params.get("offset", [2, 0, 0])
    result_name = params.get("result_name", f"{name}_copy")

    if not name:
        return 'print("ERROR: 未指定物体名称")'

    script = f"""
import bpy
import math
source = bpy.data.objects.get("{name}")
if source is None:
    print("ERROR: 物体 {name} 不存在")
else:
"""

    if mode == "single":
        script += f"""
    bpy.ops.object.select_all(action='DESELECT')
    source.select_set(True)
    bpy.ops.object.duplicate()
    new_obj = bpy.context.active_object
    new_obj.name = "{result_name}"
    print(f"SUCCESS: 复制 {{new_obj.name}}")
"""

    elif mode == "array":
        script += f"""
    bpy.ops.object.select_all(action='DESELECT')
    source.select_set(True)
    bpy.ops.object.duplicate_move({{
        'OBJECT_OT_duplicate': {{'name': '{result_name}'}},
        'TRANSFORM_OT_translate': {{'value': ({offset[0]}, {offset[1]}, {offset[2]})}}
    }})
    for i in range({count - 1}):
        bpy.ops.object.duplicate_move({{
            'TRANSFORM_OT_translate': {{'value': ({offset[0]}, {offset[1]}, {offset[2]})}}
        }})
    print(f"SUCCESS: 阵列复制 {{'{name}'}} 数量={count}")
"""

    elif mode == "mirror":
        axis = params.get("axis", "X")
        script += f"""
    bpy.ops.object.select_all(action='DESELECT')
    source.select_set(True)
    bpy.ops.object.duplicate()
    new_obj = bpy.context.active_object
    new_obj.name = "{result_name}"
    if '{axis}' == 'X':
        new_obj.scale[0] *= -1
    elif '{axis}' == 'Y':
        new_obj.scale[1] *= -1
    elif '{axis}' == 'Z':
        new_obj.scale[2] *= -1
    print(f"SUCCESS: 镜像复制 {{new_obj.name}} 轴={axis}")
"""

    elif mode == "radial":
        degrees = params.get("degrees", 360)
        script += f"""
    bpy.ops.object.select_all(action='DESELECT')
    source.select_set(True)
    bpy.ops.object.duplicate()
    angle_step = {degrees} / {count}
    for i in range({count}):
        bpy.ops.object.duplicate_move({{
            'TRANSFORM_OT_rotate': {{'value': angle_step * math.pi / 180}}
        }})
    print(f"SUCCESS: 径向复制 {{'{name}'}} 数量={count} 角度={degrees}")
"""

    return script


def add_material(params: Dict) -> str:
    """添加材质"""
    name = params.get("name", "")
    color = params.get("color", [0.8, 0.8, 0.8, 1.0])
    roughness = params.get("roughness", 0.5)
    metallic = params.get("metallic", 0.0)
    transparency = params.get("transparency", 0.0)
    material_name = params.get("material_name", f"{name}_Material")

    if not name:
        return 'print("ERROR: 未指定物体名称")'

    script = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj is None:
    print("ERROR: 物体 {name} 不存在")
else:
    mat = bpy.data.materials.new(name="{material_name}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = ({color[0]}, {color[1]}, {color[2]}, {color[3] if len(color) > 3 else 1.0})
        principled.inputs["Roughness"].default_value = {roughness}
        principled.inputs["Metallic"].default_value = {metallic}
        if {transparency} > 0:
            principled.inputs["Alpha"].default_value = {1 - transparency}
            mat.blend_method = 'BLEND'
    obj.data.materials.append(mat)
    print(f"SUCCESS: 添加材质 {{mat.name}} 到 {{obj.name}} 颜色={color[:3]} 粗糙度={roughness} 金属度={metallic}")
"""
    return script


def add_texture(params: Dict) -> str:
    """添加纹理贴图"""
    name = params.get("name", "")
    texture_path = params.get("texture_path", "")
    texture_type = params.get("texture_type", "color")
    uv_unwrap = params.get("uv_unwrap", True)

    if not name or not texture_path:
        return 'print("ERROR: 缺少必要参数")'

    type_map = {
        "color": "Base Color",
        "roughness": "Roughness",
        "metallic": "Metallic",
        "normal": "Normal",
        "height": "Height"
    }
    input_name = type_map.get(texture_type, "Base Color")

    script = f"""
import bpy
import os
obj = bpy.data.objects.get("{name}")
if obj is None:
    print("ERROR: 物体 {name} 不存在")
else:
"""

    if uv_unwrap:
        script += f"""
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')
"""

    script += f"""
    mat = obj.active_material
    if mat is None:
        mat = bpy.data.materials.new(name="{name}_TextureMat")
        mat.use_nodes = True
        obj.data.materials.append(mat)

    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")

    # 创建纹理节点
    tex_node = nodes.new(type='ShaderNodeTexImage')
    tex_node.name = "Texture_{texture_type}"

    # 加载纹理图片
    import os
    if os.path.exists(r"{texture_path}"):
        img = bpy.data.images.load(r"{texture_path}")
        tex_node.image = img

        # 连接纹理到Principled
        if principled:
            mat.node_tree.links.new(tex_node.outputs["Color"], principled.inputs["{input_name}"])
        print(f"SUCCESS: 添加纹理 {{tex_node.name}} 到 {{obj.name}} 类型={texture_type}")
    else:
        print(f"WARNING: 纹理文件不存在 {texture_path}")
"""
    return script


def add_light(params: Dict) -> str:
    """添加灯光"""
    light_type = params.get("type", "point")
    name = params.get("name", f"{light_type}_light")
    location = params.get("location", [0, 0, 5])
    rotation = params.get("rotation", [0, 0, 0])
    color = params.get("color", [1, 1, 1])
    energy = params.get("energy", 1000)

    type_map = {
        "point": "POINT",
        "spot": "SPOT",
        "sun": "SUN",
        "area": "AREA"
    }
    blender_type = type_map.get(light_type, "POINT")

    script = f"""
import bpy
bpy.ops.object.light_add(type='{blender_type}', location=({location[0]}, {location[1]}, {location[2]}))
light = bpy.context.active_object
light.name = "{name}"
light.rotation_euler = ({rotation[0]}, {rotation[1]}, {rotation[2]})
light.data.color = ({color[0]}, {color[1]}, {color[2]})
light.data.energy = {energy}
print(f"SUCCESS: 创建灯光 {{light.name}} 类型={light_type} 位置={location} 强度={energy}")
"""
    return script


def add_camera(params: Dict) -> str:
    """添加相机"""
    name = params.get("name", "Camera")
    location = params.get("location", [0, -5, 3])
    rotation = params.get("rotation", [1.2, 0, 0])
    focal_length = params.get("focal_length", 50)
    resolution_x = params.get("resolution_x", 1920)
    resolution_y = params.get("resolution_y", 1080)

    script = f"""
import bpy
bpy.ops.object.camera_add(location=({location[0]}, {location[1]}, {location[2]}))
camera = bpy.context.active_object
camera.name = "{name}"
camera.rotation_euler = ({rotation[0]}, {rotation[1]}, {rotation[2]})
camera.data.lens = {focal_length}
scene = bpy.context.scene
scene.camera = camera
scene.render.resolution_x = {resolution_x}
scene.render.resolution_y = {resolution_y}
print(f"SUCCESS: 创建相机 {{camera.name}} 焦距={focal_length}mm 分辨率={resolution_x}x{resolution_y}")
"""
    return script


def import_file(params: Dict) -> str:
    """导入文件"""
    file_path = params.get("file_path", "")
    file_type = params.get("file_type", "")
    import_opts = params.get("import_opts", {})

    if not file_path or not file_type:
        return 'print("ERROR: 缺少文件路径或类型")'

    type_map = {
        "fbx": ("fbx", "import_scene"),
        "obj": ("obj", "export_obj"),
        "glb": ("gltf", "import_glb"),
        "stl": ("stl", "import_stl"),
        "dwg": ("import_dxf", "load"),
        "dxf": ("import_dxf", "load")
    }

    if file_type not in type_map:
        return f'print("ERROR: 不支持的文件类型 {file_type}")'

    op_type, op_method = type_map[file_type]

    script = f"""
import bpy
import os
if not os.path.exists(r"{file_path}"):
    print(f"ERROR: 文件不存在 {file_path}")
else:
"""

    if file_type == "fbx":
        script += f"""
    bpy.ops.import_scene.fbx(filepath=r"{file_path}")
    print(f"SUCCESS: 导入FBX文件 {file_path}")
"""

    elif file_type == "obj":
        script += f"""
    bpy.ops.import_scene.obj(filepath=r"{file_path}")
    print(f"SUCCESS: 导入OBJ文件 {file_path}")
"""

    elif file_type == "glb":
        script += f"""
    bpy.ops.import_scene.gltf(filepath=r"{file_path}")
    print(f"SUCCESS: 导入GLB文件 {file_path}")
"""

    elif file_type == "stl":
        script += f"""
    bpy.ops.import_mesh.stl(filepath=r"{file_path}")
    print(f"SUCCESS: 导入STL文件 {file_path}")
"""

    elif file_type in ["dwg", "dxf"]:
        script += f"""
    bpy.ops.import_dxf(filepath=r"{file_path}")
    print(f"SUCCESS: 导入DXF/DWG文件 {file_path}")
"""

    return script


def export_file(params: Dict) -> str:
    """导出文件"""
    file_path = params.get("file_path", "")
    file_type = params.get("file_type", "")
    export_opts = params.get("export_opts", {})

    if not file_path or not file_type:
        return 'print("ERROR: 缺少文件路径或类型")'

    if file_type == "png":
        script = f"""
import bpy
scene = bpy.context.scene
scene.render.filepath = r"{file_path}"
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write=True)
print(f"SUCCESS: 导出PNG渲染图 {file_path}")
"""
    elif file_type == "fbx":
        script = f"""
bpy.ops.export_scene.fbx(filepath=r"{file_path}")
print(f"SUCCESS: 导出FBX文件 {file_path}")
"""
    elif file_type == "obj":
        script = f"""
bpy.ops.export_scene.obj(filepath=r"{file_path}")
print(f"SUCCESS: 导出OBJ文件 {file_path}")
"""
    elif file_type == "glb":
        script = f"""
bpy.ops.export_scene.gltf(filepath=r"{file_path}")
print(f"SUCCESS: 导出GLB文件 {file_path}")
"""
    elif file_type == "stl":
        script = f"""
bpy.ops.export_mesh.stl(filepath=r"{file_path}")
print(f"SUCCESS: 导出STL文件 {file_path}")
"""
    else:
        return f'print("ERROR: 不支持的文件类型 {file_type}")'

    return script


def manage_scene(params: Dict) -> str:
    """场景管理"""
    action = params.get("action", "")
    file_path = params.get("file_path", "")

    if action == "new":
        return """
import bpy
for obj in bpy.data.objects:
    bpy.data.objects.remove(obj)
print("SUCCESS: 新建场景")
"""
    elif action == "clear":
        return """
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
print("SUCCESS: 清空场景")
"""
    elif action == "save":
        if not file_path:
            return 'print("ERROR: 未指定保存路径")'
        return f"""
import bpy
bpy.ops.wm.save_as_mainfile(filepath=r"{file_path}")
print(f"SUCCESS: 保存场景到 {file_path}")
"""
    elif action == "load":
        if not file_path:
            return 'print("ERROR: 未指定加载路径")'
        return f"""
import bpy
bpy.ops.wm.open_mainfile(filepath=r"{file_path}")
print(f"SUCCESS: 加载场景 {file_path}")
"""
    else:
        return f'print("ERROR: 未知的场景操作 {action}")'


def select_objects(params: Dict) -> str:
    """选择物体"""
    mode = params.get("mode", "all")

    if mode == "all":
        return """
import bpy
bpy.ops.object.select_all(action='SELECT')
selected = [obj.name for obj in bpy.context.selected_objects]
print(f"SUCCESS: 选择所有物体 {selected}")
"""
    elif mode == "none":
        return """
import bpy
bpy.ops.object.select_all(action='DESELECT')
print("SUCCESS: 取消选择")
"""
    elif mode == "name":
        filter_name = params.get("filter", "")
        return f"""
import bpy
bpy.ops.object.select_all(action='DESELECT')
obj = bpy.data.objects.get("{filter_name}")
if obj:
    obj.select_set(True)
    print(f"SUCCESS: 选择物体 {filter_name}")
else:
    print(f"ERROR: 物体 {filter_name} 不存在")
"""
    elif mode == "type":
        filter_type = params.get("filter", "MESH")
        return f"""
import bpy
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.type == "{filter_type}":
        obj.select_set(True)
selected = [obj.name for obj in bpy.context.selected_objects]
print(f"SUCCESS: 选择类型={{filter_type}} 的物体 {selected}")
"""
    elif mode == "location":
        location = params.get("location", [0, 0, 0])
        radius = params.get("radius", 5)
        return f"""
import bpy
import math
bpy.ops.object.select_all(action='DESELECT')
center = ({location[0]}, {location[1]}, {location[2]})
for obj in bpy.data.objects:
    if hasattr(obj, 'location'):
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(obj.location, center)))
        if dist <= {radius}:
            obj.select_set(True)
selected = [obj.name for obj in bpy.context.selected_objects]
print(f"SUCCESS: 选择半径{radius}内的物体 {selected}")
"""
    else:
        return f'print("ERROR: 未知的选模式 {mode}")'


def delete_objects(params: Dict) -> str:
    """删除物体"""
    mode = params.get("mode", "selected")

    if mode == "selected":
        return """
import bpy
bpy.ops.object.delete(use_global=False)
print("SUCCESS: 删除所选物体")
"""
    elif mode == "all":
        return """
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
print("SUCCESS: 删除所有物体")
"""
    elif mode == "by_name":
        filter_name = params.get("filter", "")
        return f"""
import bpy
obj = bpy.data.objects.get("{filter_name}")
if obj:
    bpy.data.objects.remove(obj)
    print(f"SUCCESS: 删除物体 {filter_name}")
else:
    print(f"ERROR: 物体 {filter_name} 不存在")
"""
    else:
        return f'print("ERROR: 未知的删除模式 {mode}")'