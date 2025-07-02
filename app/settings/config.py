import os
import pytz
import matplotlib.pyplot as plt
from matplotlib import font_manager


class Config:
    # 默认值配置
    DEFAULT_BASE_URL = 'https://gitlabcode.com/api/v4'
    DEFAULT_LOCAL_TZ = 'Asia/Shanghai'
    DEFAULT_DATABASE_PATH = 'overtime_analysis.db'
    DEFAULT_ANALYSIS_YEAR = 2024

    @classmethod
    def get_access_token(cls):
        return os.getenv('ACCESS_TOKEN')

    @classmethod 
    def get_base_url(cls):
        return os.getenv('BASE_URL', cls.DEFAULT_BASE_URL)

    @classmethod
    def get_local_tz(cls):
        tz_name = os.getenv('LOCAL_TZ', cls.DEFAULT_LOCAL_TZ)
        return pytz.timezone(tz_name)

    @classmethod
    def get_database_path(cls):
        return os.getenv('DATABASE_PATH', cls.DEFAULT_DATABASE_PATH)

    @classmethod
    def get_author_email(cls):
        return os.getenv('AUTHOR_EMAIL')

    @classmethod
    def get_analysis_year(cls):
        try:
            return int(os.getenv('ANALYSIS_YEAR', cls.DEFAULT_ANALYSIS_YEAR))
        except (ValueError, TypeError):
            return cls.DEFAULT_ANALYSIS_YEAR

    # 向后兼容的属性
    @property
    def ACCESS_TOKEN(self):
        return self.get_access_token()
    
    @property 
    def BASE_URL(self):
        return self.get_base_url()
    
    @property
    def LOCAL_TZ(self):
        return self.get_local_tz()
    
    @property
    def DATABASE_PATH(self):
        return self.get_database_path()
    
    @property
    def AUTHOR_EMAIL(self):
        return self.get_author_email()
    
    @property
    def ANALYSIS_YEAR(self):
        return self.get_analysis_year()

    @classmethod
    def setup_matplotlib_font(cls):
        """设置matplotlib中文字体"""
        try:
            # Windows字体路径
            font_path = 'C:\\Windows\\Fonts\\msyh.ttc'  # Microsoft YaHei
            if os.path.exists(font_path):
                font_prop = font_manager.FontProperties(fname=font_path)
                plt.rcParams['font.family'] = font_prop.get_name()
            else:
                # 如果没有找到微软雅黑，尝试其他中文字体
                plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            # 如果字体设置失败，使用默认字体
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

# 初始化字体设置
Config.setup_matplotlib_font()
