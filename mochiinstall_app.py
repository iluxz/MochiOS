#!/usr/bin/env python3

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, Input, SelectionList, Log, Label, ProgressBar
from textual.containers import Vertical, Horizontal, Container
from textual.message import Message
from textual.binding import Binding
import subprocess
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mochi_ascii import MOCHI_ASCII
from installer import do_install


STEP_NAMES = ["Hostname", "Disk", "Filesystem", "Kernel", "Extras", "Desktop & Boot", "User", "Review"]


class LogUpdate(Message):
    def __init__(self, text: str):
        super().__init__()
        self.text = text


class InstallDone(Message):
    def __init__(self, success: bool):
        super().__init__()
        self.success = success


class StepBar(Static):
    def render_step(self, step: int) -> str:
        dots = ""
        for i in range(8):
            if i < step:
                dots += "■ "
            elif i == step:
                dots += "● "
            else:
                dots += "○ "
        return f"[bold purple]◆ mochios[/]    {dots}   [bold]{STEP_NAMES[step]}[/]"


class NavBar(Static):
    def render_nav(self, can_back: bool, can_next: bool, next_label: str = "next") -> str:
        back = r"[dim]\[b][/] back" if can_back else r"[dim]\[b][/] [bright_black]back[/]"
        nxt = rf"[dim]\[n][/] {next_label}" if can_next else ""
        return rf"  {back}    {nxt}    [dim]\[q][/] quit  "


class WelcomeScreen(Screen):
    BINDINGS = [
        Binding("enter", "guided", "guided"),
        Binding("m", "manual", "manual"),
        Binding("q", "quit", "quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            Static("", id="welcome_spacer_top"),
            Static(f"[bold purple]{MOCHI_ASCII}[/]", id="ascii"),
            Static("[bold purple]mochios installer[/]", id="title"),
            Static("arch linux, mochi-powered, atomic updates"),
            Static(""),
            Static(r"  [bold]guided[/]  [dim]\[enter][/]  step-by-step guided install"),
            Static(r"  [bold]manual[/]  [dim]\[m][/]     expert install (coming soon)"),
            Static(r"  [bold]quit[/]   [dim]\[q][/]     exit to shell"),
            id="welcome_box",
        )

    def action_guided(self):
        self.app.push_screen(GuidedScreen())

    def action_manual(self):
        self.app.push_screen(ManualScreen())

    def action_quit(self):
        self.app.exit()


class GuidedScreen(Screen):
    BINDINGS = [
        Binding("n", "next_step", "next"),
        Binding("enter", "next_step", "next"),
        Binding("b", "prev_step", "back"),
        Binding("escape", "prev_step", "back"),
        Binding("q", "quit", "quit"),
        Binding("r", "refresh_disks", "refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.step = 0
        self.config = {"de": "kde", "disk": "", "filesystem": "btrfs", "bootloader": "limine", "kernels": ["linux"], "hostname": "mochios", "username": "mochi", "password": "mochi", "extra_pkgs": []}

    def compose(self) -> ComposeResult:
        yield Container(
            StepBar(id="step_bar"),
            Container(id="step_body"),
            NavBar(id="nav_bar"),
            id="guided_shell",
        )

    def on_mount(self) -> None:
        self.body = self.query_one("#step_body")
        self.step_bar = self.query_one("#step_bar")
        self.nav_bar = self.query_one("#nav_bar")
        self.render_step()

    def render_step(self) -> None:
        if not (0 <= self.step < 8):
            self.app.pop_screen()
            return
        self.step_bar.update(self.step_bar.render_step(self.step))
        self.body.remove_children()
        step_fn = [self.step_hostname, self.step_disk, self.step_fs, self.step_kernel, self.step_extra, self.step_de_boot, self.step_user, self.step_summary][self.step]
        step_fn()
        self._focus_step()

    def _nav(self, can_back: bool = True, can_next: bool = True, next_label: str = "next") -> None:
        self.nav_bar.update(self.nav_bar.render_nav(can_back, can_next, next_label))

    def _focus_step(self) -> None:
        if self.step == 0:
            self._try_focus("#hostname", Input)
        elif self.step == 1:
            self._try_focus_sel("#disk_list")
        elif self.step == 2:
            self._try_focus_sel("#fs")
        elif self.step == 3:
            self._try_focus_sel("#kernel")
        elif self.step == 4:
            self._try_focus_sel("#extra_pkgs")
        elif self.step == 5:
            self._try_focus_sel("#de")
            self._try_focus_sel("#bootloader")
        elif self.step == 6:
            self._try_focus("#username", Input)

    def _try_focus(self, selector, widget_type):
        try:
            self.query_one(selector, widget_type).focus()
        except Exception:
            pass

    def _try_focus_sel(self, selector):
        try:
            sel = self.query_one(selector, SelectionList)
            if sel.children:
                sel.focus()
        except Exception:
            pass

    def _push_next(self) -> bool:
        if self.step == 6:
            pw = self.config.get("password", "")
            pw_c = self.config.get("password_confirm", "")
            hint = self.query_one("#pw_hint", Label) if self.body.query("#pw_hint") else None
            if not pw:
                if hint: hint.update("[red]password cannot be empty[/]")
                return False
            if pw != pw_c:
                if hint: hint.update("[red]passwords do not match[/]")
                return False
        self.collect_current()
        if self.step == 7:
            if not self.config.get("disk"):
                self.step = 1
                self.render_step()
                return False
            self.app.push_screen(ProgressScreen(self.config))
            return True
        self.step += 1
        self.render_step()
        return True

    def _pop_back(self) -> None:
        self.collect_current()
        self.step = max(0, self.step - 1)
        self.render_step()

    def action_next_step(self) -> None:
        self._push_next()

    def action_prev_step(self) -> None:
        self._pop_back()

    def action_quit(self) -> None:
        self.app.exit()

    def action_refresh_disks(self) -> None:
        if self.step == 1:
            self.render_step()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.step == 0:
            self._push_next()
        elif self.step == 6 and event.input.id == "username":
            self.query_one("#password", Input).focus()
        elif self.step == 6 and event.input.id == "password":
            self.query_one("#password_confirm", Input).focus()
        elif self.step == 6 and event.input.id == "password_confirm":
            self._push_next()

    # --- step content builders ---

    def _wrap(self, *widgets) -> Vertical:
        return Vertical(*widgets, id="step_content_wrap")

    def step_hostname(self) -> None:
        self.body.mount(self._wrap(
            Static("[bold]hostname[/]"),
            Input(placeholder="mochios", id="hostname", value=self.config["hostname"]),
        ))
        self._nav(can_back=False)

    def _disk_type(self, name: str) -> str:
        try:
            with open(f"/sys/block/{name}/queue/rotational") as f:
                rot = f.read().strip()
            if rot == "1":
                return "HDD"
            elif rot == "0":
                if name.startswith("nvme"): return "NVMe"
                elif name.startswith("mmcblk"): return "SD"
                return "SSD"
        except Exception:
            pass
        if name.startswith("nvme"): return "NVMe"
        elif name.startswith("mmcblk"): return "SD"
        elif name.startswith("vd"): return "VirtIO"
        return ""

    def step_disk(self) -> None:
        disks = []
        boot_dev = ""
        try:
            r = subprocess.run(["findmnt", "-n", "-o", "SOURCE", "/run/archiso/bootmnt"], capture_output=True, text=True, timeout=5)
            if r.stdout.strip():
                r2 = subprocess.run(["lsblk", "-ndo", "PKNAME", r.stdout.strip()], capture_output=True, text=True, timeout=5)
                boot_dev = r2.stdout.strip()
        except Exception:
            pass
        try:
            r = subprocess.run(["lsblk", "-dno", "NAME,SIZE,MODEL"], capture_output=True, text=True, timeout=5)
            for line in r.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 2)
                if parts:
                    name = parts[0]
                    if name.startswith(("loop", "sr", "ram", "cdrom", "dm-", "zram", "nbd")):
                        continue
                    if name == boot_dev:
                        continue
                    dtype = self._disk_type(name)
                    tag = f"({dtype}) " if dtype else ""
                    info = f"{parts[1]} {parts[2] if len(parts) > 2 else ''}"
                    disks.append((f"{tag}/dev/{name} - {info}", f"/dev/{name}"))
        except Exception as e:
            print(f"warning: lsblk failed: {e}", file=sys.stderr)

        kids = [Static("[bold red]WARNING: this disk will be wiped[/]")]
        if not disks:
            kids += [
                Static("[yellow]no disks detected![/]"),
                Static("make sure a disk is connected and try again"),
            ]
            self._nav(can_next=False, next_label="retry [r]")
        else:
            preselected = self.config.get("disk", "")
            kids += [
                SelectionList(*[(d, v, v == preselected) for d, v in disks], id="disk_list"),
            ]
            self._nav(next_label="next")
        self.body.mount(self._wrap(*kids))

    def step_fs(self) -> None:
        self.body.mount(self._wrap(
            Static("[bold]filesystem[/]"),
            SelectionList((("btrfs (snapshots + abroot)", "btrfs", True)), id="fs"),
        ))
        self._nav()

    def step_kernel(self) -> None:
        kernels = self.config.get("kernels", ["linux"])
        self.body.mount(self._wrap(
            Static("[bold]kernel (select one or more)[/]"),
            SelectionList(
                ("linux (stock)", "linux", "linux" in kernels),
                ("linux-zen (desktop tuned)", "linux-zen", "linux-zen" in kernels),
                ("linux-lts (longterm)", "linux-lts", "linux-lts" in kernels),
                ("linux-hardened (security)", "linux-hardened", "linux-hardened" in kernels),
                id="kernel"
            ),
        ))
        self._nav()

    def step_extra(self) -> None:
        extras = self.config.get("extra_pkgs", [])
        self.body.mount(self._wrap(
            Static("[bold]extra packages[/]"),
            SelectionList(
                ("steam", "steam", "steam" in extras),
                ("wine", "wine", "wine" in extras),
                id="extra_pkgs"
            ),
        ))
        self._nav()

    def step_de_boot(self) -> None:
        de = self.config.get("de", "kde")
        bl = self.config.get("bootloader", "limine")
        self.body.mount(self._wrap(
            Static("[bold]desktop environment[/]"),
            SelectionList(
                ("kde plasma", "kde", de == "kde"),
                ("gnome", "gnome", de == "gnome"),
                id="de"
            ),
            Static(""),
            Static("[bold]bootloader[/]"),
            SelectionList(
                ("limine", "limine", bl == "limine"),
                ("grub", "grub", bl == "grub"),
                id="bootloader"
            ),
        ))
        self._nav()

    def step_user(self) -> None:
        self.body.mount(self._wrap(
            Static("[bold]user account[/]"),
            Input(placeholder="mochi", id="username", value=self.config["username"]),
            Input(placeholder="password (required)", id="password", password=True),
            Input(placeholder="confirm password", id="password_confirm", password=True),
            Label("", id="pw_hint"),
        ))
        self._nav()

    def step_summary(self) -> None:
        c = self.config
        disk_set = bool(c["disk"])
        extras = ", ".join(c.get("extra_pkgs", [])) or "none"
        kernels = ", ".join(c.get("kernels", ["linux"])) or "linux"
        self.body.mount(self._wrap(
            Static("[bold underline]review configuration[/]"),
            Static(""),
            Static(f"  hostname:    [white]{c['hostname']}[/]"),
            Static(f"  disk:        [red]{c['disk'] or 'NOT SELECTED'}[/] {'[red bold](required!)' if not disk_set else '(will be wiped)'}"),
            Static(f"  desktop:     [white]{c['de']}[/]"),
            Static(f"  kernels:     [white]{kernels}[/]"),
            Static(f"  bootloader:  [white]{c['bootloader']}[/]"),
            Static(f"  extras:      [white]{extras}[/]"),
            Static(f"  user:        [white]{c['username']}[/]"),
            Static(""),
            Static("[red bold]WARNING: this will erase all data on the selected disk" if disk_set else "[red bold]select a disk first!"),
        ))
        self._nav(next_label="install!" if disk_set else "", can_next=disk_set)

    def collect_current(self) -> None:
        try:
            if self.step == 0:
                inp = self.query_one("#hostname", Input)
                self.config["hostname"] = inp.value or "mochios"
            elif self.step == 1:
                sel = self.query_one("#disk_list", SelectionList)
                if sel.selected:
                    self.config["disk"] = sel.selected[0]
            elif self.step == 3:
                sel = self.query_one("#kernel", SelectionList)
                self.config["kernels"] = sel.selected if sel.selected else ["linux"]
            elif self.step == 4:
                sel = self.query_one("#extra_pkgs", SelectionList)
                self.config["extra_pkgs"] = sel.selected if sel.selected else []
            elif self.step == 5:
                sel_de = self.query_one("#de", SelectionList)
                sel_bl = self.query_one("#bootloader", SelectionList)
                if sel_de.selected:
                    self.config["de"] = sel_de.selected[0]
                if sel_bl.selected:
                    self.config["bootloader"] = sel_bl.selected[0]
            elif self.step == 6:
                u = self.query_one("#username", Input)
                p = self.query_one("#password", Input)
                pc = self.query_one("#password_confirm", Input)
                if u.value:
                    self.config["username"] = u.value
                self.config["password"] = p.value
                self.config["password_confirm"] = pc.value
        except Exception:
            pass


class ManualScreen(Screen):
    BINDINGS = [Binding("escape", "back", "back"), Binding("b", "back", "back")]

    def compose(self) -> ComposeResult:
        yield Container(
            Static("[bold purple]◆ mochios    manual install[/]", id="manual_header"),
            Container(
                Static("[yellow]coming soon[/]"),
                id="manual_body",
            ),
            Static(r"  [dim]\[b][/] back    [dim]\[q][/] quit", id="manual_nav"),
            id="manual_shell",
        )

    def action_back(self):
        self.app.pop_screen()


class ProgressScreen(Screen):
    BINDINGS = [Binding("q", "quit", "quit"), Binding("escape", "quit", "quit")]

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._abort = False
        self._pulse_timer = None

    def compose(self) -> ComposeResult:
        yield Container(
            Static("[bold purple]◆ mochios    installing...[/]", id="prog_header"),
            Container(
                Static("[bold purple]installing mochios...[/]", id="prog_status"),
                ProgressBar(id="prog_bar"),
                Log(id="prog_log", max_lines=2000),
                Button("abort (may leave partial install)", id="abort", variant="error"),
                id="prog_body",
            ),
            Static(r"  [dim]\[q][/] quit", id="prog_nav"),
            id="prog_shell",
        )

    def on_mount(self) -> None:
        self.log_widget = self.query_one("#prog_log", Log)
        self.status = self.query_one("#prog_status", Static)
        self.bar = self.query_one("#prog_bar", ProgressBar)
        self.log_widget.write("starting installation...")
        self._pulse()
        t = threading.Thread(target=self._run_install, daemon=True)
        t.start()

    def _pulse(self) -> None:
        if self._abort:
            return
        self.bar.advance(1)
        self._pulse_timer = self.set_timer(0.3, self._pulse)

    def _run_install(self):
        def log_fn(msg):
            if self._abort:
                return
            self.post_message(LogUpdate(msg))

        try:
            self.post_message(LogUpdate("[dim]passing control to installer backend...[/]"))
            success = do_install("/mnt/mochios", self.config, log_fn=log_fn, abort_flag=lambda: self._abort)
            self.post_message(InstallDone(success))
        except RuntimeError as e:
            self.post_message(LogUpdate(f"[yellow]{e}"))
            self.post_message(InstallDone(False))
        except Exception as e:
            self.post_message(LogUpdate(f"[bold red]error: {e}"))
            self.post_message(InstallDone(False))

    def on_log_update(self, msg: LogUpdate) -> None:
        self.log_widget.write(msg.text)

    def on_install_done(self, msg: InstallDone) -> None:
        if self._pulse_timer:
            self._pulse_timer.cancel()
        body = self.query_one("#prog_body")
        if msg.success:
            self.bar.update(progress=100)
            self.log_widget.write("[bold green]installation complete![/]")
            self.status.update("[bold green]done![/]")
        else:
            self.bar.update(progress=0)
            self.log_widget.write("[bold red]installation failed![/]")
            self.status.update("[bold red]failed![/]")
        body.mount(Button("exit", id="exit", variant="primary"))
        try:
            self.query_one("#abort", Button).remove()
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.app.exit()
        elif event.button.id == "abort":
            self._abort = True
            if self._pulse_timer:
                self._pulse_timer.cancel()
            self.log_widget.write("[yellow]aborting after current step...[/]")

    def action_quit(self) -> None:
        pass


class MochiInstallApp(App):
    TITLE = "mochios installer"
    CSS = """
    Screen { background: $surface; }

    #welcome_box {
        align: center middle;
        width: 60;
    }
    #welcome_spacer_top { height: 3; }
    #ascii { text-align: center; color: $secondary; }
    #title { text-align: center; text-style: bold; padding: 1; }

    #guided_shell, #prog_shell, #manual_shell { layout: grid; grid-rows: 1 5fr 1; height: 100%; }
    #step_bar, #prog_header, #manual_header {
        padding: 0 2;
        background: $panel;
        content-align: left middle;
    }
    #nav_bar, #prog_nav, #manual_nav {
        padding: 0 2;
        background: $panel;
        content-align: left middle;
    }
    #step_body, #prog_body, #manual_body {
        align: center middle;
        padding: 1 4;
    }
    #step_content_wrap { width: 56; }

    Input:focus { border: tall $secondary; }
    Button:focus { text-style: bold; }
    #pw_hint { height: 1; }
    SelectionList { max-height: 12; }
    .step_label { text-style: bold; padding-bottom: 1; }

    #prog_bar { margin: 0 2; }
    #prog_log { border: solid $primary; height: 1fr; min-height: 10; }
    #abort { margin: 1 0; }
    #exit { margin: 1 0; }
    """

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())


def main():
    MochiInstallApp().run()


if __name__ == "__main__":
    main()
