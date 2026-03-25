# File:        Block.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-25
# Description: 

from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType


# ======================================== #
#    BaseBlock
# ======================================== #

@dataclass
class BaseBlock:
    lines: List[Line] = field(default_factory=list)

    def to_lines(self) -> List[Line]:
        out_lines = []
        out_lines.extend(self.lines)
        return out_lines


# ======================================== #
#    TailBlock
# ======================================== #

@dataclass
class TailBlock(BaseBlock):
    @property
    def timestamp_line(self) -> Optional[Line]:
        for ln in self.lines:
            if ln.ltype == LineType.TIMESTAMP:
                return ln
        return None

    @property
    def timestamp(self) -> str:
        ln = self.timestamp_line
        return ln.content.strip() if ln else ""


# ----- Block Factory -------------------- #

def make_tail_block(lines: List[Line]) -> TailBlock:
    return TailBlock(lines=lines)
