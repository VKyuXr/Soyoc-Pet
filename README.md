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

项目中包含了 Live2D 官方的 Hiyori 模型；

如果启动时出现如下错误
   
```
LLVM ERROR: Symbol not found: __svml_cos4_ha
```

请将 `./requirements/svml_dispmd.dll` 文件放置于 `C:/Windows/System32` 文件夹内。
