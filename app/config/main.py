import os
import pytz


class Config:
    ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')  # 请确保在环境变量中设置
    BASE_URL = os.getenv('BASE_URL', 'https://gitlabcode.com/api/v4')
    LOCAL_TZ = pytz.timezone(os.getenv('LOCAL_TZ', 'Asia/Shanghai'))
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'overtime_data.db')
    AUTHOR_EMAIL = os.getenv('AUTHOR_EMAIL')  # 请确保在环境变量中设置
    ANALYSIS_YEAR = int(os.getenv('ANALYSIS_YEAR', '2024'))

    # 必要的环境变量检查
    required_vars = ['ACCESS_TOKEN', 'AUTHOR_EMAIL']
    for var in required_vars:
        if locals()[var] is None:
            raise ValueError(f"环境变量 {var} 未设置。")
