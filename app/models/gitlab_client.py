import requests
import datetime
from urllib.parse import quote
from typing import List, Dict, Any
from app.utils.logger import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class GitLabClient:
    """GitLab API 客户端，负责所有与 GitLab API 的交互"""

    def __init__(self, access_token: str, base_url: str):
        self.access_token = access_token
        self.base_url = base_url
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建配置好的 HTTP 会话"""
        logger.info("创建GitLab API会话...")
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.1)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"PRIVATE-TOKEN": self.access_token})
        return session

    def fetch_user_projects(self) -> List[Dict[str, Any]]:
        """动态获取用户有权限访问的所有项目"""
        logger.info("获取用户项目列表...")
        projects = []
        page = 1
        per_page = 100

        while True:
            try:
                params = {
                    "membership": "true",
                    "per_page": per_page,
                    "page": page,
                    "simple": "true",
                    "archived": "false",
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

                if len(page_projects) < per_page:
                    break

                page += 1

            except Exception as e:
                logger.error(f"获取项目列表时出错: {e}")
                break

        logger.info(f"总共获取到 {len(projects)} 个可访问的项目")
        return projects

    def fetch_project_info(self, repo_url: str) -> Dict[str, Any]:
        """获取指定项目的信息"""
        try:
            logger.debug(f"从 {repo_url} 获取项目信息...")
            encoded_path = quote(repo_url.lstrip("/"), safe="")
            response = self.session.get(f"{self.base_url}/projects/{encoded_path}")

            if response.status_code == 200:
                project_data = response.json()
                return {
                    "id": project_data["id"],
                    "name": project_data["name"],
                    "path_with_namespace": project_data["path_with_namespace"],
                }
            else:
                logger.warning(f"获取项目信息失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取项目信息时出错: {e}")
        return {}

    def fetch_branches(self, project_id: str) -> List[str]:
        """获取项目的所有分支"""
        url = f"{self.base_url}/projects/{project_id}/repository/branches"
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                logger.warning(f"获取分支失败: {response.status_code}")
                return []
            branches = response.json()
            return [branch["name"] for branch in branches]
        except requests.RequestException as e:
            logger.error(f"获取分支时出错: {e}")
            return []

    def fetch_commits(
        self,
        project_id: str,
        branch: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> List[Dict[str, Any]]:
        """获取指定项目分支的提交记录"""
        url = f"{self.base_url}/projects/{project_id}/repository/commits"
        commits = []
        page = 1
        per_page = 100

        while True:
            params = {
                "since": start_date.isoformat(),
                "until": end_date.isoformat(),
                "per_page": per_page,
                "page": page,
                "ref_name": branch,
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

    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()
