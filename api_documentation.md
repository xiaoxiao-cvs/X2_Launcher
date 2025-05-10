# X2 Launcher API 文档

## 目录

- [概述](#概述)
- [基础信息](#基础信息)
- [通用API](#通用api)
  - [健康检查](#健康检查)
  - [诊断API](#诊断api)
  - [系统状态](#系统状态)
  - [实例管理](#实例管理)
  - [日志API](#日志api)
  - [文件操作](#文件操作)
- [部署API](#部署api)
  - [获取可用版本](#获取可用版本)
  - [部署特定版本](#部署特定版本)
  - [获取部署状态](#获取部署状态)
  - [配置机器人](#配置机器人)
  - [获取安装状态](#获取安装状态)
- [WebSocket API](#websocket-api)
  - [日志实时推送](#日志实时推送)

## 概述

X2 Launcher API提供了一系列接口，用于管理、部署和监控MaiBot实例。API使用REST风格设计，返回JSON格式数据。

## 基础信息

- 基础URL: `/api`
- 部分API支持不带`/api`前缀的访问
- 所有API都返回JSON格式响应
- 错误响应通常包含`status`和`message`字段

## 通用API

### 健康检查

检查API服务是否正常运行。

**请求**:
- 方法: `GET`
- 路径: `/api/health`

**响应**:
```json
{
  "status": "ok",
  "timestamp": 1623456789.123,
  "version": "0.2.0",
  "environment": "Windows-10-10.0.19041-SP0"
}
```

### 诊断API

获取服务器路由诊断信息。

**请求**:
- 方法: `GET`
- 路径: `/api/diagnose`

**响应**:
```json
{
  "routes_count": 15,
  "routes": [
    {
      "path": "/api/health",
      "name": "health_check",
      "methods": ["GET"]
    },
    // ...其他路由
  ],
  "environment": "Windows-10-10.0.19041-SP0",
  "python_version": "3.9.7",
  "timestamp": 1623456789.123
}
```

### 系统状态

获取系统各组件的运行状态。

**请求**:
- 方法: `GET`
- 路径: `/api/status`

**响应**:
```json
{
  "mongodb": {"status": "running", "info": "本地实例"},
  "napcat": {"status": "running", "info": "端口 8095"},
  "nonebot": {"status": "stopped", "info": ""},
  "maibot": {"status": "stopped", "info": ""}
}
```

### 实例管理

#### 获取实例列表

**请求**:
- 方法: `GET`
- 路径: `/api/instances`

**响应**:
```json
{
  "instances": [
    {
      "name": "maibot_latest_20230601123045",
      "version": "latest",
      "status": "running",
      "path": "C:\\Users\\username\\MaiM-with-u\\maibot_latest_20230601123045"
    },
    // ...其他实例
  ]
}
```

#### 获取实例统计

**请求**:
- 方法: `GET`
- 路径: `/api/instances/stats` 或 `/api/instance-stats`（旧版）

**响应**:
```json
{
  "total": 3,
  "running": 1,
  "stopped": 2
}
```

#### 启动实例

**请求**:
- 方法: `POST`
- 路径: `/api/start/{instance_name}`
- URL参数:
  - `instance_name`: 实例名称

**响应**:
```json
{
  "success": true,
  "message": "实例 maibot_latest_20230601123045 已启动"
}
```

#### 停止所有实例

**请求**:
- 方法: `POST`
- 路径: `/api/stop`

**响应**:
```json
{
  "success": true,
  "message": "所有实例已停止"
}
```

### 日志API

#### 获取系统日志

**请求**: 
- 方法: `GET`
- 路径: `/api/logs/system`

**响应**:
```json
{
  "logs": [
    {"time": "2023-05-07 17:15:22", "level": "INFO", "message": "系统启动"},
    {"time": "2023-05-07 17:15:25", "level": "INFO", "message": "MongoDB 连接成功"},
    {"time": "2023-05-07 17:15:30", "level": "WARNING", "message": "NoneBot 适配器未启动"},
    {"time": "2023-05-07 17:16:45", "level": "ERROR", "message": "MaiBot 初始化失败: 配置文件损坏"}
  ]
}
```

### 文件操作

#### 打开文件夹

**请求**:
- 方法: `POST`
- 路径: `/api/open-folder`
- 请求体:
```json
{
  "path": "C:\\Users\\username\\MaiM-with-u\\maibot_latest_20230601123045"
}
```

**响应**:
```json
{
  "success": true
}
```

## 部署API

### 获取可用版本

**请求**:
- 方法: `GET`
- 路径: `/api/versions` 或 `/versions`

**响应**:
```json
{
  "versions": ["latest", "main", "stable", "v0.6.3", "v0.6.2", "v0.6.1", "v0.6.0"]
}
```

### 部署特定版本

##### 通过路径参数

**请求**: 
- 方法: `POST`
- 路径: `/api/deploy/{version}` 或 `/deploy/{version}`
- URL参数:
  - `version`: 要部署的版本，如 "latest"

**响应**:
```json
{
  "success": true,
  "message": "正在部署 latest 版本",
  "instance_name": "maibot_latest_20230601123045",
  "timestamp": "2023-06-01T12:30:45"
}
```

##### 通过JSON数据

**请求**: 
- 方法: `POST`
- 路径: `/api/deploy` 或 `/deploy`
- 请求体:
```json
{
  "version": "latest",
  "instance_name": "my_custom_instance"
}
```

**响应**:
```json
{
  "success": true,
  "message": "正在部署 latest 版本",
  "instance_name": "my_custom_instance",
  "timestamp": "2023-06-01T12:30:45"
}
```

### 获取部署状态

**请求**:
- 方法: `GET`
- 路径: `/api/deploy/status/{instance_name}` 或 `/deploy/status/{instance_name}`
- URL参数:
  - `instance_name`: 实例名称

**响应示例1** (部署中):
```json
{
  "status": "running",
  "instance_name": "maibot_latest_20230601123045",
  "logs": [
    {
      "time": "2023-06-01T12:30:45",
      "level": "INFO",
      "message": "开始部署 latest 版本"
    },
    // ...更多日志
  ]
}
```

**响应示例2** (部署完成):
```json
{
  "status": "completed",
  "instance_name": "maibot_latest_20230601123045",
  "install_path": "C:\\Users\\username\\MaiM-with-u\\maibot_latest_20230601123045",
  "logs": [
    // ...日志列表
  ]
}
```

### 配置机器人

**请求**:
- 方法: `POST`
- 路径: `/api/install/configure` 或 `/install/configure`
- 请求体:
```json
{
  "instance_name": "maibot_latest_20230601123045",
  "install_napcat": true,
  "install_nonebot": false,
  "qq_number": "123456789",
  "ports": {
    "maibot": 8000,
    "napcat": 8095,
    "nonebot": 18002
  },
  "run_install_script": true,
  "install_adapter": true
}
```

**响应**:
```json
{
  "success": true,
  "message": "正在配置实例 maibot_latest_20230601123045",
  "instance_name": "maibot_latest_20230601123045"
}
```

### 获取安装状态

**请求**:
- 方法: `GET`
- 路径: `/api/install-status` 或 `/install-status`

**响应**:
```json
{
  "napcat_installing": false,
  "nonebot_installing": false
}
```

## WebSocket API

### 日志实时推送

实时接收应用日志。

**连接**:
- URL: `ws://服务器地址/api/logs/ws`

**接收的消息格式**:
```json
{
  "time": "2023-06-01 12:30:45",
  "level": "INFO",
  "message": "测试日志消息",
  "source": "system"
}
```

**连接成功响应**:
```json
{
  "time": "now",
  "level": "INFO",
  "message": "WebSocket连接已建立",
  "source": "system"
}
```

**发送消息** (客户端到服务器):

客户端可以发送JSON格式的消息，服务器会处理这些消息并记录到日志中。
