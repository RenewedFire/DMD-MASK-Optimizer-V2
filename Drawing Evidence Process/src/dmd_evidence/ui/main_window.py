from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from dmd_evidence.dmd import DmdDump, open_dump
from dmd_evidence.ui.rendering import frame_canvas_rectangles


class EvidenceCollectorWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("DMD Region Evidence Collector")
        self.resizable(False, False)

        self.dump: DmdDump | None = None
        self.current_index = 0
        self.scale = 6

        self.dump_label = tk.Label(self, text="Dump: none", anchor="w")
        self.dump_label.grid(row=0, column=0, columnspan=5, sticky="ew", padx=8, pady=(8, 4))

        self.canvas = tk.Canvas(
            self,
            width=128 * self.scale,
            height=32 * self.scale,
            bg="#000000",
            highlightthickness=1,
            highlightbackground="#555555",
        )
        self.canvas.grid(row=1, column=0, columnspan=5, padx=8, pady=4)

        self.frame_label = tk.Label(self, text="Frame: - / -", anchor="w")
        self.frame_label.grid(row=2, column=0, columnspan=5, sticky="ew", padx=8, pady=4)

        self.open_button = tk.Button(self, text="Open Dump", command=self.open_dump_file)
        self.prev_button = tk.Button(self, text="Prev", command=self.previous_frame, state=tk.DISABLED)
        self.next_button = tk.Button(self, text="Next", command=self.next_frame, state=tk.DISABLED)

        self.open_button.grid(row=3, column=0, padx=8, pady=(4, 8), sticky="ew")
        self.prev_button.grid(row=3, column=1, padx=8, pady=(4, 8), sticky="ew")
        self.next_button.grid(row=3, column=2, padx=8, pady=(4, 8), sticky="ew")

        self.bind("<Left>", lambda _event: self.previous_frame())
        self.bind("<Right>", lambda _event: self.next_frame())

    def open_dump_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open VPinMAME DMD dump",
            filetypes=(("Text dumps", "*.txt"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            self.dump = open_dump(Path(path))
        except Exception as exc:  # noqa: BLE001 - user-facing import boundary
            messagebox.showerror("Import failed", str(exc))
            return

        self.current_index = 0
        self.prev_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.NORMAL)
        self.render_current_frame()

    def previous_frame(self) -> None:
        if self.dump is None:
            return
        self.current_index = max(0, self.current_index - 1)
        self.render_current_frame()

    def next_frame(self) -> None:
        if self.dump is None:
            return
        self.current_index = min(self.dump.frame_count - 1, self.current_index + 1)
        self.render_current_frame()

    def render_current_frame(self) -> None:
        if self.dump is None:
            return
        frame = self.dump.get_frame(self.current_index)
        self.canvas.delete("all")
        for x1, y1, x2, y2, color in frame_canvas_rectangles(frame, self.scale):
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)
        self.dump_label.config(
            text=f"Dump: {self.dump.filename}   Frames: {self.dump.frame_count}"
        )
        self.frame_label.config(
            text=(
                f"Frame: {self.current_index + 1} / {self.dump.frame_count}   "
                f"Index: {self.current_index}   Header: {frame.header}"
            )
        )


def main() -> None:
    app = EvidenceCollectorWindow()
    app.mainloop()
