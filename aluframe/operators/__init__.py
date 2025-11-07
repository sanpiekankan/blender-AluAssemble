import bpy

from .core import (
    ALUFRAME_OT_new_profile,
    ALUFRAME_OT_delete_selected,
    ALUFRAME_OT_export_bom,
)
from .profile_add import (
    ALUFRAME_OT_add_selected_profile,
    ALUFRAME_OT_drag_add_profile,
)


classes = (
    ALUFRAME_OT_new_profile,
    ALUFRAME_OT_delete_selected,
    ALUFRAME_OT_export_bom,
    ALUFRAME_OT_add_selected_profile,
    ALUFRAME_OT_drag_add_profile,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)