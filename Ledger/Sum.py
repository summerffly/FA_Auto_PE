# File:        Ledger/Sum.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-31
# Description: 汇总账本对象

from dataclasses import dataclass, field
from typing import List, Optional
from colorama import Fore, Style

from Line import Line, LineType
from Segment import (
    TitleMiniSection, LifeMiniSection, make_minisection,
    SummarySection, make_summary,
    TailBlock, make_tail_block
)
from .Mixin import LedgerMixin


# ======================================== #
#    SumLedger
# ======================================== #

@dataclass
class SumLedger(LedgerMixin):
    header: List[Line] = field(default_factory=list)
    title_segments: List[TitleMiniSection] = field(default_factory=list)
    life_segments: List[LifeMiniSection] = field(default_factory=list)
    summary: Optional[SummarySection] = None
    tail: Optional[TailBlock] = None

    # ----- 解析方法 -------------------- #

    @classmethod
    def parse_lines(cls, lines: List[Line]) -> "SumLedger":
        parser = _SumLedgerParser(lines)
        return parser.parse()

    # ----- 数据访问方法 -------------------- #

    def get_segment_names(self) -> List[str]:
        """ 获取所有分段名称 """
        title_names = [seg.name for seg in self.title_segments]
        life_names = [seg.name for seg in self.life_segments]
        return title_names + life_names

    def get_title_segment(self, name: str) -> Optional[TitleMiniSection]:
        """ 获取 Title 分段 """
        for seg in self.title_segments:
            if seg.name == name:
                return seg
        return None

    def get_life_segment(self, month_no: str) -> Optional[LifeMiniSection]:
        """ 获取 Life 分段 """
        for seg in self.life_segments:
            if seg.month_no == month_no:
                return seg
        return None

    def mod_title_segment_value(self, name: str, new_value: int):
        """ 修改指定 Title 分段数值 """
        seg = self.get_title_segment(name)
        if seg is not None:
            seg.set_value(new_value)

    def mod_life_segment_value(self, month_no: str, income_value: int, expense_value: int, balance_value: int):
        """ 修改指定月份 Life 分段数值 """
        seg = self.get_life_segment(month_no)
        if seg is not None:
            seg.set_income(income_value)
            seg.set_expense(expense_value)
            seg.set_balance(balance_value)

    # ----- 验证方法 -------------------- #

    def validate(self) -> bool:
        """ 验证所有区块 """
        return True

    # ----- 序列化方法 -------------------- #

    def to_lines(self) -> List[Line]:
        all_lines: List[Line] = []
        all_lines.extend(self.header)
        for seg in self.title_segments:
            all_lines.extend(seg.lines)
        for seg in self.life_segments:
            all_lines.extend(seg.lines)
        if self.summary:
            all_lines.extend(self.summary.to_lines())
        if self.tail:
            all_lines.extend(self.tail.lines)
        return all_lines

    # ----- Debug -------------------- #

    def validate_struct(self) -> List[str]:
        """ 验证账本结构，返回错误信息列表 """
        errors = []

        # 检查重复的分段名称
        names = self.get_segment_names()
        if len(names) != len(set(names)):
            errors.append("存在重复的分段名称")

        # 检查 title_segments
        for sec in self.title_segments:
            sec_errors = sec.validate_struct()
            errors.extend([f"title_section '{sec.name}': {err}" for err in sec_errors])

        # 检查 life_segments
        for sec in self.life_segments:
            sec_errors = sec.validate_struct()
            errors.extend([f"life_section '{sec.name}': {err}" for err in sec_errors])

        # 检查 tail
        if self.tail:
            tail_errors = self.tail.validate_struct()
            errors.extend([f"tail: {err}" for err in tail_errors])

        return errors

    def dump(self):
        """ 打印账本结构信息 """
        print("=== SumLedger Dump ===")

        print("\n[HEAD]")
        for ln in self.header:
            print(f"  {ln.raw}")

        print("\n[TITLE SEGMENTS]")
        for idx, blk in enumerate(self.title_segments, 1):
            print(f"  Segment {idx}: {blk.name} ({blk.__class__.__name__})")
            for ln in blk.lines:
                print(f"    {ln.raw}")

        print("\n[LIFE SEGMENTS]")
        for idx, blk in enumerate(self.life_segments, 1):
            print(f"  Segment {idx}: {blk.name} ({blk.__class__.__name__})")
            for ln in blk.lines:
                print(f"    {ln.raw}")

        print("\n[SUMMARY]")
        if self.summary:
            for ln in self.summary.to_lines():
                print(f"  {ln.raw}")
        else:
            print("  None")

        print("\n[TAIL]")
        if self.tail:
            for ln in self.tail.lines:
                print(f"  {ln.raw}")
        else:
            print("  None")

    def __repr__(self):
        return (
            f"SumLedger("
            f"header={len(self.header)}, "
            f"title_segments={len(self.title_segments)}, "
            f"life_segments={len(self.life_segments)}, "
            f"summary={self.summary.name if self.summary else 'None'}, "
            f"tail={len(self.tail.lines) if self.tail else 0})"
        )


# ======================================== #
#    SumLedger Parser
# ======================================== #

@dataclass
class _SumLedgerParser:
    lines: List[Line]
    ledger: SumLedger = field(default_factory=SumLedger)
    index: int = 0
    curr_head: Optional[Line] = None
    curr_lines: List[Line] = field(default_factory=list)

    def parse(self) -> SumLedger:
        while self.index < len(self.lines):
            line = self.lines[self.index]

            # 处理新分段
            if line.type in (LineType.LIFE_TITLE, LineType.SUB_TITLE, LineType.SUMMARY):
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

    def _start_new_segment(self, head_line: Line):
        self.curr_head = head_line
        self.curr_lines = []
        self.index += 1

    def _finish_current_segment(self):
        if self.curr_head is None and not self.curr_lines:
            return

        if self.curr_head is None:
            pass
        elif self.curr_head.type == LineType.SUMMARY:
            self.ledger.summary = make_summary(self.curr_head, self.curr_lines)
        else:
            minisection = make_minisection(self.curr_head, self.curr_lines)
            if isinstance(minisection, LifeMiniSection):
                self.ledger.life_segments.append(minisection)
            else:
                self.ledger.title_segments.append(minisection)

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
