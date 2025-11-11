import bpy

bl_info = {
    "name": "AluFrame",
    "author": "Simon Li / AluFrame contributors",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Header / Sidebar",
    "description": "铝型材搭建插件的基础框架（迭代 1：基础框架搭建）",
    "category": "3D View",
}


def register():
    from . import operators, panels, handlers, workspace, ui, data, gn

    data.register()
    operators.register()
    panels.register()
    handlers.register()
    ui.register()

    # 尝试创建并切换到 AluFrame 工作台（非强制，失败不影响启用）
    try:
        workspace.ensure_workspace()
    except Exception as e:
        print(f"[AluFrame] 工作台初始化跳过：{e}")

    # 将场景单位设置为毫米（延迟执行，确保 scene 可用）
    try:
        workspace.set_units_millimeters_deferred()
    except Exception as e:
        print(f"[AluFrame] 单位设置跳过：{e}")


def unregister():
    from . import operators, panels, handlers, ui, data

    # 反向注销，避免依赖残留
    try:
        ui.unregister()
    except Exception:
        pass
    try:
        handlers.unregister()
    except Exception:
        pass
    try:
        panels.unregister()
    except Exception:
        pass
    try:
        operators.unregister()
    except Exception:
        pass
    try:
        data.unregister()
    except Exception:
        pass