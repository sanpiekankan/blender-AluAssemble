import bpy
from bpy.types import Operator
from bpy_extras import view3d_utils

from ..gn import add_profile_object


class ALUFRAME_OT_add_selected_profile(Operator):
    bl_idname = "aluframe.add_selected_profile"
    bl_label = "添加选中型材"
    bl_description = "在原点生成默认长度的型材"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        idx = scene.aluframe_profiles_index
        if idx < 0 or idx >= len(scene.aluframe_profiles):
            self.report({'WARNING'}, '请先选择型材')
            return {'CANCELLED'}
        item = scene.aluframe_profiles[idx]
        add_profile_object(context, item, location=(0.0, 0.0, 0.0))
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
                add_profile_object(context, item, location=location)
                self.report({'INFO'}, f"已添加型材：{item.name}")
            else:
                self.report({'WARNING'}, '请先选择型材')

            context.window.cursor_modal_restore()
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        context.window.cursor_modal_set('CROSSHAIR')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}