# Soyoc-Pet

一个基于 PySide6 和 live2d-py 的 Live2D 桌面宠物应用,让二次元角色在你的桌面上活起来!

## ✨ 主要特性

- **Live2D 模型渲染**: 支持加载和显示自定义 Live2D 模型
- **智能交互**: 鼠标跟随、点击动画、待机动画,让角色更有生命力
- **音频节奏响应**: 能够检测系统音频节拍,让角色随音乐律动
- **LLM 智能对话**: 集成大语言模型 API(支持 SiliconFlow 等平台),可以和你的宠物聊天
- **灵活配置**: 使用 TOML 配置文件,可实时调整各种参数
- **自动日志**: 内置日志系统,自动记录运行状态并清理旧日志

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8 或更高版本。

### 2. 安装依赖

**方法一:使用安装脚本(推荐)**

在 PowerShell 中运行:
```powershell
.\install.ps1
```

**方法二:手动安装**

```bash
pip install -r requirements.txt
```

### 3. 准备 Live2D 模型

1. 在项目根目录创建 `model` 文件夹
2. 将 Live2D 模型文件放入其中(支持 Cubism 3/4 格式)
3. 修改 `config.toml` 中的 `l2d_model` 路径指向你的模型

> 💡 提示:可以从 [Live2D 官网](https://www.live2d.com/) 或其他资源获取免费模型

### 4. 配置说明

编辑 `config.toml` 文件来定制你的桌面宠物:

```toml
[general]
refresh_rate = 120          # 刷新率(FPS)
l2d_size = [200.0, 600.0]   # 窗口大小[宽, 高]

[l2d]
l2d_model = "./model/hiyori_free_t08"  # 模型路径
auto_breath = "True"        # 自动呼吸
auto_blink = "True"         # 自动眨眼
tracking_sensitivity = 2    # 鼠标跟随灵敏度

[llm]
api_key = ""                # LLM API 密钥
target_platform = "siliconflow"  # AI 平台
target_model = "deepseek-ai/DeepSeek-V3"  # 模型名称
```

### 5. 启动应用

```bash
python main.py
```

运行后会在项目根目录自动创建 `logs` 文件夹存储运行日志。

## 📁 项目结构

```
Soyoc-Pet/
├── main.py                 # 程序入口,包含日志管理系统
├── config.toml             # 配置文件(模型路径、动画设置、LLM API等)
├── requirements.txt        # Python 依赖列表
├── install.ps1            # Windows 一键安装脚本
├── model/                  # Live2D 模型文件夹(需自行创建)
├── logs/                   # 运行日志文件夹(自动生成)
└── Soyoc_core/            # 核心模块
    ├── main_window.py     # 主窗口和 Live2D 渲染逻辑
    ├── config_editor.py   # 配置管理模块
    ├── live2d_manager.py  # Live2D 模型加载和管理
    ├── motion_manager.py  # 动画管理和播放
    ├── physics.py         # ⭐ 自定义物理模拟引擎(独立实现)
    ├── chat_window.py     # LLM 对话界面
    └── Soyoc_utils/       # 工具模块
        ├── audio_analyzer.py  # 音频节拍分析
        └── API_requster.py    # LLM API 调用封装
```

> 💡 **特别说明**: `physics.py` 是我自己实现的物理模拟,用于处理 Live2D 模型的物理效果(如头发、衣摆的自然摆动)。这部分由本项目开发。

## ❓ 常见问题

### 启动时出现 LLVM 错误

如果启动时出现以下错误:
```
LLVM ERROR: Symbol not found: __svml_cos4_ha
```

**解决方法:** 下载 `svml_dispmd.dll` 并将其放置于 `C:/Windows/System32` 文件夹内。

### 音频录制无法使用

如果音频节拍检测功能不工作:

1. 右键点击桌面右下角音量图标,打开"声音设置"
2. 在"输入"处找到"立体声混音",启用它并测试是否正常
3. 如果仍不能使用,搜索并打开 Realtek Audio Console
4. 点击左下角"设备高级设置",将 Audio Director 设置为经典模式
5. 重启应用后再次测试

## 📝 更新记录

### 2025-03-18
- 修复已知问题,优化部分功能和界面体验
- 新增大语言模型 API 对话功能,支持多种 AI 平台

### 2025-03-16
- 修复配置无法保存到文件的问题
- 实现 motion3 文件读取逻辑,优化动画参数解析和平滑过渡效果
