"""Docker client utilities for container detection."""


import docker
from pydantic import BaseModel, Field

# global docker client (initialized on first use)
_docker_client = None

class DockerContainerInfo(BaseModel):
    """Structured information about a Docker container for a process."""
    name: str = Field(..., description="Container name")
    project_name: str|None = Field(None, description="Docker Compose project name")
    mem_usage_mb: float|None = Field(None, description="Memory used by container in MB")
    gpus: int|None = Field(default_factory=list, description="GPUs assigned to the container")
    ports: list[str]|None = Field(default_factory=list, description="Mapped ports in HostPort→ContainerPort format")
    status: str|None = Field(None, description="Container status: running, paused, etc.")
    pid: int|None = Field(None, description="PID of the process in this container")
    image: str|None = Field(None, description="Docker image name")


def get_docker_client():
    """Lazy-load and return the Docker client, or None if unavailable."""
    global _docker_client
    if _docker_client is not None:
        return _docker_client
    try:
        _docker_client = docker.from_env()
        return _docker_client
    except Exception:
        return None


def get_container_info(pid: int) -> tuple[str, str]:
    """Return container name and ports for a given PID.
    
    Returns ("", "") if not in a container or Docker is unavailable.
    """
    client = get_docker_client()
    if client is None:
        return "", ""
    try:
        containers = client.containers.list()
        for container in containers:
            container_pids = container.top()["Processes"]
            for proc_row in container_pids:
                if proc_row and int(proc_row[0]) == pid:
                    name = container.name
                    # Extract port mappings
                    ports = container.ports or {}
                    port_strs = []
                    for container_port, host_mapping in ports.items():
                        if host_mapping:
                            for mapping in host_mapping:
                                host_port = mapping.get("HostPort", "")
                                if host_port:
                                    port_strs.append(f"{host_port}→{container_port}")
                    ports_str = ", ".join(port_strs) or "<none>"
                    return name, ports_str
    except Exception:
        # silently fail; docker may not be available or permissions denied
        pass
    return "", ""
