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

迭代 2：型材库与基础建模

- 新增 `assets/profiles.json` 含 10 种核心型材（国标 6 + 欧标 4）
- 左侧面板实现 UIList 列表、搜索（型号/系列）与标准/系列过滤
- 支持“点击添加”和“拖拽添加”，生成 3D 模型并绑定自定义属性
- 通过几何节点组生成矩形截面并在四侧切割槽口，沿 Z 轴拉伸至长度
- `assets/section_icons/` 为截面 PNG 图标目录（目前为占位，缺失时显示参数）