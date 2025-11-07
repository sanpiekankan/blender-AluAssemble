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