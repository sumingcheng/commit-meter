from app.models.github_analyzer import GitHubOvertimeAnalyzer
from app.models.github_client import GitHubClient
import pytz
import logging

logger = logging.getLogger(__name__)

def get_github_repos(access_token):
    """获取用户的GitHub仓库列表"""
    try:
        client = GitHubClient(access_token)
        repos = client.fetch_user_repos()
        client.close()
        
        # 格式化仓库信息
        repo_list = []
        for repo in repos:
            repo_info = {
                "full_name": repo["full_name"],
                "name": repo["name"],
                "description": repo.get("description", "无描述"),
                "updated_at": repo["updated_at"],
                "private": repo["private"]
            }
            repo_list.append(repo_info)
        
        return repo_list
    except Exception as e:
        logger.error(f"获取GitHub仓库列表出错: {e}")
        raise

def analyze_github_overtime(access_token, author_email, year, selected_repos, work_start_hour=9, work_end_hour=18):
    """分析GitHub仓库的加班情况"""
    try:
        analyzer = GitHubOvertimeAnalyzer(
            access_token=access_token,
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
        logger.error(f"GitHub分析过程发生错误: {e}")
        raise
    finally:
        if 'analyzer' in locals():
            analyzer.close() 