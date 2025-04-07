import requests
from ..logger import logger

class GitHubAuth:
    def __init__(self, token):
        self.token = token

    async def verify_token(self):
        """验证GitHub Token"""
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        try:
            response = requests.get("https://api.github.com/user", headers=headers)
            if response.status_code == 200:
                logger.log("GitHub token 验证成功", "INFO")
                return True
            else:
                logger.log(f"GitHub token 验证失败: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            logger.log(f"GitHub token 验证异常: {e}", "ERROR")
            return False