"""Handpan notation tokens → LilyPond .ly file content."""

from typing import TypeAlias

from .models import HandpanScale, HandpanSet

Token: TypeAlias = str

_LY_SUFFIX = "  }\n}\n"


def _split_chunks(tokens: list[Token], bars_per_chunk: int) -> list[list[Token]]:
    """トークン列を bars_per_chunk 小節ごとのチャンクに分割する。

    チャンク先頭・末尾の | は除外する。
    """
    chunks: list[list[Token]] = []
    current: list[Token] = []
    bar_count = 0

    for token in tokens:
        if token == "|":
            bar_count += 1
            if bar_count % bars_per_chunk == 0:
                if current:
                    chunks.append(current)
                current = []
            else:
                current.append(token)
        else:
            current.append(token)

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
    tokens: list[Token],
    scale: HandpanScale,
    bars_per_chunk: int = 4,
) -> str:
    """ハンドパン記法トークン列から単スケール用 LilyPond ファイル文字列を生成する。"""
    chunks = _split_chunks(tokens, bars_per_chunk)
    score_blocks = "\n    ".join(f'\\HandpanScore "{" ".join(chunk)}"' for chunk in chunks)
    return (
        _ly_preamble(scale.name, scale.name, scale.key_signature)
        + f"    \\SetTranslateTable #{scale.ly_name}\n"
        + f"    {score_blocks}\n"
        + _LY_SUFFIX
    )


def generate_set_score_ly(
    part_tokens: list[list[Token]],
    handpan_set: HandpanSet,
    bars_per_chunk: int = 4,
) -> str:
    """ハンドパン記法トークン列から HandpanSet 用 LilyPond ファイル文字列を生成する。"""
    n_parts = len(handpan_set.parts)
    chunks_per_part = [_split_chunks(pt, bars_per_chunk) for pt in part_tokens]
    n_chunks = max(len(chunks) for chunks in chunks_per_part)

    chunk_blocks: list[str] = []
    for chunk_index in range(n_chunks):
        lines = ["    <<"]
        for part_index, part in enumerate(handpan_set.parts):
            chunk_tokens = chunks_per_part[part_index][chunk_index] if chunk_index < len(chunks_per_part[part_index]) else []
            lines.append(f"      \\SetTranslateTable #{part.instrument_name}")
            lines.append(f'      \\absolute {{ \\HandpanScore "{" ".join(chunk_tokens)}" }}')
            if part_index < n_parts - 1:
                lines.append("      \\\\")
        lines.append("    >>")
        chunk_blocks.append("\n".join(lines))

    return (
        _ly_preamble(handpan_set.name, handpan_set.name, handpan_set.key_signature)
        + "\n".join(chunk_blocks) + "\n"
        + _LY_SUFFIX
    )
