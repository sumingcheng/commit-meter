import requests
import datetime
from typing import List, Dict, Any
from app.utils.logger import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class GitHubClient:
    """GitHub API 客户端，负责所有与 GitHub API 的交互"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建配置好的 HTTP 会话"""
        logger.info("创建 GitHub API 会话...")
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.1)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json"
        })
        return session
    
    def fetch_user_repos(self) -> List[Dict[str, Any]]:
        """获取用户的所有仓库"""
        logger.info("获取用户GitHub仓库列表...")
        repos = []
        page = 1
        per_page = 100
        
        while True:
            try:
                params = {
                    "per_page": per_page,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc"
                }
                
                response = self.session.get(f"{self.base_url}/user/repos", params=params)
                logger.debug(f"获取第 {page} 页仓库，状态码: {response.status_code}")
                
                if response.status_code != 200:
                    logger.warning(f"获取仓库列表失败: {response.status_code}")
                    break
                    
                page_repos = response.json()
                if not page_repos:
                    logger.info("没有更多仓库，获取完成")
                    break
                    
                repos.extend(page_repos)
                logger.info(f"第 {page} 页获取到 {len(page_repos)} 个仓库")
                
                if len(page_repos) < per_page:
                    break
                    
                page += 1
                
            except Exception as e:
                logger.error(f"获取仓库列表时出错: {e}")
                break
        
        logger.info(f"总共获取到 {len(repos)} 个GitHub仓库")
        return repos
    
    def fetch_branches(self, owner: str, repo: str) -> List[str]:
        """获取仓库的所有分支"""
        url = f"{self.base_url}/repos/{owner}/{repo}/branches"
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
        owner: str,
        repo: str,
        branch: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> List[Dict[str, Any]]:
        """获取指定仓库分支的提交记录"""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        commits = []
        page = 1
        per_page = 100
        
        while True:
            params = {
                "since": start_date.isoformat(),
                "until": end_date.isoformat(),
                "per_page": per_page,
                "page": page,
                "sha": branch,
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
            
        logger.info(f"获取 {repo}/{branch} 分支的提交数量: {len(commits)}")
        return commits
    
    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close() 