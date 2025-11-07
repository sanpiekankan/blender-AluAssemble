"""
Blender 后台烟雾测试：无需安装到偏好设置，验证插件能加载/注册/添加型材并生成几何。

运行方式（Windows 示例）：
  blender --background --python scripts/smoke_blender.py

备注：无需在仓库根目录运行，脚本会自动定位到仓库根（scripts 上一级）。
如需自定义，设置环境变量 REPO_ROOT 指向仓库根。
"""

import sys
import os


def repo_root():
    # 优先使用环境变量；否则按脚本路径的上一级作为仓库根
    env = os.environ.get("REPO_ROOT")
    if env:
        return env
    here = os.path.abspath(os.path.dirname(__file__))
    root = os.path.abspath(os.path.join(here, os.pardir))
    return root


def main():
    root = repo_root()
    addon_dir = os.path.join(root, "aluframe")
    if not os.path.isdir(addon_dir):
        print(f"[Smoke] 未找到插件目录：{addon_dir}")
        return

    # 将“仓库根”加入 sys.path（而不是插件目录），以便 "import aluframe" 作为包导入
    if root not in sys.path:
        sys.path.insert(0, root)

    import bpy  # 由 Blender 提供
    import aluframe

    print("[Smoke] 注册 AluFrame 插件...")
    aluframe.register()

    scene = bpy.context.scene
    profiles = list(scene.aluframe_profiles)
    print(f"[Smoke] 已加载型材数量：{len(profiles)}")
    assert len(profiles) >= 10, "型材 JSON 未正确加载（应≥10）"

    # 找到一个典型型号（优先 GB-4040；否则选第一个）
    idx = 0
    for i, it in enumerate(profiles):
        if it.uid == "GB-4040":
            idx = i
            break
    scene.aluframe_profiles_index = idx

    # 在原点添加型材
    print("[Smoke] 添加选中型材...")
    result = bpy.ops.aluframe.add_selected_profile()
    print(f"[Smoke] 操作结果：{result}")

    # 验证生成对象与属性
    objs = [o for o in scene.objects if "alu_type" in o]
    assert len(objs) >= 1, "场景未发现含 alu_type 属性的对象"
    obj = objs[-1]
    print(f"[Smoke] 生成对象：{obj.name}, 长度：{obj.get('length')} mm")
    assert abs(float(obj.get("length", 0.0)) - float(profiles[idx].default_length)) < 1e-6

    # 尝试保存到临时文件（可选）
    outfile = os.path.join(root, "_smoke_output.blend")
    try:
        bpy.ops.wm.save_as_mainfile(filepath=outfile)
        print(f"[Smoke] 已保存到：{outfile}")
    except Exception as e:
        print(f"[Smoke] 保存失败（忽略）：{e}")

    # 注销插件
    print("[Smoke] 注销 AluFrame 插件...")
    aluframe.unregister()
    print("[Smoke] 测试完成：SUCCESS")


if __name__ == "__main__":
    main()