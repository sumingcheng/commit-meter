import requests
import datetime
import pytz
import sqlite3
from journal.logger_setup import logger
from typing import List, Dict, Any
from urllib.parse import quote

from app.config.main import Config
from app.gitlab.constant import REPOSITORY_URLS


class OvertimeAnalyzer:
    def __init__(
            self,
            access_token: str,
            base_url: str,
            database_path: str,
            local_tz: pytz.timezone,
            repository_urls: List[str],
            author_email: str,
            year: int
    ):
        self.access_token = access_token
        self.base_url = base_url
        self.database_path = database_path
        self.local_tz = local_tz
        self.repository_urls = repository_urls
        self.author_email = author_email
        self.year = year
        self.conn = self.setup_database()
        self.session = self.create_session()
        self.repositories = self.get_repositories_info()  # 获取仓库的 ID 和名称

    def create_session(self) -> requests.Session:
        """创建带有必要头部信息的请求会话。"""
        session = requests.Session()
        session.headers.update({'PRIVATE-TOKEN': self.access_token})
        return session

    def setup_database(self) -> sqlite3.Connection:
        """创建或连接数据库，并建立所需的表结构。"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Overtime (
                repository_id TEXT,
                repository_name TEXT,
                branch TEXT,
                date TEXT,
                weekday TEXT,
                last_commit_time TEXT,
                hours_worked INTEGER,  
                last_commit_message TEXT,
                author_email TEXT, 
                commit_hash TEXT, 
                PRIMARY KEY (repository_id, branch, date)
            )
        ''')
        conn.commit()
        return conn

    def get_repositories_info(self) -> List[Dict[str, Any]]:
        """根据仓库的 URL 获取仓库的 ID 和名称。"""
        repositories = []
        for url in self.repository_urls:
            project_info = self.fetch_project_info(url)
            if project_info:
                repositories.append(project_info)
        return repositories

    def fetch_project_info(self, repo_url: str) -> Dict[str, Any]:
        """从 GitLab API 获取仓库的项目 ID 和名称。"""
        try:
            # 提取仓库的路径，例如 'vnet/datainfra/aiproject/applications/fastgpt-group/fastgpt48'
            # 如果仓库 URL 以 '/' 开头，移除它
            project_path = repo_url.lstrip('/')

            # 对路径进行 URL 编码，包括斜杠
            encoded_path = quote(project_path, safe='')  # 不保留任何特殊字符

            url = f"{self.base_url}/projects/{encoded_path}"
            response = self.session.get(url)
            if response.status_code == 200:
                project_data = response.json()
                return {
                    'id': project_data['id'],
                    'name': project_data['name'],
                    'path_with_namespace': project_data['path_with_namespace']
                }
            else:
                logger.error(f"无法获取项目信息，状态码: {response.status_code}, URL: {url}")
                logger.error(f"响应内容: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"获取项目信息时出错: {e}")
            return {}

    def fetch_branches(self, project_id: str) -> List[str]:
        """获取特定仓库的所有分支。"""
        url = f"{self.base_url}/projects/{project_id}/repository/branches"
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                logger.error(f"无法获取项目 {project_id} 的分支。状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return []
            branches = response.json()
            return [branch['name'] for branch in branches]
        except requests.RequestException as e:
            logger.error(f"请求异常: {e}")
            return []

    def fetch_commits(
            self,
            project_id: str,
            branch: str,
            start_date: datetime.datetime,
            end_date: datetime.datetime
    ) -> List[Dict[str, Any]]:
        """从 GitLab 获取特定仓库的提交数据。"""
        url = f"{self.base_url}/projects/{project_id}/repository/commits"
        commits = []
        page = 1
        per_page = 100
        while True:
            params = {
                'since': start_date.isoformat(),
                'until': end_date.isoformat(),
                'per_page': per_page,
                'page': page,
                'ref_name': branch
            }
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                logger.error(f"API 请求失败，状态码: {response.status_code}, URL: {url}")
                break
            page_commits = response.json()
            if not page_commits:
                break
            commits.extend(page_commits)
            if len(page_commits) < per_page:
                break  # 没有更多页面
            page += 1
        return commits

    def parse_commit_time(self, commit_created_at: str) -> datetime.datetime:
        """解析提交的创建时间字符串并转换为本地时区的 datetime 对象。"""
        try:
            # 尝试解析带微秒和时区偏移的日期字符串
            commit_time_utc = datetime.datetime.strptime(
                commit_created_at, '%Y-%m-%dT%H:%M:%S.%f%z'
            )
        except ValueError:
            try:
                # 尝试解析不带微秒但带时区偏移的日期字符串
                commit_time_utc = datetime.datetime.strptime(
                    commit_created_at, '%Y-%m-%dT%H:%M:%S%z'
                )
            except ValueError:
                logger.error(f"无法解析日期字符串: {commit_created_at}")
                return None  # 跳过无法解析的日期
        # 将时间转换为本地时区
        return commit_time_utc.astimezone(self.local_tz)

    def analyze_overtime(self):
        """分析指定年份的多个仓库的加班提交，并保存至数据库，过滤指定的提交人。"""
        start_date = datetime.datetime(self.year, 1, 1, tzinfo=pytz.utc)
        end_date = datetime.datetime(self.year, 12, 31, 23, 59, 59, tzinfo=pytz.utc)
        cursor = self.conn.cursor()

        total_repos = len(self.repositories)
        processed_repos = 0

        logger.info(f"开始分析 {total_repos} 个仓库的加班数据...")

        for repo in self.repositories:
            project_id = repo['id']
            repository_name = repo['name']
            processed_repos += 1
            logger.info(f"正在处理仓库 {processed_repos}/{total_repos}：项目ID {project_id}，名称 {repository_name}")
            branches = self.fetch_branches(str(project_id))
            if not branches:
                logger.warning(f"仓库 {project_id} 没有可用的分支，跳过。")
                continue

            for branch in branches:
                logger.info(f"  处理分支：{branch}")
                commits = self.fetch_commits(str(project_id), branch, start_date, end_date)

                overtime_records = {}

                for commit in commits:
                    # 解析提交时间
                    commit_time_local = self.parse_commit_time(commit['created_at'])
                    if not commit_time_local:
                        continue  # 跳过无法解析的日期

                    if commit['author_email'] != self.author_email:
                        continue

                    weekday = commit_time_local.weekday()
                    hour = commit_time_local.hour

                    # 检查提交是否在加班时间
                    if weekday < 5:
                        # 工作日
                        if hour >= 18:
                            date_key = commit_time_local.date()
                            overtime_records.setdefault(date_key, []).append(commit)
                    else:
                        # 周末
                        date_key = commit_time_local.date()
                        overtime_records.setdefault(date_key, []).append(commit)

                # 记录加班信息
                for date, commits_on_date in overtime_records.items():
                    # 对当天的提交按照时间排序
                    commits_on_date.sort(key=lambda x: self.parse_commit_time(x['created_at']))

                    first_commit_time_local = self.parse_commit_time(commits_on_date[0]['created_at'])
                    last_commit_time_local = self.parse_commit_time(commits_on_date[-1]['created_at'])

                    if not first_commit_time_local or not last_commit_time_local:
                        continue  # 跳过无法解析的日期

                    # 计算加班时长
                    hours_worked = (last_commit_time_local - first_commit_time_local).total_seconds() / 3600

                    # 获取最后一次提交的信息
                    last_commit_message = commits_on_date[-1].get('title', '')
                    last_commit_time_local_str = last_commit_time_local.strftime('%H:%M:%S')

                    # 获取星期几
                    weekday_str = self.get_weekday_str(date.weekday())

                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO Overtime (
                                repository_id, repository_name, branch, date, weekday, last_commit_time, hours_worked, last_commit_message
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            project_id,
                            repository_name,
                            branch,
                            date.isoformat(),
                            weekday_str,
                            last_commit_time_local_str,
                            hours_worked,
                            last_commit_message
                        ))
                        self.conn.commit()
                        logger.info(f"  记录加班数据：{date}（{weekday_str}），加班时长 {hours_worked:.2f} 小时")
                    except sqlite3.DatabaseError as e:
                        logger.error(f"数据库错误: {e}")

        logger.info("全部仓库处理完成，处理成功。")

    def get_weekday_str(self, weekday_int: int) -> str:
        """根据星期的整数表示返回中文字符串表示。"""
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        return weekdays[weekday_int]

    def close(self):
        self.conn.close()
        self.session.close()


if __name__ == "__main__":
    analyzer = OvertimeAnalyzer(
        access_token=Config.ACCESS_TOKEN,
        base_url=Config.BASE_URL,
        database_path=Config.DATABASE_PATH,
        local_tz=Config.LOCAL_TZ,
        repository_urls=REPOSITORY_URLS,  # 使用仓库的 URL 列表
        author_email=Config.AUTHOR_EMAIL,
        year=Config.ANALYSIS_YEAR
    )
    try:
        analyzer.analyze_overtime()
    finally:
        analyzer.close()
