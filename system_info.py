import random

import psutil
import datetime
import platform
from pydantic import BaseModel
from pynvml import *

class SystemInfo(BaseModel):
    os_name: str
    kernel_version: str
    uptime_seconds: int
    uptime_readable: str

    cpu_count_logical: int
    cpu_count_physical: int | None
    cpu_model: str

    def nice(self) -> str:
        return (
            f"{self.os_name} (Kernel: {self.kernel_version})"
            f"Uptime: {self.uptime_readable} - "
            f"CPU: {self.cpu_model} "
            f"C: {self.cpu_count_physical} p / "
            f"{self.cpu_count_logical} l"
        )

class NvidiaInfo(BaseModel):
    driver_version: str
    cuda_driver_version: str
    nvml_version: str
    device_count: int

    persistence_mode_enabled: bool|None  # None if unknown, True/False if known
    timestamp: datetime.datetime

    def nice(self) -> str:
        persistence_str = (
            "Persistence: On" if self.persistence_mode_enabled else "Persistence: Off"
            if self.persistence_mode_enabled is not None else "Persistence: Unknown"
        )
        return (
            f"NVIDIA Driver: {self.driver_version} | "
            f"CUDA Driver: {self.cuda_driver_version} | "
            f"NVML: {self.nvml_version} | "
            f"GPUs: {self.device_count} | "
            f"{persistence_str}"
        )


def _decode(value):
    if isinstance(value, bytes):
        return value.decode()
    return value


def _cuda_version_string(version_int: int) -> str:
    major = version_int // 1000
    minor = (version_int % 1000) // 10
    return f"{major}.{minor}"


def get_nvidia_info() -> NvidiaInfo|None:
    try:
        nvmlInit()  # no shutdown, as requested

        driver_version = _decode(nvmlSystemGetDriverVersion())
        nvml_version = _decode(nvmlSystemGetNVMLVersion())

        cuda_version_int = nvmlSystemGetCudaDriverVersion()
        cuda_driver_version = _cuda_version_string(cuda_version_int)

        device_count = nvmlDeviceGetCount()

        # Persistence mode (global check via first device if exists)
        persistence_mode = None
        if device_count > 0:
            try:
                handle = nvmlDeviceGetHandleByIndex(0)
                persistence_mode = (
                    nvmlDeviceGetPersistenceMode(handle)
                    == NVML_FEATURE_ENABLED
                )
            except NVMLError:
                persistence_mode = None

        return NvidiaInfo(
            driver_version=driver_version,
            cuda_driver_version=cuda_driver_version,
            nvml_version=nvml_version,
            device_count=device_count,
            persistence_mode_enabled=persistence_mode,
            timestamp=datetime.datetime.utcnow(),
        )

    except NVMLError:
        return None


def get_nvidia_demo_info() -> NvidiaInfo:
    return NvidiaInfo(
        driver_version="550.54.14",
        cuda_driver_version="12.4",
        nvml_version="12.550.54.14",
        device_count=random.choice([1, 2, 4]),
        persistence_mode_enabled=True,
        timestamp=datetime.datetime.utcnow(),
    )


def get_system_info() -> SystemInfo:
    # OS name (Linux, Windows, Darwin)
    os_name = platform.system()

    # Kernel version (Windows build, Linux kernel, macOS Darwin version)
    kernel_version = platform.release()

    # Uptime
    boot_time = psutil.boot_time()
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_time)

    # CPU info
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False)

    # CPU model (platform-dependent)
    cpu_model = platform.processor()

    # Fallback if processor() returns empty (common on Linux)
    if not cpu_model:
        cpu_model = platform.uname().processor

    return SystemInfo(
        os_name=os_name,
        kernel_version=kernel_version,
        uptime_seconds=int(uptime.total_seconds()),
        uptime_readable=str(uptime).split(".")[0],
        cpu_count_logical=cpu_count_logical,
        cpu_count_physical=cpu_count_physical,
        cpu_model=cpu_model or "Unknown"
    )
