"""Handpan notation tokens → LilyPond .ly file content."""

from .models import HandpanScale, HandpanSet
from .score_events import BarLine, ScoreEvent

_LY_SUFFIX = "  }\n}\n"


def _split_chunks(events: list[ScoreEvent], bars_per_chunk: int) -> list[list[ScoreEvent]]:
    """イベント列を bars_per_chunk 小節ごとのチャンクに分割する。

    チャンク境界の BarLine は除外する。
    """
    chunks: list[list[ScoreEvent]] = []
    current: list[ScoreEvent] = []
    bar_count = 0

    for event in events:
        if isinstance(event, BarLine):
            bar_count += 1
            if bar_count % bars_per_chunk == 0:
                if current:
                    chunks.append(current)
                current = []
            else:
                current.append(event)
        else:
            current.append(event)

    if current:
        chunks.append(current)

    return chunks


def _ly_preamble(title: str, scale_name: str, key_sig: str) -> str:
    """LilyPond ファイルのヘッダー部分を生成する。"""
    return (
        '\\version "2.24.4"\n\n'
        '\\include "../Handpan.ily"\n'
        f'\\include "../Scales/{scale_name}.ly"\n\n'
        "\\score {\n"
        "  \\header {\n"
        f'    title = "{title}"\n'
        "  }\n"
        "  \\new Staff {\n"
        "    \\clef treble\n"
        f"    \\key {key_sig.replace(' ', ' \\')}\n"
    )


def generate_score_ly(
    events: list[ScoreEvent],
    scale: HandpanScale,
    bars_per_chunk: int = 4,
) -> str:
    """ScoreEvent リストから単スケール用 LilyPond ファイル文字列を生成する。"""
    chunks = _split_chunks(events, bars_per_chunk)
    score_blocks = "\n    ".join(
        f'\\HandpanScore "{" ".join(e.to_token() for e in chunk)}"'
        for chunk in chunks
    )
    return (
        _ly_preamble(scale.name, scale.name, scale.key_signature)
        + f"    \\SetTranslateTable #{scale.ly_name}\n"
        + f"    {score_blocks}\n"
        + _LY_SUFFIX
    )


def generate_set_score_ly(
    part_events: list[list[ScoreEvent]],
    handpan_set: HandpanSet,
    bars_per_chunk: int = 4,
) -> str:
    """ScoreEvent リストから HandpanSet 用 LilyPond ファイル文字列を生成する。"""
    n_parts = len(handpan_set.parts)
    chunks_per_part = [_split_chunks(pe, bars_per_chunk) for pe in part_events]
    n_chunks = max(len(chunks) for chunks in chunks_per_part)

    chunk_blocks: list[str] = []
    for chunk_index in range(n_chunks):
        lines = ["    <<"]
        for part_index, part in enumerate(handpan_set.parts):
            chunk = chunks_per_part[part_index][chunk_index] if chunk_index < len(chunks_per_part[part_index]) else []
            lines.append(f"      \\SetTranslateTable #{part.instrument_name}")
            lines.append(f'      \\absolute {{ \\HandpanScore "{" ".join(e.to_token() for e in chunk)}" }}')
            if part_index < n_parts - 1:
                lines.append("      \\\\")
        lines.append("    >>")
        chunk_blocks.append("\n".join(lines))

    return (
        _ly_preamble(handpan_set.name, handpan_set.name, handpan_set.key_signature)
        + "\n".join(chunk_blocks) + "\n"
        + _LY_SUFFIX
    )
