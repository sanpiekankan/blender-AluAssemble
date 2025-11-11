import bpy
from bpy.types import Operator
from bpy_extras import view3d_utils

from ..gn import add_profile_object, ensure_profile_node_group


class ALUFRAME_OT_add_selected_profile(Operator):
    bl_idname = "aluframe.add_selected_profile"
    bl_label = "添加选中型材"
    bl_description = "在原点生成默认长度的型材"
    bl_options = {"REGISTER", "UNDO"}

    def _compute_view_center_location(self, context, distance=1.0):
        """获取当前布局中第一个 3D 视图的中心位置前方 `distance` 米。
        若失败则退回到 3D 游标位置。
        """
        try:
            win = context.window
            if win and win.screen:
                for area in win.screen.areas:
                    if area.type == 'VIEW_3D':
                        region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                        rv3d = area.spaces.active.region_3d if area.spaces.active else None
                        if region and rv3d:
                            coord = (region.width // 2, region.height // 2)
                            origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
                            direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
                            return origin + direction * distance
        except Exception:
            pass
        return context.scene.cursor.location.copy()

    def execute(self, context):
        scene = context.scene
        idx = scene.aluframe_profiles_index
        if idx < 0 or idx >= len(scene.aluframe_profiles):
            self.report({'WARNING'}, '请先选择型材')
            return {'CANCELLED'}
        item = scene.aluframe_profiles[idx]
        location = self._compute_view_center_location(context, distance=1.0)
        
        # 步骤 1: 创建一个带回退网格的普通对象
        obj = add_profile_object(context, item, location=location)

        if not obj:
            self.report({'ERROR'}, "创建基础对象失败，请检查控制台报错")
            return {'CANCELLED'}

        # 步骤 2: 若对象已通过Mesh布尔生成槽，则跳过GN；否则尝试添加几何节点
        if getattr(obj, 'get', lambda k, d=None: None)('alu_grooved_bmesh', False):
            self.report({'INFO'}, f"已添加型材：{item.name}（Mesh布尔构造）")
            return {'FINISHED'}
        try:
            ng = ensure_profile_node_group()
            mod = obj.modifiers.new(name="AluFrameProfile", type='NODES')
            mod.node_group = ng

            def _set_input(modifier, group, name, value):
                # 优先按名称设置（Blender 4.x）
                try:
                    modifier[name] = float(value)
                    return
                except Exception:
                    pass
                # 退回到按接口顺序映射 Input_N（Blender 3.x）
                idx = None
                try:
                    for i, sock in enumerate(getattr(group, 'inputs', [])):
                        if sock.name == name:
                            idx = i + 1  # Input_N 为 1 基
                            break
                except Exception:
                    idx = None
                if idx is not None:
                    try:
                        modifier[f"Input_{idx}"] = float(value)
                    except Exception:
                        pass

            _set_input(mod, ng, "Width", item.width)
            _set_input(mod, ng, "Height", item.height)
            _set_input(mod, ng, "SlotWidth", item.slot_width)
            _set_input(mod, ng, "WallThickness", item.wall_thickness)
            _set_input(mod, ng, "Length", item.default_length)

            # 评估几何节点输出是否为空，如为空则移除修饰器回退到立方体
            try:
                depsgraph = context.evaluated_depsgraph_get()
                obj_eval = obj.evaluated_get(depsgraph)
                mesh_eval = getattr(obj_eval, "data", None)
                poly_count = getattr(mesh_eval, "polygons", None)
                totpoly = getattr(mesh_eval, "totpoly", 0) if mesh_eval else 0
                totvert = getattr(mesh_eval, "totvert", 0) if mesh_eval else 0
                if (poly_count is not None and len(poly_count) == 0) or totpoly == 0 or totvert == 0:
                    # 输出为空，移除几何节点修饰器，保留回退立方体
                    obj.modifiers.remove(mod)
                    self.report({'WARNING'}, "几何节点输出为空，已回退到立方体")
                    return {'FINISHED'}
            except Exception:
                # 评估失败不致命，继续保留已创建对象
                pass

        except Exception as e:
            self.report({'WARNING'}, f"成功创建基础立方体，但应用几何节点失败: {e}")
            # 即使失败，基础对象依然存在，所以返回 FINISHED
            return {'FINISHED'}

        self.report({'INFO'}, f"已添加型材：{item.name}")
        return {'FINISHED'}


class ALUFRAME_OT_drag_add_profile(Operator):
    bl_idname = "aluframe.drag_add_profile"
    bl_label = "拖拽添加型材"
    bl_description = "拖拽结束位置生成型材"
    bl_options = {"REGISTER", "UNDO"}

    _start = None

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}
        if event.type in {'LEFTMOUSE'} and event.value == 'RELEASE':
            # 计算 3D 位置，若失败则退回 3D 游标
            region = context.region
            rv3d = context.region_data
            coord = (event.mouse_region_x, event.mouse_region_y)

            cursor_loc = context.scene.cursor.location.copy()
            try:
                # 使用视图原点+朝向估计
                origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
                direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
                location = origin + direction * 1.0  # 简单前方一米
            except Exception:
                location = cursor_loc

            scene = context.scene
            idx = scene.aluframe_profiles_index
            if 0 <= idx < len(scene.aluframe_profiles):
                item = scene.aluframe_profiles[idx]
                obj = add_profile_object(context, item, location=location)
                if not obj:
                    self.report({'ERROR'}, "创建基础对象失败，请检查控制台报错")
                else:
                    # 已通过Mesh布尔生成槽则直接完成
                    if getattr(obj, 'get', lambda k, d=None: None)('alu_grooved_bmesh', False):
                        self.report({'INFO'}, f"已添加型材：{item.name}（Mesh布尔构造）")
                    else:
                        # 尝试应用几何节点，若输出为空则回退
                        try:
                            ng = ensure_profile_node_group()
                            mod = obj.modifiers.new(name="AluFrameProfile", type='NODES')
                            mod.node_group = ng

                            def _set_input(modifier, group, name, value):
                                try:
                                    modifier[name] = float(value)
                                    return
                                except Exception:
                                    pass
                                idx = None
                                try:
                                    for i, sock in enumerate(getattr(group, 'inputs', [])):
                                        if sock.name == name:
                                            idx = i + 1
                                            break
                                except Exception:
                                    idx = None
                                if idx is not None:
                                    try:
                                        modifier[f"Input_{idx}"] = float(value)
                                    except Exception:
                                        pass

                            _set_input(mod, ng, "Width", item.width)
                            _set_input(mod, ng, "Height", item.height)
                            _set_input(mod, ng, "SlotWidth", item.slot_width)
                            _set_input(mod, ng, "WallThickness", item.wall_thickness)
                            _set_input(mod, ng, "Length", item.default_length)

                        except Exception as e:
                            self.report({'WARNING'}, f"成功创建基础立方体，但应用几何节点失败: {e}")
                        else:
                            # 评估几何节点输出是否为空，如为空则移除修饰器回退到立方体
                            try:
                                depsgraph = context.evaluated_depsgraph_get()
                                obj_eval = obj.evaluated_get(depsgraph)
                                mesh_eval = getattr(obj_eval, "data", None)
                                poly_count = getattr(mesh_eval, "polygons", None)
                                totpoly = getattr(mesh_eval, "totpoly", 0) if mesh_eval else 0
                                totvert = getattr(mesh_eval, "totvert", 0) if mesh_eval else 0
                                if (poly_count is not None and len(poly_count) == 0) or totpoly == 0 or totvert == 0:
                                    obj.modifiers.remove(mod)
                                    self.report({'WARNING'}, "几何节点输出为空，已回退到立方体")
                                else:
                                    self.report({'INFO'}, f"已添加型材：{item.name}")
                            except Exception:
                                # 评估失败不致命
                                self.report({'INFO'}, f"已添加型材：{item.name}")
                            ng = ensure_profile_node_group()
                            mod = obj.modifiers.new(name="AluFrameProfile", type='NODES')
                            mod.node_group = ng

                            def _set_input(modifier, group, name, value):
                                try:
                                    modifier[name] = float(value)
                                    return
                                except Exception:
                                    pass
                                idx = None
                                try:
                                    for i, sock in enumerate(getattr(group, 'inputs', [])):
                                        if sock.name == name:
                                            idx = i + 1
                                            break
                                except Exception:
                                    idx = None
                                if idx is not None:
                                    try:
                                        modifier[f"Input_{idx}"] = float(value)
                                    except Exception:
                                        pass

                            _set_input(mod, ng, "Width", item.width)
                            _set_input(mod, ng, "Height", item.height)
                            _set_input(mod, ng, "SlotWidth", item.slot_width)
                            _set_input(mod, ng, "WallThickness", item.wall_thickness)
                            _set_input(mod, ng, "Length", item.default_length)

                        # 评估几何节点输出是否为空，如为空则移除修饰器回退到立方体
                        try:
                            depsgraph = context.evaluated_depsgraph_get()
                            obj_eval = obj.evaluated_get(depsgraph)
                            mesh_eval = getattr(obj_eval, "data", None)
                            poly_count = getattr(mesh_eval, "polygons", None)
                            totpoly = getattr(mesh_eval, "totpoly", 0) if mesh_eval else 0
                            totvert = getattr(mesh_eval, "totvert", 0) if mesh_eval else 0
                            if (poly_count is not None and len(poly_count) == 0) or totpoly == 0 or totvert == 0:
                                obj.modifiers.remove(mod)
                                self.report({'WARNING'}, "几何节点输出为空，已回退到立方体")
                            else:
                                self.report({'INFO'}, f"已添加型材：{item.name}")
                        except Exception:
                            # 评估失败不致命
                            self.report({'INFO'}, f"已添加型材：{item.name}")
                        # 此处应有表达式
                        pass
                        self.report({'WARNING'}, f"成功创建基础立方体，但应用几何节点失败: {e}")
            else:
                self.report({'WARNING'}, '请先选择型材')

            context.window.cursor_modal_restore()
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        context.window.cursor_modal_set('CROSSHAIR')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}