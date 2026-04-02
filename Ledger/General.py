# File:        Ledger/Sum.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-04-02
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
    collect_segments: List[CollectMiniSection] = field(default_factory=list)
    life_segments: List[LifeMiniSection] = field(default_factory=list)
    general: Optional[GeneralSection] = None
    tail: Optional[TailBlock] = None

    # ----- 解析方法 -------------------- #

    @classmethod
    def parse_lines(cls, lines: List[Line]) -> "GeneralLedger":
        parser = _GeneralLedgerParser(lines)
        return parser.parse()

    # ----- 数据访问方法 -------------------- #

    def get_segment_names(self) -> List[str]:
        """ 获取所有分段名称 """
        collect_names = [seg.name for seg in self.collect_segments]
        life_names = [seg.name for seg in self.life_segments]
        return collect_names + life_names

    def get_collect_segment(self, name: str) -> Optional[CollectMiniSection]:
        """ 获取 Collect 分段 """
        for seg in self.collect_segments:
            if seg.name == name:
                return seg
        return None

    def get_life_segment(self, month_no: str) -> Optional[LifeMiniSection]:
        """ 获取 Life 分段 """
        for seg in self.life_segments:
            if seg.month_no == month_no:
                return seg
        return None

    def mod_collect_segment_value(self, name: str, new_value: int):
        """ 修改指定 Collect 分段数值 """
        seg = self.get_collect_segment(name)
        if seg is not None:
            seg.set_sum(new_value)

    def mod_life_segment_value(self, month_no: str, income_value: int, expense_value: int, balance_value: int):
        """ 修改指定月份 Life 分段数值 """
        seg = self.get_life_segment(month_no)
        if seg is not None:
            seg.set_income(income_value)
            seg.set_expense(expense_value)
            seg.set_balance(balance_value)

    def get_segments_total(self) -> int:
        """ 所有分段的总和 """
        collect_total = sum(seg.get_sum() for seg in self.collect_segments)
        life_total = sum(seg.balance for seg in self.life_segments)
        return collect_total + life_total

    def recalculate(self):
        """ 重建 Ledger 的所有计算值 """
        if self.general:
            segments_total = self.get_segments_total()
            self.general.recalculate(segments_total)

    def checkcum_ledger(self) -> bool:
        """ 验证 General 的所有计算值 """
        if self.general is None:
            return True
        segments_total = self.get_segments_total()
        return self.general.checksum(segments_total)

    # ----- 验证方法 -------------------- #

    def checksum(self) -> bool:
        """ 验证所有区块 """
        return True

    # ----- 序列化方法 -------------------- #

    def to_lines(self) -> List[Line]:
        all_lines: List[Line] = []
        all_lines.extend(self.header)
        for seg in self.collect_segments:
            all_lines.extend(seg.to_lines())
        for seg in self.life_segments:
            all_lines.extend(seg.to_lines())
        if self.general:
            all_lines.extend(self.general.to_lines())
        if self.tail:
            all_lines.extend(self.tail.to_lines())
        return all_lines

    # ----- Debug -------------------- #

    def validate(self) -> List[str]:
        """ 验证账目结构，返回错误信息列表 """
        errors = []

        # 检查重复的分段名称
        names = self.get_segment_names()
        if len(names) != len(set(names)):
            errors.append("存在重复的分段名称")

        # 检查 collect_segments
        for sec in self.collect_segments:
            sec_errors = sec.validate()
            errors.extend([f"collect_segment '{sec.name}': {err}" for err in sec_errors])

        # 检查 life_segments
        for sec in self.life_segments:
            sec_errors = sec.validate()
            errors.extend([f"life_segment '{sec.name}': {err}" for err in sec_errors])

        # 检查 tail
        if self.tail:
            tail_errors = self.tail.validate()
            errors.extend([f"tail: {err}" for err in tail_errors])

        return errors
    
    def dump(self):
        print("=== GeneralLedger Dump ===")
        print(f"Type             : {self.__class__.__name__}")
        print(f"header           : {len(self.header)}")
        print(f"collect_segments : {len(self.collect_segments)}")
        print(f"life_segments    : {len(self.life_segments)}")
        print(f"general          : {self.general.name if self.general else 'None'}")
        print(f"tail             : {len(self.tail.to_lines()) if self.tail else 0}")
        print()

        for i, seg in enumerate(self.collect_segments, 1):
            print(f"[CollectSegment {i}] {seg.name}")
            print(f"   class     : {seg.__class__.__name__}")
            print(f"   summaries : {len(seg.sum_lines)}")
            print(f"   value     : {'+' if seg.get_sum() >= 0 else ''}{seg.get_sum()}")
            print()

        for i, seg in enumerate(self.life_segments, 1):
            print(f"[LifeSegment {i}] {seg.name}")
            print(f"   class     : {seg.__class__.__name__}")
            print(f"   summaries : {len(seg.sum_lines)}")
            print(f"   income    : {'+' if seg.income >= 0 else ''}{seg.income}")
            print(f"   expense   : {'+' if seg.expense >= 0 else ''}{seg.expense}")
            print(f"   balance   : {'+' if seg.balance >= 0 else ''}{seg.balance}")
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
            f"collect_segments={len(self.collect_segments)}, "
            f"life_segments={len(self.life_segments)}, "
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
                self.ledger.life_segments.append(minisection)
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
