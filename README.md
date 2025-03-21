# Soyoc-Pet

这是一个基于 live2d-py 的 Live2D 桌面宠物项目，使用 PySide6 绘制用户页面。

## 功能

- 鼠标跟随
- 节奏跟随
- 模型选择
- 待机动画设置
- 点击动画设置

# 使用方法

1. 前提是已经具有 Python 环境；
2. 使用 PowerShell 打开 `install.ps1` 文件进行 Python 依赖安装，也可以按照 `requirements.txt` 手动安装依赖；
3. 使用 `main.py` 启动桌面宠物。

## 注意

本项目中包含了 Live2D 官方的 Hiyori 模型；
本项目包含大量 AI 生成代码。

## 错误信息及解决方案汇总

### 启动错误

如果启动时出现如下错误
   
```
LLVM ERROR: Symbol not found: __svml_cos4_ha
```

请将 `./requirements/svml_dispmd.dll` 文件放置于 `C:/Windows/System32` 文件夹内。

### 音频录制错误

1. 如果音频录制时出现错误，首先桌面右下角打开音量处右键，打开“声音设置”；在“输入”处找到“立体声混音”，启用。在下方测试是否能用。
2. 若不能，在 Windows 菜单处搜索 Realtek Audio Console 并打开。点击左下角“设备高级设置”，设置 Audio Director 为经典模式。
3. 设置完毕。

## 更新记录

### 2025 年 3 月 16 日

1. 修复了设置无法保存到配置文件的问题；
2. 增加了 motion3 文件的读取逻辑，自行实现了动画参数读取，并优化了动画的平滑过度。

### 2025 年 3 月 18 日
1. 修复小 bug，优化部分功能和 GUI；
2. 增加大语言模型 API 调用对话功能。
