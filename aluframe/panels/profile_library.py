import bpy
import os


class ALUFRAME_UL_profiles(bpy.types.UIList):
    # 自定义过滤：按搜索文本、标准、系列过滤
    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        helper_filter = []
        helper_order = []
        scene = context.scene
        search = (scene.aluframe_search or '').strip().lower()
        fs = scene.aluframe_filter_standard
        fr = scene.aluframe_filter_series

        for i, it in enumerate(items):
            ok = True
            if fs != 'ALL' and it.standard != fs:
                ok = False
            if fr != 'ALL' and it.series != fr:
                ok = False
            if search:
                if search not in it.name.lower() and search not in it.series.lower():
                    ok = False
            helper_filter.append(self.bitflag_filter_item if ok else 0)
            helper_order.append(i)
        return helper_filter, helper_order

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # 列表行显示：型号名 + 系列/标准
        row = layout.row(align=True)
        row.label(text=item.name)
        row.label(text=f"{item.series} 系列")
        row.label(text="国标" if item.standard == 'GB' else "欧标")


class ALUFRAME_PT_profile_library(bpy.types.Panel):
    bl_idname = "ALUFRAME_PT_profile_library"
    bl_label = "型材库"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AluFrame'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # 顶部搜索与过滤
        row = layout.row(align=True)
        row.prop(scene, 'aluframe_search', text="搜索")
        row = layout.row(align=True)
        row.prop(scene, 'aluframe_filter_standard', text="标准")
        row.prop(scene, 'aluframe_filter_series', text="系列")

        layout.template_list(
            "ALUFRAME_UL_profiles",
            "profiles",
            scene,
            "aluframe_profiles",
            scene,
            "aluframe_profiles_index",
            rows=6,
        )

        # 预览与参数
        idx = scene.aluframe_profiles_index
        if 0 <= idx < len(scene.aluframe_profiles):
            item = scene.aluframe_profiles[idx]
            box = layout.box()
            box.label(text=f"型号：{item.name}（{item.series} 系列，{'国标' if item.standard=='GB' else '欧标'}）")
            box.label(text=f"截面：{item.width:.1f} × {item.height:.1f} mm，槽宽 {item.slot_width:.1f} mm")
            box.label(text=f"壁厚：{item.wall_thickness:.1f} mm，默认长度 {item.default_length:.1f} mm")
            # 截面 PNG 预览（可选）
            try:
                icons_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'section_icons')
                icons_dir = os.path.normpath(icons_dir)
                icon_path = os.path.join(icons_dir, f"{item.uid}.png")
                if os.path.exists(icon_path):
                    img = bpy.data.images.load(icon_path)
                    layout.template_preview(img, show_buttons=False)
                else:
                    box.label(text="截面图：未提供 PNG 图标")
            except Exception:
                box.label(text="截面图载入失败（忽略，不影响功能）")

            row = layout.row(align=True)
            row.operator('aluframe.add_selected_profile')
            row.operator('aluframe.drag_add_profile')
        else:
            layout.label(text="请选择型材以查看详情")