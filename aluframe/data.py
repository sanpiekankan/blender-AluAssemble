import bpy
import json
import os


class AluFrameProfileItem(bpy.types.PropertyGroup):
    uid: bpy.props.StringProperty(name="ID")
    name: bpy.props.StringProperty(name="型号")
    standard: bpy.props.EnumProperty(
        name="标准",
        items=(
            ('GB', '国标', ''),
            ('EN', '欧标', ''),
        ),
    )
    series: bpy.props.StringProperty(name="系列")  # 20/30/40/45 等
    width: bpy.props.FloatProperty(name="宽度(mm)")
    height: bpy.props.FloatProperty(name="高度(mm)")
    slot_width: bpy.props.FloatProperty(name="槽宽(mm)")
    wall_thickness: bpy.props.FloatProperty(name="壁厚(mm)")
    default_length: bpy.props.FloatProperty(name="默认长度(mm)", default=1000.0)


def _profiles_json_path():
    return os.path.join(os.path.dirname(__file__), 'assets', 'profiles.json')


def _ensure_profiles_loaded(scene):
    # 避免重复加载
    if len(scene.aluframe_profiles) > 0:
        return

    path = _profiles_json_path()
    if not os.path.exists(path):
        print(f"[AluFrame] 未找到 profiles.json：{path}")
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[AluFrame] 读取 profiles.json 失败：{e}")
        return

    for item in data:
        it = scene.aluframe_profiles.add()
        it.uid = item.get('id', '')
        it.name = item.get('name', '')
        it.standard = item.get('standard', 'GB')
        it.series = str(item.get('series', ''))
        sp = item.get('section_params', {})
        it.width = float(sp.get('width', 0.0))
        it.height = float(sp.get('height', 0.0))
        it.slot_width = float(sp.get('slot_width', 0.0))
        it.wall_thickness = float(sp.get('wall_thickness', 0.0))
        it.default_length = float(item.get('default_length', 1000.0))


def register():
    # 避免重复注册导致 RuntimeError：already registered as a subclass
    # Blender 3.5 在重复注册时会抛 ValueError；统一处理两种异常
    try:
        # 若已存在同名类型则跳过注册，避免重复
        if not hasattr(bpy.types, 'AluFrameProfileItem'):
            bpy.utils.register_class(AluFrameProfileItem)
    except (RuntimeError, ValueError) as e:
        msg = str(e)
        if 'already registered' in msg:
            pass
        else:
            raise

    # 逐项添加属性（有则跳过），避免重复注册的报错
    if not hasattr(bpy.types.Scene, 'aluframe_profiles'):
        bpy.types.Scene.aluframe_profiles = bpy.props.CollectionProperty(type=AluFrameProfileItem)
    if not hasattr(bpy.types.Scene, 'aluframe_profiles_index'):
        bpy.types.Scene.aluframe_profiles_index = bpy.props.IntProperty(name="型材索引", default=0)
    if not hasattr(bpy.types.Scene, 'aluframe_search'):
        bpy.types.Scene.aluframe_search = bpy.props.StringProperty(name="搜索")
    if not hasattr(bpy.types.Scene, 'aluframe_filter_standard'):
        bpy.types.Scene.aluframe_filter_standard = bpy.props.EnumProperty(
            name="标准过滤",
            items=(('ALL', '全部', ''), ('GB', '国标', ''), ('EN', '欧标', '')),
            default='ALL'
        )
    if not hasattr(bpy.types.Scene, 'aluframe_filter_series'):
        bpy.types.Scene.aluframe_filter_series = bpy.props.EnumProperty(
            name="系列过滤",
            items=(('ALL', '全部', ''), ('20', '20', ''), ('30', '30', ''), ('40', '40', ''), ('45', '45', '')),
            default='ALL'
        )

    # 在 3.5 的插件启用阶段，bpy.context 可能是 _RestrictContext，无法直接访问 scene。
    # 这里不直接加载，而是通过计时器在 scene 可用时再进行一次性加载。
    def _defer_load():
        try:
            scene = getattr(bpy.context, 'scene', None)
            if scene is None:
                # 退化到数据中的第一个场景（若已有）
                if len(bpy.data.scenes) == 0:
                    return 0.25  # 稍后重试
                scene = bpy.data.scenes[0]

            if hasattr(scene, 'aluframe_profiles'):
                _ensure_profiles_loaded(scene)
                return None  # 停止计时器（一次性加载）
            else:
                return 0.25
        except Exception:
            return 0.25

    try:
        bpy.app.timers.register(_defer_load)
    except Exception:
        # 旧版本若无 timers.register，则尽力立即加载（若 scene 可用）
        scene = getattr(bpy.context, 'scene', None)
        if scene is not None and hasattr(scene, 'aluframe_profiles'):
            _ensure_profiles_loaded(scene)


def unregister():
    if hasattr(bpy.types.Scene, 'aluframe_profiles'):
        del bpy.types.Scene.aluframe_profiles
    if hasattr(bpy.types.Scene, 'aluframe_profiles_index'):
        del bpy.types.Scene.aluframe_profiles_index
    if hasattr(bpy.types.Scene, 'aluframe_search'):
        del bpy.types.Scene.aluframe_search
    if hasattr(bpy.types.Scene, 'aluframe_filter_standard'):
        del bpy.types.Scene.aluframe_filter_standard
    if hasattr(bpy.types.Scene, 'aluframe_filter_series'):
        del bpy.types.Scene.aluframe_filter_series

    try:
        bpy.utils.unregister_class(AluFrameProfileItem)
    except Exception:
        pass