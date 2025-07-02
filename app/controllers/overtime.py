from app.models.analyzer import OvertimeAnalyzer
import pytz
import logging

logger = logging.getLogger(__name__)

def analyze_and_plot(access_token, base_url, author_email, year, work_start_hour=9, work_end_hour=18):
    try:
        analyzer = OvertimeAnalyzer(
            access_token=access_token,
            base_url=base_url,
            local_tz=pytz.timezone('Asia/Shanghai'),
            author_email=author_email,
            year=year,
            work_start_hour=work_start_hour,
            work_end_hour=work_end_hour
        )
        analyzer.analyze_overtime()
        chart_path = analyzer.create_overtime_chart()
        excel_path = analyzer.export_to_excel()
        return chart_path, excel_path
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise
    finally:
        if 'analyzer' in locals():
            analyzer.close()
