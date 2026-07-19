#!/usr/bin/env python3
"""mochios gui installer — pyqt6"""

import sys
import os
import argparse
import subprocess
import threading
import re

from PyQt6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QCheckBox, QGroupBox, QProgressBar, QWidget, QRadioButton,
    QButtonGroup, QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtProperty, pyqtSignal, QObject, QThread, QTimer
from PyQt6.QtGui import QColor, QPalette, QFont

from installer import do_install

NIGHTLY_STYLE = """
QWidget { background-color: #1a1025; color: #e0d0f0; font-family: "Noto Sans", "Cantarell", sans-serif; font-size: 13px; }
QWizardPage { background-color: #1a1025; }
QLabel#pageTitle { font-size: 20px; font-weight: bold; color: #c8a0f0; padding-bottom: 2px; }
QLabel#pageDesc { font-size: 12px; color: #705090; padding-bottom: 12px; }
QLineEdit, QListWidget { background-color: #251635; border: 1px solid #3a2a4e; border-radius: 4px; padding: 6px 10px; color: #e0d0f0; }
QLineEdit:focus { border-color: #9664c8; }
QListWidget { padding: 0; outline: none; }
QListWidget::item { padding: 4px 8px; border: none; color: #d0c0e0; }
QListWidget::item:selected { background-color: #3a2a5e; color: #c8a0f0; }
QListWidget::item:hover { background-color: #2a1a3e; }
QPushButton { background-color: #3a1e5e; border: 1px solid #5a3a7e; border-radius: 4px; padding: 6px 16px; color: #e0d0f0; min-height: 24px; }
QPushButton:hover { background-color: #4a2a6e; }
QPushButton:disabled { background-color: #1a1025; color: #3a2a4e; border: 1px solid #2a1a3e; }
QPushButton#primaryBtn { background-color: #7a3cb0; border: none; font-weight: bold; padding: 8px 24px; min-width: 100px; }
QPushButton#primaryBtn:hover { background-color: #8a4cc0; }
QPushButton#dangerBtn { background-color: #6a1a2a; border: 1px solid #9a3a4a; color: #f0a0b0; }
QPushButton#dangerBtn:hover { background-color: #8a2a3a; }
QCheckBox { spacing: 8px; padding: 3px 0; color: #d0c0e0; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #5a3a7e; border-radius: 3px; background-color: #251635; }
QCheckBox::indicator:checked { background-color: #7a3cb0; border-color: #9664c8; }
QRadioButton { spacing: 8px; padding: 3px 0; color: #d0c0e0; }
QRadioButton::indicator { width: 14px; height: 14px; border: 1px solid #5a3a7e; border-radius: 7px; background-color: #251635; }
QRadioButton::indicator:checked { background-color: #7a3cb0; border-color: #9664c8; }
QProgressBar { border: 1px solid #3a2a4e; border-radius: 4px; background-color: #251635; text-align: center; color: #e0d0f0; height: 20px; }
QProgressBar::chunk { background-color: #7a3cb0; border-radius: 3px; }
QGroupBox { border: 1px solid #2a1a3e; border-radius: 6px; margin-top: 10px; padding: 14px 12px 10px; }
QGroupBox::title { subcontrol-origin: margin; padding: 0 6px; color: #b090d0; }
QTextEdit#logArea { background-color: #0d0815; border: 1px solid #2a1a3e; border-radius: 4px; padding: 8px; font-family: "JetBrains Mono", "Noto Sans Mono", monospace; font-size: 11px; color: #b0a0c0; }
QLabel#infoHighlight { color: #c08050; font-size: 11px; }
QWidget#sidebar { background-color: #150d1e; border-right: 1px solid #2a1a3e; }
QPushButton#sideBtn { text-align: left; border: none; border-radius: 0; background: transparent; padding: 8px 16px; color: #604080; font-size: 12px; min-height: 20px; border-left: 3px solid transparent; }
QPushButton#sideBtn:hover { background-color: #1e1230; }
QPushButton#sideBtn[active="true"] { background-color: #251635; color: #c8a0f0; border-left: 3px solid #9664c8; font-weight: bold; }
"""

NORMAL_STYLE = """
QWidget { background-color: #f5f0f8; color: #1a1025; font-family: "Noto Sans", "Cantarell", sans-serif; font-size: 13px; }
QWizardPage { background-color: #f5f0f8; }
QLabel#pageTitle { font-size: 20px; font-weight: bold; color: #4a2a6e; padding-bottom: 2px; }
QLabel#pageDesc { font-size: 12px; color: #705090; padding-bottom: 12px; }
QLineEdit, QListWidget { background-color: #ffffff; border: 1px solid #c0b0d0; border-radius: 4px; padding: 6px 10px; color: #1a1025; }
QLineEdit:focus { border-color: #7a3cb0; }
QListWidget { padding: 0; outline: none; }
QListWidget::item { padding: 4px 8px; border: none; color: #1a1025; }
QListWidget::item:selected { background-color: #d8c8e8; color: #3a1e5e; }
QListWidget::item:hover { background-color: #e8ddf0; }
QPushButton { background-color: #e0d0f0; border: 1px solid #c0b0d0; border-radius: 4px; padding: 6px 16px; color: #1a1025; min-height: 24px; }
QPushButton:hover { background-color: #d0c0e0; }
QPushButton:disabled { background-color: #e8e0f0; color: #a090b0; border: 1px solid #d0c0e0; }
QPushButton#primaryBtn { background-color: #7a3cb0; border: none; font-weight: bold; padding: 8px 24px; min-width: 100px; color: #ffffff; }
QPushButton#primaryBtn:hover { background-color: #8a4cc0; }
QPushButton#dangerBtn { background-color: #e8a0b0; border: 1px solid #c08090; color: #4a1020; }
QPushButton#dangerBtn:hover { background-color: #d08090; }
QCheckBox { spacing: 8px; padding: 3px 0; color: #1a1025; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #c0b0d0; border-radius: 3px; background-color: #ffffff; }
QCheckBox::indicator:checked { background-color: #7a3cb0; border-color: #7a3cb0; }
QRadioButton { spacing: 8px; padding: 3px 0; color: #1a1025; }
QRadioButton::indicator { width: 14px; height: 14px; border: 1px solid #c0b0d0; border-radius: 7px; background-color: #ffffff; }
QRadioButton::indicator:checked { background-color: #7a3cb0; border-color: #7a3cb0; }
QProgressBar { border: 1px solid #c0b0d0; border-radius: 4px; background-color: #ffffff; text-align: center; color: #1a1025; height: 20px; }
QProgressBar::chunk { background-color: #7a3cb0; border-radius: 3px; }
QGroupBox { border: 1px solid #d0c0e0; border-radius: 6px; margin-top: 10px; padding: 14px 12px 10px; }
QGroupBox::title { subcontrol-origin: margin; padding: 0 6px; color: #4a2a6e; }
QTextEdit#logArea { background-color: #ffffff; border: 1px solid #d0c0e0; border-radius: 4px; padding: 8px; font-family: "JetBrains Mono", "Noto Sans Mono", monospace; font-size: 11px; color: #1a1025; }
QLabel#infoHighlight { color: #b06030; font-size: 11px; }
QWidget#sidebar { background-color: #e8ddf0; border-right: 1px solid #d0c0e0; }
QPushButton#sideBtn { text-align: left; border: none; border-radius: 0; background: transparent; padding: 8px 16px; color: #8060a0; font-size: 12px; min-height: 20px; border-left: 3px solid transparent; }
QPushButton#sideBtn:hover { background-color: #d8c8e8; }
QPushButton#sideBtn[active="true"] { background-color: #d0b8e0; color: #3a1e5e; border-left: 3px solid #7a3cb0; font-weight: bold; }
"""

SIDEBAR_LABELS = [
    "Welcome", "Hostname & User", "Disk", "Filesystem",
    "Kernel", "Extras", "Desktop", "Greeter", "Summary", "Install",
]


def _strip_markup(t):
    return re.sub(r"\[/?\w+(?: \w+)?\]", "", t)


STEP_PATTERNS = [
    (r"starting mochios installation", 5),
    (r"partitioning", 15),
    (r"formatting", 25),
    (r"setup|subvolume", 35),
    (r"pacstrap|installing base", 55),
    (r"installing mochi packages|mochi packages", 70),
    (r"optional packages", 80),
    (r"configuring system|configure_system|fstab|hostname|locale|network|user|password|grub|initramfs|limine", 90),
    (r"installation complete", 100),
]


class InstallWorker(QObject):
    log_line = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        def log_fn(msg):
            self.log_line.emit(_strip_markup(msg))
            for pat, pct in STEP_PATTERNS:
                if re.search(pat, msg, re.IGNORECASE):
                    self.progress.emit(pct)
                    break

        def abort_flag():
            return self._abort

        try:
            ok = do_install(config=self.config, log_fn=log_fn, abort_flag=abort_flag)
            self.finished.emit(ok)
        except Exception as e:
            self.log_line.emit(f"error: {e}")
            self.finished.emit(False)


class Sidebar(QWidget):
    def __init__(self, labels, nightly, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(170)
        lo = QVBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(0)
        hdr = QLabel("mochiOS" + (" nightly" if nightly else ""))
        hdr.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
            f" color: {'#b090d0' if nightly else '#4a2a6e'};"
            " padding: 16px 16px 8px;"
        )
        lo.addWidget(hdr)
        self._btns = []
        for lbl in labels:
            b = QPushButton(lbl)
            b.setObjectName("sideBtn")
            b.setEnabled(False)
            self._btns.append(b)
            lo.addWidget(b)
        lo.addStretch()

    def set_active(self, idx):
        for i, b in enumerate(self._btns):
            b.setProperty("active", str(i == idx).lower())
            b.style().unpolish(b)
            b.style().polish(b)

    def set_enabled_up_to(self, idx):
        for i in range(idx + 1):
            self._btns[i].setEnabled(True)


class WelcomePage(QWizardPage):
    def __init__(self, nightly):
        super().__init__()
        self._nightly = nightly
        lo = QVBoxLayout(self)
        lo.setContentsMargins(32, 32, 32, 32)
        t = QLabel("Welcome to MochiOS")
        t.setObjectName("pageTitle")
        lo.addWidget(t)
        d = QLabel("This wizard will guide you through installing MochiOS.")
        d.setObjectName("pageDesc")
        lo.addWidget(d)
        art = QLabel(
            "   ____ ___  ____    __    _ ____  _____\n"
            "  / __ `__ \\/ __ \\  / /_  (_) __ \\/ ___/\n"
            " / / / / / / /_/ / / __ \\/ / / / /\\__ \\ \n"
            "/_/ /_/ /_/\\____/ /_/ /_/_/_/ /_//____/  "
        )
        art.setStyleSheet(
            f"color: {'#9664c8' if nightly else '#7a3cb0'};"
            " font-family: monospace; font-size: 13px;"
        )
        art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addSpacing(4)
        lo.addWidget(art)
        lo.addSpacing(8)
        info = QLabel(
            "Before you begin:\n  \u2022 back up your data\n"
            "  \u2022 stable internet connection\n"
            "  \u2022 UEFI boot mode\n\nClick Next to start."
        )
        info.setStyleSheet(f"color: {'#a090b0' if nightly else '#604080'};")
        lo.addWidget(info)
        lo.addStretch()


class HostnamePage(QWizardPage):
    def __init__(self, nightly):
        super().__init__()
        self._nightly = nightly
        lo = QVBoxLayout(self)
        lo.setContentsMargins(32, 32, 32, 32)
        t = QLabel("Hostname & User")
        t.setObjectName("pageTitle")
        lo.addWidget(t)
        d = QLabel("Set your computer name and primary user.")
        d.setObjectName("pageDesc")
        lo.addWidget(d)
        lo.addWidget(QLabel("Hostname"))
        self._hn = QLineEdit("mochios-pc")
        lo.addWidget(self._hn)
        lo.addSpacing(8)
        lo.addWidget(QLabel("Username"))
        self._un = QLineEdit("mochi")
        lo.addWidget(self._un)
        lo.addSpacing(8)
        lo.addWidget(QLabel("Password"))
        self._pw = QLineEdit()
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw.textChanged.connect(self._validate)
        lo.addWidget(self._pw)
        lo.addWidget(QLabel("Confirm password"))
        self._pw2 = QLineEdit()
        self._pw2.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw2.textChanged.connect(self._validate)
        lo.addWidget(self._pw2)
        self._hint = QLabel("")
        self._hint.setStyleSheet(f"color: {'#c04050' if nightly else '#c04050'}; font-size: 11px;")
        lo.addWidget(self._hint)
        lo.addStretch()
        self.registerField("hostname*", self._hn)
        self.registerField("username*", self._un)
        self.registerField("password*", self._pw)

    def _validate(self):
        pw = self._pw.text()
        ok = bool(pw) and pw == self._pw2.text() and bool(self._hn.text()) and bool(self._un.text())
        nb = self.wizard().button(QWizard.WizardButton.NextButton)
        if nb:
            nb.setEnabled(ok)
        if pw and pw != self._pw2.text():
            self._hint.setText("passwords do not match")
        elif not self._hn.text():
            self._hint.setText("hostname required")
        elif not self._un.text():
            self._hint.setText("username required")
        else:
            self._hint.setText("")

    def initializePage(self):
        self._validate()


class DiskPage(QWizardPage):
    def __init__(self, nightly):
        super().__init__()
        self._nightly = nightly
        lo = QVBoxLayout(self)
        lo.setContentsMargins(32, 32, 32, 32)
        t = QLabel("Disk Setup")
        t.setObjectName("pageTitle")
        lo.addWidget(t)
        d = QLabel("Select the disk to install MochiOS onto. All data will be wiped.")
        d.setObjectName("pageDesc")
        lo.addWidget(d)
        w = QLabel("this will erase everything on the selected disk!")
        w.setObjectName("infoHighlight")
        lo.addWidget(w)
        lo.addSpacing(8)
        self._list = QListWidget()
        self._list.setMinimumHeight(140)
        self._list.itemSelectionChanged.connect(self._changed)
        lo.addWidget(self._list)
        hr = QHBoxLayout()
        ref = QPushButton("Refresh")
        ref.clicked.connect(self._scan)
        hr.addWidget(ref)
        hr.addStretch()
        lo.addLayout(hr)
        lo.addStretch()
        self._disk_path = ""
        self._list.itemSelectionChanged.connect(self._update_path)
        self.registerField("disk", self, "disk_path")

    disk_path_changed = pyqtSignal()
    disk_path = pyqtProperty(str, lambda self: self._disk_path, notify=disk_path_changed)

    def _update_path(self):
        sel = self._list.selectedItems()
        self._disk_path = sel[0].data(Qt.ItemDataRole.UserRole) or "" if sel else ""
        self.disk_path_changed.emit()

    def _changed(self):
        nb = self.wizard().button(QWizard.WizardButton.NextButton)
        if nb:
            nb.setEnabled(bool(self._list.selectedItems()))

    def _scan(self):
        self._list.clear()
        try:
            raw = subprocess.run(
                ["lsblk", "-dno", "NAME,SIZE,MODEL"], capture_output=True,
                text=True, timeout=10
            ).stdout.strip().split("\n")
        except Exception:
            self._list.addItem("(could not scan disks)")
            return
        for line in raw:
            parts = line.strip().split(None, 2)
            if not parts:
                continue
            name = parts[0]
            if name.startswith(("loop", "sr", "ram", "cdrom", "dm-", "zram", "nbd")):
                continue
            size = parts[1] if len(parts) > 1 else ""
            model = parts[2] if len(parts) > 2 else ""
            it = QListWidgetItem(f"/dev/{name}  \u00b7  {size}" + (f"  \u00b7  {model}" if model else ""))
            it.setData(Qt.ItemDataRole.UserRole, f"/dev/{name}")
            self._list.addItem(it)
        if self._list.count() == 0:
            self._list.addItem("(no suitable disks found)")

    def initializePage(self):
        self._scan()


class FSPage(QWizardPage):
    def __init__(self, nightly):
        super().__init__()
        self._nightly = nightly
        lo = QVBoxLayout(self)
        lo.setContentsMargins(32, 32, 32, 32)
        t = QLabel("Filesystem & Bootloader")
        t.setObjectName("pageTitle")
        lo.addWidget(t)
        lo.addWidget(QLabel("Filesystem"))
        self._fs = QButtonGroup(self)
        for i, (n, d) in enumerate([
            ("btrfs", "snapshots, compression, subvolumes"),
            ("ext4",  "simple, reliable, widely used"),
            ("xfs",   "good for large files, media workloads"),
        ]):
            rb = QRadioButton(f"  {n}  \u2014  {d}")
            self._fs.addButton(rb, i)
            lo.addWidget(rb)
        self._fs.buttons()[0].setChecked(True)
        lo.addSpacing(12)
        gb = QGroupBox("Bootloader")
        bl = QVBoxLayout(gb)
        self._bl = QButtonGroup(self)
        for i, (n, d) in enumerate([
            ("limine", "modern, fast (recommended)"),
            ("grub",   "classic, widely compatible"),
            ("mochiboot", "custom mochi fork of limine"),
        ]):
            rb = QRadioButton(f"  {n}  \u2014  {d}")
            self._bl.addButton(rb, i)
            bl.addWidget(rb)
        self._bl.buttons()[0].setChecked(True)
        lo.addWidget(gb)
        lo.addStretch()


class KernelPage(QWizardPage):
    def __init__(self, nightly):
        super().__init__()
        lo = QVBoxLayout(self)
        lo.setContentsMargins(32, 32, 32, 32)
        t = QLabel("Kernel Selection")
        t.setObjectName("pageTitle")
        lo.addWidget(t)
        d = QLabel("Choose one or more kernels. linux is selected by default.")
        d.setObjectName("pageDesc")
        lo.addWidget(d)
        self._cbs = []
        for n, desc in [
            ("linux",        "stock arch kernel"),
            ("linux-lts",    "long-term support"),
            ("linux-zen",    "desktop performance tweaks"),
            ("linux-hardened","security-focused patches"),
        ]:
            cb = QCheckBox(f"  {n}  \u2014  {desc}")
            cb.setChecked(n == "linux")
            self._cbs.append(cb)
            lo.addWidget(cb)
        lo.addStretch()


class ExtrasPage(QWizardPage):
    def __init__(self, nightly):
        super().__init__()
        lo = QVBoxLayout(self)
        lo.setContentsMargins(32, 32, 32, 32)
        t = QLabel("Extra Packages")
        t.setObjectName("pageTitle")
        lo.addWidget(t)
        d = QLabel("Optional packages installed from the network.")
        d.setObjectName("pageDesc")
        lo.addWidget(d)
        self._cbs = []
        for n, desc in [
            ("firefox", "web browser"),
            ("steam",   "gaming platform"),
            ("wine",    "windows compatibility layer"),
            ("flatpak", "universal package manager"),
            ("docker",  "container runtime"),
            ("code",    "visual studio code"),
        ]:
            cb = QCheckBox(f"  {n}  \u2014  {desc}")
            self._cbs.append(cb)
            lo.addWidget(cb)
        lo.addStretch()


class DesktopPage(QWizardPage):
    def __init__(self, nightly):
        super().__init__()
        lo = QVBoxLayout(self)
        lo.setContentsMargins(32, 32, 32, 32)
        t = QLabel("Desktop Environment")
        t.setObjectName("pageTitle")
        lo.addWidget(t)
        d = QLabel("Choose your desktop environment.")
        d.setObjectName("pageDesc")
        lo.addWidget(d)
        self._de = QButtonGroup(self)
        for i, (n, desc) in enumerate([
            ("kde",      "feature-rich, customizable (recommended)"),
            ("gnome",    "modern, streamlined design"),
            ("hyprland", "dynamic tiling wayland compositor"),
        ]):
            rb = QRadioButton(f"  {n}  \u2014  {desc}")
            self._de.addButton(rb, i)
            lo.addWidget(rb)
        self._de.buttons()[0].setChecked(True)
        lo.addStretch()


class GreeterPage(QWizardPage):
    def __init__(self, nightly):
        super().__init__()
        lo = QVBoxLayout(self)
        lo.setContentsMargins(32, 32, 32, 32)
        t = QLabel("Greeter / Display Manager")
        t.setObjectName("pageTitle")
        lo.addWidget(t)
        d = QLabel("Choose your login screen.")
        d.setObjectName("pageDesc")
        lo.addWidget(d)
        self._gr = QButtonGroup(self)
        self._opts = []
        for i, (n, desc) in enumerate([
            ("sddm",    "Qt-based, kde integration (recommended)"),
            ("gdm",     "gnome display manager"),
            ("lightdm", "lightweight, flexible, gtk-based"),
            ("ly",      "minimal tui login"),
            ("greetd",  "minimal agnostic greeter daemon"),
        ]):
            rb = QRadioButton(f"  {n}  \u2014  {desc}")
            self._gr.addButton(rb, i)
            lo.addWidget(rb)
            self._opts.append(n)
        lo.addStretch()

    def initializePage(self):
        de = self.wizard()._cfg.get("de", "kde")
        default = {"kde": "sddm", "gnome": "gdm", "hyprland": "sddm"}.get(de, "sddm")
        for i, n in enumerate(self._opts):
            if n == default:
                self._gr.buttons()[i].setChecked(True)
                break


class SummaryPage(QWizardPage):
    def __init__(self, nightly):
        super().__init__()
        self._nightly = nightly
        self._lo = QVBoxLayout(self)
        self._lo.setContentsMargins(32, 32, 32, 32)
        self._info = QLabel("")
        self._info.setStyleSheet(
            f"color: {'#c0b0d0' if nightly else '#1a1025'};"
            " font-family: monospace; line-height: 1.6;"
        )
        self._lo.addWidget(self._info)
        self._lo.addStretch()

    def initializePage(self):
        w = self.wizard()
        c = w._cfg
        disk = self.field("disk") or c.get("disk", "-")
        self._info.setText(
            f"hostname:   {self.field('hostname')}\n"
            f"username:   {self.field('username')}\n"
            f"disk:       {disk}\n"
            f"filesystem: {c.get('fs', 'btrfs')}\n"
            f"desktop:    {c.get('de', 'kde')}\n"
            f"greeter:    {c.get('greeter', 'sddm')}\n"
            f"bootloader: {c.get('bl', 'limine')}\n"
            f"kernels:    {', '.join(c.get('kernels', ['linux']))}\n"
            f"extras:     {', '.join(c.get('extras', [])) or 'none'}"
        )


class ProgressPage(QWizardPage):
    def __init__(self, nightly):
        super().__init__()
        self._nightly = nightly
        lo = QVBoxLayout(self)
        lo.setContentsMargins(32, 32, 32, 32)
        self._status = QLabel("Ready to install.")
        self._status.setStyleSheet(
            "font-size: 15px;"
            f" color: {'#c8a0f0' if nightly else '#4a2a6e'};"
        )
        lo.addWidget(self._status)
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        lo.addWidget(self._bar)
        self._log = QTextEdit()
        self._log.setObjectName("logArea")
        self._log.setReadOnly(True)
        lo.addWidget(self._log, stretch=1)
        hr = QHBoxLayout()
        self._abort_btn = QPushButton("Abort")
        self._abort_btn.setObjectName("dangerBtn")
        hr.addStretch()
        hr.addWidget(self._abort_btn)
        lo.addLayout(hr)
        self._worker = None
        self._thread = None

    def isComplete(self):
        return False

    def start_install(self, config):
        self._status.setText("Installing...")
        self._bar.setValue(0)
        self._log.clear()
        self._abort_btn.setEnabled(True)

        self._thread = QThread(self)
        self._worker = InstallWorker(config)
        self._worker.moveToThread(self._thread)

        self._worker.log_line.connect(self._on_log)
        self._worker.progress.connect(self._bar.setValue)
        self._worker.finished.connect(self._on_finished)
        self._abort_btn.clicked.connect(self._worker.abort)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _on_log(self, msg):
        self._log.append(msg)
        self._log.verticalScrollBar().setValue(self._log.verticalScrollBar().maximum())

    def _on_finished(self, ok):
        if ok:
            self._status.setText("Installation complete!")
            self._bar.setValue(100)
        else:
            self._status.setText("Installation failed. Check the log for details.")
        self._abort_btn.setEnabled(True)
        self._abort_btn.setText("Close")
        try:
            self._abort_btn.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass
        self._abort_btn.clicked.connect(self.wizard().close)


class MochiWizard(QWizard):
    def __init__(self, nightly=False):
        super().__init__()
        self._nightly = nightly
        self.setObjectName("MochiWizard")
        self.setWindowTitle("MochiOS Installer" + (" (Nightly)" if nightly else ""))
        self.setMinimumSize(820, 560)
        self.setWizardStyle(QWizard.WizardStyle.ClassicStyle)
        self.setOption(QWizard.WizardOption.NoBackButtonOnLastPage)
        self.setOption(QWizard.WizardOption.HaveFinishButtonOnEarlyPages, False)
        self.setOption(QWizard.WizardOption.NoDefaultButton)
        self.setStyleSheet(NIGHTLY_STYLE if nightly else NORMAL_STYLE)

        self._cfg = {}
        self._sidebar = Sidebar(SIDEBAR_LABELS, nightly)
        self.setSideWidget(self._sidebar)

        self._pids = []
        self._pids.append(self.addPage(WelcomePage(nightly)))
        self._pids.append(self.addPage(HostnamePage(nightly)))
        self._pids.append(self.addPage(DiskPage(nightly)))
        self._pids.append(self.addPage(FSPage(nightly)))
        self._pids.append(self.addPage(KernelPage(nightly)))
        self._pids.append(self.addPage(ExtrasPage(nightly)))
        self._pids.append(self.addPage(DesktopPage(nightly)))
        self._pids.append(self.addPage(GreeterPage(nightly)))
        self._pids.append(self.addPage(SummaryPage(nightly)))

        self._progress_page = ProgressPage(nightly)
        self._pids.append(self.addPage(self._progress_page))

        self._sidebar.set_enabled_up_to(0)
        self._sidebar.set_active(0)
        self.currentIdChanged.connect(self._on_page_change)

        for name in ("NextButton", "BackButton", "FinishButton", "CancelButton"):
            b = self.button(getattr(QWizard.WizardButton, name))
            if b is not None:
                b.setMinimumHeight(30)

        nb = self.button(QWizard.WizardButton.NextButton)
        nb.setText("Next")
        nb.setObjectName("primaryBtn")
        fb = self.button(QWizard.WizardButton.FinishButton)
        fb.setText("Install")
        fb.setObjectName("primaryBtn")

    def _on_page_change(self, pid):
        idx = self._pids.index(pid)
        self._sidebar.set_active(idx)
        self._sidebar.set_enabled_up_to(idx)

    def nextId(self):
        cur = self._pids.index(self.currentId())
        p = self.page(self.currentId())

        if isinstance(p, FSPage):
            self._cfg["fs"] = ["btrfs", "ext4", "xfs"][p._fs.checkedId()]
            self._cfg["bl"] = ["limine", "grub", "mochiboot"][p._bl.checkedId()]
        elif isinstance(p, KernelPage):
            self._cfg["kernels"] = [
                c.text().split("  ")[1] for c in p._cbs if c.isChecked()
            ]
        elif isinstance(p, ExtrasPage):
            self._cfg["extras"] = [
                c.text().split("  ")[1] for c in p._cbs if c.isChecked()
            ]
        elif isinstance(p, DesktopPage):
            self._cfg["de"] = ["kde", "gnome", "hyprland"][p._de.checkedId()]
        elif isinstance(p, GreeterPage):
            self._cfg["greeter"] = p._opts[p._gr.checkedId()]

        # SummaryPage is the last navigable page — show Install button
        if isinstance(p, SummaryPage):
            return -1

        pid = self._pids[cur + 1] if cur + 1 < len(self._pids) else -1
        return pid

    def accept(self):
        install_cfg = {
            "disk": self.field("disk"),
            "hostname": self.field("hostname"),
            "username": self.field("username"),
            "password": self.field("password"),
            "bootloader": self._cfg.get("bl", "limine"),
            "kernels": self._cfg.get("kernels", ["linux"]),
            "extra_pkgs": self._cfg.get("extras", []),
            "de": self._cfg.get("de", "kde"),
            "greeter": self._cfg.get("greeter", "sddm"),
        }

        self._progress_page.start_install(install_cfg)
        self.setCurrentId(self._pids[-1])


def main():
    ap = argparse.ArgumentParser(description="MochiOS Installer")
    ap.add_argument("--nightly", action="store_true", help="use nightly theme (dark purple)")
    args = ap.parse_args()

    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mochios.installer.1")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    if args.nightly:
        p = QPalette()
        p.setColor(QPalette.Window, QColor("#1a1025"))
        p.setColor(QPalette.WindowText, QColor("#e0d0f0"))
        p.setColor(QPalette.Base, QColor("#251635"))
        p.setColor(QPalette.Button, QColor("#3a1e5e"))
        p.setColor(QPalette.ButtonText, QColor("#e0d0f0"))
        p.setColor(QPalette.Highlight, QColor("#7a3cb0"))
        app.setPalette(p)

    w = MochiWizard(nightly=args.nightly)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
