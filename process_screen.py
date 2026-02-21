"""Modal screen for showing detailed process information."""

from textual.screen import ModalScreen
from textual.containers import ScrollableContainer
from textual.widgets import Static
from textual.binding import Binding

from process_info import get_process_details
from gpu import get_gpu_stats


class ProcessInfoScreen(ModalScreen):
    """Modal screen showing detailed process information."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("q", "app.pop_screen", "Close"),
        Binding("pageup", "scroll_up", "Scroll Up"),
        Binding("pagedown", "scroll_down", "Scroll Down"),
    ]

    CSS = """
    ProcessInfoScreen {
        align: center middle;
    }
    
    ProcessInfoScreen > ScrollableContainer {
        width: 90%;
        height: 90%;
        border: solid $accent;
        background: $panel;
    }
    
    ProcessInfoScreen > ScrollableContainer > Static {
        width: 100%;
    }
    """

    def __init__(self, gpu_index: int, pid: int):
        super().__init__()
        self.gpu_index = gpu_index
        self.pid = pid

    def compose(self):
        with ScrollableContainer(id="process-info-scroll"):
            yield Static(id="process-info-content")

    def on_mount(self):
        self.title = f"Process Info: PID {self.pid}"
        self._update_content()

    def action_scroll_up(self) -> None:
        """Scroll up in the content."""
        container = self.query_one("#process-info-scroll", ScrollableContainer)
        container.scroll_up()

    def action_scroll_down(self) -> None:
        """Scroll down in the content."""
        container = self.query_one("#process-info-scroll", ScrollableContainer)
        container.scroll_down()

    def _update_content(self):
        """Update the screen content with process details."""
        details = get_process_details(self.pid)
        
        # Get GPU model info
        gpu_name = "Unknown GPU"
        stats = get_gpu_stats()
        for g in stats:
            if g.index == self.gpu_index:
                gpu_name = g.name
                break
        
        # Build the info text
        output = []
        output.append(f"\n[bold cyan]Process Information[/] PID: {self.pid}\n")
        output.append(f"[yellow]GPU:[/] {gpu_name} (Index: {self.gpu_index})\n")
        
        if details["error"]:
            output.append(f"[red]{details['error']}[/]\n")
        else:
            if details["exe"]:
                output.append(f"[yellow]Executable:[/] {details['exe']}\n")
            if details["cwd"]:
                output.append(f"[yellow]Working Dir:[/] {details['cwd']}\n")
            if details["status"]:
                output.append(f"[yellow]Status:[/] {details['status']}\n")
            
            # Environment variables (limit to first 20)
            if details["env"]:
                output.append("\n[bold yellow]Environment Variables[/]\n")
                env_items = list(details["env"].items())[:20]
                for key, val in env_items:
                    # Truncate long values
                    val_str = str(val)[:60]
                    output.append(f"  {key}={val_str}\n")
                if len(details["env"]) > 20:
                    output.append(f"  ... and {len(details['env']) - 20} more\n")
            
            # Open files
            if details["open_files"]:
                output.append("\n[bold yellow]Open Files[/]\n")
                for f in details["open_files"]:
                    output.append(f"  FD {f['fd']}: {f['path']}\n")
            
            # Network connections
            if details["connections"]:
                output.append("\n[bold yellow]Network Connections[/]\n")
                for c in details["connections"]:
                    output.append(
                        f"  {c['type'].upper()}: {c['laddr']} -> {c['raddr']} [{c['status']}]\n"
                    )
        
        output.append("\n[dim]Press 'q' or 'Esc' to close[/]\n")
        
        content_widget = self.query_one("#process-info-content", Static)
        content_widget.update("".join(output))
