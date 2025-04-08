import logging
import requests
import aiohttp
import asyncio
from typing import List, Dict, Any
from .logger import XLogger  # 修改这里
from .errors import GitHubAPIError  # 添加这行导入

class GitHubClient:
    def __init__(self, token=None):
        self.token = token
        self.timeout = 30
        XLogger.log("初始化GitHub客户端")  # 更新logger使用

    def _get_headers(self) -> Dict[str, str]:
        """共享的请求头生成"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'X-Deploy-Station'
        }
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        return headers

    def get_releases(self, repo_url: str) -> List[Dict]:
        """获取发行版"""
        releases = []
        try:
            repo_path = repo_url.rstrip('/').replace('.git', '').split('github.com/')[-1]
            page = 1
            
            while True:
                api_url = f"https://api.github.com/repos/{repo_path}/releases?page={page}&per_page=100"
                response = requests.get(
                    api_url, 
                    headers=self._get_headers(), 
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                page_releases = response.json()
                if not page_releases:
                    break
                    
                releases.extend(page_releases)
                page += 1
                
            return releases
            
        except Exception as e:
            XLogger.log(f"发行版获取失败: {e}", "ERROR")  # 更新logger使用
            return []

    async def async_get_releases(self, repo_url: str) -> List[Dict]:
        """异步获取发行版"""
        releases = []
        try:
            repo_path = repo_url.rstrip('/').replace('.git', '').split('github.com/')[-1]
            page = 1
            
            async with aiohttp.ClientSession() as session:
                while True:
                    api_url = f"https://api.github.com/repos/{repo_path}/releases?page={page}&per_page=100"
                    async with session.get(
                        api_url, 
                        headers=self._get_headers(), 
                        timeout=self.timeout
                    ) as resp:
                        resp.raise_for_status()
                        page_releases = await resp.json()
                        
                    if not page_releases:
                        break
                        
                    releases.extend(page_releases)
                    page += 1
                    
            return releases
                
        except Exception as e:
            XLogger.log(f"发行版获取失败: {e}", "ERROR")  # 更新logger使用
            return []

    async def async_get_repo_info(self, repo_url: str) -> Dict:
        """异步获取仓库信息"""
        try:
            repo_path = repo_url.rstrip('/').replace('.git', '').split('github.com/')[-1]
            api_url = f"https://api.github.com/repos/{repo_path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self._get_headers(), timeout=15) as resp:
                    resp.raise_for_status()
                    return await resp.json()
                    
        except Exception as e:
            logging.error(f"仓库信息获取失败: {e}")
            return {}

    async def async_get_branches(self, repo_url: str) -> List[Dict]:
        """异步获取分支"""
        try:
            repo_path = repo_url.rstrip('/').replace('.git', '').split('github.com/')[-1]
            api_url = f"https://api.github.com/repos/{repo_path}/branches"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self._get_headers(), timeout=15) as resp:
                    resp.raise_for_status()
                    return await resp.json()
                    
        except Exception as e:
            logging.error(f"分支获取失败: {e}")
            return []

    def get_repo_info(self, repo_url: str) -> Dict:
        """获取仓库信息"""
        try:
            repo_path = repo_url.rstrip('/').replace('.git', '').split('github.com/')[-1]
            api_url = f"https://api.github.com/repos/{repo_path}"
            
            response = requests.get(api_url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logging.error(f"仓库信息获取失败: {e}")
            return {}

    def get_branches(self, repo_url: str) -> List[Dict]:
        """获取分支"""
        try:
            repo_path = repo_url.rstrip('/').replace('.git', '').split('github.com/')[-1]
            api_url = f"https://api.github.com/repos/{repo_path}/branches"
            
            response = requests.get(api_url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logging.error(f"分支获取失败: {e}")
            return []

    def _handle_error(self, e: Exception, action: str):
        error_msg = f"GitHub {action}失败: {str(e)}"
        XLogger.log(error_msg, "ERROR")  # 更新logger使用
        raise GitHubAPIError(error_msg)  # 修复拼写错误
