import bpy
import bmesh


def ensure_profile_node_group():
    name = "AluFrame_ProfileGN"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    ng = bpy.data.node_groups.new(name=name, type='GeometryNodeTree')
    nodes = ng.nodes
    links = ng.links
    # 定义组接口：优先使用 4.x 的 interface API；在 3.5 退回到 inputs/outputs API
    use_interface = hasattr(ng, "interface") and hasattr(ng.interface, "new_socket")
    if use_interface:
        iface = ng.interface
        iface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        iface.new_socket(name="Width", in_out='INPUT', socket_type='NodeSocketFloat')
        iface.new_socket(name="Height", in_out='INPUT', socket_type='NodeSocketFloat')
        iface.new_socket(name="SlotWidth", in_out='INPUT', socket_type='NodeSocketFloat')
        iface.new_socket(name="WallThickness", in_out='INPUT', socket_type='NodeSocketFloat')
        iface.new_socket(name="Length", in_out='INPUT', socket_type='NodeSocketFloat')
        iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    else:
        # Blender 3.5：旧接口
        try:
            ng.inputs.new('NodeSocketGeometry', 'Geometry')
            ng.inputs.new('NodeSocketFloat', 'Width')
            ng.inputs.new('NodeSocketFloat', 'Height')
            ng.inputs.new('NodeSocketFloat', 'SlotWidth')
            ng.inputs.new('NodeSocketFloat', 'WallThickness')
            ng.inputs.new('NodeSocketFloat', 'Length')
            ng.outputs.new('NodeSocketGeometry', 'Geometry')
        except Exception as e:
            print(f"[AluFrame] 旧接口定义失败：{e}")

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

    # 工具函数：按名称优先、类型兜底查找输入插槽
    def _find_input_socket(node, prefer_name, prefer_type="NodeSocketVector"):
        # 先按名称匹配
        for s in node.inputs:
            if s.name == prefer_name:
                return s
        # 再按类型匹配（例如 Vector）
        for s in node.inputs:
            if getattr(s, "type", "") == prefer_type:
                return s
        # 兜底返回第一个输入（不推荐，但避免抛异常）
        return node.inputs[0] if len(node.inputs) > 0 else None

    # 为尺寸输入加入最小值保护，防止 0 导致空几何
    def _min_eps(sock_out, eps=0.0001):
        m = nodes.new("ShaderNodeMath"); m.operation = 'MAXIMUM'
        m.inputs[1].default_value = eps
        links.new(sock_out, m.inputs[0])
        return m.outputs[0]

    w_m_safe = _min_eps(w_m); h_m_safe = _min_eps(h_m); l_m_safe = _min_eps(l_m)
    s_m_safe = _min_eps(s_m); t_m_safe = _min_eps(t_m)
    # 为槽尺寸加入微缩因子，避免与基体面完全共面导致布尔不稳定
    shrink_s = nodes.new("ShaderNodeMath"); shrink_s.operation = 'MULTIPLY'; shrink_s.inputs[1].default_value = 0.999
    links.new(s_m_safe, shrink_s.inputs[0])
    shrink_t = nodes.new("ShaderNodeMath"); shrink_t.operation = 'MULTIPLY'; shrink_t.inputs[1].default_value = 0.999
    links.new(t_m_safe, shrink_t.inputs[0])

    # 基础立方体作为实体，使用 Transform 的 Scale 进行非均匀缩放以适配 3.5/4.x
    cube = nodes.new("GeometryNodeMeshCube"); cube.location = (-300, 100)
    trans_base = nodes.new("GeometryNodeTransform"); trans_base.location = (-150, 100)
    links.new(cube.outputs[0], trans_base.inputs[0])
    combine_size = nodes.new("ShaderNodeCombineXYZ"); combine_size.location = (-450, 100)
    links.new(w_m_safe, combine_size.inputs[0])
    links.new(h_m_safe, combine_size.inputs[1])
    links.new(l_m_safe, combine_size.inputs[2])
    scale_socket = _find_input_socket(trans_base, "Scale", "NodeSocketVector")
    if scale_socket:
        links.new(combine_size.outputs[0], scale_socket)

    # 槽口与布尔差集（在后台模式中，部分节点可能不稳定，加入保护）
    try:
        def make_slot(dx, dy, y_offset):
            slot_cube = nodes.new("GeometryNodeMeshCube"); slot_cube.location = (-300, y_offset)
            size = nodes.new("ShaderNodeCombineXYZ"); size.location = (-450, y_offset)
            links.new(l_m, size.inputs[2])
            links.new(shrink_s.outputs[0], size.inputs[0])
            links.new(shrink_t.outputs[0], size.inputs[1])
            # 与基体一致，用 Transform 的 Scale 进行非均匀缩放，避免 Size 输入差异
            trans_size = nodes.new("GeometryNodeTransform"); trans_size.location = (-225, y_offset)
            links.new(slot_cube.outputs[0], trans_size.inputs[0])
            scale_sock = _find_input_socket(trans_size, "Scale", "NodeSocketVector")
            if scale_sock:
                links.new(size.outputs[0], scale_sock)

            trans = nodes.new("GeometryNodeTransform"); trans.location = (-75, y_offset)
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

            links.new(trans_size.outputs[0], trans.inputs[0])
            links.new(sx.outputs[0], join.inputs[0]); links.new(sy.outputs[0], join.inputs[1])
            trans_socket = _find_input_socket(trans, "Translation", "NodeSocketVector")
            if trans_socket:
                links.new(join.outputs[0], trans_socket)
            return trans.outputs[0]

        s1 = make_slot(+1, 0, -200)
        s2 = make_slot(-1, 0, -260)
        s3 = make_slot(0, +1, -320)
        s4 = make_slot(0, -1, -380)

        # 链式合并四个槽几何，避免 JoinGeometry 多输入兼容问题
        join1 = nodes.new("GeometryNodeJoinGeometry"); join1.location = (-100, -160)
        # 动态插槽：始终连接到 inputs[0]，Blender 会自动扩展插槽
        links.new(s1, join1.inputs[0])
        links.new(s2, join1.inputs[0])
        join2 = nodes.new("GeometryNodeJoinGeometry"); join2.location = (0, -160)
        links.new(join1.outputs[0], join2.inputs[0])
        links.new(s3, join2.inputs[0])
        join3 = nodes.new("GeometryNodeJoinGeometry"); join3.location = (100, -160)
        links.new(join2.outputs[0], join3.inputs[0])
        links.new(s4, join3.inputs[0])

        # 可选：Realize 保证布尔稳定（不同版本对实例的处理差异）
        try:
            realize = nodes.new("GeometryNodeRealizeInstances"); realize.location = (250, -160)
            links.new(join3.outputs[0], realize.inputs[0])
            slots_geo = realize.outputs[0]
        except Exception:
            slots_geo = join3.outputs[0]

        # 兼容不同 Blender 版本的布尔节点类型
        try:
            boolean = nodes.new("GeometryNodeMeshBoolean")
        except Exception:
            boolean = nodes.new("GeometryNodeBoolean")
        boolean.location = (150, 0)
        boolean.operation = 'DIFFERENCE'
        # 尝试使用更稳定的求解器
        try:
            boolean.solver = 'EXACT'
        except Exception:
            pass
        links.new(trans_base.outputs[0], boolean.inputs[0])
        links.new(slots_geo, boolean.inputs[1])
        links.new(boolean.outputs[0], out.inputs[0])
    except Exception as e:
        print(f"[AluFrame] GN 槽口/布尔构建失败，退回为实心立方体：{e}")
        links.new(cube.outputs[0], out.inputs[0])
    return ng


def add_profile_object(context, item, location=(0.0, 0.0, 0.0)):
    """创建并链接一个带槽的型材网格（Mesh布尔差集构造，避免GN兼容问题）。
    若布尔失败，将回退为实心立方体。
    """
    # 1. 创建基体 Mesh（回退几何：实心立方体）
    mesh = bpy.data.meshes.new(name=f"AluFrameMesh_{item.name}")
    try:
        w2 = float(item.width) / 2000.0
        h2 = float(item.height) / 2000.0
        l2 = float(item.default_length) / 2000.0

        verts = [
            (-w2, -h2, -l2), (w2, -h2, -l2), (w2, h2, -l2), (-w2, h2, -l2),
            (-w2, -h2, l2), (w2, -h2, l2), (w2, h2, l2), (-w2, h2, l2)
        ]
        faces = [
            (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
            (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)
        ]

        mesh.from_pydata(verts, [], faces)
        mesh.update(calc_edges=True)
    except Exception as e:
        print(f"[AluFrame] CRITICAL: Fallback mesh creation failed: {e}")
        bpy.data.meshes.remove(mesh)
        return None

    # 2. 用创建好的 Mesh 创建 Object
    obj = bpy.data.objects.new(name=f"AluProfile_{item.name}", object_data=mesh)
    obj.location = location

    # 3. 链接到场景并设为活动
    try:
        (context.collection or context.scene.collection).objects.link(obj)
        obj.select_set(True)
        context.view_layer.objects.active = obj
    except Exception as e:
        print(f"[AluFrame] Linking object to scene failed: {e}")
        bpy.data.objects.remove(obj) # 清理失败的对象
        return None

    # 4. 添加自定义属性（后续用于手动添加 GN）
    obj["alu_type"] = item.name
    obj["standard"] = item.standard
    obj["series"] = item.series
    obj["length"] = float(item.default_length)

    # 5. 构造槽几何并添加布尔修饰器（Mesh级布尔，更稳健）
    try:
        s = float(item.slot_width) / 1000.0
        t = float(item.wall_thickness) / 1000.0
        L = float(item.default_length) / 1000.0

        # 微缩以避免与基体共面
        s *= 0.999
        t *= 0.999

        slots_mesh = bpy.data.meshes.new(name=f"AluFrameSlots_{item.name}")
        verts = []
        faces = []

        def add_box(cx, cy, sx, sy, sz):
            base = len(verts)
            vx = sx / 2.0; vy = sy / 2.0; vz = sz / 2.0
            verts.extend([
                (cx - vx, cy - vy, -vz), (cx + vx, cy - vy, -vz), (cx + vx, cy + vy, -vz), (cx - vx, cy + vy, -vz),
                (cx - vx, cy - vy,  vz), (cx + vx, cy - vy,  vz), (cx + vx, cy + vy,  vz), (cx - vx, cy + vy,  vz),
            ])
            faces.extend([
                (base+0, base+1, base+2, base+3), (base+4, base+7, base+6, base+5), (base+0, base+4, base+5, base+1),
                (base+1, base+5, base+6, base+2), (base+2, base+6, base+7, base+3), (base+3, base+7, base+4, base+0),
            ])

        # 槽位置（沿 Z 方向贯穿）
        add_box(+ (w2 - t/2.0), 0.0, s, t, 2.0*l2)  # 右侧槽
        add_box(- (w2 - t/2.0), 0.0, s, t, 2.0*l2)  # 左侧槽
        add_box(0.0, + (h2 - t/2.0), t, s, 2.0*l2)  # 上侧槽
        add_box(0.0, - (h2 - t/2.0), t, s, 2.0*l2)  # 下侧槽

        slots_mesh.from_pydata(verts, [], faces)
        slots_mesh.update(calc_edges=True)

        slots_obj = bpy.data.objects.new(name=f"AluSlots_{item.name}", object_data=slots_mesh)
        slots_obj.location = location
        (context.collection or context.scene.collection).objects.link(slots_obj)
        # 使其不影响选择与视图杂乱
        try:
            slots_obj.display_type = 'WIRE'
            slots_obj.hide_select = True
        except Exception:
            pass

        # 添加布尔修饰器
        bool_mod = obj.modifiers.new(name="AluFrameGroove", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = slots_obj
        try:
            bool_mod.solver = 'EXACT'
        except Exception:
            pass
        # 标记：本对象已通过Mesh布尔生成槽
        obj["alu_grooved_bmesh"] = True
    except Exception as e:
        print(f"[AluFrame] Mesh布尔槽构造失败：{e}")
        # 失败时仅保留实心立方体
        obj["alu_grooved_bmesh"] = False

    return obj