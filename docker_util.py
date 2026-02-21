"""Docker client utilities for container detection."""

try:
    import docker
except ImportError:
    docker = None

# global docker client (initialized on first use)
_docker_client = None


def get_docker_client():
    """Lazy-load and return the Docker client, or None if unavailable."""
    global _docker_client
    if _docker_client is not None:
        return _docker_client
    if docker is None:
        return None
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
