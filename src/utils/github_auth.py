import requests
from ..logger import XLogger  # 修改为两层相对导入，因为是从 src/utils 导入到 src/logger

class GitHubAuth:
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    async def verify_token(self):
        try:
            response = requests.get(
                'https://api.github.com/user',
                headers=self.headers
            )
            if response.status_code == 200:
                XLogger.log("GitHub token 验证成功", "INFO")
                return True
            else:
                XLogger.log(f"GitHub token 验证失败: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            XLogger.log(f"GitHub token 验证出错: {e}", "ERROR")
            return False