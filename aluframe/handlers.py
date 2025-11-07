import bpy

_handler_registered = False


def _depsgraph_update(scene, depsgraph):
    # 根据选中状态更新场景级标记，供右侧面板使用
    try:
        selected = [o for o in bpy.context.selected_objects if o.type in {'MESH', 'CURVE', 'EMPTY', 'ARMATURE'}]
        scene.aluframe_has_selection = len(selected) > 0
    except Exception:
        pass


def register():
    global _handler_registered

    if not hasattr(bpy.types.Scene, "aluframe_has_selection"):
        bpy.types.Scene.aluframe_has_selection = bpy.props.BoolProperty(
            name="AluFrame 有选中", default=False
        )

    if _depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_depsgraph_update)
        _handler_registered = True


def unregister():
    global _handler_registered

    if _handler_registered and _depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_depsgraph_update)
        _handler_registered = False

    if hasattr(bpy.types.Scene, "aluframe_has_selection"):
        del bpy.types.Scene.aluframe_has_selection