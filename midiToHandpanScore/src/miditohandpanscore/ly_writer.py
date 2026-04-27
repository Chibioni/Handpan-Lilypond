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
        if not isinstance(event, BarLine) or event.tied:
            current.append(event)
            continue

        bar_count += 1
        if bar_count % bars_per_chunk != 0:
            current.append(event)
            continue

        if current:
            chunks.append(current)
        current = []

    if current:
        chunks.append(current)

    return chunks


def _handpan_score_blocks(events: list[ScoreEvent], bars_per_chunk: int) -> list[str]:
    """events を bars_per_chunk 小節ごとに分割し、\\HandpanScore "..." 文字列のリストを返す。

    Args:
        events: ScoreEvent のリスト。
        bars_per_chunk: 1ブロックあたりの小節数。

    Returns:
        \\HandpanScore "..." 文字列のリスト。
    """
    result: list[str] = []
    for chunk in _split_chunks(events, bars_per_chunk):
        tokens = " ".join(e.to_token() for e in chunk)
        result.append(f'\\HandpanScore "{tokens}"')
    return result


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
    blocks = _handpan_score_blocks(events, bars_per_chunk)
    score_blocks = "\n    ".join(blocks)
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
    blocks_per_part = [_handpan_score_blocks(pe, bars_per_chunk) for pe in part_events]
    n_chunks = len(blocks_per_part[0])
    if not all(len(b) == n_chunks for b in blocks_per_part):
        raise RuntimeError("パート間でチャンク数が一致しない")

    chunk_blocks: list[str] = []
    for chunk_index in range(n_chunks):
        lines = ["    <<"]
        for part_index, part in enumerate(handpan_set.parts):
            if part_index > 0:
                lines.append("      \\\\")
            part_blocks = blocks_per_part[part_index]
            block = part_blocks[chunk_index]
            lines.append(f"      \\SetTranslateTable #{part.instrument_name}")
            lines.append(f"      \\absolute {{ {block} }}")
        lines.append("    >>")
        chunk_blocks.append("\n".join(lines))

    return (
        _ly_preamble(handpan_set.name, handpan_set.name, handpan_set.key_signature)
        + "\n".join(chunk_blocks) + "\n"
        + _LY_SUFFIX
    )
