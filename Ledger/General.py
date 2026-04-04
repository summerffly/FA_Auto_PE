# File:        Ledger/Sum.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-04-04
# Description: 汇总账目对象

from dataclasses import dataclass, field
from typing import List, Optional
from colorama import Fore, Style

from Line import Line, LineType
from Segment import (
    CollectMiniSection, LifeMiniSection, make_minisection,
    GeneralSection, make_general,
    TailBlock, make_tail_block
)
from .Mixin import LedgerMixin


# ======================================== #
#    GeneralLedger
# ======================================== #

@dataclass
class GeneralLedger(LedgerMixin):
    header: List[Line] = field(default_factory=list)
    life_segment: Optional[LifeMiniSection] = None
    collect_segments: List[CollectMiniSection] = field(default_factory=list)
    general: Optional[GeneralSection] = None
    tail: Optional[TailBlock] = None

    # ----- 解析方法 -------------------- #

    @classmethod
    def parse_lines(cls, lines: List[Line]) -> "GeneralLedger":
        parser = _GeneralLedgerParser(lines)
        return parser.parse()

    # ----- 数据访问方法 -------------------- #

    @property
    def seg_names(self) -> List[str]:
        return [seg.name for seg in self.collect_segments]

    def get_life_segment(self) -> Optional[LifeMiniSection]:
        return self.life_segment

    def get_collect_segment(self, name: str) -> Optional[CollectMiniSection]:
        for seg in self.collect_segments:
            if seg.name == name:
                return seg
        return None

    def mod_collect_segment(self, name: str, new_value: int):
        seg = self.get_collect_segment(name)
        if seg is not None:
            seg.set_sum(new_value)
        else:
            raise ValueError(f"无法找到 Collect 分段 '{name}'")

    def mod_life_segment(self, income_value: int, expense_value: int, balance_value: int):
        seg = self.get_life_segment()
        if seg is not None:
            seg.set_income(income_value)
            seg.set_expense(expense_value)
            seg.set_balance(balance_value)
        else:
            raise ValueError(f"无法找到 Life 分段")

    def get_segments_total(self) -> int:
        life_total = self.life_segment.balance if self.life_segment else 0
        collect_total = sum(seg.sum for seg in self.collect_segments)
        return collect_total + life_total

    def rebuild(self):
        if self.general:
            segments_total = self.get_segments_total()
            self.general.rebuild(segments_total)

    # ----- 验证方法 -------------------- #

    def checksum(self) -> bool:
        """ 验证所有区块 """
        if self.general is None:
            return True
        segments_total = self.get_segments_total()
        return self.general.checksum(segments_total)
    
    # ----- 序列化 -------------------- #

    def to_lines(self) -> List[Line]:
        all_lines: List[Line] = []
        all_lines.extend(self.header)
        if self.life_segment:
            all_lines.extend(self.life_segment.to_lines())
        for seg in self.collect_segments:
            all_lines.extend(seg.to_lines())
        if self.general:
            all_lines.extend(self.general.to_lines())
        if self.tail:
            all_lines.extend(self.tail.to_lines())
        return all_lines

    # ----- Debug -------------------- #

    def validate(self) -> List[str]:
        errors = []

        if len(self.seg_names) != len(set(self.seg_names)):
            errors.append("存在重复的分段名称")

        if self.life_segment:
            seg_errors = self.life_segment.validate()
            errors.extend([f"life_segment '{self.life_segment.name}': {err}" for err in seg_errors])

        for seg in self.collect_segments:
            seg_errors = seg.validate()
            errors.extend([f"collect_segment '{seg.name}': {err}" for err in seg_errors])

        if self.general:
            general_errors = self.general.validate()
            errors.extend([f"general: {err}" for err in general_errors])

        if not self.tail:
            errors.append("缺失 tail")
        else:
            tail_errors = self.tail.validate()
            errors.extend([f"tail: {err}" for err in tail_errors])

        return errors
    
    def dump(self):
        print("=== GeneralLedger Dump ===")
        print(f"Type             : {self.__class__.__name__}")
        print(f"header           : {len(self.header)}")
        print(f"life_segment     : {self.life_segment.name if self.life_segment else 'None'}")
        print(f"collect_segments : {len(self.collect_segments)}")
        print(f"general          : {self.general.name if self.general else 'None'}")
        print(f"tail             : {len(self.tail.to_lines()) if self.tail else 0}")
        print()

        if self.life_segment:
            print(f"[LifeSegment] {self.life_segment.name}")
            print(f"   class     : {self.life_segment.__class__.__name__}")
            print(f"   summaries : {len(self.life_segment.sum_lines)}")
            print(f"   income    : {'+' if self.life_segment.income >= 0 else ''}{self.life_segment.income}")
            print(f"   expense   : {'+' if self.life_segment.expense >= 0 else ''}{self.life_segment.expense}")
            print(f"   balance   : {'+' if self.life_segment.balance >= 0 else ''}{self.life_segment.balance}")
            print()

        for i, seg in enumerate(self.collect_segments, 1):
            print(f"[CollectSegment {i}] {seg.name}")
            print(f"   class     : {seg.__class__.__name__}")
            print(f"   summaries : {len(seg.sum_lines)}")
            print(f"   value     : {'+' if seg.sum >= 0 else ''}{seg.sum}")
            print()

        if self.general:
            print(f"[General] {self.general.name}")
            print(f"   class     : {self.general.__class__.__name__}")
            print(f"   wealth    : {len(self.general.wealth_block.lines)}")
            print(f"   extra     : {len(self.general.extra_block.lines)}")
            print(f"   allocation: {len(self.general.allocation_block.lines)}")
            print()

    def __repr__(self):
        return (
            f"GeneralLedger("
            f"header={len(self.header)}, "
            f"life_segment={self.life_segment.name if self.life_segment else 'None'}, "
            f"collect_segments={len(self.collect_segments)}, "
            f"general={self.general.name if self.general else 'None'}, "
            f"tail={len(self.tail.to_lines()) if self.tail else 0})"
        )


# ======================================== #
#    GeneralLedger Parser
# ======================================== #

@dataclass
class _GeneralLedgerParser:
    lines: List[Line]
    ledger: GeneralLedger = field(default_factory=GeneralLedger)
    index: int = 0
    curr_head: Optional[Line] = None
    curr_lines: List[Line] = field(default_factory=list)

    def parse(self) -> GeneralLedger:
        while self.index < len(self.lines):
            line = self.lines[self.index]

            # 处理新分段
            if line.type in (LineType.LIFE_TITLE, LineType.COLLECT_TITLE, LineType.GENERAL_TITLE):
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

        return self.ledger

    def _process_normal_line(self, line: Line):
        if self.curr_head is None:
            self.ledger.header.append(line)
        else:
            self.curr_lines.append(line)

    def _start_new_segment(self, title_line: Line):
        self.curr_head = title_line
        self.curr_lines = []
        self.index += 1

    def _finish_current_segment(self):
        if self.curr_head is None and not self.curr_lines:
            return

        if self.curr_head is None:
            pass
        elif self.curr_head.type == LineType.GENERAL_TITLE:
            self.ledger.general = make_general(self.curr_head, self.curr_lines)
        else:
            minisection = make_minisection(self.curr_head, self.curr_lines)
            if isinstance(minisection, LifeMiniSection):
                self.ledger.life_segment = minisection
            else:
                self.ledger.collect_segments.append(minisection)

        # 重置状态
        self.curr_head = None
        self.curr_lines = []

    def _parse_tail(self):
        tail_lines = []
        while self.index < len(self.lines):
            tail_lines.append(self.lines[self.index])
            self.index += 1

        if tail_lines:
            self.ledger.tail = make_tail_block(tail_lines)
