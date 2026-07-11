#!/usr/bin/env python3

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static, Input, SelectionList, Log, Label
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.message import Message
import subprocess
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mochi_ascii import MOCHI_ASCII
from installer import do_install


class LogUpdate(Message):
    def __init__(self, text: str):
        super().__init__()
        self.text = text


class StatusUpdate(Message):
    def __init__(self, text: str):
        super().__init__()
        self.text = text


class InstallDone(Message):
    def __init__(self, success: bool):
        super().__init__()
        self.success = success


class WelcomeScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static(r"[bold purple]               _    _          ", id="ascii"),
            Static(r"[bold purple] _ __  ___  __| |_ (_)  ___ ___"),
            Static(r"[bold purple]| '  \/ _ \/ _| ' \| | / _ (_-<"),
            Static(r"[bold purple]|_|_|_\___/\__|_||_|_| \___/__/"),
            Static(""),
            Static("[bold purple]mochios installer[/]", id="title"),
            Static("mochi-powered arch linux with atomic updates"),
            Static(""),
            Button("guided install", id="guided", variant="primary"),
            Button("manual install", id="manual", variant="default"),
            Button("exit", id="exit", variant="error"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "guided":
            self.app.push_screen(GuidedScreen())
        elif event.button.id == "manual":
            self.app.push_screen(ManualScreen())
        elif event.button.id == "exit":
            self.app.exit()


class GuidedScreen(Screen):
    def __init__(self):
        super().__init__()
        self.step = 0
        self.config = {"de": "kde", "disk": "", "filesystem": "btrfs", "bootloader": "limine", "kernels": ["linux"], "hostname": "mochios", "username": "mochi", "password": "mochi", "extra_pkgs": []}

    def compose(self) -> ComposeResult:
        yield Header()
        self.content = ScrollableContainer(id="content")
        yield self.content
        yield Footer()

    def on_mount(self) -> None:
        self.render_step()

    def render_step(self) -> None:
        self.content.remove_children()
        steps = [self.step_hostname, self.step_disk, self.step_fs, self.step_kernel, self.step_extra, self.step_de_boot, self.step_user, self.step_summary]
        if 0 <= self.step < len(steps):
            steps[self.step]()
            self._focus_step()
        else:
            self.app.pop_screen()

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
        elif self.step == 6:
            self._try_focus("#password", Input)

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

    def step_hostname(self) -> None:
        self.content.mount(Vertical(
            Static("[bold]step 1/8 - hostname"),
            Input(placeholder="mochios", id="hostname", value=self.config["hostname"]),
            Horizontal(Button("next", id="next", variant="primary")),
        ))

    def _disk_type(self, name: str) -> str:
        try:
            with open(f"/sys/block/{name}/queue/rotational") as f:
                rot = f.read().strip()
            if rot == "1":
                return "HDD"
            elif rot == "0":
                if name.startswith("nvme"):
                    return "NVMe"
                elif name.startswith("mmcblk"):
                    return "SD"
                return "SSD"
        except Exception:
            pass
        if name.startswith("nvme"):
            return "NVMe"
        elif name.startswith("mmcblk"):
            return "SD"
        elif name.startswith("vd"):
            return "VirtIO"
        return ""

    def step_disk(self) -> None:
        disks = []
        boot_dev = ""
        try:
            r = subprocess.run(
                ["findmnt", "-n", "-o", "SOURCE", "/run/archiso/bootmnt"],
                capture_output=True, text=True, timeout=5
            )
            src = r.stdout.strip()
            if src:
                r2 = subprocess.run(
                    ["lsblk", "-ndo", "PKNAME", src],
                    capture_output=True, text=True, timeout=5
                )
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
                    dtype_tag = f"({dtype}) " if dtype else ""
                    label = f"/dev/{name}"
                    info = f"{parts[1]} {parts[2] if len(parts) > 2 else ''}"
                    disks.append((f"{dtype_tag}{label} - {info}", label))
        except Exception as e:
            print(f"warning: lsblk failed: {e}", file=sys.stderr)

        children = [
            Static("[bold red]WARNING: this disk will be wiped"),
            Static("[bold]step 2/8 - select disk"),
        ]
        if not disks:
            children += [
                Static("[yellow]no disks detected![/]"),
                Static("make sure a disk is connected and try again"),
                Horizontal(Button("back", id="back"), Button("refresh", id="refresh")),
            ]
        else:
            preselected = self.config.get("disk", "")
            children += [
                SelectionList(*[(d, v, v == preselected) for d, v in disks], id="disk_list", max_selected=1),
                Horizontal(Button("back", id="back"), Button("next", id="next", variant="primary"), Button("refresh", id="refresh")),
            ]
        self.content.mount(Vertical(*children))

    def step_fs(self) -> None:
        self.content.mount(Vertical(
            Static("[bold]step 3/8 - filesystem"),
            SelectionList((("btrfs (snapshots + abroot)", "btrfs", True)), id="fs"),
            Horizontal(Button("back", id="back"), Button("next", id="next", variant="primary")),
        ))

    def step_kernel(self) -> None:
        kernels = self.config.get("kernels", ["linux"])
        self.content.mount(Vertical(
            Static("[bold]step 4/8 - kernel (select one or more)"),
            SelectionList(
                ("linux (stock)", "linux", "linux" in kernels),
                ("linux-zen (desktop tuned)", "linux-zen", "linux-zen" in kernels),
                ("linux-lts (longterm)", "linux-lts", "linux-lts" in kernels),
                ("linux-hardened (security)", "linux-hardened", "linux-hardened" in kernels),
                id="kernel"
            ),
            Horizontal(Button("back", id="back"), Button("next", id="next", variant="primary")),
        ))

    def step_extra(self) -> None:
        extras = self.config.get("extra_pkgs", [])
        self.content.mount(Vertical(
            Static("[bold]step 5/8 - extra packages"),
            Static("optional apps:"),
            SelectionList(
                ("steam", "steam", "steam" in extras),
                ("wine", "wine", "wine" in extras),
                ("sober (roblox)", "sober", "sober" in extras),
                ("zen-browser", "zen-browser", "zen-browser" in extras),
                id="extra_pkgs"
            ),
            Horizontal(Button("back", id="back"), Button("next", id="next", variant="primary")),
        ))

    def step_de_boot(self) -> None:
        de = self.config.get("de", "kde")
        bl = self.config.get("bootloader", "limine")
        self.content.mount(Vertical(
            Static("[bold]step 6/8 - desktop & bootloader"),
            Static("desktop environment:"),
            SelectionList(
                ("kde plasma", "kde", de == "kde"), ("gnome", "gnome", de == "gnome"), ("none", "none", de == "none"), id="de"
            ),
            Static("bootloader:"),
            SelectionList(
                ("limine", "limine", bl == "limine"), ("grub", "grub", bl == "grub"), id="bootloader"
            ),
            Horizontal(Button("back", id="back"), Button("next", id="next", variant="primary")),
        ))

    def step_user(self) -> None:
        self.content.mount(Vertical(
            Static("[bold]step 7/8 - user account"),
            Input(placeholder="mochi", id="username", value=self.config["username"]),
            Input(placeholder="password (required)", id="password", password=True),
            Label("", id="pw_hint"),
            Horizontal(Button("back", id="back"), Button("next", id="next", variant="primary")),
        ))

    def step_summary(self) -> None:
        c = self.config
        disk_set = bool(c["disk"])
        extras = ", ".join(c.get("extra_pkgs", [])) or "none"
        kernels = ", ".join(c.get("kernels", ["linux"])) or "linux"
        self.content.mount(Vertical(
            Static("[bold]step 8/8 - review"),
            Static(f"hostname: {c['hostname']}"),
            Static(f"disk: [red]{c['disk'] or 'NOT SELECTED'}[/] {'[red bold](required!)' if not disk_set else '(will be wiped)'}"),
            Static(f"desktop: {c['de']}"),
            Static(f"kernels: {kernels}"),
            Static(f"bootloader: {c['bootloader']}"),
            Static(f"extra: {extras}"),
            Static(f"user: {c['username']}"),
            Static(""),
            Static("[red bold]WARNING: this will erase all data on the selected disk" if disk_set else "[red bold]select a disk first!"),
            Horizontal(Button("back", id="back"), Button("install!", id="install", variant="primary", disabled=not disk_set)),
        ))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.step == 0:
            self.collect_current()
            self.step += 1
            self.render_step()
        elif self.step == 6 and event.input.id == "username":
            self.query_one("#password", Input).focus()
        elif self.step == 6 and event.input.id == "password":
            pw_hint = self.query_one("#pw_hint", Label)
            self.collect_current()
            if self.config.get("password"):
                self.step += 1
                self.render_step()
            else:
                pw_hint.update("[red]password cannot be empty[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.collect_current()
            self.step = max(0, self.step - 1)
            self.render_step()
        elif event.button.id == "next":
            if self.step == 6:
                pw_hint = self.query_one("#pw_hint", Label)
                self.collect_current()
                pw = self.config.get("password", "")
                if not pw:
                    pw_hint.update("[red]password cannot be empty[/]")
                    return
            else:
                self.collect_current()
            self.step += 1
            self.render_step()
        elif event.button.id == "refresh":
            self.render_step()
        elif event.button.id == "install":
            self.collect_current()
            if not self.config.get("disk"):
                self.step = 1
                self.render_step()
                return
            self.app.push_screen(ProgressScreen(self.config))

    def collect_current(self) -> None:
        try:
            if self.step == 0:
                inp = self.query_one("#hostname", Input)
                self.config["hostname"] = inp.value or "mochios"
            elif self.step == 1:
                sel = self.query_one("#disk_list", SelectionList)
                if sel.selected:
                    self.config["disk"] = sel.selected[0]
            elif self.step == 2:
                pass
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
                if u.value:
                    self.config["username"] = u.value
                self.config["password"] = p.value
        except Exception:
            pass


class ManualScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("[bold]manual install"),
            Static("coming soon"),
            Button("back", id="back"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


class ProgressScreen(Screen):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._abort = False

    def compose(self) -> ComposeResult:
        yield Header()
        self.install_box = Vertical(
            Static("[bold green]installing mochios...", id="status"),
            Log(id="log", max_lines=2000),
            Button("abort (may leave partial install)", id="abort", variant="error"),
        )
        yield self.install_box
        yield Footer()

    def on_mount(self) -> None:
        self.log_widget = self.query_one("#log", Log)
        self.status = self.query_one("#status", Static)
        self.log_widget.write("starting installation...")
        t = threading.Thread(target=self.run_install, daemon=True)
        t.start()

    def run_install(self):
        def log_fn(msg):
            if self._abort:
                return
            self.post_message(LogUpdate(msg))

        try:
            self.post_message(LogUpdate("[dim]passing control to installer backend...[/]"))
            success = do_install(
                "/mnt/mochios", self.config,
                log_fn=log_fn,
                abort_flag=lambda: self._abort,
            )
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
        if msg.success:
            self.log_widget.write("[bold green]installation complete![/]")
            self.status.update("[bold green]done![/]")
        else:
            self.log_widget.write("[bold red]installation failed![/]")
            self.status.update("[bold red]failed![/]")
        self.install_box.mount(Button("exit", id="exit", variant="primary"))
        try:
            self.query_one("#abort", Button).remove()
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.app.exit()
        elif event.button.id == "abort":
            self._abort = True
            self.log_widget.write("[yellow]aborting after current step...[/]")


class MochiInstallApp(App):
    TITLE = "mochios installer"
    CSS = """
    Input:focus { border: tall $secondary; }
    Button { margin: 1 0; }
    #title { text-align: center; text-style: bold; padding: 1; }
    #ascii { text-align: center; color: $secondary; }
    #pw_hint { height: 1; }
    SelectionList { max-height: 14; }
    """

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())


def main():
    MochiInstallApp().run()


if __name__ == "__main__":
    main()
