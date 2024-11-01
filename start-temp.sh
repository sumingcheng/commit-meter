#!/bin/bash

# 获取脚本所在目录
SHELL_FOLDER=$(cd "$(dirname "$0")"; pwd)
echo "Script directory: $SHELL_FOLDER"

echo "Current PYTHONPATH: $PYTHONPATH"

# 设置环境变量（请根据您的实际情况填写）
export ACCESS_TOKEN = ''
export BASE_URL = 'https://gitlabcode.com/api/v4'
export LOCAL_TZ = pytz.timezone('Asia/Shanghai')  # 设定你所在的时区
export DATABASE_PATH = 'overtime_data.db'  # 数据库文件路径
export AUTHOR_EMAIL = 'xxx@qq.com'  # 指定提交人邮箱
export ANALYSIS_YEAR = 2024  # 分析的年份

# 设置 Python 环境变量
export PYTHONUNBUFFERED=1
export PYTHONPATH=$PYTHONPATH:$SHELL_FOLDER

# 启动 Python 应用
python /app/commit-meter.py
