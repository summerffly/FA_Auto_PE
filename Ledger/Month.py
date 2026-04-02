# File:        Ledger/Month.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-03-30
# Description: Month账目实现

from dataclasses import dataclass
from typing import List
from Line import Line, LineType

from Segment import MonthSection, make_section
from .Base import BaseLedger, _BaseLedgerParser


# ======================================== #
#    MonthLedger
# ======================================== #

@dataclass
class MonthLedger(BaseLedger):    
    @classmethod
    def _create_parser(cls, lines: List[Line]) -> "_MonthLedgerParser":
        return _MonthLedgerParser(lines, ledger=MonthLedger())

    def recalculate(self):
        for seg in self.segments:
            seg.recalculate_sum()

    def get_month_total(self, month: str) -> int:
        """ 获取月度总计 """
        for seg in self.segments:
            if seg.name == month:
                return seg.get_sum()
        return 0

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"header={len(self.header)}, "
            f"segments={len(self.segments)}, "
            f"tail={len(self.tail.to_lines()) if self.tail else 0})"
        )


# ======================================== #
#    MonthLedger Parser
# ======================================== #

@dataclass
class _MonthLedgerParser(_BaseLedgerParser):    
    def __post_init__(self):
        if self.ledger is None:
            self.ledger = MonthLedger()

    def _finish_current_segment(self):
        if self.curr_head is None and not self.curr_lines:
            return
        
        if self.curr_head is None:
            pass
        elif self.curr_head.type == LineType.MONTH_TITLE:
            # 分段部分
            section = make_section(self.curr_head, self.curr_lines)
            # 验证类型
            if not isinstance(section, MonthSection):
                print(f"[警告] Month账目中创建了非MonthSection: {section.__class__.__name__}")
            self.ledger.segments.append(section)
        else:
            print(f"[警告] Month账目中出现其他分段类型: {self.curr_head.type}")
            pass

        # 重置状态
        self.curr_head = None
        self.curr_lines = []
