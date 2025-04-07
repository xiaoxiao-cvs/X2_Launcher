class DeploymentError(Exception):
    """部署过程中的基础错误类"""
    pass

class GitHubAPIError(DeploymentError):
    """GitHub API相关错误"""
    pass

class ProcessError(DeploymentError):
    """进程操作相关错误"""
    pass

class ConfigError(DeploymentError):
    """配置相关错误"""
    pass

class DependencyError(DeploymentError):
    """依赖安装相关错误"""
    pass

class BotError(DeploymentError):
    """机器人操作相关错误"""
    pass
