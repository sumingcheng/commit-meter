import pytz
import datetime
from typing import List, Dict, Any, Optional
from app.utils.logger import logger
from app.models.gitlab_client import GitLabClient
from app.models.database_manager import DatabaseManager
from app.models.overtime_calculator import OvertimeCalculator
from app.models.report_generator import ReportGenerator


class OvertimeAnalyzer:
    """加班分析器主协调器，组合使用各个功能模块"""

    def __init__(
        self,
        access_token: str,
        base_url: str,
        local_tz: pytz.timezone,
        author_email: str,
        year: int,
        selected_repos: Optional[List[str]] = None,
        work_start_hour: int = 9,
        work_end_hour: int = 18,
    ):
        self.local_tz = local_tz
        self.author_emails = [email.strip() for email in author_email.split(",")]
        self.year = year
        self.selected_repos = selected_repos

        # 初始化各个功能模块
        self.gitlab_client = GitLabClient(access_token, base_url)
        self.db_manager = DatabaseManager()
        self.calculator = OvertimeCalculator(local_tz, work_start_hour, work_end_hour)
        self.report_generator = ReportGenerator(self.db_manager)

        # 获取仓库信息
        self.repositories = self._get_repositories_info()

    def _get_repositories_info(self) -> List[Dict[str, Any]]:
        """获取用户可访问的仓库信息"""
        logger.info("获取可访问仓库...")
        all_projects = self.gitlab_client.fetch_user_projects()

        repositories = []
        for project in all_projects:
            # 如果指定了选择的仓库，只处理选中的
            if self.selected_repos:
                if project["path_with_namespace"] not in self.selected_repos:
                    continue

            repositories.append(
                {
                    "id": project["id"],
                    "name": project["name"],
                    "path_with_namespace": project["path_with_namespace"],
                }
            )

        logger.info(f"获取{len(repositories)}个仓库")
        return repositories

    def analyze_overtime(self):
        """分析加班情况的主流程"""
        logger.info("开始分析加班情况...")
        start_date = datetime.datetime(self.year, 1, 1, tzinfo=pytz.utc)
        end_date = datetime.datetime(self.year, 12, 31, 23, 59, 59, tzinfo=pytz.utc)

        for repo in self.repositories:
            project_id = repo["id"]
            repository_name = repo["name"]

            # 获取项目分支
            branches = self.gitlab_client.fetch_branches(str(project_id))
            if not branches:
                continue

            for branch in branches:
                # 获取分支提交记录
                commits = self.gitlab_client.fetch_commits(
                    str(project_id), branch, start_date, end_date
                )

                # 按日期分类提交记录
                overtime_records = self.calculator.categorize_commits_by_date(
                    commits, self.author_emails
                )

                # 处理每日的加班记录
                for date, record in overtime_records.items():
                    commits_on_date = record["commits"]
                    if not commits_on_date:
                        continue

                    # 计算加班时长
                    hours_worked = self.calculator.calculate_overtime_hours(
                        commits_on_date, record["start_time"], record["is_weekend"]
                    )

                    if hours_worked <= 0:
                        continue

                    # 检查重复记录
                    last_commit_hash = commits_on_date[-1].get("id", "")
                    if self.db_manager.check_duplicate_record(last_commit_hash):
                        continue

                    # 创建加班记录
                    overtime_record = self.calculator.create_overtime_record(
                        project_id,
                        repository_name,
                        branch,
                        date,
                        commits_on_date,
                        hours_worked,
                        self.author_emails[0],
                        commit_hash_field="id",  # GitLab使用id字段
                    )

                    # 保存到数据库
                    self.db_manager.insert_overtime_record(overtime_record)

        logger.info("分析完成")

    def create_overtime_chart(self, output_path: str = "overtime_chart.png") -> str:
        """生成加班情况图表"""
        return self.report_generator.create_overtime_chart(output_path)

    def export_to_excel(self, output_path: str = "overtime_data.xlsx") -> str:
        """导出数据为Excel文件"""
        return self.report_generator.export_to_excel(output_path)

    def close(self):
        if hasattr(self, "gitlab_client"):
            self.gitlab_client.close()
        if hasattr(self, "db_manager"):
            self.db_manager.close()
