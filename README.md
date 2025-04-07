# X² Deploy Station 🚀

一个现代化的机器人部署和管理工具 🤖

## 项目介绍 📖

X² Deploy Station 是一个专门为机器人项目设计的部署管理平台。它提供了直观的图形界面，让用户可以轻松地管理不同版本的机器人，进行部署、更新和运行控制。

### 主要特性 ✨

- 🎯 直观的图形用户界面
- 🔄 自动版本管理和更新
- 🌐 GitHub 集成支持
- 💻 虚拟环境隔离
- 📊 实时日志显示
- ⚙️ 可配置的部署选项
- 🔒 安全的进程管理
- 🌈 自定义主题支持

## 技术栈 🛠️

- Python 3.8+
- CustomTkinter (现代化UI)
- asyncio (异步支持)
- GitHub API (版本控制)
- FastAPI (后端服务)
- SQLite (数据存储)

## 快速开始 🚀

### 环境要求

- Python 3.8 或更高版本
- Git
- Windows/Linux/MacOS 支持

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/your-username/X-Deploy-Station.git
cd X-Deploy-Station
```

2. 创建虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/MacOS
.venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行程序
```bash
python main.py
```

### 打包步骤

1. 安装打包工具
```bash
pip install pyinstaller
```

2. 打包应用
```bash
# Windows
pyinstaller --noconfirm --onedir --windowed --icon "assets/icon.ico" --add-data "assets;assets/" --name "X-Deploy-Station" main.py

# Linux/MacOS
pyinstaller --noconfirm --onedir --windowed --icon "assets/icon.png" --add-data "assets:assets/" --name "X-Deploy-Station" main.py
```

打包后的文件将在 `dist/X-Deploy-Station` 目录中。

## 配置说明 ⚙️

配置文件位于 `settings.json`，支持以下配置项：

```json
{
    "appearance": {
        "background_image": "path/to/image",
        "transparency": 0.7,
        "theme": "dark",
        "accent_color": "#1E90FF",
        "window_size": "1280x720"
    },
    "deployment": {
        "auto_check_update": true,### 长期计划 (v2.0+)
        "python_version": "3.13.0",
        "install_path": "maibot_versions",- [ ] 多机器人实例管理
        "repo_url": "your-repo-url"
    }
}支持
```
生成器
## 开发计划 📅
## 贡献指南 🤝
### 近期计划 (v1.x)
欢迎提交 Pull Request 或创建 Issue！
- [ ] 添加插件系统支持
- [ ] 实现自动更新功能1. Fork 本仓库
- [ ] 优化依赖安装性能`git checkout -b feature/AmazingFeature`)
- [ ] 添加部署进度显示
- [ ] 改进错误处理机制
- [ ] 支持 Docker 部署

### 长期计划 (v2.0+)## 问题反馈 🐛

- [ ] 多机器人实例管理如果你发现了 bug 或有新功能建议，请创建 issue。
- [ ] 分布式部署支持
- [ ] 资源监控面板## 许可证 📄
- [ ] WebUI 支持
- [ ] 云端同步功能本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
- [ ] API 文档生成器
## 作者 👨‍💻
## 贡献指南 🤝
XiaoXiao - [@xiaoxiao](https://github.com/xiaoxiao)
欢迎提交 Pull Request 或创建 Issue！
## 致谢 🙏
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)- CustomTkinter 提供的优秀UI框架
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request
---
## 问题反馈 🐛如果这个项目对你有帮助，欢迎点个 star!
如果你发现了 bug 或有新功能建议，请创建 issue。

## 许可证 📄

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 作者 👨‍💻

XiaoXiao - [@xiaoxiao](https://github.com/xiaoxiao)

## 致谢 🙏

- CustomTkinter 提供的优秀UI框架
- GitHub API 提供的版本控制支持
- 所有贡献者和用户

---
⭐️ 如果这个项目对你有帮助，欢迎点个 star!
