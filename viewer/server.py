from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_config
from src.frames import DmdFrame
from src.parsing import FrameParseError, parse_dump_file
from src.spatial import (
    candidate_boxes_to_payload,
    components_to_payload,
    find_component_relationships,
    find_lit_components,
    generate_candidate_boxes,
    relationships_to_payload,
)


VIEWER_DIR = Path(__file__).resolve().parent


def list_datasets() -> list[str]:
    config = get_config()
    if not config.datasets_dir.exists():
        return []
    return sorted(
        path.name
        for path in config.datasets_dir.iterdir()
        if path.is_file() and not path.name.startswith(".")
    )


def resolve_dataset(name: str) -> Path:
    config = get_config()
    candidate = (config.datasets_dir / name).resolve()
    datasets_dir = config.datasets_dir.resolve()
    if candidate.parent != datasets_dir or not candidate.is_file():
        raise FileNotFoundError(name)
    return candidate


def frame_to_payload(frame: DmdFrame) -> dict[str, object]:
    components = find_lit_components(frame.binary_pixels)
    relationships = find_component_relationships(components)
    candidate_boxes = generate_candidate_boxes(components, relationships)
    return {
        "frame_number": frame.frame_number,
        "header": frame.header,
        "exact_pixels": frame.exact_pixels,
        "binary_pixels": frame.binary_pixels,
        "components": components_to_payload(components),
        "relationship_count": len(relationships),
        "relationships": relationships_to_payload(relationships),
        "candidate_box_count": len(candidate_boxes),
        "candidate_boxes": candidate_boxes_to_payload(candidate_boxes),
    }


def dataset_summary(name: str) -> dict[str, object]:
    path = resolve_dataset(name)
    frames = parse_dump_file(path)
    return {
        "name": name,
        "frame_count": len(frames),
        "width": get_config().dmd_width,
        "height": get_config().dmd_height,
        "first_header": frames[0].header if frames else None,
        "last_header": frames[-1].header if frames else None,
    }


def dataset_frame(name: str, frame_number: int) -> dict[str, object]:
    path = resolve_dataset(name)
    frames = parse_dump_file(path)
    if frame_number < 0 or frame_number >= len(frames):
        raise IndexError(frame_number)
    payload = dataset_summary(name)
    payload["frame"] = frame_to_payload(frames[frame_number])
    return payload


class ViewerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self._send_file(VIEWER_DIR / "index.html")
            elif parsed.path in {"/style.css", "/viewer.js"}:
                self._send_file(VIEWER_DIR / parsed.path.lstrip("/"))
            elif parsed.path == "/api/datasets":
                self._send_json({"datasets": list_datasets()})
            elif parsed.path == "/api/dataset":
                self._handle_dataset(parsed.query)
            elif parsed.path == "/api/frame":
                self._handle_frame(parsed.query)
            else:
                self._send_json({"error": "not found"}, status=404)
        except FileNotFoundError:
            self._send_json({"error": "dataset not found"}, status=404)
        except FrameParseError as exc:
            self._send_json({"error": str(exc)}, status=422)
        except (IndexError, ValueError):
            self._send_json({"error": "invalid frame number"}, status=400)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _handle_dataset(self, query: str) -> None:
        params = parse_qs(query)
        name = unquote(params.get("name", [""])[0])
        self._send_json(dataset_summary(name))

    def _handle_frame(self, query: str) -> None:
        params = parse_qs(query)
        name = unquote(params.get("name", [""])[0])
        frame_number = int(params.get("frame", ["0"])[0])
        self._send_json(dataset_frame(name, frame_number))

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if not path.is_file() or path.parent != VIEWER_DIR:
            self._send_json({"error": "not found"}, status=404)
            return
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), ViewerRequestHandler)
    print(f"Forensic DMD Viewer running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Stage 2 forensic DMD viewer.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
