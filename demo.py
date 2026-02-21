"""Demo mode data generation for testing without hardware."""

import random
from typing import List, Dict, Any

from models import GPUStats, GPUProcess


def get_demo_gpu_stats() -> List[GPUStats]:
    """Generate synthetic GPU statistics for demo mode."""
    stats: List[GPUStats] = []
    for idx in range(4):
        stats.append(
            GPUStats(
                index=idx,
                name=f"DemoGPU{idx}",
                util=random.randint(0, 100),
                mem_used=random.randint(0, 16384),
                mem_total=16384,
                temp=random.randint(20, 90),
                power=random.uniform(10.0, 250.0),
            )
        )
    return stats


def get_demo_gpu_processes(gpu_index: int) -> List[GPUProcess]:
    """Generate synthetic process data for demo mode."""
    procs: List[GPUProcess] = []
    for i in range(10):
        pid = 1000 + gpu_index * 10 + i
        is_container = (i % 3 == 0)
        container_name = f"demo-container-{pid}" if is_container else ""
        container_ports = "8000→8000, 5432→5432" if is_container else ""
        procs.append(
            GPUProcess(
                gpu_index=gpu_index,
                pid=pid,
                name=f"proc{pid}",
                cmdline=f"/usr/bin/proc{pid} --arg",
                mem_mb=random.uniform(10, 2048),
                container=is_container,
                container_name=container_name,
                container_ports=container_ports,
            )
        )
    return procs


def get_demo_process_details(pid: int) -> Dict[str, Any]:
    """Generate fake process details for demo mode."""
    # Determine if this is a Triton process (some demo processes)
    is_triton = (pid % 5 == 0)
    
    fake_env = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "CUDA_VISIBLE_DEVICES": "0,1",
        "USER": "ubuntu",
        "HOME": f"/home/proc{pid}",
        "SHELL": "/bin/bash",
        "PWD": "/workspace",
        "LANG": "en_US.UTF-8",
        "LD_LIBRARY_PATH": "/usr/local/cuda/lib64:/opt/nvidia/lib64",
        "NVIDIA_VISIBLE_DEVICES": "all",
        "PYTHONUNBUFFERED": "1",
        "TF_CPP_MIN_LOG_LEVEL": "2",
    }
    
    if is_triton:
        fake_env.update({
            "TRITON_MODEL_REPOSITORY": "/models",
            "TRITON_METRICS_PORT": "8002",
            "TRITON_GRPC_PORT": "8001",
            "TRITON_HTTP_PORT": "8000",
        })
    
    fake_open_files = [
        {"path": "/dev/nvidia0", "fd": 3},
        {"path": "/dev/nvidia1", "fd": 4},
        {"path": f"/proc/{pid}/stat", "fd": 5},
        {"path": "/var/log/app.log", "fd": 6},
        {"path": "/tmp/cache.db", "fd": 7},
    ]
    
    if is_triton:
        fake_open_files.extend([
            {"path": "/models/resnet50/config.pbtxt", "fd": 8},
            {"path": "/models/bert/model.pb", "fd": 9},
            {"path": "/var/log/triton.log", "fd": 10},
        ])
    
    fake_connections = [
        {
            "type": "socket",
            "laddr": "0.0.0.0:8000",
            "raddr": "127.0.0.1:45000",
            "status": "LISTEN" if is_triton else "ESTABLISHED",
        },
        {
            "type": "socket",
            "laddr": "127.0.0.1:45000",
            "raddr": "192.168.1.100:5432",
            "status": "ESTABLISHED",
        },
        {
            "type": "socket",
            "laddr": "127.0.0.1:45001",
            "raddr": "10.0.0.50:6379",
            "status": "ESTABLISHED",
        },
    ]
    
    if is_triton:
        fake_connections.append({
            "type": "socket",
            "laddr": "0.0.0.0:8001",
            "raddr": "",
            "status": "LISTEN",
        })
    
    return {
        "pid": pid,
        "env": fake_env,
        "cwd": "/workspace",
        "exe": "/usr/bin/python3" if is_triton else f"/usr/bin/proc{pid}",
        "status": "running",
        "open_files": fake_open_files,
        "connections": fake_connections,
        "error": None,
    }


def get_demo_triton_info(pid: int, container_ports: str = "") -> Dict[str, Any]:
    """Generate fake Triton server information for demo mode."""
    # Only return Triton info for processes where (pid % 5 == 0)
    if pid % 5 != 0:
        return {
            "is_triton": False,
            "server_url": None,
            "models": [],
            "error": "Process is not running Triton",
        }
    
    # Generate fake models
    models = [
        {
            "name": "resnet50",
            "state": "READY",
            "version": "1",
            "stats": {
                "inference_count": random.randint(100, 5000),
                "execution_count": random.randint(100, 5000),
            },
            "config": "input_shape: [1, 224, 224, 3], output_shape: [1, 1000]...",
        },
        {
            "name": "bert-base",
            "state": "READY",
            "version": "1",
            "stats": {
                "inference_count": random.randint(100, 5000),
                "execution_count": random.randint(100, 5000),
            },
            "config": "input_tokens: [1, 512], output_logits: [1, 30522]...",
        },
        {
            "name": "yolov8",
            "state": "LOADING" if random.random() > 0.7 else "READY",
            "version": "2",
            "stats": {
                "inference_count": random.randint(50, 2000),
                "execution_count": random.randint(50, 2000),
            },
            "config": "input_image: [1, 640, 640, 3], output_detections: [1, 25200, 85]...",
        },
        {
            "name": "gpt-neo-small",
            "state": "READY",
            "version": "1",
            "stats": {
                "inference_count": random.randint(500, 10000),
                "execution_count": random.randint(500, 10000),
            },
            "config": "input_ids: [1, 512], output_logits: [1, 512, 50257]...",
        },
    ]
    
    return {
        "is_triton": True,
        "server_url": "http://localhost:8000",
        "models": models,
        "error": None,
    }
