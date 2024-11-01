# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Script directory: $ScriptDir"

Write-Host "Current PYTHONPATH: $Env:PYTHONPATH"

# 设置环境变量（请根据您的实际情况填写）
$Env:ACCESS_TOKEN = '您的访问令牌'
$Env:BASE_URL = 'https://gitlabcode.com/api/v4'
$Env:DATABASE_PATH = 'overtime_data.db'  # 数据库文件路径
$Env:AUTHOR_EMAIL = '您的邮箱@example.com'  # 指定提交人邮箱
$Env:ANALYSIS_YEAR = '2024'  # 分析的年份

# 设置 Python 环境变量
$Env:PYTHONUNBUFFERED = '1'
$Env:PYTHONPATH = if ($Env:PYTHONPATH) { "$Env:PYTHONPATH;$ScriptDir" } else { $ScriptDir }

# 启动 Python 应用
python "$ScriptDir\app\main.py"
