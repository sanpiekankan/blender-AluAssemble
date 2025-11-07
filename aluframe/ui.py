import bpy


def draw_aluframe_header(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.label(text="AluFrame")
    row.operator("aluframe.new_profile", text="新建型材")
    row.operator("aluframe.delete_selected", text="删除选中")
    row.operator("ed.undo", text="撤销")
    row.operator("ed.redo", text="重做")
    row.operator("aluframe.export_bom", text="导出BOM")
    # 快捷：添加当前选中型材
    row.operator("aluframe.add_selected_profile", text="添加当前型材")


def register():
    try:
        bpy.types.VIEW3D_HT_header.append(draw_aluframe_header)
    except Exception as e:
        print(f"[AluFrame] Header UI 注册失败：{e}")


def unregister():
    try:
        bpy.types.VIEW3D_HT_header.remove(draw_aluframe_header)
    except Exception:
        pass