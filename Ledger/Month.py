# File:        Ledger/Month.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-04-06
# Description: Month账目实现

from dataclasses import dataclass
from typing import List
from Line import Line, LineType

from Segment import MonthSection, make_section
from Segment.Block import TailBlock
from .Base import BaseLedger, _BaseLedgerParser


# ======================================== #
#    MonthLedger
# ======================================== #

@dataclass
class MonthLedger(BaseLedger):
    @classmethod
    def _create_parser(cls, lines: List[Line]) -> "_MonthLedgerParser":
        return _MonthLedgerParser(lines, ledger=MonthLedger())

    def get_month_segment(self, month_no: str) -> MonthSection:
        for seg in self.segments:
            if seg.month_no == month_no:
                return seg
        raise ValueError(f"无法找到 Month 分段 '{month_no}'")

    def get_month_sum(self, month_no: str) -> int:
        seg = self.get_month_segment(month_no)
        return seg.sum

    def rebuild(self):
        for seg in self.segments:
            seg.rebuild()

    def validate(self) -> List[str]:
        errors = []
        if len(self.seg_names) != len(set(self.seg_names)):
            errors.append(f"存在重复Segments")

        for seg in self.segments:
            if not isinstance(seg, MonthSection):
                errors.append(f"segment '{seg.name}' 类型错误: {type(seg).__name__}")
                continue
            else:
                seg_errors = seg.validate()
                errors.extend([f"segment '{seg.name}': {err}" for err in seg_errors])
        
        if not self.tail:
            errors.append(f"缺失 tail")
        else:
            if not isinstance(self.tail, TailBlock):
                errors.append(f"tail 类型错误: {type(self.tail).__name__}")
            else:
                tail_errors = self.tail.validate()
                errors.extend([f"tail: {err}" for err in tail_errors])
        
        return errors

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
