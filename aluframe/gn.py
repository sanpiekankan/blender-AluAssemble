import bpy


def ensure_profile_node_group():
    name = "AluFrame_ProfileGN"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    ng = bpy.data.node_groups.new(name=name, type='GeometryNodeTree')
    nodes = ng.nodes
    links = ng.links

    # 使用 Geometry Nodes 接口 API 定义输入/输出（Blender 4.x）
    iface = ng.interface
    iface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    iface.new_socket(name="Width", in_out='INPUT', socket_type='NodeSocketFloat')
    iface.new_socket(name="Height", in_out='INPUT', socket_type='NodeSocketFloat')
    iface.new_socket(name="SlotWidth", in_out='INPUT', socket_type='NodeSocketFloat')
    iface.new_socket(name="WallThickness", in_out='INPUT', socket_type='NodeSocketFloat')
    iface.new_socket(name="Length", in_out='INPUT', socket_type='NodeSocketFloat')
    iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = nodes.new("NodeGroupInput"); inp.location = (-800, 0)
    out = nodes.new("NodeGroupOutput"); out.location = (450, 0)

    # 单位换算：毫米 -> 米
    def mm2m(socket_output):
        node = nodes.new("ShaderNodeMath"); node.operation = 'MULTIPLY'
        node.inputs[1].default_value = 0.001
        node.location = (-650, 0)
        links.new(socket_output, node.inputs[0])
        return node.outputs[0]

    w_m = mm2m(inp.outputs["Width"])   # X 尺寸（m）
    h_m = mm2m(inp.outputs["Height"])  # Y 尺寸（m）
    s_m = mm2m(inp.outputs["SlotWidth"])  # 槽宽（m）
    t_m = mm2m(inp.outputs["WallThickness"])  # 壁厚（m）
    l_m = mm2m(inp.outputs["Length"])  # Z 长度（m）

    # 基础立方体作为实体，尺寸为 (Width, Height, Length)
    cube = nodes.new("GeometryNodeMeshCube"); cube.location = (-300, 100)
    combine_size = nodes.new("ShaderNodeCombineXYZ"); combine_size.location = (-450, 100)
    links.new(w_m, combine_size.inputs[0])
    links.new(h_m, combine_size.inputs[1])
    links.new(l_m, combine_size.inputs[2])
    # 兼容不同版本的尺寸输入名称
    if "Size" in [i.name for i in cube.inputs]:
        links.new(combine_size.outputs[0], cube.inputs["Size"])
    else:
        links.new(combine_size.outputs[0], cube.inputs[0])

    # 槽口与布尔差集（在后台模式中，部分节点可能不稳定，加入保护）
    try:
        slots_join = nodes.new("GeometryNodeJoinGeometry"); slots_join.location = (-100, -100)

        def make_slot(dx, dy, y_offset):
            slot_cube = nodes.new("GeometryNodeMeshCube")
            slot_cube.location = (-300, y_offset)
            size = nodes.new("ShaderNodeCombineXYZ"); size.location = (-450, y_offset)
            links.new(l_m, size.inputs[2])
            links.new(s_m, size.inputs[0])
            links.new(t_m, size.inputs[1])
            if "Size" in [i.name for i in slot_cube.inputs]:
                links.new(size.outputs[0], slot_cube.inputs["Size"])
            else:
                links.new(size.outputs[0], slot_cube.inputs[0])

            trans = nodes.new("GeometryNodeTransform"); trans.location = (-150, y_offset)
            join = nodes.new("ShaderNodeCombineXYZ"); join.location = (-300, y_offset - 30)
            mulx = nodes.new("ShaderNodeMath"); mulx.operation = 'MULTIPLY'; mulx.location = (-450, y_offset - 120)
            links.new(w_m, mulx.inputs[0]); mulx.inputs[1].default_value = 0.5
            muly = nodes.new("ShaderNodeMath"); muly.operation = 'MULTIPLY'; muly.location = (-450, y_offset - 160)
            links.new(h_m, muly.inputs[0]); muly.inputs[1].default_value = 0.5

            offset_x = nodes.new("ShaderNodeMath"); offset_x.operation = 'SUBTRACT'; offset_x.location = (-300, y_offset - 120)
            half_wall = nodes.new("ShaderNodeMath"); half_wall.operation = 'MULTIPLY'; half_wall.location = (-300, y_offset - 160)
            links.new(t_m, half_wall.inputs[0]); half_wall.inputs[1].default_value = 0.5
            links.new(mulx.outputs[0], offset_x.inputs[0]); links.new(half_wall.outputs[0], offset_x.inputs[1])

            offset_y = nodes.new("ShaderNodeMath"); offset_y.operation = 'SUBTRACT'; offset_y.location = (-300, y_offset - 200)
            half_slot = nodes.new("ShaderNodeMath"); half_slot.operation = 'MULTIPLY'; half_slot.location = (-300, y_offset - 240)
            links.new(s_m, half_slot.inputs[0]); half_slot.inputs[1].default_value = 0.5
            links.new(muly.outputs[0], offset_y.inputs[0]); links.new(half_slot.outputs[0], offset_y.inputs[1])

            sx = nodes.new("ShaderNodeMath"); sx.operation = 'MULTIPLY'; sx.location = (-150, y_offset - 120); sx.inputs[1].default_value = dx
            sy = nodes.new("ShaderNodeMath"); sy.operation = 'MULTIPLY'; sy.location = (-150, y_offset - 160); sy.inputs[1].default_value = dy
            links.new(offset_x.outputs[0], sx.inputs[0]); links.new(offset_y.outputs[0], sy.inputs[0])

            links.new(slot_cube.outputs[0], trans.inputs[0])
            links.new(sx.outputs[0], join.inputs[0]); links.new(sy.outputs[0], join.inputs[1])
            if "Translation" in [i.name for i in trans.inputs]:
                links.new(join.outputs[0], trans.inputs["Translation"])
            else:
                links.new(join.outputs[0], trans.inputs[2])
            links.new(trans.outputs[0], slots_join.inputs[0])

        make_slot(+1, 0, -200)
        make_slot(-1, 0, -260)
        make_slot(0, +1, -320)
        make_slot(0, -1, -380)

        boolean = nodes.new("GeometryNodeMeshBoolean"); boolean.location = (150, 0); boolean.operation = 'DIFFERENCE'
        links.new(cube.outputs[0], boolean.inputs[0])
        links.new(slots_join.outputs[0], boolean.inputs[1])
        links.new(boolean.outputs[0], out.inputs[0])
    except Exception as e:
        print(f"[AluFrame] GN 槽口/布尔构建失败，退回为实心立方体：{e}")
        links.new(cube.outputs[0], out.inputs[0])
    return ng


def add_profile_object(context, item, location=(0.0, 0.0, 0.0)):
    ng = ensure_profile_node_group()

    bpy.ops.object.add(type='MESH', location=location)
    obj = context.active_object
    obj.name = f"AluProfile_{item.name}"

    obj["alu_type"] = item.name
    obj["standard"] = item.standard
    obj["series"] = item.series
    obj["length"] = float(item.default_length)

    mod = obj.modifiers.new(name="AluFrameProfile", type='NODES')
    mod.node_group = ng

    # 通过输入名称设置值（Blender 4.x 的推荐方式），单位为毫米
    for key, val in {
        "Width": item.width,
        "Height": item.height,
        "SlotWidth": item.slot_width,
        "WallThickness": item.wall_thickness,
        "Length": item.default_length,
    }.items():
        try:
            mod[key] = val
        except Exception:
            pass

    return obj