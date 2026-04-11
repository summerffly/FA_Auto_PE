# File:        Ledger/Collect.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-04-10
# Description: Collect账目实现

from dataclasses import dataclass, field
from typing import List, Optional, Type
from Line import Line, LineType

from Segment import BaseSection, CollectSection, make_section, make_minisection
from Segment.MiniSection import TotalMiniSection
from .Base import BaseLedger, _BaseLedgerParser


# ======================================== #
#    CollectLedger
# ======================================== #

@dataclass
class CollectLedger(BaseLedger):

    total_seg: Optional[TotalMiniSection] = None

    @classmethod
    def _create_parser(cls, lines: List[Line]) -> "_CollectLedgerParser":
        return _CollectLedgerParser(lines, ledger=CollectLedger())

    def _get_segment_type(self) -> Type[BaseSection]:
        return CollectSection
    
    # ----- 数据访问 -------------------- #

    def get_total(self) -> int:
        return sum(seg.sum for seg in self.segments)
    
    @property
    def total(self) -> int:
        return self.total_seg.total

    # ----- 序列化 -------------------- #

    def to_lines(self) -> List[Line]:
        all_lines: List[Line] = []
        all_lines.extend(self.header)
        for seg in self.segments:
            all_lines.extend(seg.to_lines())
        all_lines.extend(self.total_seg.to_lines())
        all_lines.extend(self.tail.to_lines())
        return all_lines

    # ----- 操作 -------------------- #

    def rebuild(self):
        super().rebuild()
        
        total_sum = self.get_total()
        self.total_seg.set_total(total_sum)

    def checksum(self) -> bool:
        if not super().checksum():
            return False
        else:
            return self.total_seg.checksum(self.get_total())
    
    # ----- 验证 -------------------- #

    def validate(self) -> List[str]:
        errors = super().validate()
        
        # 检查 total_seg
        if self.total_seg is None:
            errors.append("缺失 total_seg")
        else:
            if not isinstance(self.total_seg, TotalMiniSection):
                errors.append(f"total_seg 类型错误: {type(self.total_seg).__name__}")
            else:
                total_errors = self.total_seg.validate()
                errors.extend(f"total_seg: {err}" for err in total_errors)
        
        return errors

    # ----- Debug -------------------- #
    
    def dump(self):
        print("=== Ledger Dump ===")
        print(f"class     : {self.__class__.__name__}")
        print(f"header    : {len(self.header)}")
        print(f"segments  : {len(self.segments)}")
        print(f"total_seg : {self.total_seg.name if self.total_seg else 'None'}")
        print(f"tail      : {len(self.tail.to_lines())}")
        print()

        for i, seg in enumerate(self.segments, 1):
            print(f"[Segment {i}] {seg.name}")
            print(f"   class  : {seg.__class__.__name__}")
            print(f"   sum    : {len(seg.sum_lines)}")
            print(f"   body   : {len(seg.body_lines)}")
            print(f"   units  : {len(seg.unit_lines)}")
            print(f"   blanks : {len(seg.blank_lines)}")
            print()

        print(f"[Total] {self.total_seg.name}")
        print(f"   class : {self.total_seg.__class__.__name__}")
        print(f"   lines : {len(self.total_seg.sum_lines)}")
        print()

        print(f"[Tail] {len(self.tail.to_lines())} lines")
        print()

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"header={len(self.header)}, "
            f"segments={len(self.segments)}, "
            f"total_seg={self.total_seg.name}, "
            f"tail={len(self.tail.to_lines())})"
        )


# ======================================== #
#    CollectLedger Parser
# ======================================== #

@dataclass
class _CollectLedgerParser(_BaseLedgerParser):
    def __post_init__(self):
        if self.ledger is None:
            self.ledger = CollectLedger()

    def parse(self) -> CollectLedger:
        """ Collect解析流程 """
        while self.index < len(self.lines):
            line = self.lines[self.index]

            # Collect 支持 TOTAL_TITLE
            if line.type in (LineType.COLLECT_TITLE, LineType.TOTAL_TITLE):
                self._finish_current_segment()
                self._start_new_segment(line)
                continue

            # 处理尾部行
            if line.type in (LineType.TIMESTAMP, LineType.EOF):
                self._finish_current_segment()
                self._parse_tail()
                break

            # 处理普通行
            self._process_normal_line(line)
            self.index += 1

        self._finish_current_segment()
        return self.ledger

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
                print(f"[警告] Collect账目中创建了非CollectSection: {section.__class__.__name__}")
            self.ledger.segments.append(section)
        else:
            print(f"[警告] Collect账目中出现其他分段类型: {self.curr_head.type}")
            pass
        
        # 重置状态
        self.curr_head = None
        self.curr_lines = []
