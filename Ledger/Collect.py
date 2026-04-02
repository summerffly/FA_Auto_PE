# File:        Ledger/Collect.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-04-01
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

    def recalculate(self):
        # 重建每个分段
        for seg in self.segments:
            seg.recalculate_sum()
        
        # 重建总计
        if self.total:
            self.recalculate_total()
    

    def get_total_value(self) -> Optional[int]:
        """获取总计值"""
        if self.total is None:
            return None
        else:
            return self.total.get_total()

    def recalculate_total(self):
        """ 重建总计 """
        if self.total is None:
            return

        total_sum = self.get_all_segments_sum()
        self.total.set_total(total_sum)

    def checksum_total(self) -> bool:
        """验证总计是否正确"""
        if self.total is None:
            return True
        
        total_value = self.get_total_value()
        if total_value is None:
            return False
        
        all_sections_sum = self.get_all_segments_sum()
        return total_value == all_sections_sum

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"header={len(self.header)}, "
            f"segments={len(self.segments)}, "
            f"total={self.total.name if self.total else 'None'}, "
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
            self.ledger.total = make_minisection(self.curr_head, self.curr_lines)
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
