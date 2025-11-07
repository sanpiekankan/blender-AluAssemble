# AluFrame (Blender 铝型材搭建插件)

迭代 1：基础框架搭建

- 插件目录结构：`aluframe/` 包含入口、operators、panels、workspace、handlers、ui、assets
- 支持 Blender 3.6+，在偏好设置中可安装启用
- 顶部工具栏提供 5 个占位按钮：新建型材、删除选中、撤销、重做、导出 BOM
- 右侧面板根据是否选中对象显示提示（“选中物体” / “请添加型材”）

安装步骤：
- 将本仓库打包为 ZIP（包含 `aluframe` 目录）或直接将 `aluframe` 目录复制到 Blender 的 `scripts/addons` 目录
- 在 Blender 中：编辑 > 偏好设置 > 插件 > 安装，选择 ZIP 后启用 AluFrame
- 启用后，顶部工具栏将出现 AluFrame 按钮；侧边栏（N）中出现 AluFrame 标签与两个面板

备注：
- “AluFrame 工作台”当前为占位实现（复制当前工作台并重命名），后续将按三栏布局进行 Area 拆分
- BOM 导出为占位统计，后续将集成 Excel 导出