"""COMPTIA Parser — Desktop application entry point."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
import time
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from excel_exporter import export_to_excel
from pdf_parser import parse_pdf

# ── Black & blue palette ─────────────────────────────────────────────────────
BG = "#06080F"
BG_GRADIENT = "#0A1020"
SURFACE = "#0D1424"
CARD = "#111B2E"
CARD_HOVER = "#152238"
CARD_ACTIVE = "#1A2D4A"
BORDER = "#1E3050"
BORDER_HOVER = "#2563EB"
BORDER_ACTIVE = "#3B82F6"
BLUE = "#2563EB"
BLUE_LIGHT = "#3B82F6"
BLUE_BRIGHT = "#60A5FA"
BLUE_DEEP = "#1D4ED8"
BLUE_GLOW = "#93C5FD"
CYAN = "#0EA5E9"
TEXT = "#F1F5F9"
MUTED = "#8B9CB8"
DIM = "#4A5D7A"
SUCCESS = "#38BDF8"
ERROR = "#F87171"


class ComptiaParserApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("COMPTIA Parser")
        self.geometry("660x600")
        self.minsize(600, 560)
        self.configure(bg=BG)

        self._pdf_path: str = ""
        self._output_dir: str = ""
        self._exported_files: list[str] = []
        self._processing = False
        self._pulse_on = False
        self._target_progress = 0.0
        self._current_progress = 0.0
        self._file_selected = False

        self.file_label = tk.StringVar(value="Drop a PDF here or click to browse")
        self.status_text = tk.StringVar(value="Waiting for file…")
        self.stats_text = tk.StringVar(value="")

        self._configure_styles()
        self._build_ui()
        self._animate_progress()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Blue.Horizontal.TProgressbar",
            troughcolor=SURFACE,
            background=BLUE_LIGHT,
            bordercolor=BORDER,
            lightcolor=BLUE_BRIGHT,
            darkcolor=BLUE,
            thickness=8,
        )

    def _build_ui(self) -> None:
        # Top accent strip
        tk.Frame(self, bg=BLUE, height=3).pack(fill=tk.X)

        outer = tk.Frame(self, bg=BG, padx=36, pady=30)
        outer.pack(fill=tk.BOTH, expand=True)

        # Header
        header = tk.Frame(outer, bg=BG)
        header.pack(fill=tk.X, pady=(0, 24))

        title_row = tk.Frame(header, bg=BG)
        title_row.pack(anchor=tk.W)
        tk.Label(title_row, text="COMPTIA", bg=BG, fg=BLUE_BRIGHT, font=("Segoe UI", 28, "bold")).pack(
            side=tk.LEFT
        )
        tk.Label(title_row, text=" Parser", bg=BG, fg=TEXT, font=("Segoe UI", 28, "bold")).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="Upload a CompTIA MCQ PDF and export structured Excel files instantly",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor=tk.W, pady=(8, 0))

        # Upload zone
        self.upload_outer = tk.Frame(outer, bg=BORDER, padx=1, pady=1)
        self.upload_outer.pack(fill=tk.X, pady=(0, 22))
        self.upload_card = tk.Frame(self.upload_outer, bg=CARD, cursor="hand2")
        self.upload_card.pack(fill=tk.X)
        self._build_upload_card()

        self.upload_card.bind("<Enter>", self._on_card_enter)
        self.upload_card.bind("<Leave>", self._on_card_leave)
        self.upload_card.bind("<Button-1>", self._on_card_click)

        # Action buttons
        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill=tk.X, pady=(0, 22))

        self.parse_btn = self._make_button(
            btn_row,
            "⚡  Parse & Export",
            self._start_processing,
            bg=BLUE,
            hover=BLUE_LIGHT,
            active=BLUE_DEEP,
            font_size=11,
            bold=True,
            padx=30,
            pady=13,
        )
        self.parse_btn.pack(side=tk.LEFT)

        self.download_btn = self._make_button(
            btn_row,
            "↓  Download",
            self._download_files,
            bg=SURFACE,
            hover=CARD_HOVER,
            active=CARD,
            fg=MUTED,
            font_size=11,
            bold=True,
            padx=26,
            pady=13,
            state=tk.DISABLED,
            outline=True,
        )
        self.download_btn.pack(side=tk.LEFT, padx=(14, 0))

        # Progress section
        prog_section = tk.Frame(outer, bg=BG)
        prog_section.pack(fill=tk.X, pady=(0, 8))

        prog_header = tk.Frame(prog_section, bg=BG)
        prog_header.pack(fill=tk.X, pady=(0, 8))

        self.status_dot = tk.Label(prog_header, text="●", bg=BG, fg=DIM, font=("Segoe UI", 8))
        self.status_dot.pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(prog_header, textvariable=self.status_text, bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(
            side=tk.LEFT
        )
        self.pct_label = tk.Label(prog_header, text="0%", bg=BG, fg=BLUE_BRIGHT, font=("Segoe UI", 9, "bold"))
        self.pct_label.pack(side=tk.RIGHT)

        prog_wrap = tk.Frame(prog_section, bg=BORDER, padx=1, pady=1)
        prog_wrap.pack(fill=tk.X)
        self.progress = ttk.Progressbar(prog_wrap, mode="determinate", style="Blue.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, padx=1, pady=1)
        self.progress["value"] = 0

        self.stats_label = tk.Label(
            outer, textvariable=self.stats_text, bg=BG, fg=SUCCESS, font=("Segoe UI", 9, "bold")
        )
        self.stats_label.pack(anchor=tk.W, pady=(6, 0))

        # Feature pills
        pills = tk.Frame(outer, bg=BG)
        pills.pack(anchor=tk.W, pady=(22, 0))
        for text in ("Single & multi-select", "Auto-split at 100", "Ignores explanations"):
            self._make_pill(pills, text).pack(side=tk.LEFT, padx=(0, 8))

    def _build_upload_card(self) -> None:
        self.card_inner = tk.Frame(self.upload_card, bg=CARD, padx=28, pady=30)
        self.card_inner.pack(fill=tk.X)

        self.icon_bg = tk.Frame(self.card_inner, bg=SURFACE, width=64, height=64)
        self.icon_bg.pack()
        self.icon_bg.pack_propagate(False)
        self.icon_label = tk.Label(self.icon_bg, text="📄", bg=SURFACE, font=("Segoe UI", 26))
        self.icon_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.file_name_label = tk.Label(
            self.card_inner,
            textvariable=self.file_label,
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 11),
        )
        self.file_name_label.pack(pady=(16, 6))

        self.file_hint = tk.Label(
            self.card_inner,
            text="PDF only  ·  Max recommended 500+ questions",
            bg=CARD,
            fg=DIM,
            font=("Segoe UI", 8),
        )
        self.file_hint.pack(pady=(0, 18))

        self.select_btn = self._make_button(
            self.card_inner,
            "Browse Files",
            self._browse_pdf,
            bg=SURFACE,
            hover=CARD_HOVER,
            active=CARD_ACTIVE,
            fg=BLUE_BRIGHT,
            font_size=10,
            padx=22,
            pady=9,
            outline=True,
        )
        self.select_btn.pack()

        for widget in (self.card_inner, self.icon_bg, self.icon_label, self.file_name_label, self.file_hint):
            widget.bind("<Button-1>", self._on_card_click)
            widget.configure(cursor="hand2")

    def _on_card_click(self, event) -> None:
        if self._processing or isinstance(event.widget, tk.Button):
            return
        self._browse_pdf()

    def _make_pill(self, parent: tk.Frame, text: str) -> tk.Frame:
        wrap = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        inner = tk.Label(wrap, text=text, bg=SURFACE, fg=MUTED, font=("Segoe UI", 8), padx=10, pady=4)
        inner.pack()
        return wrap

    def _make_button(
        self,
        parent,
        text: str,
        command,
        bg: str,
        hover: str,
        active: str,
        fg: str = "white",
        font_size: int = 10,
        bold: bool = False,
        padx: int = 16,
        pady: int = 8,
        state=tk.NORMAL,
        outline: bool = False,
    ) -> tk.Button:
        weight = "bold" if bold else "normal"
        base_bg = bg
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active,
            activeforeground=fg,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", font_size, weight),
            padx=padx,
            pady=pady,
            state=state,
            borderwidth=1 if outline else 0,
            highlightthickness=1 if outline else 0,
            highlightbackground=BORDER if outline else bg,
            highlightcolor=BLUE_LIGHT if outline else bg,
        )

        def on_enter(_e) -> None:
            if btn["state"] == tk.DISABLED:
                return
            btn.configure(bg=hover)
            if outline:
                btn.configure(highlightbackground=BLUE_LIGHT)

        def on_leave(_e) -> None:
            if btn["state"] == tk.DISABLED:
                return
            btn.configure(bg=base_bg)
            if outline:
                btn.configure(highlightbackground=BORDER)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn._base_bg = base_bg  # type: ignore[attr-defined]
        btn._hover_bg = hover  # type: ignore[attr-defined]
        btn._outline = outline  # type: ignore[attr-defined]
        return btn

    def _on_card_enter(self, _event=None) -> None:
        if self._processing:
            return
        color = BORDER_ACTIVE if self._file_selected else BORDER_HOVER
        self.upload_outer.configure(bg=color)
        self.upload_card.configure(bg=CARD_HOVER)
        self.card_inner.configure(bg=CARD_HOVER)
        self.file_name_label.configure(bg=CARD_HOVER)
        self.file_hint.configure(bg=CARD_HOVER)

    def _on_card_leave(self, _event=None) -> None:
        if self._processing:
            return
        color = BORDER_ACTIVE if self._file_selected else BORDER
        bg = CARD_ACTIVE if self._file_selected else CARD
        self.upload_outer.configure(bg=color)
        self.upload_card.configure(bg=bg)
        self.card_inner.configure(bg=bg)
        self.file_name_label.configure(bg=bg)
        self.file_hint.configure(bg=bg)

    def _set_file_selected(self, name: str) -> None:
        self._file_selected = True
        self.file_label.set(name)
        self.file_name_label.configure(fg=TEXT, font=("Segoe UI", 12, "bold"))
        self.file_hint.configure(text="File ready — click Parse & Export")
        self.icon_label.configure(text="✓", fg=SUCCESS, bg=SURFACE)
        self.upload_outer.configure(bg=BORDER_ACTIVE)
        self.upload_card.configure(bg=CARD_ACTIVE)
        self.card_inner.configure(bg=CARD_ACTIVE)
        self.file_name_label.configure(bg=CARD_ACTIVE)
        self.file_hint.configure(bg=CARD_ACTIVE, fg=BLUE_GLOW)
        self.status_dot.configure(fg=BLUE_BRIGHT)
        self.status_text.set("Ready to parse")

    def _reset_file_state(self) -> None:
        self._file_selected = False
        self.file_label.set("Drop a PDF here or click to browse")
        self.file_name_label.configure(fg=MUTED, font=("Segoe UI", 11))
        self.file_hint.configure(text="PDF only  ·  Max recommended 500+ questions", fg=DIM)
        self.icon_label.configure(text="📄", fg=TEXT)
        self._on_card_leave()

    def _browse_pdf(self) -> None:
        if self._processing:
            return
        path = filedialog.askopenfilename(
            title="Select CompTIA MCQ PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if path:
            self._pdf_path = path
            self._set_file_selected(Path(path).name)
            self.stats_text.set("")
            self._disable_download()
            self._exported_files.clear()

    def _enable_download(self) -> None:
        self.download_btn.configure(
            state=tk.NORMAL,
            bg=BLUE,
            fg="white",
            highlightbackground=BLUE,
            cursor="hand2",
        )
        self.download_btn._base_bg = BLUE  # type: ignore[attr-defined]
        self.download_btn._hover_bg = BLUE_LIGHT  # type: ignore[attr-defined]

    def _disable_download(self) -> None:
        self.download_btn.configure(
            state=tk.DISABLED,
            bg=SURFACE,
            fg=MUTED,
            highlightbackground=BORDER,
            cursor="arrow",
        )

    def _set_busy(self, busy: bool) -> None:
        self._processing = busy
        self.parse_btn.configure(state=tk.DISABLED if busy else tk.NORMAL)
        self.select_btn.configure(state=tk.DISABLED if busy else tk.NORMAL)
        self.upload_card.configure(cursor="watch" if busy else "hand2")

        if busy:
            self._pulse_on = True
            self.status_dot.configure(fg=BLUE_BRIGHT)
            self._pulse_status()
        else:
            self._pulse_on = False
            self.status_dot.configure(fg=BLUE_BRIGHT if self._file_selected else DIM)

    def _pulse_status(self) -> None:
        if not self._pulse_on:
            return
        current = self.status_dot.cget("fg")
        self.status_dot.configure(fg=BG if current == BLUE_BRIGHT else BLUE_BRIGHT)
        self.after(500, self._pulse_status)

    def _animate_progress(self) -> None:
        if self._current_progress < self._target_progress:
            self._current_progress = min(self._current_progress + 2.5, self._target_progress)
            self.progress["value"] = self._current_progress
            self.pct_label.configure(text=f"{int(self._current_progress)}%")
        elif self._current_progress > self._target_progress:
            self._current_progress = self._target_progress
            self.progress["value"] = self._current_progress
            self.pct_label.configure(text=f"{int(self._current_progress)}%")
        self.after(16, self._animate_progress)

    def _update_progress(self, fraction: float, message: str) -> None:
        self.after(0, lambda: self._apply_progress(fraction, message))

    def _apply_progress(self, fraction: float, message: str) -> None:
        self._target_progress = min(fraction * 100, 100)
        self.status_text.set(message)

    def _start_processing(self) -> None:
        if self._processing:
            return

        if not self._pdf_path or not os.path.isfile(self._pdf_path):
            messagebox.showwarning("No PDF Selected", "Please select a PDF file first.")
            return

        self._set_busy(True)
        self._disable_download()
        self._target_progress = 0
        self._current_progress = 0
        self.progress["value"] = 0
        self.pct_label.configure(text="0%")
        self.status_text.set("Starting…")
        self.stats_text.set("")

        if self._output_dir and os.path.isdir(self._output_dir):
            shutil.rmtree(self._output_dir, ignore_errors=True)
        self._output_dir = tempfile.mkdtemp(prefix="comptia_export_")
        self._exported_files.clear()

        thread = threading.Thread(target=self._run_pipeline, daemon=True)
        thread.start()

    def _run_pipeline(self) -> None:
        start = time.perf_counter()
        try:
            def parse_progress(fraction: float, msg: str) -> None:
                self._update_progress(fraction * 0.88, msg)

            mcqs = parse_pdf(self._pdf_path, progress_callback=parse_progress)

            if not mcqs:
                self.after(0, lambda: messagebox.showwarning(
                    "No Questions Found",
                    "Could not extract any MCQs from this PDF.\n\n"
                    "Expected format:\n"
                    "  QUESTION 1\n  [text]\n  A. … B. …\n  Answer: C",
                ))
                self.after(0, lambda: self._finish(False, "No questions found.", 0.0))
                return

            base_name = Path(self._pdf_path).stem

            def export_progress(fraction: float, msg: str) -> None:
                self._update_progress(0.88 + fraction * 0.12, msg)

            files = export_to_excel(
                mcqs,
                self._output_dir,
                base_name=base_name,
                progress_callback=export_progress,
            )

            elapsed = time.perf_counter() - start
            count = len(mcqs)
            file_word = "file" if len(files) == 1 else "files"
            summary = f"Exported {count} questions into {len(files)} {file_word}"
            self.after(0, lambda: self._finish(True, summary, elapsed, files))

        except Exception as exc:
            elapsed = time.perf_counter() - start
            self.after(0, lambda: messagebox.showerror("Error", f"Something went wrong:\n\n{exc}"))
            self.after(0, lambda: self._finish(False, f"Error: {exc}", elapsed))

    def _finish(
        self,
        success: bool,
        message: str,
        elapsed: float,
        files: list[str] | None = None,
    ) -> None:
        self._set_busy(False)
        self._target_progress = 100 if success else 0

        if success:
            self.status_text.set(message)
            self.stats_text.set(f"✓  Completed in {elapsed:.1f}s  —  Ready to download")
            self._exported_files = files or []
            self._enable_download()
            self.status_dot.configure(fg=SUCCESS)
        else:
            self.status_text.set(message)
            self.stats_text.set("")
            self._disable_download()
            self.status_dot.configure(fg=ERROR)

    def _download_files(self) -> None:
        if not self._exported_files:
            return

        if len(self._exported_files) == 1:
            src = self._exported_files[0]
            dest = filedialog.asksaveasfilename(
                title="Save Excel File",
                defaultextension=".xlsx",
                initialfile=Path(src).name,
                filetypes=[("Excel files", "*.xlsx")],
            )
            if dest:
                shutil.copy2(src, dest)
                self.status_text.set(f"Saved {Path(dest).name}")
                self.stats_text.set(f"✓  Downloaded to your chosen location")
        else:
            default_name = f"{Path(self._pdf_path).stem}_comptia_mcqs.zip"
            dest = filedialog.asksaveasfilename(
                title="Save All Files",
                defaultextension=".zip",
                initialfile=default_name,
                filetypes=[("ZIP archive", "*.zip")],
            )
            if dest:
                with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
                    for file_path in self._exported_files:
                        archive.write(file_path, Path(file_path).name)
                self.status_text.set(f"Saved {len(self._exported_files)} files as {Path(dest).name}")
                self.stats_text.set(f"✓  Downloaded {len(self._exported_files)} files as ZIP")


def main() -> None:
    app = ComptiaParserApp()
    app.mainloop()


if __name__ == "__main__":
    main()
