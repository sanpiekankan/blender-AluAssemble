import bpy


class ALUFRAME_PT_property_panel(bpy.types.Panel):
    bl_idname = "ALUFRAME_PT_property_panel"
    bl_label = "属性 / BOM"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AluFrame'

    def draw(self, context):
        layout = self.layout
        has_sel = getattr(context.scene, "aluframe_has_selection", False)
        if has_sel:
            layout.label(text="选中物体")
        else:
            layout.label(text="请添加型材")