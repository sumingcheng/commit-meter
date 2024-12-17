from app.model.overtime_analyzer import OvertimeAnalyzer
from app.gitlab.constant import REPOSITORY_URLS
import pytz
import logging

logger = logging.getLogger(__name__)

def analyze_and_plot(access_token, base_url, author_email, year):
    try:
        analyzer = OvertimeAnalyzer(
            access_token=access_token,
            base_url=base_url,
            local_tz=pytz.timezone('Asia/Shanghai'),
            repository_urls=REPOSITORY_URLS,
            author_email=author_email,
            year=year
        )
        analyzer.analyze_overtime()
        chart_path = analyzer.create_overtime_chart()
        excel_path = analyzer.export_to_excel()
        return chart_path, excel_path
    except Exception as e:
        logger.error(f"分析过程发生错误: {e}")
        raise
    finally:
        if 'analyzer' in locals():
            analyzer.close()
