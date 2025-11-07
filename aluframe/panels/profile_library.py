import bpy


class ALUFRAME_PT_profile_library(bpy.types.Panel):
    bl_idname = "ALUFRAME_PT_profile_library"
    bl_label = "型材库"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AluFrame'

    def draw(self, context):
        layout = self.layout
        layout.label(text="型材库（占位）")
        layout.separator()
        layout.label(text="此处将显示：")
        col = layout.column(align=True)
        col.label(text="- 标准/系列树形结构")
        col.label(text="- 2D/3D 预览")
        col.label(text="- 点击/拖拽添加")