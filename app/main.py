import pytz
import requests
import datetime
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from urllib.parse import quote
import gradio as gr
from typing import List, Dict, Any
from app.config.main import Config
from app.gitlab.constant import REPOSITORY_URLS
from app.journal.logger_setup import logger


class OvertimeAnalyzer:
    def __init__(self, access_token: str, base_url: str, local_tz: pytz.timezone,
                 repository_urls: List[str], author_email: str, year: int):
        self.access_token = access_token
        self.base_url = base_url
        self.database_path = Config.DATABASE_PATH
        self.local_tz = local_tz
        self.repository_urls = repository_urls
        self.author_email = author_email
        self.year = year
        self.conn = self.setup_database()
        self.session = self.create_session()
        self.repositories = self.get_repositories_info()

    def create_session(self) -> requests.Session:
        logger.info("创建会话...")
        session = requests.Session()
        session.headers.update({'PRIVATE-TOKEN': self.access_token})
        return session

    def setup_database(self) -> sqlite3.Connection:
        logger.info("设置数据库...")
        conn = sqlite3.connect(self.database_path)
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
        logger.info("获取仓库信息...")
        repositories = []
        for url in self.repository_urls:
            project_info = self.fetch_project_info(url)
            if project_info:
                repositories.append(project_info)
                logger.info(f"获取项目信息: {project_info['name']}")
        return repositories

    def fetch_project_info(self, repo_url: str) -> Dict[str, Any]:
        try:
            logger.debug(f"从 {repo_url} 获取项目信息...")
            encoded_path = quote(repo_url.lstrip('/'), safe='')
            response = self.session.get(f"{self.base_url}/projects/{encoded_path}")
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
            commit_time_utc = datetime.datetime.strptime(commit_created_at, '%Y-%m-%dT%H:%M:%S.%f%z')
        except ValueError:
            commit_time_utc = datetime.datetime.strptime(commit_created_at, '%Y-%m-%dT%H:%M:%S%z')
        return commit_time_utc.astimezone(self.local_tz)

    def analyze_overtime(self):
        start_date = datetime.datetime(self.year, 1, 1, tzinfo=pytz.utc)
        end_date = datetime.datetime(self.year, 12, 31, 23, 59, 59, tzinfo=pytz.utc)
        cursor = self.conn.cursor()

        for repo in self.repositories:
            project_id = repo['id']
            repository_name = repo['name']
            branches = self.fetch_branches(str(project_id))
            if not branches:
                continue

            for branch in branches:
                commits = self.fetch_commits(str(project_id), branch, start_date, end_date)
                overtime_records = {}

                for commit in commits:
                    commit_time_local = self.parse_commit_time(commit['created_at'])
                    if commit['author_email'] != self.author_email:
                        continue

                    weekday = commit_time_local.weekday()
                    hour = commit_time_local.hour

                    if weekday < 5 and hour >= 18:
                        date_key = commit_time_local.date()
                        overtime_records.setdefault(date_key, []).append(commit)
                    elif weekday >= 5:
                        date_key = commit_time_local.date()
                        overtime_records.setdefault(date_key, []).append(commit)

                for date, commits_on_date in overtime_records.items():
                    commits_on_date.sort(key=lambda x: self.parse_commit_time(x['created_at']))
                    first_commit_time_local = self.parse_commit_time(commits_on_date[0]['created_at'])
                    last_commit_time_local = self.parse_commit_time(commits_on_date[-1]['created_at'])
                    hours_worked = (last_commit_time_local - first_commit_time_local).total_seconds() / 3600

                    # 插入时确保包含 commit_hash
                    last_commit_hash = commits_on_date[-1].get('id', '')  # 使用 'id' 字段作为 commit_hash
                    cursor.execute(''' 
                        INSERT OR REPLACE INTO Overtime (
                            repository_id, repository_name, branch, date, last_commit_time, hours_worked, last_commit_message, commit_hash
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        project_id,
                        repository_name,
                        branch,
                        date.isoformat(),
                        last_commit_time_local.strftime('%H:%M:%S'),
                        hours_worked,
                        commits_on_date[-1].get('title', ''),
                        last_commit_hash  # 添加 commit_hash
                    ))
                    self.conn.commit()

        logger.info("加班分析完成。")

    def create_overtime_chart(self):
        logger.info("生成加班图表...")
        cursor = self.conn.cursor()
        cursor.execute("SELECT date, SUM(hours_worked) FROM Overtime GROUP BY date")
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


# 创建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("# 加班分析工具")

    with gr.Row():
        access_token = gr.Textbox(label="GitLab Token", placeholder="请输入访问令牌", elem_id="token")
        base_url = gr.Textbox(label="Git Base URL", placeholder="请输入 GitLab 的基础 URL", elem_id="url")
        author_email = gr.Textbox(label="邮箱", placeholder="请输入作者邮箱", elem_id="email")
        year = gr.Number(label="年份", value=datetime.datetime.now().year, elem_id="year")

    with gr.Row():
        submit_btn = gr.Button("分析加班数据")

    chart_output = gr.Image(label="加班情况图")
    excel_output = gr.File(label="下载数据 Excel")


    def on_submit(access_token, base_url, author_email, year):
        chart_path, excel_path = analyze_and_plot(access_token, base_url, author_email, year)
        return chart_path, excel_path


    submit_btn.click(on_submit, inputs=[access_token, base_url, author_email, year],
                     outputs=[chart_output, excel_output])

# 启动 Gradio 应用
demo.launch()
