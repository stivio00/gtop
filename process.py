"""GPU process retrieval and container detection."""

from typing import List

import psutil
import pynvml

from models import GPUProcess
from docker_util import get_container_info
from demo import get_demo_gpu_processes

# Runtime mode flag - will be set by main.py
DEMO_MODE = False


def get_gpu_processes(gpu_index: int) -> List[GPUProcess]:
    """Return list of processes currently using the given GPU index.
    
    In demo mode, returns synthetic data. Otherwise queries NVML.
    Returns an empty list if NVML is unavailable.
    """
    if DEMO_MODE:
        return get_demo_gpu_processes(gpu_index)

    if pynvml is None:
        return []

    procs: List[GPUProcess] = []
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
        # compute and graphics processes are both interesting
        nvml_procs = []
        try:
            nvml_procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
        except pynvml.NVMLError:
            pass
        try:
            nvml_procs += pynvml.nvmlDeviceGetGraphicsRunningProcesses(handle)
        except pynvml.NVMLError:
            pass
    except pynvml.NVMLError:
        return procs

    seen = set()
    for np in nvml_procs:
        pid = getattr(np, "pid", None)
        if pid is None or pid in seen:
            continue
        seen.add(pid)

        # Check if running in a container and get info
        container_name = ""
        container_ports = ""
        is_container = False
        try:
            with open(f"/proc/{pid}/cgroup", "r") as f:
                data = f.read()
                is_container = any(
                    term in data for term in ("docker", "kubepols", "containerd", "lxc")
                )
                if is_container:
                    container_name, container_ports = get_container_info(pid)
        except Exception:
            pass

        try:
            p = psutil.Process(pid)
            name = p.name()
            cmdline = " ".join(p.cmdline())
            mem_mb = p.memory_info().rss / 1024.0 / 1024.0
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            name = "<unknown>"
            cmdline = ""
            mem_mb = 0.0

        procs.append(
            GPUProcess(
                gpu_index=gpu_index,
                pid=pid,
                name=name,
                cmdline=cmdline,
                mem_mb=mem_mb,
                container=is_container,
                container_name=container_name,
                container_ports=container_ports,
            )
        )
    return procs
