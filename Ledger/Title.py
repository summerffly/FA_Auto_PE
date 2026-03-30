# File:        Ledger/Title.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-03-30
# Description: Title账本实现

from dataclasses import dataclass
from typing import List, Optional
from Line import Line, LineType

from Segment import TitleSection, make_section, make_minisection
from .Base import BaseLedger, _BaseLedgerParser


# ======================================== #
#    TitleLedger
# ======================================== #

@dataclass
class TitleLedger(BaseLedger):    
    @classmethod
    def _create_parser(cls, lines: List[Line]) -> "_TitleLedgerParser":
        return _TitleLedgerParser(lines, ledger=TitleLedger())

    def rebuild_ledger(self):
        # 重建每个分段
        for seg in self.segments:
            seg.rebuild_summary()
        
        # 重建总计
        if self.total:
            self.rebuild_total()
    

    def get_total_value(self) -> Optional[int]:
        """获取总计值"""
        if self.total is None:
            return None
        else:
            return self.total.value

    def rebuild_total(self):
        """ 重建总计 """
        if self.total is None:
            return

        if self.total:
            total_sum = self.get_total_value()
            self.total.set_value(total_sum)

    def validate_total(self) -> bool:
        """验证总计是否正确"""
        if self.total is None:
            return True
        
        total_value = self.get_total_value()
        if total_value is None:
            return False
        
        all_sections_sum = self.get_all_segments_sum()
        return total_value == all_sections_sum


# ======================================== #
#    TitleLedger Parser
# ======================================== #

@dataclass
class _TitleLedgerParser(_BaseLedgerParser):    
    def __post_init__(self):
        if self.ledger is None:
            self.ledger = TitleLedger()

    def _finish_current_segment(self):
        if self.curr_head is None and not self.curr_lines:
            return
        
        if self.curr_head is None:
            pass
        elif self.curr_head.ltype == LineType.TOTAL:
            # 总计部分
            self.ledger.total = make_minisection(self.curr_head, self.curr_lines)
        elif self.curr_head.ltype == LineType.SUB_TAG:
            # 分段部分
            section = make_section(self.curr_head, self.curr_lines)
            # 验证类型
            if not isinstance(section, TitleSection):
                print(f"[警告] Title账本中创建了非TitleSection: {section.__class__.__name__}")
            self.ledger.segments.append(section)
        else:
            print(f"[警告] Title账本中出现其他分段类型: {self.curr_head.ltype}")
            pass
        
        # 重置状态
        self.curr_head = None
        self.curr_lines = []
