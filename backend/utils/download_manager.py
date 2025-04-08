import os
import sys
import time
import uuid
import threading
import requests
import shutil
import tempfile
import subprocess
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path

from .logger import XLogger

@dataclass
class DownloadTask:
    id: str
    name: str
    url: str
    path: str
    type: str = "file"  # "file" or "repository"
    branch: str = "master"  # 仅用于repository类型
    progress: int = 0
    speed: str = "0 KB/s"
    status: str = "等待"  # 等待, 下载中, 暂停, 完成, 失败
    error: str = ""
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self):
        return asdict(self)

class DownloadManager:
    def __init__(self):
        self.downloads: Dict[str, DownloadTask] = {}
        self.active_downloads: Dict[str, Dict] = {}
        self.logger = XLogger
        self.logger.log("初始化下载管理器")
        
        # 示例下载任务
        self._add_sample_downloads()
    
    def _add_sample_downloads(self):
        """添加示例下载任务用于前端展示"""
        sample_downloads = [
            {
                "id": "sample1", 
                "name": "MaiBot-v2.1.0.zip", 
                "url": "https://example.com/maibot.zip",
                "path": "D:/Downloads/MaiBot-v2.1.0.zip",
                "progress": 100,
                "speed": "0 KB/s",
                "status": "完成"
            },
            {
                "id": "sample2", 
                "name": "Resources-pack.rpk", 
                "url": "https://example.com/resources.rpk",
                "path": "D:/Downloads/Resources-pack.rpk",
                "progress": 65,
                "speed": "1.2 MB/s",
                "status": "下载中"
            },
            {
                "id": "sample3", 
                "name": "Update-patch.exe", 
                "url": "https://example.com/update.exe",
                "path": "D:/Downloads/Update-patch.exe",
                "progress": 0,
                "speed": "0 KB/s",
                "status": "等待"
            }
        ]
        
        for sample in sample_downloads:
            task = DownloadTask(
                id=sample["id"],
                name=sample["name"],
                url=sample["url"],
                path=sample["path"],
                progress=sample["progress"],
                speed=sample["speed"],
                status=sample["status"]
            )
            self.downloads[task.id] = task
    
    def add_download(self, url: str, path: str, download_type: str = "file", branch: str = "master") -> DownloadTask:
        """添加下载任务"""
        task_id = str(uuid.uuid4())
        name = self._get_filename_from_url(url) if download_type == "file" else self._get_repo_name(url)
        
        task = DownloadTask(
            id=task_id,
            name=name,
            url=url,
            path=path,
            type=download_type,
            branch=branch
        )
        
        self.downloads[task_id] = task
        self.logger.log(f"添加下载任务: {name}")
        return task
    
    def start_download(self, task_id: str) -> bool:
        """开始下载任务"""
        if task_id not in self.downloads:
            self.logger.log(f"未找到下载任务 ID: {task_id}", "ERROR")
            return False
            
        task = self.downloads[task_id]
        
        # 如果已经在下载中，不重复启动
        if task_id in self.active_downloads:
            return True
            
        # 设置状态为下载中
        task.status = "下载中"
        task.speed = "计算中..."
        
        if task.type == "file":
            thread = threading.Thread(target=self._download_file, args=(task_id,))
        else:
            thread = threading.Thread(target=self._clone_repository, args=(task_id,))
            
        thread.daemon = True
        thread.start()
        
        self.active_downloads[task_id] = {"thread": thread, "start_time": time.time()}
        self.logger.log(f"开始下载: {task.name}")
        return True
    
    def pause_download(self, task_id: str) -> bool:
        """暂停下载任务"""
        if task_id not in self.downloads or task_id not in self.active_downloads:
            return False
            
        # 目前仅支持标记暂停状态
        self.downloads[task_id].status = "暂停"
        self.downloads[task_id].speed = "0 KB/s"
        self.active_downloads[task_id]["cancel"] = True
        
        self.logger.log(f"暂停下载: {self.downloads[task_id].name}")
        return True
    
    def delete_download(self, task_id: str) -> bool:
        """删除下载任务"""
        if task_id not in self.downloads:
            return False
            
        task_name = self.downloads[task_id].name
        
        # 如果下载正在进行，先停止
        if task_id in self.active_downloads:
            self.pause_download(task_id)
            
        # 删除任务
        del self.downloads[task_id]
        if task_id in self.active_downloads:
            del self.active_downloads[task_id]
        
        self.logger.log(f"删除下载任务: {task_name}")    
        return True
    
    def get_downloads(self) -> List[Dict[str, Any]]:
        """获取所有下载任务"""
        return [task.to_dict() for task in self.downloads.values()]
    
    def _download_file(self, task_id: str):
        """实际的文件下载过程"""
        task = self.downloads[task_id]
        
        try:
            # 模拟下载过程 (TODO: 实现实际下载)
            total_steps = 100
            for i in range(task.progress, total_steps + 1):
                if task_id in self.active_downloads and self.active_downloads[task_id].get("cancel"):
                    break
                    
                task.progress = i
                # 计算模拟速度
                elapsed = time.time() - self.active_downloads[task_id]["start_time"]
                if elapsed > 0:
                    speed = (i / 100) * 1024 * 1024 / elapsed  # 假设文件大小为1MB
                    task.speed = self._format_speed(speed)
                    
                time.sleep(0.1)  # 模拟下载延迟
            
            if task.progress >= 100:
                task.status = "完成"
                task.progress = 100
                task.speed = "0 KB/s"
                self.logger.log(f"下载完成: {task.name}")
                
        except Exception as e:
            task.status = "失败"
            task.error = str(e)
            self.logger.log(f"下载失败: {task.name} - {str(e)}", "ERROR")
            
        # 从活动下载中移除
        if task_id in self.active_downloads:
            del self.active_downloads[task_id]
    
    def _clone_repository(self, task_id: str):
        """克隆Git仓库 (模拟实现)"""
        task = self.downloads[task_id]
        
        try:
            # 模拟克隆过程
            total_steps = 100
            for i in range(task.progress, total_steps + 1):
                if task_id in self.active_downloads and self.active_downloads[task_id].get("cancel"):
                    break
                    
                task.progress = i
                time.sleep(0.2)  # Git克隆通常比文件下载慢
                
                # 更新状态信息
                if i < 30:
                    task.speed = "正在连接仓库..."
                elif i < 60:
                    task.speed = "正在拉取代码..."
                else:
                    task.speed = "正在解析文件..."
            
            if task.progress >= 100:
                task.status = "完成"
                task.progress = 100
                task.speed = "0 KB/s"
                self.logger.log(f"仓库克隆完成: {task.name}")
                
        except Exception as e:
            task.status = "失败"
            task.error = str(e)
            self.logger.log(f"仓库克隆失败: {task.name} - {str(e)}", "ERROR")
            
        # 从活动下载中移除
        if task_id in self.active_downloads:
            del self.active_downloads[task_id]
    
    def _get_filename_from_url(self, url: str) -> str:
        """从URL中提取文件名"""
        try:
            path = url.split("?")[0]  # 移除查询参数
            return os.path.basename(path) or "download"
        except:
            return "download"
    
    def _get_repo_name(self, url: str) -> str:
        """从Git URL中提取仓库名"""
        try:
            # 处理常见的Git URL格式
            if url.endswith(".git"):
                url = url[:-4]
                
            parts = url.rstrip("/").split("/")
            return parts[-1]
        except:
            return "repository"
    
    def _format_speed(self, bytes_per_second: float) -> str:
        """格式化下载速度"""
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.1f} B/s"
        elif bytes_per_second < 1024 * 1024:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"
