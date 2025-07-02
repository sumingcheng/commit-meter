from app.models.analyzer import OvertimeAnalyzer
from app.models.gitlab_client import GitLabClient
import pytz
import logging

logger = logging.getLogger(__name__)

def get_gitlab_projects(access_token, base_url):
    try:
        client = GitLabClient(access_token, base_url)
        projects = client.fetch_user_projects()
        client.close()
        
        project_list = []
        for project in projects:
            project_info = {
                "id": project["id"],
                "name": project["name"],
                "path_with_namespace": project["path_with_namespace"],
                "description": project.get("description", "无描述"),
                "last_activity_at": project.get("last_activity_at", ""),
            }
            project_list.append(project_info)
        
        return project_list
    except Exception as e:
        logger.error(f"获取GitLab项目列表失败: {e}")
        raise

def analyze_and_plot(access_token, base_url, author_email, year, selected_repos=None, work_start_hour=9, work_end_hour=18):
    try:
        analyzer = OvertimeAnalyzer(
            access_token=access_token,
            base_url=base_url,
            local_tz=pytz.timezone('Asia/Shanghai'),
            author_email=author_email,
            year=year,
            selected_repos=selected_repos,
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
