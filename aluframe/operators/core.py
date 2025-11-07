import bpy


class ALUFRAME_OT_new_profile(bpy.types.Operator):
    bl_idname = "aluframe.new_profile"
    bl_label = "新建型材"
    bl_description = "创建占位型材对象（默认长度 1000mm）"
    bl_options = {"REGISTER", "UNDO"}

    length_mm: bpy.props.FloatProperty(
        name="长度 (mm)",
        default=1000.0,
        min=50.0,
        max=3000.0,
        description="占位型材长度，后续将由几何节点精确生成",
    )

    def execute(self, context):
        # 使用 20mm 边长立方体作为占位截面，并沿 X 方向按长度缩放
        bpy.ops.mesh.primitive_cube_add(size=0.02)
        obj = context.active_object
        if obj is None:
            self.report({"ERROR"}, "创建占位型材失败")
            return {"CANCELLED"}

        obj.name = "AluProfile"
        # 绑定自定义属性（占位值）
        obj["alu_type"] = "placeholder"
        obj["standard"] = "GB/EN"
        obj["length"] = float(self.length_mm)
        obj["material"] = "Aluminium"

        # 将 20mm 立方体沿 X 方向按长度缩放，近似为一段型材
        # length_mm / 20mm 作为缩放倍数
        obj.scale.x = max(self.length_mm / 20.0, 0.1)

        self.report({"INFO"}, f"已创建占位型材，长度 {self.length_mm:.1f} mm")
        return {"FINISHED"}


class ALUFRAME_OT_delete_selected(bpy.types.Operator):
    bl_idname = "aluframe.delete_selected"
    bl_label = "删除选中"
    bl_description = "删除当前选中的对象"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not context.selected_objects:
            self.report({"WARNING"}, "无选中对象")
            return {"CANCELLED"}
        try:
            bpy.ops.object.delete(use_global=False)
        except Exception as e:
            self.report({"ERROR"}, f"删除失败：{e}")
            return {"CANCELLED"}
        return {"FINISHED"}


class ALUFRAME_OT_export_bom(bpy.types.Operator):
    bl_idname = "aluframe.export_bom"
    bl_label = "导出 BOM"
    bl_description = "占位：统计场景中含长度属性的对象数量与总长度"
    bl_options = {"REGISTER"}

    def execute(self, context):
        count = 0
        total_len = 0.0
        for obj in context.scene.objects:
            if "length" in obj:
                count += 1
                try:
                    total_len += float(obj["length"])
                except Exception:
                    pass
        self.report({"INFO"}, f"占位：已统计 {count} 根型材，总长度 {total_len:.1f} mm")
        return {"FINISHED"}