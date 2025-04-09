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

# X2 Launcher

这是X2 Launcher，一个用于管理和运行MaiBot的启动器。

## 初始安装

首次运行项目前，请执行以下步骤安装必要的依赖：

1. 确保已安装Node.js (v16+)和Python (v3.9+)
2. 克隆项目并进入项目目录：
   ```
   git clone <repo-url>
   cd X2_Launcher
   ```
3. 安装Node.js依赖：
   ```
   npm install
   ```
4. 运行依赖安装脚本安装Python依赖：
   ```
   install_dependencies.bat
   ```
   这个脚本会创建Python虚拟环境并安装所有必要的依赖。

## 运行开发环境

安装完成后，运行以下命令启动开发环境：

```
npm run dev
```

## 常见问题

### 缺少依赖

如果出现"No module named 'xxx'"错误，请执行以下操作：

1. 运行`install_dependencies.bat`脚本安装所有依赖
2. 或者在应用内点击"检查依赖"按钮来检查和安装缺失的依赖

### app.ico错误

需要添加一个图标文件到assets目录：
1. 创建一个名为`app.ico`的图标文件
2. 将其放置在项目的`assets`目录下

### 连接后端失败

如果前端无法连接到后端，请检查：
1. 后端服务是否已启动
2. 检查日志中是否有Python依赖缺失的错误
3. 运行`install_dependencies.bat`安装所需依赖

## 开发计划 📅

### 近期计划 (v1.x)

- [ ] 添加插件系统支持
- [ ] 实现自动更新功能
- [ ] 优化依赖安装性能
- [ ] 添加部署进度显示
- [ ] 改进错误处理机制
- [ ] 支持 Docker 部署

### 长期计划 (v2.0+)

- [ ] 多机器人实例管理
- [ ] 分布式部署支持
- [ ] 资源监控面板
- [ ] WebUI 支持
- [ ] 云端同步功能
- [ ] API 文档生成器

## 贡献指南 🤝

欢迎提交 Pull Request 或创建 Issue！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 问题反馈 🐛

如果你发现了 bug 或有新功能建议，请创建 issue。

## 许可证 📄

本项目采用 GPLv3 许可证 - 详见 [LICENSE](LICENSE) 文件

## 作者 👨‍💻

XiaoXiao - [@xiaoxiao](https://github.com/xiaoxiao)

## 致谢 🙏

- CustomTkinter 提供的优秀UI框架
- GitHub API 提供的版本控制支持
- 所有贡献者和用户

---

⭐️ 如果这个项目对你有帮助，欢迎点个 star!
