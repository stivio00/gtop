"""GTOP - GPU monitoring TUI.

Entry point for the application.
"""

import sys
import argparse
import json

# Set demo mode early if needed
import demo as demo_module
import gpu as gpu_module
import process as process_module
import process_info as process_info_module
import triton_util as triton_util_module
import ui as ui_module

VERSION = "0.1.0"


def main() -> None:
    """Entry point: run the textual app or query mode."""
    parser = argparse.ArgumentParser(description="GTOP GPU monitor")
    parser.add_argument(
        "-d",
        "--demo",
        action="store_true",
        help="run in demo mode with synthetic GPU/process data",
    )
    parser.add_argument(
        "-q",
        "--query",
        action="store_true",
        help="query GPU/process info and output as JSON, then exit",
    )
    args = parser.parse_args()

    # Set demo mode globally
    demo_module.DEMO_MODE = args.demo
    gpu_module.DEMO_MODE = args.demo
    process_module.DEMO_MODE = args.demo
    process_info_module.DEMO_MODE = args.demo
    triton_util_module.DEMO_MODE = args.demo
    ui_module.DEMO_MODE = args.demo

    # If --query flag is set, dump data as JSON and exit
    if args.query:
        if args.demo:
            stats = demo_module.get_demo_gpu_stats()
        else:
            stats = gpu_module.get_gpu_stats()

        output = {"gpus": [s.model_dump() for s in stats], "processes": {}}
        for gpu in stats:
            if args.demo:
                procs = demo_module.get_demo_gpu_processes(gpu.index)
            else:
                procs = process_module.get_gpu_processes(gpu.index)
            output["processes"][str(gpu.index)] = [
                p.model_dump() for p in procs
            ]
        print(json.dumps(output, indent=2))
        sys.exit(0)

    # Otherwise run the TUI
    app = ui_module.GPUApp()
    app.title = f"GTOP v{VERSION}"
    app.run()


if __name__ == "__main__":
    main()
