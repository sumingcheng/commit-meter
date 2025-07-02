import pytz
import requests
import datetime
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from urllib.parse import quote
from typing import List, Dict, Any
from app.settings.config import Config
from app.utils.logger import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class OvertimeAnalyzer:
    def __init__(self, access_token: str, base_url: str, local_tz: pytz.timezone,
                 author_email: str, year: int, work_start_hour: int = 9, work_end_hour: int = 18):
        self.access_token = access_token
        self.base_url = base_url
        self.database_path = Config.DATABASE_PATH
        self.local_tz = local_tz
        self.author_emails = [email.strip()
                              for email in author_email.split(',')]
        self.year = year
        self.work_start_hour = work_start_hour
        self.work_end_hour = work_end_hour
        self.conn = self.setup_database()
        self.session = self.create_session()
        self.repositories = self.get_repositories_info()

    def create_session(self) -> requests.Session:
        logger.info("创建会话...")
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.1)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update({'PRIVATE-TOKEN': self.access_token})
        return session

    def setup_database(self) -> sqlite3.Connection:
        logger.info("设置数据库...")
        conn = sqlite3.connect(self.database_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Overtime (
                repository_id TEXT,
                repository_name TEXT,
                branch TEXT,
                date TEXT,
                last_commit_time TEXT,
                hours_worked INTEGER,
                last_commit_message TEXT,
                author_email TEXT,
                commit_hash TEXT,
                PRIMARY KEY (repository_id, branch, date)
            )
        ''')
        conn.commit()
        logger.info("数据库设置完成。")
        return conn

    def get_repositories_info(self) -> List[Dict[str, Any]]:
        logger.info("获取用户可访问的仓库信息...")
        repositories = []
        user_projects = self.fetch_user_projects()
        for project in user_projects:
            repositories.append({
                'id': project['id'],
                'name': project['name'],
                'path_with_namespace': project['path_with_namespace']
            })
            logger.info(f"获取项目信息: {project['name']}")
        logger.info(f"共获取到 {len(repositories)} 个可访问的仓库")
        return repositories

    def fetch_user_projects(self) -> List[Dict[str, Any]]:
        """动态获取用户有权限访问的所有项目"""
        logger.info("动态获取用户项目列表...")
        projects = []
        page = 1
        per_page = 100
        
        while True:
            try:
                # 获取用户有权限的项目，包括作为成员的项目
                params = {
                    'membership': 'true',  # 只获取用户有权限的项目
                    'per_page': per_page,
                    'page': page,
                    'simple': 'true',  # 简化响应，提高性能
                    'archived': 'false'  # 排除已归档的项目
                }
                
                response = self.session.get(f"{self.base_url}/projects", params=params)
                logger.debug(f"获取第 {page} 页项目，状态码: {response.status_code}")
                
                if response.status_code != 200:
                    logger.warning(f"获取项目列表失败: {response.status_code}")
                    break
                    
                page_projects = response.json()
                if not page_projects:
                    logger.info("没有更多项目，获取完成")
                    break
                    
                projects.extend(page_projects)
                logger.info(f"第 {page} 页获取到 {len(page_projects)} 个项目")
                
                # 如果返回的项目数小于每页数量，说明是最后一页
                if len(page_projects) < per_page:
                    break
                    
                page += 1
                
            except Exception as e:
                logger.error(f"获取项目列表时出错: {e}")
                break
        
        logger.info(f"总共获取到 {len(projects)} 个可访问的项目")
        return projects

    def fetch_project_info(self, repo_url: str) -> Dict[str, Any]:
        try:
            logger.debug(f"从 {repo_url} 获取项目信息...")
            encoded_path = quote(repo_url.lstrip('/'), safe='')
            response = self.session.get(
                f"{self.base_url}/projects/{encoded_path}")
            if response.status_code == 200:
                project_data = response.json()
                return {
                    'id': project_data['id'],
                    'name': project_data['name'],
                    'path_with_namespace': project_data['path_with_namespace']
                }
            else:
                logger.warning(f"获取项目信息失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取项目信息时出错: {e}")
        return {}

    def fetch_branches(self, project_id: str) -> List[str]:
        url = f"{self.base_url}/projects/{project_id}/repository/branches"
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                logger.warning(f"获取分支失败: {response.status_code}")
                return []
            branches = response.json()
            return [branch['name'] for branch in branches]
        except requests.RequestException as e:
            logger.error(f"获取分支时出错: {e}")
            return []

    def fetch_commits(self, project_id: str, branch: str, start_date: datetime.datetime,
                      end_date: datetime.datetime) -> List[Dict[str, Any]]:
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
                logger.warning(f"获取提交失败: {response.status_code}")
                break
            page_commits = response.json()
            if not page_commits:
                break
            commits.extend(page_commits)
            if len(page_commits) < per_page:
                break
            page += 1
        logger.info(f"获取 {branch} 分支的提交数量: {len(commits)}")
        return commits

    def parse_commit_time(self, commit_created_at: str) -> datetime.datetime:
        try:
            commit_time_utc = datetime.datetime.strptime(
                commit_created_at, '%Y-%m-%dT%H:%M:%S.%f%z')
        except ValueError:
            commit_time_utc = datetime.datetime.strptime(
                commit_created_at, '%Y-%m-%dT%H:%M:%S%z')
        return commit_time_utc.astimezone(self.local_tz)

    def analyze_overtime(self):
        start_date = datetime.datetime(self.year, 1, 1, tzinfo=pytz.utc)
        end_date = datetime.datetime(
            self.year, 12, 31, 23, 59, 59, tzinfo=pytz.utc)
        cursor = self.conn.cursor()

        # 使用用户定义的工作时间
        WORK_START_HOUR = self.work_start_hour  # 用户定义的上班时间
        WORK_END_HOUR = self.work_end_hour      # 用户定义的下班时间
        OVERTIME_END_HOUR = 23  # 加班统计截止时间 23:59:59

        for repo in self.repositories:
            project_id = repo['id']
            repository_name = repo['name']
            branches = self.fetch_branches(str(project_id))
            if not branches:
                continue

            for branch in branches:
                commits = self.fetch_commits(
                    str(project_id), branch, start_date, end_date)
                overtime_records = {}

                for commit in commits:
                    commit_time_local = self.parse_commit_time(
                        commit['created_at'])
                    if commit['author_email'] not in self.author_emails:
                        continue

                    weekday = commit_time_local.weekday()
                    hour = commit_time_local.hour
                    date_key = commit_time_local.date()

                    # 区分周末和工作日
                    if weekday >= 5:  # 周末
                        # 周末从早上9点开始计算，不管提交时间是什么时候
                        start_time = datetime.datetime.combine(
                            date_key,
                            datetime.time(WORK_START_HOUR, 0),
                            tzinfo=self.local_tz
                        )
                        overtime_records.setdefault(date_key, {
                            'commits': [],
                            'start_time': start_time,
                            'is_weekend': True  # 标记是否为周末
                        })['commits'].append(commit)
                    else:  # 工作日
                        if hour >= WORK_END_HOUR and hour < OVERTIME_END_HOUR:
                            start_time = datetime.datetime.combine(
                                date_key,
                                datetime.time(WORK_END_HOUR, 0),
                                tzinfo=self.local_tz
                            )
                            overtime_records.setdefault(date_key, {
                                'commits': [],
                                'start_time': start_time,
                                'is_weekend': False
                            })['commits'].append(commit)

                for date, record in overtime_records.items():
                    commits_on_date = record['commits']
                    if not commits_on_date:
                        continue

                    commits_on_date.sort(
                        key=lambda x: self.parse_commit_time(x['created_at']))
                    first_commit_time = self.parse_commit_time(
                        commits_on_date[0]['created_at'])
                    last_commit_time = self.parse_commit_time(
                        commits_on_date[-1]['created_at'])

                    # 确保最后提交时间不超过当天23:59:59
                    end_time = datetime.datetime.combine(
                        date,
                        datetime.time(OVERTIME_END_HOUR, 59, 59),
                        tzinfo=self.local_tz
                    )
                    last_commit_time = min(last_commit_time, end_time)

                    if record['is_weekend']:  # 周末
                        # 周末一律从9点开始算，如果第一次提交在9点之前，仍从9点算起
                        hours_worked = (last_commit_time - record['start_time']).total_seconds() / 3600
                    else:  # 工作日
                        overtime_duration = (last_commit_time - record['start_time']).total_seconds() / 3600
                        if overtime_duration < 1:
                            logger.info(f"工作日加班时间不足1小时，跳过记录: {date}")
                            continue
                        hours_worked = overtime_duration

                    last_commit_hash = commits_on_date[-1].get('id', '')

                    cursor.execute('''
                        SELECT COUNT(*) FROM Overtime 
                        WHERE commit_hash = ?
                    ''', (last_commit_hash,))
                    if cursor.fetchone()[0] > 0:
                        logger.warning(f"跳过重复记录: {last_commit_hash} 已存在于数据库")
                        continue

                    cursor.execute(''' 
                        INSERT INTO Overtime (
                            repository_id, repository_name, branch, date, 
                            last_commit_time, hours_worked, last_commit_message, 
                            commit_hash, author_email
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        project_id,
                        repository_name,
                        branch,
                        date.isoformat(),
                        last_commit_time.strftime('%H:%M:%S'),
                        round(hours_worked, 2),  # 保留两位小数
                        commits_on_date[-1].get('title', ''),
                        last_commit_hash,
                        self.author_emails[0]
                    ))

                    self.conn.commit()

        logger.info("加班分析完成。")

    def create_overtime_chart(self):
        logger.info("生成加班图表...")
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT date, SUM(hours_worked) FROM Overtime GROUP BY date")
        data = cursor.fetchall()
        if not data:
            logger.warning("没有可用数据生成图表。")
            return None

        df = pd.DataFrame(data, columns=['Date', 'Hours_Worked'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        plt.figure(figsize=(10, 6))
        plt.plot(df.index, df['Hours_Worked'], marker='o', linestyle='-')
        plt.title('加班情况一览')
        plt.xlabel('日期')
        plt.ylabel('加班小时数')
        plt.xticks(rotation=45)
        plt.grid()
        plt.tight_layout()
        chart_path = 'overtime_chart.png'
        plt.savefig(chart_path)
        plt.close()
        logger.info("加班图表生成成功。")
        return chart_path

    def export_to_excel(self) -> str:
        logger.info("导出数据为 Excel...")
        conn = sqlite3.connect(self.database_path)
        df = pd.read_sql_query("SELECT * FROM Overtime", conn)
        excel_path = "overtime_data.xlsx"
        df.to_excel(excel_path, index=False)
        conn.close()
        logger.info("数据成功导出为 Excel。")
        return excel_path

    def close(self):
        logger.info("关闭数据库连接...")
        self.conn.close()
