# encoding: utf-8
"""
Cable v2.0 — By 0.6 :3

"""

import os
import sys
import shutil
import tkinter as tk
import argparse
import fnmatch
import hashlib
import json
import subprocess
from tkinter import filedialog
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging
import threading

# Force UTF-8 encoding for Windows terminals and compiled executables
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
        if sys.stderr:
            sys.stderr.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        if sys.stderr:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    Observer = None  # type: ignore[assignment,misc]
    FileSystemEventHandler = object  # type: ignore[assignment,misc]

try:  # type: ignore[import]
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import (
        Progress, SpinnerColumn, BarColumn,
        TextColumn, TaskProgressColumn, TimeElapsedColumn,
    )
    from rich.prompt import Confirm, Prompt
    from rich.text import Text
    from rich.rule import Rule
    from rich import box
    from rich.align import Align
    from rich.padding import Padding
    from rich.columns import Columns
    import time
except ImportError:
    print("[ERROR] Missing 'rich' library.  Run: pip install rich")
    sys.exit(1)

try:
    import tomllib  # type: ignore[import]
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[import,no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

console = Console(highlight=False)

C_ACCENT   = "bold #a78bfa"
C_ACCENT2  = "bold #60a5fa"
C_DIM      = "dim #6b7280"
C_GOOD     = "bold #34d399"
C_WARN     = "bold #fbbf24"
C_BAD      = "bold #f87171"
C_WHITE    = "bold #f9fafb"
C_BORDER   = "#4c1d95"
C_PROGRESS = "#818cf8"
C_DONE     = "#34d399"

_SELF_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
CABLE_JSON_PATH = _SELF_DIR / "cable.json"

_DEFAULT_CABLE_CONFIG: dict = {
    "session": {
        "run_mode":         "1",
        "sort_mode":        "alpha",
        "copy_mode":        False,
        "date_subfolders":  False,
        "dest_mode":        "here",
        "dest_custom":      "",
        "exclude_patterns": ["desktop.ini", "*.tmp", "Thumbs.db"],
    },
    "defaults_map": {
        "\U0001f5bc\ufe0f   Images":   "~/Pictures",
        "\U0001f3ac  Video":     "~/Videos",
        "\U0001f50a  Sound":     "~/Music",
        "\U0001f4d1  Documents": "~/Documents",
        "\U0001f4c4  Notepads":  "~/Documents",
        "\U0001f4bb  Code":      "~/Documents",
        "\U0001f4c1  Folders":   "~/Documents",
    },
    "defaults_fallback": "~/Downloads",
    "date_media_cats": [
        "\U0001f5bc\ufe0f   Images",
        "\U0001f3ac  Video",
        "\U0001f50a  Sound",
    ],
    "categories": [
        {
            "key":        "\U0001f4c1  Folders",
            "folder":     "Folders",
            "icon":       "\U0001f4c1",
            "color":      "#fbbf24",
            "extensions": [],
        },
        {
            "key":        "\U0001f4c4  Notepads",
            "folder":     "Notepads",
            "icon":       "\U0001f4c4",
            "color":      "#e5e7eb",
            "extensions": [".txt", ".md", ".markdown", ".log", ".ini",
                           ".cfg", ".conf", ".nfo", ".rtf", ".csv"],
        },
        {
            "key":        "\u2699\ufe0f   Executables",
            "folder":     "Executables",
            "icon":       "\u2699\ufe0f ",
            "color":      "#f87171",
            "extensions": [".exe", ".msi", ".bat", ".cmd", ".ps1",
                           ".vbs", ".sh", ".com", ".pif", ".scr", ".appx", ".msix"],
        },
        {
            "key":        "\U0001f5dc\ufe0f   Archives",
            "folder":     "Archives",
            "icon":       "\U0001f5dc\ufe0f ",
            "color":      "#67e8f9",
            "extensions": [".rar", ".zip", ".7z", ".tar", ".gz",
                           ".bz2", ".xz", ".iso", ".cab", ".lz", ".lzma", ".zst"],
        },
        {
            "key":        "\U0001f4d1  Documents",
            "folder":     "Documents",
            "icon":       "\U0001f4d1",
            "color":      "#93c5fd",
            "extensions": [".pdf", ".docx", ".doc", ".xlsx", ".xls",
                           ".pptx", ".ppt", ".odt", ".ods", ".odp",
                           ".pages", ".numbers", ".key", ".epub", ".mobi"],
        },
        {
            "key":        "\U0001f4bb  Code",
            "folder":     "Code",
            "icon":       "\U0001f4bb",
            "color":      "#6ee7b7",
            "extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".html",
                           ".css", ".scss", ".sass", ".java", ".c", ".cpp",
                           ".h", ".hpp", ".cs", ".php", ".rb", ".go", ".rs",
                           ".swift", ".kt", ".json", ".xml", ".yaml", ".yml",
                           ".toml", ".sql", ".lua", ".r", ".m", ".asm",
                           ".dart", ".vue"],
        },
        {
            "key":        "\U0001f517  Shortcuts",
            "folder":     "Shortcuts",
            "icon":       "\U0001f517",
            "color":      "#a5f3fc",
            "extensions": [".lnk", ".url", ".webloc"],
        },
        {
            "key":        "\U0001f5bc\ufe0f   Images",
            "folder":     "Media/Images",
            "icon":       "\U0001f5bc\ufe0f ",
            "color":      "#f0abfc",
            "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
                           ".webp", ".ico", ".tiff", ".tif", ".heic", ".heif",
                           ".raw", ".cr2", ".nef", ".psd", ".ai", ".xcf"],
        },
        {
            "key":        "\U0001f3ac  Video",
            "folder":     "Media/Video",
            "icon":       "\U0001f3ac",
            "color":      "#fde68a",
            "extensions": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
                           ".webm", ".m4v", ".3gp", ".ts", ".vob", ".rmvb", ".asf"],
        },
        {
            "key":        "\U0001f50a  Sound",
            "folder":     "Media/Sound",
            "icon":       "\U0001f50a",
            "color":      "#a5b4fc",
            "extensions": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma",
                           ".m4a", ".opus", ".alac", ".aiff", ".mid", ".midi"],
        },
    ],
}


def _write_default_cable_json() -> None:
    """Write the default cable.json next to the script (best-effort)."""
    try:
        CABLE_JSON_PATH.write_text(
            json.dumps(_DEFAULT_CABLE_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def load_cable_config() -> dict:
    """Load cable.json.  Creates it with defaults if absent or unreadable."""
    if not CABLE_JSON_PATH.exists():
        _write_default_cable_json()
        return json.loads(json.dumps(_DEFAULT_CABLE_CONFIG))  # deep copy
    try:
        raw = json.loads(CABLE_JSON_PATH.read_text(encoding="utf-8"))
        # Deep-merge with defaults so missing keys always have a value
        merged: dict = json.loads(json.dumps(_DEFAULT_CABLE_CONFIG))
        if isinstance(raw.get("session"), dict):
            merged["session"].update(raw["session"])
        for key in ("defaults_map", "defaults_fallback", "date_media_cats", "categories"):
            if key in raw:
                merged[key] = raw[key]
        return merged
    except Exception:
        return json.loads(json.dumps(_DEFAULT_CABLE_CONFIG))


_CABLE_CFG = load_cable_config()

CATEGORIES: dict[str, dict] = {
    entry["key"]: {
        "folder":     entry.get("folder", entry["key"]),
        "icon":       entry.get("icon", "📄"),
        "color":      entry.get("color", "#9ca3af"),
        "extensions": [e.lower() for e in entry.get("extensions", [])],
    }
    for entry in _CABLE_CFG.get("categories", [])
}

# flat ext → category key
EXT_MAP: dict[str, str] = {}
for _cat, _data in CATEGORIES.items():
    for _ext in _data["extensions"]:
        EXT_MAP.setdefault(_ext, _cat)

MISC_KEY        = "❓  Misc"
SKIP_ROOT       = set(str(d["folder"]).split("/")[0] for d in CATEGORIES.values() if d["folder"])
DATE_MEDIA_CATS = set(_CABLE_CFG.get("date_media_cats", []))

CONFIG_PATH = Path.home() / ".sortconfig.toml"

# Session defaults come from cable.json["session"]
_CFG_DEFAULTS: dict = dict(_CABLE_CFG.get("session", {
    "run_mode":         "1",
    "sort_mode":        "alpha",
    "copy_mode":        False,
    "date_subfolders":  False,
    "dest_mode":        "here",
    "dest_custom":      "",
    "exclude_patterns": ["desktop.ini", "*.tmp", "Thumbs.db"],
}))


def load_config() -> dict:
    cfg: dict = dict(_CFG_DEFAULTS)
    if tomllib is None or not CONFIG_PATH.exists():
        return cfg
    try:
        with open(CONFIG_PATH, "rb") as fh:
            data = tomllib.load(fh)
        cfg.update(data)
    except Exception:
        pass
    return cfg


def save_config(cfg: dict) -> None:
    excludes = "[" + ", ".join(f'"{x}"' for x in cfg["exclude_patterns"]) + "]"
    lines = [
        f'run_mode        = "{cfg.get("run_mode", "1")}"',
        f'sort_mode       = "{cfg["sort_mode"]}"',
        f'copy_mode       = {"true" if cfg["copy_mode"] else "false"}',
        f'date_subfolders = {"true" if cfg["date_subfolders"] else "false"}',
        f'dest_mode       = "{cfg.get("dest_mode", "here")}"',
        f'dest_custom     = "{str(cfg.get("dest_custom", "")).replace(chr(92), chr(92)+chr(92))}"',
        f"exclude_patterns = {excludes}",
    ]
    try:
        CONFIG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:
        pass

BANNER_LINES = [
    "   ██████╗ █████╗ ██████╗ ██╗     ███████╗",
    "  ██╔════╝██╔══██╗██╔══██╗██║     ██╔════╝",
    "  ██║     ███████║██████╔╝██║     █████╗  ",
    "  ██║     ██╔══██║██╔══██╗██║     ██╔══╝  ",
    "  ╚██████╗██║  ██║██████╔╝███████╗███████╗",
    "   ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝",
]

GRADIENT = ["#a78bfa", "#818cf8", "#60a5fa", "#38bdf8", "#60a5fa", "#818cf8", "#a78bfa", "#7c3aed"]


def print_banner() -> None:
    console.print()
    for i, line in enumerate(BANNER_LINES):
        color = GRADIENT[i % len(GRADIENT)]
        console.print(Align.center(Text(line, style=f"bold {color}")))
    console.print()
    tag_line = Text("  ✦  Intelligent Folder Organizer  ✦  By 0.6 :3  ✦", style="bold #6d28d9")
    console.print(Align.center(tag_line))
    console.print()

def step_header(n: int, label: str) -> None:
    badge = f"[reverse bold #a78bfa] {n} [/]"
    console.print()
    console.print(Rule(f"{badge} [bold #c4b5fd]{label}[/]", style="#4c1d95"))
    console.print()

def print_legend() -> None:
    items = [
        Text(f"{d['icon']} {k.split('  ')[-1]:<14}", style=f"{d['color']}")
        for k, d in CATEGORIES.items()
    ]
    items.append(Text("❓ Misc", style="dim"))
    console.print(
        Panel(
            Columns(items, padding=(0, 2), equal=True),
            title="[bold #a78bfa]Categories[/]",
            border_style="#4c1d95",
            padding=(1, 2),
        )
    )

def pick_folder(title: str = "Select a folder to sort") -> Optional[Path]:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(title=title)
    root.destroy()
    return Path(folder) if folder else None

def _expand(p: str) -> Path:
    """Expand ~ and env-vars, return a Path."""
    return Path(os.path.expandvars(os.path.expanduser(p)))


_DEFAULTS_MAP: dict[str, Path] = {
    k: _expand(v)
    for k, v in _CABLE_CFG.get("defaults_map", {}).items()
}
_DEFAULTS_FALLBACK = _expand(str(_CABLE_CFG.get("defaults_fallback", "~/Downloads")))


def get_default_dest(cat: str) -> Path:
    """Return the Windows known-folder for a category key."""
    return _DEFAULTS_MAP.get(cat, _DEFAULTS_FALLBACK)

def pick_destination(
    source_folder: Path,
    default_mode: str = "here",
    default_custom: str = "",
) -> tuple[str, Optional[Path]]:
    """Ask the user WHERE sorted subfolders should land.

    Returns (dest_mode, dest_root) where dest_root is:
      None  → 'here' or 'defaults'  (handled at call-site)
      Path  → chosen directory for 'where'
    """
    default_key = {"here": "1", "defaults": "2", "where": "3"}.get(default_mode, "1")

    here_note     = f"[{C_DIM}](subfolders inside [bold]{source_folder.name}[/])[/]"
    default_note  = f"[{C_DIM}](Pictures, Videos, Music, Documents, Downloads…)[/]"
    where_note    = f"[{C_DIM}](pick any folder via dialog)[/]"

    console.print(Panel(
        f"  [{C_ACCENT}]1[/]  [#f9fafb]Here[/]      {here_note}\n"
        f"  [{C_ACCENT}]2[/]  [#f9fafb]Defaults[/]  {default_note}\n"
        f"  [{C_ACCENT}]3[/]  [#f9fafb]Where[/]     {where_note}",
        title="[bold #a78bfa]Destination[/]",
        border_style="#4c1d95",
        padding=(1, 2),
    ))
    console.print()

    while True:
        raw = Prompt.ask(
            "  [bold #c4b5fd]Choose destination[/]",
            default=default_key,
            console=console,
        ).strip()

        if raw == "1":
            console.print(
                f"  [bold #34d399]✔[/]  [#f9fafb]Destination:[/] "
                f"[{C_ACCENT}]Here[/]  [{C_DIM}]({source_folder})[/]\n"
            )
            return "here", None

        if raw == "2":
            console.print(
                f"  [bold #34d399]✔[/]  [#f9fafb]Destination:[/] "
                f"[{C_ACCENT}]Windows Defaults[/]\n"
            )
            return "defaults", None

        if raw == "3":
            console.print(f"  [{C_DIM}]A folder dialog will open — choose where you want files to go.[/]")
            console.print()
            # Pre-fill with last custom path if available
            while True:
                dest = pick_folder(title="Select destination folder")
                if dest:
                    console.print(
                        f"  [bold #34d399]✔[/]  [#f9fafb]Destination:[/] "
                        f"[{C_ACCENT}]{dest}[/]\n"
                    )
                    return "where", dest.resolve()
                # Closed dialog without picking — ask again
                retry = Confirm.ask(
                    f"  [{C_WARN}]No folder selected. Try again?[/]",
                    default=True,
                    console=console,
                )
                if not retry:
                    console.print(f"  [{C_DIM}]Falling back to [bold]Here[/].[/]\n")
                    return "here", None

        console.print(f"  [{C_BAD}]Please enter 1, 2 or 3.[/]")

def pick_run_mode(default: str = "1") -> str:
    """Ask the user if they want a one-time sort or a continuous background watcher."""
    console.print(Panel(
        f"  [{C_ACCENT}]1[/]  [#f9fafb]One-Time Sort[/]      [dim](Sort files now and exit)[/]\n"
        f"  [{C_ACCENT}]2[/]  [#f9fafb]Background Watcher[/] [dim](Run silently in system tray, auto-sorting new files)[/]",
        title="[bold #a78bfa]Operation Mode[/]",
        border_style="#4c1d95",
        padding=(1, 2),
    ))
    console.print()
    while True:
        raw = Prompt.ask(
            "  [bold #c4b5fd]Choose mode[/]",
            default=default,
            console=console,
        ).strip()
        if raw in ("1", "2"):
            label = "One-Time Sort" if raw == "1" else "Background Watcher"
            console.print(
                f"  [bold #34d399]✔[/]  [#f9fafb]Mode:[/] "
                f"[{C_ACCENT}]{label}[/]\n"
            )
            return raw
        console.print(f"  [{C_BAD}]Please enter 1 or 2.[/]")
    return "1"  # unreachable; satisfies type checker

SORT_OPTIONS = [
    ("1", "Alphabetical",  "alpha"),
    ("2", "Extension",     "ext"),
    ("3", "Size",          "size"),
    ("4", "Date Modified", "date"),
    ("5", "Combination",   "combo"),
]


def pick_sort_order(default: str = "alpha") -> str:
    """Ask the user how to order files within each category before moving."""
    code_to_key = {code: key for key, _, code in SORT_OPTIONS}
    default_key = code_to_key.get(default, "1")
    console.print(Panel(
        "\n".join(
            f"  [{C_ACCENT}]{key}[/]  [#f9fafb]{label}[/]"
            for key, label, _ in SORT_OPTIONS
        ),
        title="[bold #a78bfa]Sort Order[/]",
        border_style="#4c1d95",
        padding=(1, 2),
    ))
    console.print()
    valid  = {key: code for key, _, code in SORT_OPTIONS}
    labels = {code: label for _, label, code in SORT_OPTIONS}
    while True:
        raw = Prompt.ask(
            "  [bold #c4b5fd]Choose sort order[/]",
            default=default_key,
            console=console,
        ).strip()
        if raw in valid:
            code = valid[raw]
            console.print(
                f"  [bold #34d399]✔[/]  [#f9fafb]Sorting by:[/] "
                f"[{C_ACCENT}]{labels[code]}[/]\n"
            )
            return code
        console.print(f"  [{C_BAD}]Please enter a number 1\u2013{len(SORT_OPTIONS)}.[/]")
    return "alpha"  # unreachable; satisfies type checker

def pick_options(cfg: dict) -> dict:
    """Interactive step to configure copy mode, date subfolders, and exclude patterns."""
    # Copy mode
    copy_mode = Confirm.ask(
        "  [bold #c4b5fd]Copy files instead of moving?[/]",
        default=bool(cfg["copy_mode"]),
        console=console,
    )
    console.print()

    # Date subfolders
    date_subfolders = Confirm.ask(
        "  [bold #c4b5fd]Organise media into YYYY/MM subfolders?[/]",
        default=bool(cfg["date_subfolders"]),
        console=console,
    )
    console.print()

    # Exclude patterns
    current: list[str] = list(cfg["exclude_patterns"])
    if current:
        console.print(Panel(
            "  " + "  ".join(f"[{C_ACCENT}]{p}[/]" for p in current),
            title="[bold #a78bfa]Active Exclude Patterns[/]",
            border_style="#4c1d95",
            padding=(1, 2),
        ))
    else:
        console.print(f"  [{C_DIM}]No exclude patterns set.[/]")
    console.print()

    edit = Confirm.ask(
        "  [bold #c4b5fd]Edit exclude patterns?[/]",
        default=False,
        console=console,
    )
    if edit:
        console.print(f"  [{C_DIM}]Enter patterns separated by commas (e.g. *.tmp, desktop.ini).[/]")
        console.print(f"  [{C_DIM}]Leave blank to clear all patterns.[/]")
        raw = Prompt.ask(
            "  [bold #c4b5fd]Patterns[/]",
            default=",".join(current) if current else "",
            console=console,
        )
        current = [p.strip() for p in raw.split(",") if p.strip()]
    console.print()

    return {
        **cfg,
        "copy_mode":        copy_mode,
        "date_subfolders":  date_subfolders,
        "exclude_patterns": current,
    }

def apply_excludes(items: list[Path], patterns: list[str]) -> list[Path]:
    if not patterns:
        return items
    return [
        item for item in items
        if not any(fnmatch.fnmatch(item.name, p) for p in patterns)
    ]

def _item_sort_key(item: Path, mode: str):
    name_lower = item.name.lower()
    ext_lower  = item.suffix.lower()
    try:
        stat  = item.stat()
        size  = stat.st_size
        mtime = stat.st_mtime
    except OSError:
        size, mtime = 0, 0.0

    if mode == "alpha":
        return (name_lower,)
    elif mode == "ext":
        return (ext_lower, name_lower)
    elif mode == "size":
        return (-size, name_lower)
    elif mode == "date":
        return (-mtime, name_lower)
    else:  # combo
        return (ext_lower, -size, name_lower)


def sorted_items(items: list[Path], mode: str) -> list[Path]:
    return sorted(items, key=lambda p: _item_sort_key(p, mode))

def classify(item: Path) -> str:
    if item.is_dir():
        return "📁  Folders"
    return EXT_MAP.get(item.suffix.lower(), MISC_KEY)


def cat_meta(key: str) -> dict:
    return CATEGORIES.get(key, {"folder": "Miscellaneous", "icon": "❓", "color": "#9ca3af"})

def unique_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    counter = 1
    while True:
        nd = dest.parent / f"{dest.stem} ({counter}){dest.suffix}"
        if not nd.exists():
            return nd
        counter += 1
    return dest  # unreachable; satisfies type checker

def file_hash(path: Path, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            while True:
                buf = fh.read(chunk)
                if not buf:
                    break
                h.update(buf)
    except OSError:
        return ""
    return h.hexdigest()

def _fmt_size(b: int) -> str:
    n: float = b
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _item_size(item: Path) -> int:
    try:
        return item.stat().st_size
    except OSError:
        return 0

def build_preview(items: list[Path], sort_mode: str = "alpha") -> Table:
    extra_labels = {
        "alpha": "Extension",
        "ext":   "Extension",
        "size":  "Size",
        "date":  "Modified",
        "combo": "Ext / Size",
    }
    extra_label = extra_labels.get(sort_mode, "Info")
    total_size  = sum(_item_size(i) for i in items)

    t = Table(
        box=box.SIMPLE_HEAD,
        border_style="#4c1d95",
        header_style="bold #a78bfa",
        show_edge=True,
        show_lines=False,
        expand=True,
        title=(
            f"[bold #c4b5fd]Preview — {len(items)} item{'s' if len(items) != 1 else ''}"
            f"  ·  {_fmt_size(total_size)} total[/]"
        ),
        title_style="bold",
    )
    t.add_column("#",          style=C_DIM,    width=4, justify="right")
    t.add_column("Name",       style="#f9fafb", ratio=5)
    t.add_column("Category",   ratio=3)
    t.add_column(extra_label,  style="#60a5fa", ratio=2)
    t.add_column("→ Folder",   style="#818cf8", ratio=3)

    for idx, item in enumerate(items[:60], 1):  # type: ignore[misc]
        cat   = classify(item)
        meta  = cat_meta(cat)
        label = cat.split("  ")[-1] if "  " in cat else cat

        try:
            stat = item.stat()
            if sort_mode == "size":
                extra = _fmt_size(stat.st_size)
            elif sort_mode == "date":
                extra = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
            elif sort_mode == "combo":
                extra = f"{item.suffix.lower() or '–'}  {_fmt_size(stat.st_size)}"
            else:
                extra = item.suffix.lower() or "–"
        except OSError:
            extra = "–"

        t.add_row(
            f"[dim]{idx}[/]",
            f"[{meta['color']}]{meta['icon']}[/]  {item.name}",
            f"[{meta['color']}]{label}[/]",
            f"[dim]{extra}[/]",
            f"[dim]{meta['folder']}/[/]",
        )

    if len(items) > 60:
        t.add_row("…", f"[dim]…and {len(items)-60} more[/]", "", "", "")

    return t

def build_summary(
    results:      dict,
    size_results: dict,
    elapsed:      float,
    copy_mode:    bool,
    duplicates:   int,
) -> Table:
    verb = "Copied" if copy_mode else "Moved"
    t = Table(
        box=box.SIMPLE_HEAD,
        border_style="#065f46",
        header_style="bold #34d399",
        show_edge=True,
        show_lines=False,
        expand=True,
        title="[bold #34d399]✔  All Done[/]",
    )
    t.add_column("Category",   ratio=4)
    t.add_column(verb,         justify="right", width=8)
    t.add_column("Size",       style="#6ee7b7", width=10, justify="right")
    t.add_column("Dest Folder", style="#6ee7b7", ratio=3)

    total_count: int = 0
    total_bytes: int = 0
    for cat, count in sorted(results.items(), key=lambda x: -x[1]):
        if count == 0:
            continue
        meta  = cat_meta(cat)
        label = cat.split("  ")[-1] if "  " in cat else cat
        sz    = size_results.get(cat, 0)
        t.add_row(
            f"[{meta['color']}]{meta['icon']}  {label}[/]",
            f"[bold #f9fafb]{count}[/]",
            f"[dim]{_fmt_size(sz)}[/]",
            f"[dim]{meta['folder']}/[/]",
        )
        total_count += count
        total_bytes += sz

    if duplicates:
        t.add_row(
            f"[{C_WARN}]⊘  Duplicates skipped[/]",
            f"[{C_WARN}]{duplicates}[/]",
            "",
            "[dim]—[/]",
        )

    t.add_section()
    t.add_row(
        "[bold #f9fafb]Total[/]",
        f"[bold #fbbf24]{total_count}[/]",
        f"[bold #fbbf24]{_fmt_size(total_bytes)}[/]",
        f"[dim]in {elapsed:.1f}s[/]",
    )
    return t

def build_stats_panel(results: dict, size_results: dict) -> Panel:
    BAR_WIDTH = 28
    total     = max(sum(results.values()), 1)
    lines: list[Text] = []

    for cat, count in sorted(results.items(), key=lambda x: -x[1]):
        if count == 0:
            continue
        meta   = cat_meta(cat)
        label  = (cat.split("  ")[-1] if "  " in cat else cat)[:12]
        sz     = size_results.get(cat, 0)
        filled = round(BAR_WIDTH * count / total)
        empty  = BAR_WIDTH - filled

        bar = Text()
        bar.append(f"  {meta['icon']}  ", style=meta["color"])
        bar.append(f"{label:<12}  ", style=meta["color"])
        bar.append("█" * filled, style=f"bold {meta['color']}")
        bar.append("░" * empty,  style="dim #4c1d95")
        bar.append(f"  {count:>3}  ", style="bold #f9fafb")
        bar.append(f"({_fmt_size(sz)})", style=C_DIM)
        lines.append(bar)

    return Panel(
        Group(*lines),
        title="[bold #a78bfa]Stats[/]",
        border_style="#4c1d95",
        padding=(1, 2),
    )

def _dest_dir_for(
    item:            Path,
    target:          Path,
    meta:            dict,
    cat:             str,
    date_subfolders: bool,
    dest_mode:       str  = "here",
    dest_root:       Optional[Path] = None,
) -> Path:
    if dest_mode == "defaults":
        base = get_default_dest(cat)
    elif dest_mode == "where" and dest_root is not None:
        base = dest_root / str(meta["folder"])
    else:  # "here"
        base = target / str(meta["folder"])

    if date_subfolders and cat in DATE_MEDIA_CATS:
        try:
            dt   = datetime.fromtimestamp(item.stat().st_mtime)
            base = base / str(dt.year) / f"{dt.month:02d}"
        except OSError:
            pass
    return base

def sort_folder(
    target:          Path,
    items:           list[Path],
    copy_mode:       bool = False,
    date_subfolders: bool = False,
    dest_mode:       str  = "here",
    dest_root:       Optional[Path] = None,
) -> tuple[dict, dict, float, list[dict], int]:
    """
    Returns: (results, size_results, elapsed, ops_log, duplicates_count)
    ops_log entries only written for move operations (for undo support).
    """
    results:      dict[str, int] = {}
    size_results: dict[str, int] = {}
    ops_log:      list[dict]     = []
    duplicates = 0

    t0 = time.perf_counter()

    with Progress(
        SpinnerColumn(spinner_name="dots2", style=C_ACCENT),
        TextColumn("[bold #c4b5fd]{task.description}"),
        BarColumn(bar_width=36, style=C_PROGRESS, complete_style=C_DONE),
        TaskProgressColumn(style="#a78bfa"),
        TextColumn("[dim]·[/]"),
        TimeElapsedColumn(),
        TextColumn("[dim]{task.fields[fn]}[/]"),
        console=console,
        transient=False,
    ) as prog:
        task = prog.add_task("Sorting", total=len(items), fn="")

        for item in items:
            cat       = classify(item)
            meta      = cat_meta(cat)
            dest_dir  = _dest_dir_for(item, target, meta, cat, date_subfolders, dest_mode, dest_root)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest      = dest_dir / item.name
            item_size = _item_size(item)

            if dest.exists():
                if file_hash(item) == file_hash(dest):
                    duplicates += 1
                    prog.update(task, advance=1, fn=item.name[:45])  # type: ignore[misc]
                    time.sleep(0.008)
                    continue
                dest = unique_dest(dest)

            src_str = str(item)
            dst_str = str(dest)
            if copy_mode:
                shutil.copy2(src_str, dst_str)
            else:
                shutil.move(src_str, dst_str)
                ops_log.append({"src": src_str, "dst": dst_str})

            results[cat]      = results.get(cat, 0) + 1
            size_results[cat] = size_results.get(cat, 0) + item_size
            prog.update(task, advance=1, fn=item.name[:45])  # type: ignore[misc]
            time.sleep(0.008)

    return results, size_results, time.perf_counter() - t0, ops_log, duplicates

def write_undo_log(target: Path, ops: list[dict]) -> None:
    log = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode":      "move",
        "ops":       ops,
    }
    try:
        (target / "sort_log.json").write_text(
            json.dumps(log, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def undo_sort(folder: Path) -> None:
    console.clear()
    print_banner()

    log_path = folder / "sort_log.json"
    if not log_path.exists():
        console.print(Panel(
            f"  [{C_BAD}]No sort_log.json found in:[/]  [#f9fafb]{folder}[/]",
            border_style="#7f1d1d", padding=(1, 2),
        ))
        return

    try:
        log = json.loads(log_path.read_text(encoding="utf-8"))
    except Exception as exc:
        console.print(f"  [{C_BAD}]Could not read sort_log.json: {exc}[/]")
        return

    if log.get("mode") != "move":
        console.print(Panel(
            f"  [{C_WARN}]This log is from a copy operation — undo is not available for copies.[/]",
            border_style="#78350f", padding=(1, 2),
        ))
        return

    ops: list[dict] = log.get("ops", [])
    step_header(1, "Restoring Files")

    ok: int = 0
    fail: int = 0
    with Progress(
        SpinnerColumn(spinner_name="dots2", style=C_ACCENT),
        TextColumn("[bold #c4b5fd]{task.description}"),
        BarColumn(bar_width=36, style=C_PROGRESS, complete_style=C_DONE),
        TaskProgressColumn(style="#a78bfa"),
        console=console,
    ) as prog:
        task = prog.add_task("Restoring", total=len(ops))
        for op in reversed(ops):
            src = Path(op["src"])
            dst = Path(op["dst"])
            if dst.exists():
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(src))
                ok += 1
            else:
                fail += 1
            prog.update(task, advance=1)

    log_path.unlink(missing_ok=True)

    msg = f"  [{C_GOOD}]✔  Restored {ok} file{'s' if ok != 1 else ''}.[/]"
    if fail:
        msg += f"\n  [{C_WARN}]⚠  {fail} file{'s' if fail != 1 else ''} not found (already moved?).[/]"
    console.print()
    console.print(Panel(msg, title="[bold #34d399]Undo Complete[/]", border_style="#065f46", padding=(1, 2)))
    console.print()

LOG_FILE = Path.home() / ".sort_watcher.log"

def create_icon_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon([(8, 16), (24, 16), (32, 24), (56, 24), (56, 52), (8, 52)], fill="#a78bfa")
    draw.rectangle([(8, 24), (56, 52)], fill="#818cf8")
    return img

class SortingHandler(FileSystemEventHandler):  # type: ignore[misc,valid-type]
    def __init__(self, target_folder, icon, dest_mode_override: str = "", dest_custom_override: str = ""):
        self.target = Path(target_folder).resolve()
        self.icon = icon
        self.cfg = load_config()
        # CLI-supplied overrides always win over whatever is in the config file
        if dest_mode_override:
            self.cfg["dest_mode"]   = dest_mode_override
            self.cfg["dest_custom"] = dest_custom_override
        self.sorted_count = 0
        self._lock = threading.Lock()
        self._timers: dict[str, threading.Timer] = {}

    def on_created(self, event):
        if not event.is_directory:
            self._schedule(event.src_path)
            
    def on_modified(self, event):
        if not event.is_directory:
            self._schedule(event.src_path)

    def _schedule(self, src_path):
        with self._lock:
            if src_path in self._timers:
                self._timers[src_path].cancel()
            timer = threading.Timer(2.0, self.process_file, args=[src_path])
            self._timers[src_path] = timer
            timer.start()

    def process_file(self, src_str):
        with self._lock:
            self._timers.pop(src_str, None)
                
            self.cfg = load_config()
            src = Path(src_str)
            if not src.exists():
                return
                
            if src.parent.resolve() != self.target:
                return
                
            if src.name in SKIP_ROOT or src.name.startswith(".") or src.name == "sort_log.json":
                return
                
            if apply_excludes([src], list(self.cfg.get("exclude_patterns", []))) == []:
                return
                
            cat = classify(src)
            meta = cat_meta(cat)
            date_subfolders = bool(self.cfg.get("date_subfolders"))
            dest_mode      = str(self.cfg.get("dest_mode", "here"))
            dest_custom    = str(self.cfg.get("dest_custom", ""))
            dest_root      = Path(dest_custom) if dest_mode == "where" and dest_custom else None

            dest_dir = _dest_dir_for(src, self.target, meta, cat, date_subfolders, dest_mode, dest_root)
            dest = dest_dir / src.name
            
            if src.resolve() == dest.resolve():
                return
                
            if dest.exists():
                if file_hash(src) == file_hash(dest):
                    logging.warning(f"[SKIP] Identical file exists: {src.name}")
                    return
                dest = unique_dest(dest)
                
            copy_mode = bool(self.cfg.get("copy_mode"))
            
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
                # Use full path for log when dest is outside the watched folder
                try:
                    folder_name = dest.parent.relative_to(self.target)
                except ValueError:
                    folder_name = dest.parent
                if copy_mode:
                    shutil.copy2(str(src), str(dest))
                    logging.info(f"[COPY] {src.name}  ->  {folder_name}")
                else:
                    shutil.move(str(src), str(dest))
                    logging.info(f"[MOVE] {src.name}  ->  {folder_name}")
                
                self.sorted_count += 1
                self.icon.title = f"Folder Sorter Watcher\n{self.target.name}\nSorted: {self.sorted_count}"
            except PermissionError:
                self._schedule(src_str)
            except Exception as e:
                logging.error(f"[ERR]  Could not process {src.name}: {e}")

def run_watcher(target_folder: Path, dest_mode_override: str = "", dest_custom_override: str = "") -> None:
    try:
        if Observer is None:
            print("[ERROR] Watcher dependencies not installed.")
            sys.exit(1)
            
        target = target_folder.resolve()
        if not target.is_dir():
            sys.exit(1)
            
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format="%(asctime)s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        logging.info("")
        logging.info("==================================================")
        logging.info(f" STARTED WATCHER")
        logging.info(f" Watching: {target}")
        logging.info("==================================================")
        
        icon = pystray.Icon("sort_watcher")
        icon.icon = create_icon_image()
        icon.title = f"Folder Sorter Watcher\n{target.name}\nSorted: 0"
        
        event_handler = SortingHandler(target, icon,
                                        dest_mode_override=dest_mode_override,
                                        dest_custom_override=dest_custom_override)
        observer = Observer()
        observer.schedule(event_handler, str(target), recursive=False)
        observer.start()
        
        def open_log(icon, item):
            if sys.platform == "win32":
                os.startfile(LOG_FILE)
            else:
                subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", str(LOG_FILE)])
                
        def stop_watcher(icon, item):
            observer.stop()
            icon.stop()
            logging.info("")
            logging.info("--- Watcher Stopped ---")
            
        icon.menu = pystray.Menu(
            pystray.MenuItem(f"Watching: {target.name}", lambda: None, enabled=False),
            pystray.MenuItem(lambda text: f"Sorted items: {event_handler.sorted_count}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Log File", open_log),
            pystray.MenuItem("Exit Watcher", stop_watcher)
        )
        
        icon.run()
        observer.join()
    except Exception as e:
        import traceback
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\nCRITICAL DAEMON CRASH:\n{e}\n")
            f.write(traceback.format_exc())
            f.write("\n")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Folder Sorter v2.0 — Intelligent file organiser",
        add_help=True,
    )
    parser.add_argument(
        "--undo", metavar="FOLDER",
        help="Undo the last sort operation in FOLDER (reads sort_log.json)",
    )
    parser.add_argument(
        "--watch", metavar="FOLDER", nargs="?", const="GUI",
        help="Run as a background watcher on FOLDER (or open a picker if omitted)",
    )
    parser.add_argument(
        "--run-watch-daemon", metavar="FOLDER",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--daemon-dest-mode", metavar="MODE", default="here",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--daemon-dest-custom", metavar="PATH", default="",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.undo:
        undo_sort(Path(args.undo))
        return
        
    if args.run_watch_daemon:
        run_watcher(
            Path(args.run_watch_daemon),
            dest_mode_override=args.daemon_dest_mode,
            dest_custom_override=args.daemon_dest_custom,
        )
        return

    if args.watch:
        if Observer is None:
            console.print(f"[{C_BAD}]Error: Watcher dependencies missing.[/]")
            console.print(f"[{C_DIM}]Run: python -m pip install watchdog pystray pillow[/]")
            return
        if args.watch == "GUI":
            console.clear()
            print_banner()
            step_header(1, "Select a Folder to Watch")
            console.print("  [dim]A system dialog will open \u2014 choose the folder you want to watch.[/]")
            console.print()
            target_path = pick_folder()
            if not target_path:
                console.print(Panel(
                    "  [bold #f87171]No folder was selected.  Exiting.[/]",
                    border_style="#7f1d1d", padding=(1, 2),
                ))
                return
            target = target_path.resolve()
        else:
            target = Path(args.watch).resolve()
            
        if not target.is_dir():
            console.print(f"[{C_BAD}]Error: {target} is not a valid directory.[/]")
            return
            
        flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
        
        try:
            is_compiled = getattr(sys, 'frozen', False)
            exe_name = Path(sys.executable).name.lower()
            if not is_compiled and not exe_name.startswith("python"):
                is_compiled = True
                
            if is_compiled:
                cmd = [sys.executable, "--run-watch-daemon", str(target)]
            else:
                cmd = [sys.executable, __file__, "--run-watch-daemon", str(target)]
            
            subprocess.Popen(cmd, creationflags=flags)
            console.print()
            console.print(f"  [bold #34d399]✔[/]  Watcher started in background for [bold]{target}[/]")
            console.print("  [dim]Look for the purple folder icon in your system tray.[/]")
            console.print()
        except Exception as e:
            console.print(f"[{C_BAD}]Failed to start watcher: {e}[/]")
        return

    console.clear()
    print_banner()
    print_legend()

    cfg = load_config()

    step_header(1, "Select a Folder")
    console.print("  [dim]A system dialog will open — choose the folder you want to sort.[/]")
    console.print()

    target = pick_folder()

    if not target:
        console.print(Panel(
            "  [bold #f87171]No folder was selected.  Exiting.[/]",
            border_style="#7f1d1d", padding=(1, 2),
        ))
        return

    console.print(Panel(
        f"  [bold #34d399]✔[/]  [#f9fafb]{target}[/]",
        title="[bold #a78bfa]Selected Folder[/]",
        border_style="#4c1d95",
        padding=(1, 2),
    ))

    step_header(2, "Destination")
    dest_mode, dest_root = pick_destination(
        source_folder=target,
        default_mode=str(cfg.get("dest_mode", "here")),
        default_custom=str(cfg.get("dest_custom", "")),
    )
    cfg["dest_mode"]   = dest_mode
    cfg["dest_custom"] = str(dest_root) if dest_root else ""

    step_header(3, "Operation Mode")
    run_mode = pick_run_mode(default=str(cfg.get("run_mode", "1")))
    cfg["run_mode"] = run_mode
    
    if run_mode == "2":
        if Observer is None:
            console.print(f"[{C_BAD}]Error: Watcher dependencies missing.[/]")
            console.print(f"[{C_DIM}]Run: python -m pip install watchdog pystray pillow[/]")
            return
            
        flags = 0x08000000 if sys.platform == "win32" else 0
        try:
            is_compiled = getattr(sys, 'frozen', False)
            exe_name = Path(sys.executable).name.lower()
            if not is_compiled and not exe_name.startswith("python"):
                is_compiled = True

            # Pass dest settings directly as CLI args — avoids TOML config dependency.
            save_config(cfg)

            if is_compiled:
                cmd = [sys.executable, "--run-watch-daemon", str(target),
                       "--daemon-dest-mode", dest_mode,
                       "--daemon-dest-custom", cfg["dest_custom"]]
            else:
                cmd = [sys.executable, __file__, "--run-watch-daemon", str(target),
                       "--daemon-dest-mode", dest_mode,
                       "--daemon-dest-custom", cfg["dest_custom"]]
                
            subprocess.Popen(cmd, creationflags=flags)
            console.print()
            console.print(f"  [bold #34d399]✔[/]  Watcher started in background for [bold]{target}[/]")
            # Show where files will land
            if dest_mode == "defaults":
                console.print("  [dim]Files will be sent to their Windows default folders.[/]")
            elif dest_mode == "where" and dest_root:
                console.print(f"  [dim]Sorted subfolders will be created in [bold]{dest_root}[/].[/]")
            else:
                console.print(f"  [dim]Sorted subfolders will be created inside [bold]{target}[/].[/]")
            console.print("  [dim]Look for the purple folder icon in your system tray.[/]")
            console.print()
        except Exception as e:
            console.print(f"[{C_BAD}]Failed to start watcher: {e}[/]")
            
        return

    step_header(4, "Sort Order")
    sort_mode     = pick_sort_order(default=str(cfg["sort_mode"]))
    cfg["sort_mode"] = sort_mode

    step_header(5, "Options")
    cfg = pick_options(cfg)

    raw_items = [
        i for i in target.iterdir()
        if i.name not in SKIP_ROOT and not i.name.startswith(".")
        and i.name != "sort_log.json"
    ]
    raw_items = apply_excludes(raw_items, list(cfg["exclude_patterns"]))

    if not raw_items:
        console.print()
        console.print(Panel(
            "  [bold #fbbf24]The folder is already empty or fully organised![/]",
            border_style="#78350f", padding=(1, 2),
        ))
        save_config(cfg)
        return

    items = sorted_items(raw_items, sort_mode)

    step_header(6, "Preview")
    console.print(build_preview(items, sort_mode))

    # quick category breakdown bar
    counts: dict[str, int] = {}
    for i in items:
        k = classify(i)
        counts[k] = counts.get(k, 0) + 1

    bar_parts: list[Text] = []
    for cat, cnt in list(sorted(counts.items(), key=lambda x: -x[1]))[:6]:  # type: ignore[misc]
        meta  = cat_meta(cat)
        label = cat.split("  ")[-1] if "  " in cat else cat
        bar_parts.append(Text(f"  {meta['icon']} {label}: {cnt}", style=meta["color"]))

    console.print()
    console.print(Columns(bar_parts, padding=(0, 1)))
    console.print()

    # options summary line
    mode_str = "[bold #60a5fa]copy[/]" if cfg["copy_mode"] else "[bold #34d399]move[/]"
    date_str = "[bold #a78bfa]YYYY/MM[/]" if cfg["date_subfolders"] else "[dim]flat[/]"
    excl_str = f"[{C_ACCENT}]{', '.join(cfg['exclude_patterns'])}[/]" if cfg["exclude_patterns"] else "[dim]none[/]"
    if dest_mode == "defaults":
        dest_str = "[bold #a78bfa]Defaults[/]"
    elif dest_mode == "where" and dest_root:
        dest_str = f"[{C_ACCENT}]{dest_root}[/]"
    else:
        dest_str = f"[{C_ACCENT}]Here[/]  [{C_DIM}]({target})[/]"
    console.print(
        f"  [{C_DIM}]Mode:[/] {mode_str}  "
        f"[{C_DIM}]·[/]  [{C_DIM}]Dest:[/] {dest_str}  "
        f"[{C_DIM}]·[/]  [{C_DIM}]Media:[/] {date_str}  "
        f"[{C_DIM}]·[/]  [{C_DIM}]Excluded:[/] {excl_str}"
    )
    console.print()

    step_header(7, "Confirm")
    proceed = Confirm.ask(
        f"  [bold #c4b5fd]{'Copy' if cfg['copy_mode'] else 'Sort'} "
        f"[#fbbf24]{len(items)}[/] items into subfolders?[/]",
        default=True,
        console=console,
    )

    if not proceed:
        console.print()
        console.print("  [bold #fbbf24]Cancelled — nothing was moved.[/]")
        console.print()
        save_config(cfg)
        return

    step_header(8, "Sorting")
    results, size_results, elapsed, ops_log, duplicates = sort_folder(
        target,
        items,
        copy_mode=bool(cfg["copy_mode"]),
        date_subfolders=bool(cfg["date_subfolders"]),
        dest_mode=dest_mode,
        dest_root=dest_root,
    )

    # Write undo log (move mode only)
    # Undo log is written relative to target (source) folder always
    if ops_log and not cfg["copy_mode"]:
        write_undo_log(target, ops_log)
        console.print(f"\n  [{C_DIM}]Undo log saved \u2192 [bold]sort_log.json[/]  (run with --undo to restore)[/]")

    # ── Done ─────────────────────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold #34d399]  ✔  Complete  [/]", style="#065f46"))
    console.print()
    console.print(build_summary(results, size_results, elapsed, bool(cfg["copy_mode"]), duplicates))
    console.print()
    console.print(build_stats_panel(results, size_results))
    console.print()
    console.print(Align.center(
        Text(
            f"Sorted on {datetime.now().strftime('%A, %d %b %Y at %H:%M:%S')}  ·  By 0.6 :3",
            style=C_DIM,
        )
    ))
    console.print()

    # Save config for next run
    save_config(cfg)

    console.print(Align.center(Text("[ Press Enter to exit ]", style="bold #4c1d95")))
    input()


if __name__ == "__main__":
    main()
