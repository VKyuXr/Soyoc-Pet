# 定义脚本的执行策略
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "正在安装依赖..." -ForegroundColor Green

# 检查 pip 是否存在
if (-not (Get-Command pip -ErrorAction SilentlyContinue)) {
    Write-Host "未找到 pip，请确保已安装 Python 和 pip。" -ForegroundColor Red
    Read-Host "按 Enter 键退出..."
    exit 1
}

# 安装依赖
try {
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if ($LASTEXITCODE -eq 0) {
        Write-Host "依赖安装成功！" -ForegroundColor Green
    } else {
        Write-Host "依赖安装失败，请检查错误信息。" -ForegroundColor Red
    }
} catch {
    Write-Host "发生错误：$_" -ForegroundColor Red
}

Read-Host "按 Enter 键退出..."