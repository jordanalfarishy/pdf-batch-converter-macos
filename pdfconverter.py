"""macOS interface for PDF Batch Converter."""

from __future__ import annotations

import os
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import filedialog, messagebox

import customtkinter as ctk

from converter_core import COMPRESS_PRESETS, convert_folder, list_subfolders

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG, CARD, FIELD, BORDER = "#10151E", "#19212D", "#111923", "#303C4C"
TEXT, MUTED, BLUE = "#F4F7FB", "#A3B0C2", "#4A91FF"
PRESET_HELP = {
    "None": "Original JPEG/PNG; WebP becomes lossless PNG.",
    "Low": "Higher clarity · JPEG 85% · up to 3000 px",
    "Medium": "Balanced size and clarity · JPEG 65% · up to 2000 px",
    "High": "Smaller files · JPEG 40% · up to 1200 px",
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF Batch Converter")
        self.geometry("760x840")
        self.minsize(650, 780)
        self.configure(fg_color=BG)
        self.input_path = self.output_path = ""
        self.cancel_event = threading.Event()
        self.events = queue.Queue()
        self.running = self.closing = False
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(80, self._drain_events)

    @staticmethod
    def _card(parent):
        return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12)

    @staticmethod
    def _section(parent, text):
        return ctk.CTkLabel(parent, text=text, text_color=MUTED,
                            font=ctk.CTkFont(size=10, weight="bold"), anchor="w")

    def _build_ui(self):
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=28, pady=(26, 22))
        ctk.CTkLabel(root, text="PDF Batch Converter", font=ctk.CTkFont(size=27, weight="bold"),
                     text_color=TEXT, anchor="w").pack(fill="x")
        ctk.CTkLabel(root, text="Create one PDF from the images in each subfolder.",
                     font=ctk.CTkFont(size=13), text_color=MUTED, anchor="w").pack(fill="x", pady=(3, 22))

        setup = self._card(root)
        setup.pack(fill="x")
        self._section(setup, "FOLDERS").pack(fill="x", padx=20, pady=(17, 13))
        self.input_entry, self.input_button = self._folder_row(
            setup, "Input folder", self._pick_input)
        self.output_entry, self.output_button = self._folder_row(
            setup, "Save PDFs to", self._pick_output, bottom=19)

        options = self._card(root)
        options.pack(fill="x", pady=(14, 0))
        self._section(options, "COMPRESSION").pack(fill="x", padx=20, pady=(17, 11))
        self.compress_var = ctk.StringVar(value="Medium")
        self.compress_control = ctk.CTkSegmentedButton(
            options, values=list(COMPRESS_PRESETS), variable=self.compress_var,
            command=self._compression_changed, height=36, corner_radius=8,
            fg_color=FIELD, selected_color=BLUE, selected_hover_color="#337BE9",
            unselected_color=FIELD, unselected_hover_color=BORDER,
            text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold"))
        self.compress_control.pack(fill="x", padx=20)
        self.compress_help = ctk.CTkLabel(
            options, text=PRESET_HELP["Medium"], text_color=MUTED,
            font=ctk.CTkFont(size=11), anchor="w")
        self.compress_help.pack(fill="x", padx=20, pady=(10, 17))

        actions = ctk.CTkFrame(root, fg_color="transparent")
        actions.pack(fill="x", pady=(18, 18))
        self.start_button = ctk.CTkButton(
            actions, text="Convert folders", command=self._start,
            fg_color=BLUE, hover_color="#337BE9", text_color="#FFFFFF",
            height=42, corner_radius=9, font=ctk.CTkFont(size=13, weight="bold"))
        self.start_button.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.cancel_button = ctk.CTkButton(
            actions, text="Cancel", command=self._cancel, state="disabled",
            fg_color=CARD, hover_color=BORDER, border_width=1, border_color=BORDER,
            text_color=TEXT, height=42, width=116, corner_radius=9,
            font=ctk.CTkFont(size=13))
        self.cancel_button.pack(side="left")

        activity = self._card(root)
        activity.pack(fill="both", expand=True)
        heading = ctk.CTkFrame(activity, fg_color="transparent")
        heading.pack(fill="x", padx=20, pady=(17, 11))
        self._section(heading, "ACTIVITY").pack(side="left")
        self.count_label = ctk.CTkLabel(
            heading, text="0 / 0", text_color=MUTED, font=ctk.CTkFont(size=12))
        self.count_label.pack(side="right")
        self.progress_bar = ctk.CTkProgressBar(
            activity, height=7, corner_radius=4, fg_color=FIELD, progress_color=BLUE)
        self.progress_bar.pack(fill="x", padx=20)
        self.progress_bar.set(0)
        self.status_label = ctk.CTkLabel(
            activity, text="Ready to convert", text_color=MUTED,
            font=ctk.CTkFont(size=12), anchor="w")
        self.status_label.pack(fill="x", padx=20, pady=(10, 11))
        self.console = ctk.CTkTextbox(
            activity, fg_color=FIELD, border_width=1, border_color=BORDER,
            text_color=TEXT, font=ctk.CTkFont(family="Menlo", size=11),
            corner_radius=8, wrap="word", activate_scrollbars=True)
        self.console.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        for tag, color in {"ok": "#58D39B", "warn": "#F1BD65",
                           "err": "#F07878", "info": MUTED}.items():
            self.console.tag_config(tag, foreground=color)
        self.console.configure(state="disabled")

    def _folder_row(self, parent, label, command, bottom=13):
        ctk.CTkLabel(parent, text=label, text_color=TEXT,
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(
                         fill="x", padx=20, pady=(0, 7))
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, bottom))
        entry = ctk.CTkEntry(
            row, state="normal",
            fg_color=FIELD, border_color=BORDER, text_color=TEXT,
            placeholder_text_color=MUTED, height=37, corner_radius=8,
            font=ctk.CTkFont(size=12))
        entry.insert(0, "No folder selected")
        entry.configure(state="readonly")
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        button = ctk.CTkButton(
            row, text="Choose…", command=command, fg_color=FIELD,
            hover_color=BORDER, border_width=1, border_color=BORDER,
            text_color=TEXT, width=96, height=37, corner_radius=8,
            font=ctk.CTkFont(size=12))
        button.pack(side="left")
        return entry, button

    @staticmethod
    def _set_entry(entry, path):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, path)
        entry.configure(state="readonly")

    def _pick_input(self):
        path = filedialog.askdirectory(title="Choose the folder containing image subfolders")
        if path:
            self.input_path = path
            self._set_entry(self.input_entry, path)

    def _pick_output(self):
        path = filedialog.askdirectory(title="Choose where to save the PDFs")
        if path:
            self.output_path = path
            self._set_entry(self.output_entry, path)

    def _compression_changed(self, choice):
        self.compress_help.configure(text=PRESET_HELP[choice])

    def _log(self, text, tag="info"):
        self.console.configure(state="normal")
        self.console.insert("end", text + "\n", tag)
        self.console.see("end")
        self.console.configure(state="disabled")

    def _start(self):
        if self.running:
            return
        if not os.path.isdir(self.input_path) or not os.path.isdir(self.output_path):
            messagebox.showerror("Select folders", "Choose existing input and output folders first.")
            return
        if os.path.samefile(self.input_path, self.output_path):
            messagebox.showerror("Choose another output folder", "Input and output must be different folders.")
            return
        try:
            folders = [path for path in list_subfolders(self.input_path)
                       if not os.path.samefile(path, self.output_path)]
        except OSError as exc:
            messagebox.showerror("Cannot read input folder", str(exc))
            return
        if not folders:
            messagebox.showinfo("No subfolders", "The input folder has no subfolders to convert.")
            return

        self.running = True
        self.cancel_event.clear()
        self.completed = self.succeeded = self.skipped = self.failed = 0
        self.total = len(folders)
        self.started_at = time.monotonic()
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
        self._log(f"Found {self.total} folders · {self.compress_var.get()} compression")
        self.count_label.configure(text=f"0 / {self.total}")
        self.status_label.configure(text="Converting…")
        self.progress_bar.set(0)
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.input_button.configure(state="disabled")
        self.output_button.configure(state="disabled")
        self.compress_control.configure(state="disabled")
        args = (folders, self.output_path, self.compress_var.get())
        threading.Thread(target=self._worker, args=args, daemon=True).start()

    def _cancel(self):
        if self.running:
            self.cancel_event.set()
            self.cancel_button.configure(state="disabled")
            self.status_label.configure(text="Cancelling after current folder…")

    def _worker(self, folders, output_path, preset):
        try:
            with ThreadPoolExecutor(max_workers=min(4, len(folders))) as executor:
                futures = [executor.submit(convert_folder, path, output_path, preset, self.cancel_event)
                           for path in folders]
                for future in as_completed(futures):
                    self.events.put(("result", future.result()))
        except Exception as exc:
            self.events.put(("fatal", str(exc)))
        finally:
            self.events.put(("done",))

    def _drain_events(self):
        if self.closing:
            return
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "result":
                    self._show_result(event[1])
                elif event[0] == "fatal":
                    self.failed += 1
                    self._log(f"Batch error: {event[1]}", "err")
                elif event[0] == "done":
                    self._finish()
        except queue.Empty:
            pass
        self.after(80, self._drain_events)

    def _show_result(self, result):
        self.completed += 1
        if result.status == "ok":
            self.succeeded += 1
            tag = "ok"
            message = f"✓  {result.output_name}  ·  {result.page_count} pages"
            if result.skipped_images:
                message += f"  ·  {result.skipped_images} unreadable skipped"
        elif result.status == "skipped":
            self.skipped += 1
            tag, message = "warn", f"!  {result.folder_name}  ·  {result.detail}"
        elif result.status == "cancelled":
            tag, message = "warn", f"–  {result.folder_name}  ·  cancelled"
        else:
            self.failed += 1
            tag, message = "err", f"×  {result.folder_name}  ·  {result.detail}"
        self._log(message, tag)
        self.count_label.configure(text=f"{self.completed} / {self.total}")
        self.progress_bar.set(self.completed / self.total)
        if not self.cancel_event.is_set():
            self.status_label.configure(
                text=f"{self.succeeded} created · {self.skipped} skipped · {self.failed} failed")

    def _finish(self):
        elapsed = time.monotonic() - self.started_at
        prefix = "Cancelled" if self.cancel_event.is_set() else "Complete"
        self.status_label.configure(
            text=f"{prefix} · {self.succeeded} created · {self.skipped} skipped · "
                 f"{self.failed} failed · {elapsed:.1f}s")
        self.running = False
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.input_button.configure(state="normal")
        self.output_button.configure(state="normal")
        self.compress_control.configure(state="normal")

    def _close(self):
        self.closing = True
        self.cancel_event.set()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
