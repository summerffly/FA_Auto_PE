# File:        Ledger/Collect.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-04-03
# Description: Collect账目实现

from dataclasses import dataclass
from typing import List, Optional
from Line import Line, LineType

from Segment import CollectSection, make_section, make_minisection
from .Base import BaseLedger, _BaseLedgerParser


# ======================================== #
#    CollectLedger
# ======================================== #

@dataclass
class CollectLedger(BaseLedger):    
    @classmethod
    def _create_parser(cls, lines: List[Line]) -> "_CollectLedgerParser":
        return _CollectLedgerParser(lines, ledger=CollectLedger())

    @property
    def total(self) -> Optional[int]:
        if self.total_seg is None:
            return None
        else:
            return self.total_seg.total

    def get_total(self) -> int:
        total_sum = 0
        for seg in self.segments:
            total_sum += seg.sum
        return total_sum

    def rebuild(self):
        for seg in self.segments:
            seg.rebuild()
        
        if self.total_seg:
            total_sum = self.get_total()
            self.total_seg.set_total(total_sum)

    def checksum(self) -> bool:
        if not all(seg.checksum() for seg in self.segments):
            return False

        if self.total_seg is None:
            return False
        else:
            return self.total_seg.checksum(self.get_total())

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"header={len(self.header)}, "
            f"segments={len(self.segments)}, "
            f"total_seg={self.total_seg.name if self.total_seg else 'None'}, "
            f"tail={len(self.tail.to_lines()) if self.tail else 0})"
        )


# ======================================== #
#    CollectLedger Parser
# ======================================== #

@dataclass
class _CollectLedgerParser(_BaseLedgerParser):    
    def __post_init__(self):
        if self.ledger is None:
            self.ledger = CollectLedger()

    def _finish_current_segment(self):
        if self.curr_head is None and not self.curr_lines:
            return
        
        if self.curr_head is None:
            pass
        elif self.curr_head.type == LineType.TOTAL_TITLE:
            # 总计部分
            self.ledger.total_seg = make_minisection(self.curr_head, self.curr_lines)
        elif self.curr_head.type == LineType.COLLECT_TITLE:
            # 分段部分
            section = make_section(self.curr_head, self.curr_lines)
            # 验证类型
            if not isinstance(section, CollectSection):
                print(f"[警告] Title账目中创建了非CollectSection: {section.__class__.__name__}")
            self.ledger.segments.append(section)
        else:
            print(f"[警告] Title账目中出现其他分段类型: {self.curr_head.type}")
            pass
        
        # 重置状态
        self.curr_head = None
        self.curr_lines = []
