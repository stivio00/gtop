"""Utilities for detecting and connecting to NVIDIA Triton servers."""

import psutil
import socket
from typing import Optional, Dict, List, Any

# Use this in the module when DEMO_MODE is set
DEMO_MODE = False

# Triton client is required; import unconditionally
import tritonclient.http as triton_http
TRITON_AVAILABLE = True


def is_triton_process(pid: int) -> bool:
    """Check if a process is a Triton server.
    
    Looks for:
    - Process name containing 'triton'
    - Executable containing 'tritonserver'
    - Environment variable TRITON_MODEL_REPOSITORY
    """
    # In demo mode, processes with PIDs ending in 5 are Triton processes (1005, 1015, 1025, etc.)
    if DEMO_MODE:
        return pid % 5 == 0
    
    try:
        p = psutil.Process(pid)
        name = p.name().lower()
        exe = p.exe().lower() if p.exe() else ""
        
        if "triton" in name or "tritonserver" in exe:
            return True
        
        # Check environment for Triton indicators
        try:
            env = p.environ()
            if "TRITON_MODEL_REPOSITORY" in env:
                return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        
        return False
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return False


def find_triton_server_url(pid: int, container_ports: Optional[str] = None) -> Optional[str]:
    """Find the Triton server URL for a given process.
    
    Try to detect the server from:
    1. Container port mappings
    2. Process open ports
    3. Standard Triton ports (8000, 8001, 8002)
    """
    # Try common Triton ports in order
    standard_ports = [8000, 8001, 8002]  # HTTP, gRPC, Metrics
    
    # If container ports are provided, try to extract the mapped port
    if container_ports:
        # container_ports format: "8000→8000, 8001→8001"
        parts = container_ports.split(",")
        for part in parts:
            try:
                # Extract the host port (first number)
                host_port = int(part.split("→")[0].strip())
                if _is_port_open("localhost", host_port):
                    return f"http://localhost:{host_port}"
            except (ValueError, IndexError):
                pass
    
    # Try standard ports
    for port in standard_ports:
        if _is_port_open("localhost", port):
            return f"http://localhost:{port}"
    
    return None


def _is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Check if a port is open on the given host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def get_triton_models(server_url: str) -> Dict[str, Any]:
    """Get model information from a Triton server.
    
    Returns a dict with:
    - models: List of model info (name, version, state)
    - server_status: Server metadata
    - error: Error message if connection failed
    """
    result = {
        "models": [],
        "server_status": {},
        "error": None,
    }
    
    if not TRITON_AVAILABLE:
        result["error"] = "tritonclient not installed"
        return result
    
    try:
        # Create client
        client = triton_http.InferenceServerClient(url=server_url, verbose=False)
        
        # Check if server is live
        if not client.is_server_live(as_soon=True):
            result["error"] = "Triton server not responding"
            return result
        
        # Get server metadata
        try:
            result["server_status"] = {
                "version": client.get_server_metadata().model_dump() if hasattr(client.get_server_metadata(), 'model_dump') else str(client.get_server_metadata()),
            }
        except Exception as e:
            result["server_status"] = {"error": str(e)}
        
        # Get model repository
        try:
            index = client.get_model_repository_index()
            for model_info in index:
                model_data = {
                    "name": model_info.name if hasattr(model_info, 'name') else "unknown",
                    "state": model_info.state if hasattr(model_info, 'state') else "unknown",
                    "version": getattr(model_info, 'version', None),
                }
                
                # Try to get model config and stats
                try:
                    config = client.get_model_config(model_data["name"])
                    model_data["config"] = str(config)[:200]  # Truncate for display
                except Exception:
                    pass
                
                try:
                    stats = client.get_model_statistics(model_data["name"])
                    if stats and len(stats) > 0:
                        stat = stats[0]
                        model_data["stats"] = {
                            "inference_count": getattr(stat, 'inference_count', 0),
                            "execution_count": getattr(stat, 'execution_count', 0),
                        }
                except Exception:
                    pass
                
                result["models"].append(model_data)
        
        except Exception as e:
            result["error"] = f"Failed to get models: {str(e)}"
    
    except Exception as e:
        result["error"] = f"Failed to connect to Triton: {str(e)}"
    
    return result


def get_triton_info(pid: int, container_ports: Optional[str] = None) -> Dict[str, Any]:
    """Get complete Triton information for a process.
    
    Returns info about Triton models loaded on the server if running.
    """
    # In demo mode, return synthetic data
    if DEMO_MODE:
        from demo import get_demo_triton_info
        return get_demo_triton_info(pid, container_ports or "")
    
    info = {
        "is_triton": False,
        "server_url": None,
        "models": [],
        "error": None,
    }
    
    # Check if this is a Triton process
    if not is_triton_process(pid):
        info["error"] = "Process is not running Triton"
        return info
    
    info["is_triton"] = True
    
    # Try to find the server URL
    server_url = find_triton_server_url(pid, container_ports)
    if not server_url:
        info["error"] = "Could not find Triton server URL"
        return info
    
    info["server_url"] = server_url
    
    # Get models
    models_info = get_triton_models(server_url)
    info["models"] = models_info["models"]
    info["error"] = models_info.get("error")
    
    return info
