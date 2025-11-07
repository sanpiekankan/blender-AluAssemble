import bpy

from .profile_library import ALUFRAME_PT_profile_library, ALUFRAME_UL_profiles
from .property_panel import ALUFRAME_PT_property_panel


classes = (
    ALUFRAME_UL_profiles,
    ALUFRAME_PT_profile_library,
    ALUFRAME_PT_property_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)