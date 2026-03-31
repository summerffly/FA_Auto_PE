# File:        Block.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-30
# Description: Block分段模块

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from Line import Line, LineType


# ======================================== #
#    BaseBlock
# ======================================== #

@dataclass
class BaseBlock(ABC):
    block_lines: List[Line] = field(default_factory=list)

    @property
    def lines(self) -> List[Line]:
        return self.block_lines

    # ----- 抽象方法 -------------------- #

    @abstractmethod
    def validate_struct(self) -> List[str]:
        raise NotImplementedError


# ======================================== #
#    TailBlock
# ======================================== #

@dataclass
class TailBlock(BaseBlock):
    def validate_struct(self) -> List[str]:
        errors = []
        timestamp_line_cnt = [ln for ln in self.block_lines if ln.type == LineType.TIMESTAMP]
        eof_line_cnt = [ln for ln in self.block_lines if ln.type == LineType.EOF]
        if len(timestamp_line_cnt) != 1:
            errors.append(f"包含 {timestamp_line_cnt} Timestamp")
        if len(eof_line_cnt) != 1:
            errors.append(f"包含 {timestamp_line_cnt} EOF")
        return errors
    
    @property
    def timestamp_line(self) -> Optional[Line]:
        for ln in self.block_lines:
            if ln.type == LineType.TIMESTAMP:
                return ln
        return None

    @property
    def timestamp(self) -> str:
        ln = self.timestamp_line
        return ln.content.strip() if ln else ""
    
    def refresh_timestamp(self):
        ln = self.timestamp_line
        if ln:
            ln.content = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ======================================== #
#    Block Factory
# ======================================== #

def make_tail_block(lines: List[Line]) -> TailBlock:
    return TailBlock(block_lines=lines)
