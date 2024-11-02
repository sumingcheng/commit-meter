from app.model.overtime_analyzer import OvertimeAnalyzer
from app.gitlab.constant import REPOSITORY_URLS
import pytz

def analyze_and_plot(access_token, base_url, author_email, year):
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
    analyzer.close()
    return chart_path, excel_path
