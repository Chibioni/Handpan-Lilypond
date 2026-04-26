"""Handpan notation tokens → LilyPond .ly file content."""

from .models import HandpanScale, HandpanSet
from .score_events import BarLine, ScoreEvent

_LY_SUFFIX = "  }\n}\n"


def _split_chunks(events: list[ScoreEvent], bars_per_chunk: int) -> list[list[ScoreEvent]]:
    """ScoreEvent リストを bars_per_chunk 小節ごとのチャンクに分割する。

    チャンク境界となる BarLine はどちらのチャンクにも含まれない。
    チャンク内の BarLine（境界以外）はそのまま残る。

    Args:
        events: 分割対象の ScoreEvent リスト。
        bars_per_chunk: 1チャンクあたりの小節数。

    Returns:
        チャンクのリスト。各チャンクは ScoreEvent のリスト。
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
    """LilyPond ファイルのヘッダー部分を生成する。

    Args:
        title: 楽譜タイトル（\\header の title に使用）。
        scale_name: スケール定義ファイル名（拡張子なし、\\include パスに使用）。
        key_sig: 調号文字列（例: "d minor"）。スペース区切りで "tonic mode" の形式。

    Returns:
        \\version から \\key 行までの LilyPond ヘッダー文字列。
    """
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
    """ScoreEvent リストから単スケール用 LilyPond ファイル文字列を生成する。

    Args:
        events: events_to_tokens の出力。ScoreEvent のリスト。
        scale: 使用するハンドパンスケール。
        bars_per_chunk: 1行（1 \\HandpanScore ブロック）あたりの小節数。

    Returns:
        LilyPond ファイルの内容文字列（.ly ファイルとしてそのまま書き出せる）。
    """
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
    """ScoreEvent リストから HandpanSet 用 LilyPond ファイル文字列を生成する。

    各チャンクを << ... >> ブロックで囲み、パートを \\\\ で区切る。

    Args:
        part_events: events_to_tokens_per_part の出力。パートごとの ScoreEvent リスト。
        handpan_set: 使用するハンドパンセット。
        bars_per_chunk: 1チャンクあたりの小節数。

    Returns:
        LilyPond ファイルの内容文字列（.ly ファイルとしてそのまま書き出せる）。
    """
    n_parts = len(handpan_set.parts)
    chunks_per_part = [_split_chunks(pe, bars_per_chunk) for pe in part_events]
    n_chunks = max(len(chunks) for chunks in chunks_per_part)

    chunk_blocks: list[str] = []
    for chunk_index in range(n_chunks):
        lines = ["    <<"]
        for part_index, part in enumerate(handpan_set.parts):
            part_chunks = chunks_per_part[part_index]
            chunk = part_chunks[chunk_index] if chunk_index < len(part_chunks) else []
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
