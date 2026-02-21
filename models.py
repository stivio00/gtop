"""Pydantic models for GPU and process data."""

from pydantic import BaseModel


class GPUStats(BaseModel):
    """Statistics for a single GPU."""

    index: int
    name: str
    util: int
    mem_used: int
    mem_total: int
    temp: int
    power: float


class GPUProcess(BaseModel):
    """Information about a process using a GPU."""

    gpu_index: int
    pid: int
    name: str
    cmdline: str
    mem_mb: float
    container: bool
    container_name: str = ""
    container_ports: str = ""
