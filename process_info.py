"""Utilities for retrieving detailed process information."""

import psutil

# Use this in the module when DEMO_MODE is set
DEMO_MODE = False


def get_process_details(pid: int) -> dict:
    """Retrieve detailed information about a process.
    
    Returns a dict with env vars, open files, connections, and other details.
    """
    # In demo mode, return synthetic data
    if DEMO_MODE:
        from demo import get_demo_process_details
        return get_demo_process_details(pid)
    
    details = {
        "pid": pid,
        "env": {},
        "cwd": "",
        "exe": "",
        "status": "",
        "open_files": [],
        "connections": [],
        "error": None,
    }
    
    try:
        p = psutil.Process(pid)
        
        # Basic info
        details["exe"] = p.exe()
        details["cwd"] = p.cwd()
        details["status"] = p.status()
        
        # Environment variables
        try:
            details["env"] = dict(p.environ())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            details["env"] = {"error": "Permission denied"}
        
        # Open files
        try:
            details["open_files"] = [
                {"path": f.path, "fd": f.fd} for f in p.open_files()[:10]
            ]
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        
        # Network connections
        try:
            details["connections"] = [
                {
                    "type": c.type,
                    "laddr": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "",
                    "raddr": f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "",
                    "status": c.status,
                }
                for c in p.net_connections()[:5]
            ]
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        
    except psutil.NoSuchProcess:
        details["error"] = f"Process {pid} not found"
    except psutil.AccessDenied:
        details["error"] = f"Access denied for process {pid}"
    except Exception as e:
        details["error"] = str(e)
    
    return details
