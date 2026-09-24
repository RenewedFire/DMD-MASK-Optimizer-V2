from __future__ import annotations


def filter_evidence_summaries(
    summaries: tuple[object, ...] | list[object],
    dump_id: int | None = None,
    text: str = "",
) -> tuple[object, ...]:
    text_filter = text.strip().lower()
    filtered = []
    for summary in summaries:
        if dump_id is not None and summary.dump_id != dump_id:
            continue
        row_text = (
            f"{summary.filename} "
            f"{summary.descriptor} "
            f"frame {summary.source_frame_index + 1} "
            f"index {summary.source_frame_index} "
            f"{summary.region_count} boxes"
        ).lower()
        if text_filter and text_filter not in row_text:
            continue
        filtered.append(summary)
    return tuple(filtered)
