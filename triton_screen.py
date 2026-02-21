"""Modal screen for displaying Triton models information."""

from textual.screen import ModalScreen
from textual.containers import ScrollableContainer
from textual.widgets import Static
from textual.binding import Binding

from triton_util import get_triton_info


class TritonModelsScreen(ModalScreen):
    """Modal screen showing Triton models and statistics."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("q", "app.pop_screen", "Close"),
        Binding("pageup", "scroll_up", "Scroll Up"),
        Binding("pagedown", "scroll_down", "Scroll Down"),
    ]

    CSS = """
    TritonModelsScreen {
        align: center middle;
    }
    
    TritonModelsScreen > ScrollableContainer {
        width: 90%;
        height: 90%;
        border: solid $accent;
        background: $panel;
    }
    
    TritonModelsScreen > ScrollableContainer > Static {
        width: 100%;
    }
    """

    def __init__(self, pid: int, container_ports: str = ""):
        super().__init__()
        self.pid = pid
        self.container_ports = container_ports

    def compose(self):
        with ScrollableContainer(id="triton-scroll"):
            yield Static(id="triton-content")

    def on_mount(self):
        self.title = f"Triton Models: PID {self.pid}"
        self._update_content()

    def action_scroll_up(self) -> None:
        """Scroll up in the content."""
        container = self.query_one("#triton-scroll", ScrollableContainer)
        container.scroll_up()

    def action_scroll_down(self) -> None:
        """Scroll down in the content."""
        container = self.query_one("#triton-scroll", ScrollableContainer)
        container.scroll_down()

    def _update_content(self):
        """Update the screen content with Triton model information."""
        info = get_triton_info(self.pid, self.container_ports)

        output = []
        output.append(f"\n[bold cyan]Triton Model Server[/] PID: {self.pid}\n")

        if info["error"]:
            output.append(f"[red]Error: {info['error']}[/]\n")
        elif not info["is_triton"]:
            output.append("[yellow]Process is not running Triton[/]\n")
        else:
            output.append(f"[green]✓ Triton Server Detected[/]\n")
            
            if info["server_url"]:
                output.append(f"[yellow]Server URL:[/] {info['server_url']}\n")

            # Display models
            if info["models"]:
                output.append(f"\n[bold yellow]Loaded Models ({len(info['models'])})[/]\n")
                output.append("[dim]─ " * 30 + "[/]\n")
                
                for model in info["models"]:
                    output.append(f"\n  [bold white]{model.get('name', 'Unknown')}[/]\n")
                    
                    state = model.get('state', 'unknown').upper()
                    state_color = "green" if state == "READY" else "yellow" if state == "LOADING" else "red"
                    output.append(f"    [blue]State:[/] [{state_color}]{state}[/]\n")
                    
                    if model.get('version'):
                        output.append(f"    [blue]Version:[/] {model['version']}\n")
                    
                    if "stats" in model and model["stats"]:
                        stats = model["stats"]
                        output.append(f"    [blue]Inference Count:[/] {stats.get('inference_count', 0)}\n")
                        output.append(f"    [blue]Execution Count:[/] {stats.get('execution_count', 0)}\n")
                    
                    if "config" in model:
                        output.append(f"    [blue]Config:[/] {model['config']}\n")
            else:
                output.append("\n[yellow]No models currently loaded[/]\n")

        output.append("\n[dim]Press 'q' or 'Esc' to close[/]\n")

        content_widget = self.query_one("#triton-content", Static)
        content_widget.update("".join(output))
