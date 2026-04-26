"""Score event types: building blocks of a handpan score."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .quantize import DurationStr

Token: TypeAlias = str


class Articulation(Enum):
    """ノートのアーティキュレーション記号。"""
    NORMAL = ""
    ACCENT = "!"
    GHOST  = "."


class Technique(Enum):
    """ハンドパン奏法のプレフィックス記号。"""
    NORMAL = ""
    APEX   = "O"  # Apex リング打奏
    SLAP   = "S"  # スラップ


class ScoreEvent(ABC):
    """ハンドパン楽譜を構成するイベントの基底クラス。

    すべてのサブクラスは to_token() を実装し、
    ハンドパン記法トークン文字列を返す。
    """

    @abstractmethod
    def to_token(self) -> Token: ...


@dataclass
class ToneFieldNote(ScoreEvent):
    """1つのハンドパン音符を表すイベント。

    Attributes:
        part_index: 所属パートのインデックス（HandpanSet.parts の順）。
        number: トーンフィールド番号（0 = Ding、1–9 = トーンフィールド）。
        harmonic: ハーモニクス番号（0 = 基音、1 = ^1、2 = ^2）。
        articulation: アーティキュレーション（NORMAL / ACCENT / GHOST）。
        technique: 奏法プレフィックス（NORMAL / APEX / SLAP）。
        duration: 音価文字列（例: "4", "8.", "4.."）。
    """
    part_index: int
    number: int
    harmonic: int
    articulation: Articulation
    technique: Technique
    duration: DurationStr

    def to_token(self, duration: DurationStr | None = None) -> Token:
        """ハンドパン記法トークン文字列を生成する。

        Args:
            duration: 音価を上書きする場合に指定する。省略時は self.duration を使用。

        Returns:
            ハンドパン記法トークン（例: "1-4", "O2!-8", "3^1-4."）。
        """
        dur = duration if duration is not None else self.duration
        token = self.technique.value + str(self.number)
        if self.harmonic:
            token += f"^{self.harmonic}"
        return token + self.articulation.value + f"-{dur}"


@dataclass
class Chord(ScoreEvent):
    """同一 tick に発音される1つ以上の ToneFieldNote をまとめた和音イベント。

    単音の場合も Chord として扱い、to_token() で単音形式と和音形式を自動判別する。

    Attributes:
        notes: 構成音の ToneFieldNote リスト。
        duration: 全音符に適用する共通音価文字列。
    """
    notes: list[ToneFieldNote]
    duration: DurationStr

    def to_token(self) -> Token:
        """ハンドパン記法トークン文字列を生成する。

        Returns:
            単音なら "1-4" 形式、複数音なら "< 1-4 3-4 >" 形式。
        """
        tokens = [n.to_token(self.duration) for n in self.notes]
        if len(tokens) == 1:
            return tokens[0]
        return "< " + " ".join(tokens) + " >"


@dataclass
class Rest(ScoreEvent):
    """休符イベント。

    Attributes:
        duration: 音価文字列（例: "4", "8."）。
        hidden: True の場合は非表示休符（H）、False の場合は通常休符（R）。
    """
    duration: DurationStr
    hidden: bool = False

    def to_token(self) -> Token:
        """ハンドパン記法トークン文字列を生成する。

        Returns:
            通常休符なら "R-4"、非表示休符なら "H-4" 形式。
        """
        prefix = "H" if self.hidden else "R"
        return f"{prefix}-{self.duration}"


@dataclass
class BarLine(ScoreEvent):
    """小節線イベント。"""

    def to_token(self) -> Token:
        """ハンドパン記法の小節線トークン "|" を返す。

        Returns:
            常に "|"。
        """
        return "|"
