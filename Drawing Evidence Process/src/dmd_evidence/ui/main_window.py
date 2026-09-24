from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from dmd_evidence.config import get_config
from dmd_evidence.dmd import DmdDump, DmdFrame, open_dump
from dmd_evidence.geometry import NativeRect, display_rect_to_native, native_rect_to_display
from dmd_evidence.repository import EvidenceSummaryRecord
from dmd_evidence.services import EvidenceService
from dmd_evidence.ui.annotations import (
    AnnotationHit,
    HitKind,
    hit_test,
    move_rect,
    normalized_rect,
    resize_rect,
)
from dmd_evidence.ui.browser import filter_evidence_summaries
from dmd_evidence.ui.navigation import (
    clamp_frame_index,
    nearest_saved_frame_index,
    slider_to_frame_index,
    step_frame_index,
)
from dmd_evidence.ui.rendering import frame_photo_image


class EvidenceCollectorWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("DMD Region Evidence Collector")
        self.minsize(900, 420)

        self.dump: DmdDump | None = None
        self.current_index = 0
        self.canvas_width = 128 * 6
        self.canvas_height = 32 * 6
        self.frame_display_x = 0.0
        self.frame_display_y = 0.0
        self.frame_display_width = float(self.canvas_width)
        self.frame_display_height = float(self.canvas_height)
        self.frame_display_scale = self.frame_display_width / 128
        self.frame_image: tk.PhotoImage | None = None
        self.playing = False
        self.playback_delay_ms = 100
        self.draft_annotations: dict[int, list[NativeRect]] = {}
        self.saved_frame_indices: set[int] = set()
        self.repository_summaries: tuple[EvidenceSummaryRecord, ...] = ()
        self.repository_dump_options: list[tuple[str, int | None]] = [("All dumps", None)]
        self.duplicate_summaries: tuple[EvidenceSummaryRecord, ...] = ()
        self.preview_frame: DmdFrame | None = None
        self.preview_annotations: list[NativeRect] = []
        self.preview_evidence_frame_id: int | None = None
        self.preview_label = ""
        self.selected_annotation: int | None = None
        self.active_hit: AnnotationHit | None = None
        self.drag_start_native: tuple[int, int] | None = None
        self.drag_original_rect: NativeRect | None = None
        self.evidence_service = EvidenceService(get_config().database_path)

        self.dump_label = tk.Label(self, text="Dump: none", anchor="w")
        self.dump_label.grid(row=0, column=0, columnspan=8, sticky="ew", padx=8, pady=(8, 4))

        self.canvas = tk.Canvas(
            self,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#000000",
            highlightthickness=1,
            highlightbackground="#555555",
        )
        self.canvas.grid(row=1, column=0, columnspan=8, padx=8, pady=4, sticky="nsew")
        self.canvas.bind("<Button-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.frame_label = tk.Label(self, text="Frame: - / -", anchor="w")
        self.frame_label.grid(row=2, column=0, columnspan=8, sticky="ew", padx=8, pady=4)

        self.repository_label = tk.Label(self, text="Repository: 0 dumps | 0 evidence frames | 0 boxes", anchor="w")
        self.repository_label.grid(row=3, column=0, columnspan=8, sticky="ew", padx=8, pady=4)

        self.status_label = tk.Label(self, text="Status: ready", anchor="w")
        self.status_label.grid(row=4, column=0, columnspan=8, sticky="ew", padx=8, pady=4)

        self.duplicate_label = tk.Label(self, text="Exact frame matches: none", anchor="w")
        self.duplicate_jump_button = tk.Button(
            self,
            text="Open First Match",
            command=self.open_first_duplicate_match,
            state=tk.DISABLED,
        )
        self.duplicate_label.grid(row=5, column=0, columnspan=6, sticky="ew", padx=8, pady=4)
        self.duplicate_jump_button.grid(row=5, column=6, columnspan=2, sticky="ew", padx=8, pady=4)

        self.timeline = tk.Scale(
            self,
            from_=0,
            to=0,
            orient=tk.HORIZONTAL,
            showvalue=False,
            state=tk.DISABLED,
            command=self.on_timeline_changed,
        )
        self.timeline.grid(row=6, column=0, columnspan=8, sticky="ew", padx=8, pady=4)

        self.marker_canvas = tk.Canvas(
            self,
            width=self.canvas_width,
            height=12,
            bg=self.cget("bg"),
            highlightthickness=0,
        )
        self.marker_canvas.grid(row=7, column=0, columnspan=8, sticky="ew", padx=8, pady=(0, 4))
        self.marker_canvas.bind("<Button-1>", self.on_marker_press)

        self.open_button = tk.Button(self, text="Open Dump", command=self.open_dump_file)
        self.back_10_button = tk.Button(
            self, text="-10", command=lambda: self.step_frames(-10), state=tk.DISABLED
        )
        self.prev_button = tk.Button(
            self, text="-1", command=lambda: self.step_frames(-1), state=tk.DISABLED
        )
        self.next_button = tk.Button(
            self, text="+1", command=lambda: self.step_frames(1), state=tk.DISABLED
        )
        self.forward_10_button = tk.Button(
            self, text="+10", command=lambda: self.step_frames(10), state=tk.DISABLED
        )
        self.play_button = tk.Button(
            self, text="Play", command=self.toggle_playback, state=tk.DISABLED
        )
        self.delete_button = tk.Button(
            self, text="Delete Box", command=self.delete_selected_annotation, state=tk.DISABLED
        )
        self.clear_button = tk.Button(
            self, text="Clear Boxes", command=self.clear_current_annotations, state=tk.DISABLED
        )
        self.submit_button = tk.Button(
            self,
            text="Submit Evidence",
            command=self.submit_current_evidence,
            state=tk.DISABLED,
        )
        self.descriptor_label = tk.Label(self, text="Descriptor", anchor="w")
        self.descriptor_entry = tk.Entry(self, state=tk.DISABLED)
        self.saved_frames_label = tk.Label(
            self,
            text="Saved Frames For Current Dump",
            anchor="w",
        )
        self.saved_frames_list = tk.Listbox(self, height=4, exportselection=False)
        self.saved_frames_list.bind("<<ListboxSelect>>", self.on_saved_frame_selected)
        self.repository_evidence_label = tk.Label(
            self,
            text="All Repository Evidence",
            anchor="w",
        )
        self.repository_filter_frame = tk.Frame(self)
        self.repository_dump_filter = ttk.Combobox(
            self.repository_filter_frame,
            state="readonly",
            width=28,
            values=("All dumps",),
        )
        self.repository_dump_filter.current(0)
        self.repository_dump_filter.bind("<<ComboboxSelected>>", self.on_repository_filter_changed)
        self.repository_text_filter = tk.Entry(self.repository_filter_frame)
        self.repository_text_filter.bind("<KeyRelease>", self.on_repository_filter_changed)
        self.repository_refresh_button = tk.Button(
            self.repository_filter_frame,
            text="Refresh",
            command=self.refresh_repository_browser,
        )
        self.repository_export_button = tk.Button(
            self.repository_filter_frame,
            text="Export Report",
            command=self.export_repository_report,
        )
        self.repository_evidence_list = tk.Listbox(self, height=5, exportselection=False)
        self.repository_evidence_list.bind("<<ListboxSelect>>", self.on_repository_evidence_selected)
        self.jump_entry = tk.Entry(self, width=8, state=tk.DISABLED)
        self.jump_button = tk.Button(self, text="Jump", command=self.jump_to_entry, state=tk.DISABLED)

        self.open_button.grid(row=8, column=0, padx=8, pady=(4, 8), sticky="ew")
        self.back_10_button.grid(row=8, column=1, padx=8, pady=(4, 8), sticky="ew")
        self.prev_button.grid(row=8, column=2, padx=8, pady=(4, 8), sticky="ew")
        self.next_button.grid(row=8, column=3, padx=8, pady=(4, 8), sticky="ew")
        self.forward_10_button.grid(row=8, column=4, padx=8, pady=(4, 8), sticky="ew")
        self.play_button.grid(row=8, column=5, padx=8, pady=(4, 8), sticky="ew")
        self.jump_entry.grid(row=8, column=6, padx=8, pady=(4, 8), sticky="ew")
        self.jump_button.grid(row=8, column=7, padx=8, pady=(4, 8), sticky="ew")
        self.delete_button.grid(row=9, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")
        self.clear_button.grid(row=9, column=2, columnspan=2, padx=8, pady=(0, 8), sticky="ew")
        self.submit_button.grid(row=9, column=4, columnspan=4, padx=8, pady=(0, 8), sticky="ew")
        self.descriptor_label.grid(row=10, column=0, columnspan=1, sticky="ew", padx=8)
        self.descriptor_entry.grid(row=10, column=1, columnspan=7, sticky="ew", padx=8)
        self.saved_frames_label.grid(row=11, column=0, columnspan=8, sticky="ew", padx=8)
        self.saved_frames_list.grid(row=12, column=0, columnspan=8, sticky="ew", padx=8, pady=(0, 8))
        self.repository_evidence_label.grid(row=13, column=0, columnspan=8, sticky="ew", padx=8)
        self.repository_filter_frame.grid(row=14, column=0, columnspan=8, sticky="ew", padx=8, pady=(0, 4))
        self.repository_dump_filter.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.repository_text_filter.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.repository_refresh_button.grid(row=0, column=2, sticky="ew")
        self.repository_export_button.grid(row=0, column=3, sticky="ew", padx=(8, 0))
        self.repository_filter_frame.grid_columnconfigure(1, weight=1)
        self.repository_evidence_list.grid(row=15, column=0, columnspan=8, sticky="ew", padx=8, pady=(0, 8))

        self.grid_columnconfigure(tuple(range(8)), weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.bind("<Left>", lambda event: self.step_frames(-10 if event.state & 0x0001 else -1))
        self.bind("<Right>", lambda event: self.step_frames(10 if event.state & 0x0001 else 1))
        self.bind("<Return>", lambda _event: self.jump_to_entry())
        self.bind("<Delete>", lambda _event: self.delete_selected_annotation())
        self.bind("<F11>", lambda _event: self.toggle_fullscreen())
        self.bind("<Escape>", lambda _event: self.attributes("-fullscreen", False))
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_repository_status()
        self.refresh_repository_browser()

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

        self.evidence_service.open_dump(self.dump)
        self.saved_frame_indices = set(self.evidence_service.saved_frame_indices())
        self.clear_repository_preview()
        self.update_repository_status()
        self.refresh_repository_browser()
        self.current_index = 0
        self.selected_annotation = None
        self.draft_annotations = {}
        self.load_saved_annotations_for_current_frame()
        self.load_descriptor_for_displayed_frame()
        self.set_navigation_state(tk.NORMAL)
        self.timeline.config(to=max(0, self.dump.frame_count - 1))
        self.refresh_saved_frames_list()
        known_text = "known dump" if self.evidence_service.last_opened_dump_was_known else "new dump"
        self.set_status(
            f"Loaded {known_text}: {self.dump.filename}; "
            f"{len(self.saved_frame_indices)} saved frames found."
        )
        self.render_current_frame()

    def set_navigation_state(self, state: str) -> None:
        self.timeline.config(state=state)
        self.back_10_button.config(state=state)
        self.prev_button.config(state=state)
        self.next_button.config(state=state)
        self.forward_10_button.config(state=state)
        self.play_button.config(state=state)
        self.jump_entry.config(state=state)
        self.jump_button.config(state=state)
        self.submit_button.config(state=state)
        self.descriptor_entry.config(state=state)
        self.clear_button.config(state=state)
        self.update_annotation_button_state()

    def step_frames(self, delta: int) -> None:
        if self.dump is None:
            return
        self.clear_repository_preview()
        self.selected_annotation = None
        self.current_index = step_frame_index(self.current_index, self.dump.frame_count, delta)
        self.load_saved_annotations_for_current_frame()
        self.load_descriptor_for_displayed_frame()
        self.render_current_frame(update_timeline=True)

    def on_timeline_changed(self, value: str) -> None:
        if self.dump is None:
            return
        self.clear_repository_preview()
        self.selected_annotation = None
        self.current_index = slider_to_frame_index(value, self.dump.frame_count)
        self.load_saved_annotations_for_current_frame()
        self.load_descriptor_for_displayed_frame()
        self.render_current_frame(update_timeline=False)

    def jump_to_entry(self) -> None:
        if self.dump is None:
            return
        try:
            requested = int(self.jump_entry.get()) - 1
        except ValueError:
            messagebox.showerror("Invalid frame", "Enter a frame number.")
            return
        self.clear_repository_preview()
        self.selected_annotation = None
        self.current_index = clamp_frame_index(requested, self.dump.frame_count)
        self.load_saved_annotations_for_current_frame()
        self.load_descriptor_for_displayed_frame()
        self.render_current_frame(update_timeline=True)

    def toggle_playback(self) -> None:
        if self.dump is None:
            return
        self.playing = not self.playing
        self.play_button.config(text="Pause" if self.playing else "Play")
        if self.playing:
            self.after(self.playback_delay_ms, self.playback_tick)

    def playback_tick(self) -> None:
        if self.dump is None or not self.playing:
            return
        if self.current_index >= self.dump.frame_count - 1:
            self.playing = False
            self.play_button.config(text="Play")
            return
        self.step_frames(1)
        self.after(self.playback_delay_ms, self.playback_tick)

    def render_current_frame(self, update_timeline: bool = True) -> None:
        frame = self.displayed_frame()
        if frame is None:
            return
        self.canvas.delete("all")
        self.update_frame_display_bounds()
        self.frame_image = frame_photo_image(frame, int(self.frame_display_scale))
        self.canvas.create_image(
            round(self.frame_display_x),
            round(self.frame_display_y),
            anchor=tk.NW,
            image=self.frame_image,
        )
        if self.preview_frame is not None:
            self.dump_label.config(text=f"Repository Preview: {self.preview_label}")
            self.frame_label.config(
                text=f"Stored frame index: {frame.source_index}   Header: {frame.header}"
            )
        else:
            self.dump_label.config(
                text=(
                    f"Dump: {self.dump.filename}   Frames: {self.dump.frame_count}   "
                    f"Saved evidence frames: {len(self.saved_frame_indices)}"
                )
            )
            self.frame_label.config(
                text=(
                    f"Frame: {self.current_index + 1} / {self.dump.frame_count}   "
                    f"Index: {self.current_index}   Header: {frame.header}"
                )
            )
        if update_timeline and self.preview_frame is None:
            self.timeline.set(self.current_index)
        if self.preview_frame is None:
            self.jump_entry.delete(0, tk.END)
            self.jump_entry.insert(0, str(self.current_index + 1))
        self.draw_annotations()
        self.draw_evidence_markers()
        self.select_current_saved_frame_row()
        self.update_duplicate_notice(frame)
        self.update_annotation_button_state()

    def current_annotations(self) -> list[NativeRect]:
        if self.preview_frame is not None:
            return self.preview_annotations
        return self.draft_annotations.setdefault(self.current_index, [])

    def displayed_frame(self) -> DmdFrame | None:
        if self.preview_frame is not None:
            return self.preview_frame
        if self.dump is None:
            return None
        return self.dump.get_frame(self.current_index)

    def load_saved_annotations_for_current_frame(self) -> None:
        if self.current_index in self.draft_annotations:
            return
        self.draft_annotations[self.current_index] = self.evidence_service.load_regions(
            self.current_index
        )

    def load_descriptor_for_displayed_frame(self) -> None:
        descriptor = ""
        if self.preview_evidence_frame_id is not None:
            for summary in self.evidence_service.all_evidence_summaries():
                if summary.evidence_frame_id == self.preview_evidence_frame_id:
                    descriptor = summary.descriptor
                    break
        elif self.dump is not None and self.current_index in self.saved_frame_indices:
            for summary in self.evidence_service.all_evidence_summaries():
                if (
                    self.evidence_service.dump_record is not None
                    and summary.dump_id == self.evidence_service.dump_record.id
                    and summary.source_frame_index == self.current_index
                ):
                    descriptor = summary.descriptor
                    break
        self.descriptor_entry.delete(0, tk.END)
        self.descriptor_entry.insert(0, descriptor)

    def canvas_to_native(self, canvas_x: float, canvas_y: float) -> tuple[int, int]:
        rect = display_rect_to_native(
            x=canvas_x - self.frame_display_x,
            y=canvas_y - self.frame_display_y,
            width=1,
            height=1,
            display_width=self.frame_display_width,
            display_height=self.frame_display_height,
            frame_width=128,
            frame_height=32,
        )
        return rect.x, rect.y

    def on_canvas_press(self, event: tk.Event) -> None:
        if self.displayed_frame() is None:
            return
        native_x, native_y = self.canvas_to_native(event.x, event.y)
        annotations = self.current_annotations()
        hit = hit_test(annotations, native_x, native_y)
        self.drag_start_native = (native_x, native_y)
        if hit is not None:
            self.selected_annotation = hit.index
            self.active_hit = hit
            self.drag_original_rect = annotations[hit.index]
        else:
            self.selected_annotation = len(annotations)
            self.active_hit = None
            self.drag_original_rect = normalized_rect(native_x, native_y, native_x, native_y)
            annotations.append(self.drag_original_rect)
        self.draw_annotations()
        self.update_annotation_button_state()

    def on_canvas_drag(self, event: tk.Event) -> None:
        if self.displayed_frame() is None or self.drag_start_native is None or self.selected_annotation is None:
            return
        native_x, native_y = self.canvas_to_native(event.x, event.y)
        annotations = self.current_annotations()
        if self.selected_annotation >= len(annotations) or self.drag_original_rect is None:
            return
        if self.active_hit is None:
            start_x, start_y = self.drag_start_native
            annotations[self.selected_annotation] = normalized_rect(
                start_x, start_y, native_x, native_y
            ).clamped(128, 32)
        elif self.active_hit.kind == HitKind.BODY:
            start_x, start_y = self.drag_start_native
            annotations[self.selected_annotation] = move_rect(
                self.drag_original_rect,
                native_x - start_x,
                native_y - start_y,
                128,
                32,
            )
        else:
            annotations[self.selected_annotation] = resize_rect(
                self.drag_original_rect,
                self.active_hit.kind,
                native_x,
                native_y,
                128,
                32,
            )
        self.draw_annotations()

    def on_canvas_release(self, _event: tk.Event) -> None:
        self.drag_start_native = None
        self.drag_original_rect = None
        self.active_hit = None
        self.draw_annotations()

    def draw_annotations(self) -> None:
        self.canvas.delete("annotation")
        annotations = self.current_annotations() if self.displayed_frame() is not None else []
        for index, rect in enumerate(annotations):
            x, y, width, height = native_rect_to_display(
                rect,
                display_width=self.frame_display_width,
                display_height=self.frame_display_height,
                frame_width=128,
                frame_height=32,
            )
            x += self.frame_display_x
            y += self.frame_display_y
            selected = index == self.selected_annotation
            outline = "#57ff6a" if selected else "#ffea3b"
            self.canvas.create_rectangle(
                x,
                y,
                x + width,
                y + height,
                outline=outline,
                width=3 if selected else 2,
                tags=("annotation",),
            )
            if selected:
                self.draw_annotation_handles(x, y, width, height)

    def draw_annotation_handles(self, x: float, y: float, width: float, height: float) -> None:
        size = 8
        for handle_x, handle_y in (
            (x, y),
            (x + width, y),
            (x, y + height),
            (x + width, y + height),
        ):
            self.canvas.create_rectangle(
                handle_x - size / 2,
                handle_y - size / 2,
                handle_x + size / 2,
                handle_y + size / 2,
                fill="#57ff6a",
                outline="#111111",
                tags=("annotation",),
            )

    def delete_selected_annotation(self) -> None:
        if self.displayed_frame() is None or self.selected_annotation is None:
            return
        annotations = self.current_annotations()
        if self.selected_annotation < len(annotations):
            del annotations[self.selected_annotation]
        self.selected_annotation = None
        self.draw_annotations()
        self.update_annotation_button_state()

    def clear_current_annotations(self) -> None:
        if self.displayed_frame() is None:
            return
        if self.preview_frame is not None:
            self.preview_annotations = []
        else:
            self.draft_annotations[self.current_index] = []
        self.selected_annotation = None
        self.draw_annotations()
        self.update_annotation_button_state()

    def update_annotation_button_state(self) -> None:
        if self.displayed_frame() is None:
            self.delete_button.config(state=tk.DISABLED)
            self.clear_button.config(state=tk.DISABLED)
            self.submit_button.config(state=tk.DISABLED)
            return
        has_selection = self.selected_annotation is not None
        self.delete_button.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.clear_button.config(state=tk.NORMAL)
        self.submit_button.config(state=tk.NORMAL)

    def submit_current_evidence(self) -> None:
        if self.preview_frame is not None:
            if self.preview_evidence_frame_id is None:
                return
            try:
                self.evidence_service.update_evidence_regions(
                    self.preview_evidence_frame_id,
                    list(self.preview_annotations),
                    self.descriptor_entry.get(),
                )
            except Exception as exc:  # noqa: BLE001 - user-facing persistence boundary
                messagebox.showerror("Submit failed", str(exc))
                self.set_status(f"Submit failed: {exc}")
                return
            self.update_repository_status()
            self.refresh_repository_browser()
            self.set_status("Repository preview evidence updated.")
            self.render_current_frame()
            return
        if self.dump is None:
            return
        frame = self.dump.get_frame(self.current_index)
        regions = list(self.current_annotations())
        try:
            self.evidence_service.submit_current_frame(
                frame,
                regions,
                self.descriptor_entry.get(),
            )
        except Exception as exc:  # noqa: BLE001 - user-facing persistence boundary
            messagebox.showerror("Submit failed", str(exc))
            self.set_status(f"Submit failed: {exc}")
            return
        self.saved_frame_indices = set(self.evidence_service.saved_frame_indices())
        self.update_repository_status()
        self.refresh_saved_frames_list()
        self.refresh_repository_browser()
        self.draw_evidence_markers()
        self.set_status(
            f"Evidence saved for frame {self.current_index + 1}; "
            f"{len(self.saved_frame_indices)} saved frames in current dump."
        )
        self.render_current_frame()

    def draw_evidence_markers(self) -> None:
        self.marker_canvas.delete("all")
        if self.dump is None or self.dump.frame_count <= 0:
            return
        width = max(1, self.marker_canvas.winfo_width())
        for index in sorted(self.saved_frame_indices):
            x = 0 if self.dump.frame_count == 1 else round(index / (self.dump.frame_count - 1) * width)
            self.marker_canvas.create_line(x, 0, x, 12, fill="#57ff6a", width=2)

    def update_repository_status(self) -> None:
        counts = self.evidence_service.counts()
        self.repository_label.config(
            text=(
                "Repository: "
                f"{counts['dumps']} dumps | "
                f"{counts['evidence_frames']} evidence frames | "
                f"{counts['regions']} boxes"
            )
        )

    def refresh_repository_browser(self) -> None:
        self.refresh_repository_dump_filter()
        self.refresh_repository_evidence_list()
        frame = self.displayed_frame()
        if frame is not None:
            self.update_duplicate_notice(frame)

    def refresh_repository_dump_filter(self) -> None:
        selected_dump_id = self.selected_repository_dump_id()
        dumps = self.evidence_service.all_dumps()
        self.repository_dump_options = [("All dumps", None)]
        self.repository_dump_options.extend((dump.filename, dump.id) for dump in dumps)
        values = tuple(label for label, _dump_id in self.repository_dump_options)
        self.repository_dump_filter.config(values=values)
        matching_index = 0
        for index, (_label, dump_id) in enumerate(self.repository_dump_options):
            if dump_id == selected_dump_id:
                matching_index = index
                break
        self.repository_dump_filter.current(matching_index)

    def selected_repository_dump_id(self) -> int | None:
        selection = self.repository_dump_filter.current()
        if selection < 0 or selection >= len(self.repository_dump_options):
            return None
        return self.repository_dump_options[selection][1]

    def on_repository_filter_changed(self, _event: tk.Event | None = None) -> None:
        self.refresh_repository_evidence_list()

    def export_repository_report(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export Evidence Report",
            defaultextension=".json",
            filetypes=(("JSON reports", "*.json"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            payload = self.evidence_service.export_repository_report(path)
        except Exception as exc:  # noqa: BLE001 - user-facing export boundary
            messagebox.showerror("Export failed", str(exc))
            self.set_status(f"Export failed: {exc}")
            return
        counts = payload["counts"]
        self.set_status(
            "Exported evidence report: "
            f"{counts['dumps']} dumps, "
            f"{counts['evidence_frames']} evidence frames, "
            f"{counts['regions']} boxes."
        )

    def refresh_repository_evidence_list(self) -> None:
        self.repository_evidence_list.delete(0, tk.END)
        selected_dump_id = self.selected_repository_dump_id()
        text_filter = self.repository_text_filter.get().strip().lower()
        self.repository_summaries = filter_evidence_summaries(
            self.evidence_service.all_evidence_summaries(),
            selected_dump_id,
            text_filter,
        )
        for summary in self.repository_summaries:
            self.repository_evidence_list.insert(
                tk.END,
                (
                    f"{summary.filename} | "
                    f"{summary.descriptor or '(no descriptor)'} | "
                    f"Frame {summary.source_frame_index + 1} | "
                    f"index {summary.source_frame_index} | "
                    f"{summary.region_count} boxes"
                ),
            )

    def refresh_saved_frames_list(self) -> None:
        self.saved_frames_list.delete(0, tk.END)
        if self.dump is None:
            return
        for index in sorted(self.saved_frame_indices):
            regions = self.evidence_service.load_regions(index)
            self.saved_frames_list.insert(
                tk.END,
                f"Frame {index + 1} | index {index} | {len(regions)} boxes",
            )
        self.select_current_saved_frame_row()

    def select_current_saved_frame_row(self) -> None:
        self.saved_frames_list.selection_clear(0, tk.END)
        if self.current_index not in self.saved_frame_indices:
            return
        row = sorted(self.saved_frame_indices).index(self.current_index)
        self.saved_frames_list.selection_set(row)
        self.saved_frames_list.see(row)

    def on_saved_frame_selected(self, _event: tk.Event) -> None:
        selection = self.saved_frames_list.curselection()
        if self.dump is None or not selection:
            return
        saved_indices = sorted(self.saved_frame_indices)
        row = selection[0]
        if row >= len(saved_indices):
            return
        self.jump_to_frame_index(saved_indices[row])

    def on_marker_press(self, event: tk.Event) -> None:
        if self.dump is None or not self.saved_frame_indices:
            return
        width = max(1, self.marker_canvas.winfo_width())
        if self.dump.frame_count == 1:
            self.jump_to_frame_index(0)
            return
        approximate = round(event.x / width * (self.dump.frame_count - 1))
        nearest = nearest_saved_frame_index(approximate, self.saved_frame_indices)
        if nearest is not None:
            self.jump_to_frame_index(nearest)

    def jump_to_frame_index(self, frame_index: int) -> None:
        if self.dump is None:
            return
        self.clear_repository_preview()
        self.selected_annotation = None
        self.current_index = clamp_frame_index(frame_index, self.dump.frame_count)
        self.load_saved_annotations_for_current_frame()
        self.load_descriptor_for_displayed_frame()
        self.render_current_frame(update_timeline=True)

    def on_repository_evidence_selected(self, _event: tk.Event) -> None:
        selection = self.repository_evidence_list.curselection()
        if not selection:
            return
        row = selection[0]
        if row >= len(self.repository_summaries):
            return
        summary = self.repository_summaries[row]
        if self.dump is not None and self.evidence_service.dump_record is not None:
            if summary.dump_id == self.evidence_service.dump_record.id:
                self.jump_to_frame_index(summary.source_frame_index)
                return
        self.preview_evidence_frame_id = summary.evidence_frame_id
        self.preview_frame = self.evidence_service.load_evidence_frame(summary.evidence_frame_id)
        self.preview_annotations = self.evidence_service.load_evidence_regions(
            summary.evidence_frame_id
        )
        self.preview_label = (
            f"{summary.filename} | frame {summary.source_frame_index + 1} | "
            f"index {summary.source_frame_index}"
        )
        self.selected_annotation = None
        self.load_descriptor_for_displayed_frame()
        self.set_status(f"Previewing repository evidence: {self.preview_label}")
        self.render_current_frame(update_timeline=False)

    def open_first_duplicate_match(self) -> None:
        if not self.duplicate_summaries:
            return
        self.open_repository_summary(self.duplicate_summaries[0])

    def open_repository_summary(self, summary: EvidenceSummaryRecord) -> None:
        if self.dump is not None and self.evidence_service.dump_record is not None:
            if summary.dump_id == self.evidence_service.dump_record.id:
                self.jump_to_frame_index(summary.source_frame_index)
                return
        self.preview_evidence_frame_id = summary.evidence_frame_id
        self.preview_frame = self.evidence_service.load_evidence_frame(summary.evidence_frame_id)
        self.preview_annotations = self.evidence_service.load_evidence_regions(
            summary.evidence_frame_id
        )
        self.preview_label = (
            f"{summary.filename} | frame {summary.source_frame_index + 1} | "
            f"index {summary.source_frame_index}"
        )
        self.selected_annotation = None
        self.load_descriptor_for_displayed_frame()
        self.set_status(f"Previewing exact frame match: {self.preview_label}")
        self.render_current_frame(update_timeline=False)

    def update_duplicate_notice(self, frame: DmdFrame) -> None:
        self.duplicate_summaries = self.evidence_service.matching_evidence_summaries(frame)
        if not self.duplicate_summaries:
            self.duplicate_label.config(text="Exact frame matches: none")
            self.duplicate_jump_button.config(state=tk.DISABLED)
            return
        first = self.duplicate_summaries[0]
        plural = "match" if len(self.duplicate_summaries) == 1 else "matches"
        self.duplicate_label.config(
            text=(
                f"Exact frame matches: {len(self.duplicate_summaries)} {plural}; "
                f"first is {first.filename} frame {first.source_frame_index + 1}"
            )
        )
        self.duplicate_jump_button.config(state=tk.NORMAL)

    def clear_repository_preview(self) -> None:
        self.preview_frame = None
        self.preview_annotations = []
        self.preview_evidence_frame_id = None
        self.preview_label = ""

    def on_close(self) -> None:
        self.evidence_service.close()
        self.destroy()

    def on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas_width = max(1, event.width)
        self.canvas_height = max(1, event.height)
        if self.displayed_frame() is not None:
            self.render_current_frame(update_timeline=False)

    def update_frame_display_bounds(self) -> None:
        canvas_width = max(1, self.canvas_width)
        canvas_height = max(1, self.canvas_height)
        self.frame_display_scale = max(1, int(min(canvas_width / 128, canvas_height / 32)))
        self.frame_display_width = self.frame_display_scale * 128
        self.frame_display_height = self.frame_display_scale * 32
        self.frame_display_x = (canvas_width - self.frame_display_width) / 2
        self.frame_display_y = (canvas_height - self.frame_display_height) / 2

    def toggle_fullscreen(self) -> None:
        self.attributes("-fullscreen", not bool(self.attributes("-fullscreen")))

    def set_status(self, message: str) -> None:
        self.status_label.config(text=f"Status: {message}")


def main() -> None:
    app = EvidenceCollectorWindow()
    app.mainloop()
