import pytz
import datetime
from typing import List, Dict, Any
from app.utils.logger import logger
from app.models.github_client import GitHubClient
from app.models.database_manager import DatabaseManager
from app.models.overtime_calculator import OvertimeCalculator
from app.models.report_generator import ReportGenerator


class GitHubOvertimeAnalyzer:
    """GitHub加班分析器，独立的GitHub分析逻辑"""
    
    def __init__(
        self,
        access_token: str,
        local_tz: pytz.timezone,
        author_email: str,
        year: int,
        selected_repos: List[str],
        work_start_hour: int = 9,
        work_end_hour: int = 18,
    ):
        self.local_tz = local_tz
        self.author_emails = [email.strip() for email in author_email.split(",")]
        self.year = year
        self.selected_repos = selected_repos
        
        # 初始化各个功能模块
        self.github_client = GitHubClient(access_token)
        self.db_manager = DatabaseManager("github_overtime_analysis.db")  # 使用独立的数据库
        self.calculator = OvertimeCalculator(local_tz, work_start_hour, work_end_hour)
        self.report_generator = ReportGenerator(self.db_manager)
    
    def analyze_overtime(self):
        """分析GitHub仓库的加班情况"""
        logger.info("开始分析GitHub加班情况...")
        start_date = datetime.datetime(self.year, 1, 1, tzinfo=pytz.utc)
        end_date = datetime.datetime(self.year, 12, 31, 23, 59, 59, tzinfo=pytz.utc)

        for repo_full_name in self.selected_repos:
            try:
                owner, repo_name = repo_full_name.split("/")
            except ValueError:
                logger.warning(f"无效的仓库名称格式: {repo_full_name}")
                continue
            
            logger.info(f"分析仓库: {repo_full_name}")
            
            # 获取仓库分支
            branches = self.github_client.fetch_branches(owner, repo_name)
            if not branches:
                continue

            for branch in branches:
                # 获取分支提交记录
                commits = self.github_client.fetch_commits(
                    owner, repo_name, branch, start_date, end_date
                )
                
                # 转换提交数据格式以适配计算器
                formatted_commits = self._format_github_commits(commits)
                
                # 按日期分类提交记录
                overtime_records = self.calculator.categorize_commits_by_date(
                    formatted_commits, self.author_emails
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
                    last_commit_hash = commits_on_date[-1].get("sha", "")
                    if self.db_manager.check_duplicate_record(last_commit_hash):
                        logger.warning(f"跳过重复记录: {last_commit_hash}")
                        continue

                    # 创建加班记录
                    overtime_record = self.calculator.create_overtime_record(
                        repo_full_name,
                        repo_name,
                        branch,
                        date,
                        commits_on_date,
                        hours_worked,
                        self.author_emails[0],
                        commit_hash_field="sha"  # GitHub使用sha字段
                    )
                    
                    # 保存到数据库
                    self.db_manager.insert_overtime_record(overtime_record)

        logger.info("GitHub加班分析完成。")
    
    def _format_github_commits(self, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将GitHub提交数据格式转换为通用格式"""
        formatted_commits = []
        for commit in commits:
            try:
                formatted_commit = {
                    "created_at": commit["commit"]["author"]["date"],
                    "author_email": commit["commit"]["author"]["email"],
                    "title": commit["commit"]["message"].split('\n')[0],
                    "sha": commit["sha"]
                }
                formatted_commits.append(formatted_commit)
            except (KeyError, TypeError) as e:
                logger.warning(f"跳过格式异常的提交: {e}")
                continue
        return formatted_commits
    
    def create_overtime_chart(self, output_path: str = "github_overtime_chart.png") -> str:
        """生成GitHub加班情况图表"""
        return self.report_generator.create_overtime_chart(output_path)

    def export_to_excel(self, output_path: str = "github_overtime_data.xlsx") -> str:
        """导出GitHub数据为Excel文件"""
        return self.report_generator.export_to_excel(output_path)

    def close(self):
        """关闭所有资源连接"""
        logger.info("关闭GitHub分析器资源连接...")
        if hasattr(self, "github_client"):
            self.github_client.close()
        if hasattr(self, "db_manager"):
            self.db_manager.close() 