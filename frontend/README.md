# X2 Launcher 前端项目

## 开发指南

### 环境准备

项目依赖于某些 PostCSS 插件，如果启动时遇到以下错误：

```
Error: Cannot find module 'postcss-preset-env'
```

请运行以下命令安装必要的依赖：

```bash
npm run install-deps
```

或者手动安装：

```bash
npm install --save-dev autoprefixer postcss-preset-env
```

### 启动开发服务器

```bash
npm run dev
```

这个命令会自动检查并安装必要的依赖，然后启动开发服务器。

### 构建项目

```bash
npm run build
```

### 启动本地预览

```bash
npm run preview
```

## 技术栈

- Vue 3
- Vite
- Element Plus
- Axios
- ECharts

## 项目结构

- `src/components`：组件目录
- `src/assets`：静态资源
- `src/utils`：工具函数

## 贡献指南

1. 确保安装所有依赖
2. 遵循项目的代码风格
3. 提交前进行代码检查：`npm run lint`
