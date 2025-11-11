import bpy


def ensure_workspace():
    """创建或激活自定义工作台 'AluFrame'（占位实现）。

    说明：为了兼容不同版本与用户当前布局，此处采用复制当前工作台并重命名的方式。
    后续迭代将按“三栏式布局（左/中/右）”进行更精细的 Area 拆分。
    """
    win = bpy.context.window
    if win is None:
        return

    target_name = "AluFrame"
    ws = None
    for w in bpy.data.workspaces:
        if w.name == target_name:
            ws = w
            break

    if ws is None:
        try:
            ws = bpy.context.workspace.copy()
            ws.name = target_name
        except Exception as e:
            print(f"[AluFrame] 工作台创建失败：{e}")
            return

    # 切换到 AluFrame 工作台（若失败则静默）
    try:
        win.workspace = ws
    except Exception:
        pass


def set_units_millimeters_deferred():
    """将场景单位设置为毫米（兼容 3.5/4.x），在 scene 可用时执行。

    - system 统一设为 METRIC
    - 若支持 length_unit，则设为 MILLIMETERS
    - 统一将 scale_length 设为 0.001（1 BU = 1mm），确保旧版本表现一致
    """

    def _apply():
        try:
            scene = getattr(bpy.context, 'scene', None)
            if scene is None and len(bpy.data.scenes) > 0:
                scene = bpy.data.scenes[0]
            if scene is None:
                return 0.25

            us = scene.unit_settings
            try:
                us.system = 'METRIC'
            except Exception:
                pass
            if hasattr(us, 'length_unit'):
                try:
                    us.length_unit = 'MILLIMETERS'
                except Exception:
                    pass
            try:
                us.scale_length = 0.001
            except Exception:
                pass
            return None  # 完成后停止计时器
        except Exception:
            return 0.25

    try:
        bpy.app.timers.register(_apply)
    except Exception:
        # 老版本若无 timers.register，则静默跳过
        pass