# File:        Block.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-25
# Description: 

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType


# ======================================== #
#    BaseBlock
# ======================================== #

@dataclass
class BaseBlock(ABC):
    lines: List[Line] = field(default_factory=list)

    def to_lines(self) -> List[Line]:
        out_lines = []
        out_lines.extend(self.lines)
        return out_lines

    # ----- 抽象方法 -------------------- #

    @abstractmethod
    def validate_structure(self) -> List[str]:
        raise NotImplementedError


# ======================================== #
#    TailBlock
# ======================================== #

@dataclass
class TailBlock(BaseBlock):
    def validate_structure(self) -> List[str]:
        errors = []
        timestamp_line_cnt = [ln for ln in self.lines if ln.ltype == LineType.TIMESTAMP]
        eof_line_cnt = [ln for ln in self.lines if ln.ltype == LineType.EOF]
        if len(timestamp_line_cnt) != 1:
            errors.append(f"尾部应该有1个TIMESTAMP行 实际有 {len(timestamp_line_cnt)} 个")
        if len(eof_line_cnt) != 1:
            errors.append(f"尾部应该有1个EOF行 实际有 {len(eof_line_cnt)} 个")
        return errors
    
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
