"""Textual TUI for GPU monitoring."""

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header
from rich.progress import ProgressBar

from gpu import get_gpu_stats
from process import get_gpu_processes
from process_screen import ProcessInfoScreen
from triton_screen import TritonModelsScreen
import triton_util

# Use this in the module when DEMO_MODE is set
DEMO_MODE = False


class GPUApp(App):
    """GPU monitoring TUI powered by NVML."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("up,down", "select_gpu", "Navigate GPU"),
        ("tab", "focus_processes", "Focus Processes"),
        ("i", "show_process_info", "Process Info"),
        ("m", "show_triton_models", "Triton Models"),
    ]

    CSS_PATH = None  # no CSS for now

    def compose(self) -> ComposeResult:
        yield Header()
        # use renderable priority so colored progress bars keep their hue when a row is selected
        self.table = DataTable(
            zebra_stripes=True,
            id="gpu-table",
            cursor_type="row",
            cursor_foreground_priority="renderable",
            cursor_background_priority="renderable",
        )
        self.table.add_columns(
            "GPU",
            "Name",
            "%Util",
            "Mem %",
            "Mem [used/total]",
            "Mem Bar",
            "Temp C",
            "Power W",
        )
        self.proc_table = DataTable(
            zebra_stripes=True,
            id="proc-table",
            cursor_type="row",
            cursor_foreground_priority="renderable",
            cursor_background_priority="renderable",
        )
        self.proc_table.add_columns(
            "GPU",
            "PID",
            "Name",
            "Cmdline",
            "RAM MB",
            "Container",
            "Container Name",
            "Ports",
        )
        yield self.table
        yield self.proc_table
        yield Footer()

    def on_mount(self) -> None:
        # set title and subtitle
        self.title = "GTOP v0.1.0"
        self.sub_title = "GPU Monitor"
        # refresh once per second
        self.set_interval(1.0, self._refresh)
        # immediately fill table so UI isn't blank for one tick
        self._refresh()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        # same behaviour as selecting a row; keep process table in sync
        if event.data_table is self.table:
            self._update_process_table(event.cursor_row)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # when a row becomes selected (e.g. via Enter or click), refresh process table
        if event.data_table is self.table:
            self._update_process_table(event.cursor_row)

    def action_select_gpu(self) -> None:
        """Move cursor in GPU table (handled via default bindings)."""
        pass

    def action_focus_processes(self) -> None:
        """Switch focus to the process table."""
        if self.proc_table.visible:
            self.proc_table.focus()

    def action_show_process_info(self) -> None:
        """Show detailed info for the selected process."""
        # Only works if proc_table is focused
        if self.proc_table.has_focus:
            row = self.proc_table.cursor_row
            if row is not None and 0 <= row < self.proc_table.row_count:
                try:
                    proc_row = self.proc_table.get_row_at(row)
                    # proc_row is (gpu_idx, pid, name, ...)
                    gpu_idx = int(proc_row[0])
                    pid = int(proc_row[1])
                    self.push_screen(
                        ProcessInfoScreen(gpu_idx, pid)
                    )
                except (ValueError, IndexError):
                    pass

    def action_show_triton_models(self) -> None:
        """Show Triton models for the selected process."""
        # Only works if proc_table is focused
        if self.proc_table.has_focus:
            row = self.proc_table.cursor_row
            if row is not None and 0 <= row < self.proc_table.row_count:
                try:
                    proc_row = self.proc_table.get_row_at(row)
                    # proc_row is (gpu_idx, pid, name, cmdline, mem_mb, container, container_name, container_ports)
                    pid = int(proc_row[1])
                    container_ports = str(proc_row[7]) if len(proc_row) > 7 else ""
                    
                    # Check if this process is running Triton
                    if triton_util.is_triton_process(pid):
                        self.push_screen(
                            TritonModelsScreen(pid, container_ports)
                        )
                except (ValueError, IndexError):
                    pass

    def _refresh(self) -> None:
        stats = get_gpu_stats()
        # remember where cursor was so we don't lose selection
        old_cursor = self.table.cursor_row
        self.table.clear()
        if not stats:
            # show a placeholder message in the table
            self.table.add_row(
                "-",
                "No NVIDIA GPUs detected",
                "",
                "",
                "",
                "",
                "",
                "",
            )
            # clear or populate process table with a message
            self.proc_table.clear()
            self.proc_table.add_row("-", "-", "No GPUs", "", "", "", "", "")
        else:
            for g in stats:
                mem_pct = (
                    int((g.mem_used / g.mem_total) * 100) if g.mem_total else 0
                )
                # choose bar color based on percent
                if mem_pct < 75:
                    complete_style = "green"
                elif mem_pct < 90:
                    complete_style = "yellow"
                else:
                    complete_style = "red"
                bar = ProgressBar(
                    total=g.mem_total,
                    completed=g.mem_used,
                    width=10,
                    style="bar.back",
                    complete_style=complete_style,
                )
                self.table.add_row(
                    str(g.index),
                    g.name,
                    str(g.util),
                    f"{mem_pct}%",
                    f"{g.mem_used}/{g.mem_total}",
                    bar,
                    str(g.temp),
                    f"{g.power:.1f}",
                )
            # restore cursor position if still valid
            if 0 <= old_cursor < self.table.row_count:
                # use keyword arguments; cursor_column may be None
                self.table.move_cursor(
                    row=old_cursor, column=self.table.cursor_column or 0
                )
            # refresh processes for the currently highlighted/selected row
            self._update_process_table(self.table.cursor_row)

    def _update_process_table(self, row: int) -> None:
        # remember where cursor was in process table
        old_proc_cursor = self.proc_table.cursor_row
        # clear first
        self.proc_table.clear()
        # sanity check input
        if row is None or row < 0 or row >= self.table.row_count:
            return
        try:
            gpu_index = int(self.table.get_row_at(row)[0])
        except Exception:
            return
        procs = get_gpu_processes(gpu_index)
        if not procs:
            self.proc_table.add_row(str(gpu_index), "-", "", "", "", "", "", "")
            return
        for p in procs:
            self.proc_table.add_row(
                str(p.gpu_index),
                str(p.pid),
                p.name,
                p.cmdline,
                f"{p.mem_mb:.1f}",
                "yes" if p.container else "no",
                p.container_name,
                p.container_ports,
            )
        # restore cursor position in process table if it was valid
        if 0 <= old_proc_cursor < self.proc_table.row_count:
            self.proc_table.move_cursor(
                row=old_proc_cursor, column=self.proc_table.cursor_column or 0
            )
