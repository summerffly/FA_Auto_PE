# File:        Ledger/Life.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-03-30
# Description: Life账本实现

from dataclasses import dataclass, field
from typing import List

from Line import Line, LineType
from Segment import LifeSection, make_section
from .Base import BaseLedger, _BaseLedgerParser


# ======================================== #
#    LifeLedger
# ======================================== #

@dataclass
class LifeLedger(BaseLedger):    
    @classmethod
    def _create_parser(cls, lines: List[Line]) -> "_LifeLedgerParser":
        return _LifeLedgerParser(lines, ledger=LifeLedger())

    def rebuild_ledger(self):
        for seg in self.segments:
            seg.rebuild_summary()


# ======================================== #
#    LifeLedger Parser
# ======================================== #

@dataclass
class _LifeLedgerParser(_BaseLedgerParser):    
    def __post_init__(self):
        if self.ledger is None:
            self.ledger = LifeLedger()

    def _finish_current_segment(self):
        if self.curr_head is None and not self.curr_lines:
            return
        
        if self.curr_head is None:
            pass
        elif self.curr_head.ltype == LineType.LIFE_TITLE:
            # 分段部分
            section = make_section(self.curr_head, self.curr_lines)
            # 验证类型
            if not isinstance(section, LifeSection):
                print(f"[警告] Life账本中创建了非LifeSection: {section.__class__.__name__}")
            self.ledger.segments.append(section)
        else:
            print(f"[警告] Life账本中出现其他分段类型: {self.curr_head.ltype}")
            pass
        
        # 重置状态
        self.curr_head = None
        self.curr_lines = []
