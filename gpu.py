"""GPU statistics retrieval via NVML."""

from typing import List

import pynvml

from models import GPUStats
from demo import get_demo_gpu_stats

# Runtime mode flag - will be set by main.py
DEMO_MODE = False


def get_gpu_stats() -> List[GPUStats]:
    """Return a list of GPUStats objects for each NVIDIA GPU.
    
    In demo mode, returns synthetic data. Otherwise queries NVML.
    Returns an empty list if NVML is unavailable or no GPUs are found.
    """
    if DEMO_MODE:
        return get_demo_gpu_stats()

    if pynvml is None:
        return []

    try:
        pynvml.nvmlInit()
    except pynvml.NVMLError:
        return []

    stats: List[GPUStats] = []
    try:
        count = pynvml.nvmlDeviceGetCount()
    except pynvml.NVMLError:
        return stats

    for idx in range(count):
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
            name = pynvml.nvmlDeviceGetName(handle).decode("utf-8", errors="ignore")
            util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            mem_used = mem.used // 1024 // 1024
            mem_total = mem.total // 1024 // 1024
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            try:
                power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
            except pynvml.NVMLError:
                power = 0.0

            stats.append(
                GPUStats(
                    index=idx,
                    name=name,
                    util=util,
                    mem_used=mem_used,
                    mem_total=mem_total,
                    temp=temp,
                    power=power,
                )
            )
        except pynvml.NVMLError:
            continue

    return stats
