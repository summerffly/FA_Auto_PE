# File:        Segment/General.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-25
# LastEdit:    2026-04-01
# Description: General分段模块

from dataclasses import dataclass, field
from typing import List, Optional

from Line import Line, LineType
from Line import LineRegex as RE


# ======================================== #
#    WealthBlock
# ======================================== #

@dataclass
class WealthBlock:
    lines: List[Line]

    def _get_line(self, keyword: str) -> Optional[Line]:
        for ln in self.lines:
            if ln.type == LineType.PRIMARY and keyword in ln.content:
                return ln
        return None

    @property
    def initial_wealth(self) -> int:
        """ 初始财富（固定不变）"""
        ln = self._get_line("初始财富")
        return ln.value if ln else 0

    @property
    def current_wealth(self) -> int:
        """ 当前财富 """
        ln = self._get_line("当前财富")
        return ln.value if ln else 0

    def set_current_wealth(self, value: int):
        """ 更新当前财富 """
        ln = self._get_line("当前财富")
        if ln:
            ln.value = value

    def calc_current_wealth(self, segments_total: int) -> int:
        """ 根据初始财富和segments总和计算当前财富 """
        return self.initial_wealth + segments_total

    def checksum(self, segments_total: int) -> bool:
        """ 验证当前财富是否正确 """
        return self.current_wealth == self.calc_current_wealth(segments_total)


# ======================================== #
#    ExtraBlock
# ======================================== #

@dataclass
class ExtraBlock:
    lines: List[Line]

    @property
    def unit_lines(self) -> List[Line]:
        return [ln for ln in self.lines if ln.type == LineType.UNIT]

    def get_total(self) -> int:
        """ 额外支出总和 """
        return sum(ln.value for ln in self.unit_lines)


# ======================================== #
#    AllocationBlock
# ======================================== #

@dataclass
class AllocationBlock:
    lines: List[Line]

    def _get_primary_lines(self) -> List[Line]:
        return [ln for ln in self.lines if ln.type == LineType.PRIMARY]

    def _get_line(self, keyword: str) -> Optional[Line]:
        for ln in self.lines:
            if ln.type == LineType.PRIMARY and keyword in ln.content:
                return ln
        return None

    @property
    def disposable_wealth(self) -> int:
        """ 可支配财富 """
        ln = self._get_primary_lines()
        return ln[0].value if ln else 0

    def set_disposable_wealth(self, value: int):
        """ 更新可支配财富 """
        lines = self._get_primary_lines()
        if lines:
            lines[0].value = value

    @property
    def primary_line(self) -> Optional[Line]:
        """ 主分配行（阿里-余额宝，第一行）"""
        lines = self.allocation_lines
        return lines[0] if lines else None

    @property
    def secondary_lines(self) -> List[Line]:
        """ 次要分配行（固定不变，第二行起）"""
        return self.allocation_lines[1:]

    @property
    def allocation_lines(self) -> List[Line]:
        """ 资产分布各行（可支配财富以外）"""
        return self._get_primary_lines()[1:]

    def get_secondary_total(self) -> int:
        """ 固定分配总和（除主分配行以外）"""
        return sum(ln.value for ln in self.secondary_lines)

    def get_allocation_total(self) -> int:
        """ 资产分布总和 """
        return sum(ln.value for ln in self.allocation_lines)

    def calc_disposable_wealth(self, current_wealth: int, special_total: int) -> int:
        """ 根据当前财富和特殊支出计算可支配财富 """
        return current_wealth + special_total

    def calc_primary_value(self) -> int:
        """ 计算主分配行的值（可支配财富扣除固定分配后的剩余）"""
        return self.disposable_wealth - self.get_secondary_total()

    def recalculate(self):
        """ 重建主分配行的值 """
        ln = self.primary_line
        if ln:
            ln.value = self.calc_primary_value()

    def checksum(self, current_wealth: int, special_total: int) -> bool:
        """ 验证可支配财富是否正确 """
        expected = self.calc_disposable_wealth(current_wealth, special_total)
        return (
            self.disposable_wealth == expected and
            self.disposable_wealth == self.get_allocation_total()
        )


# ======================================== #
#    GeneralSection
# ======================================== #

@dataclass
class GeneralSection:
    title_line: Optional[Line] = None
    lines: List[Line] = field(default_factory=list)

    wealth_block: Optional[WealthBlock] = None
    extra_block: Optional[ExtraBlock] = None
    allocation_block: Optional[AllocationBlock] = None

    def __post_init__(self):        
        self._name = ""
        self._parse_title()

    def _parse_title(self) -> str:
        if m := RE.GENERAL_TITLE.match(self.title_line.raw):
            self._name = m.group(1)

    @property
    def name(self) -> str:
        return self._name

    # ----- 数据访问 -------------------- #

    @property
    def initial_wealth(self) -> int:
        """ 初始财富 """
        return self.wealth_block.initial_wealth if self.wealth_block else 0

    @property
    def current_wealth(self) -> int:
        """ 当前财富 """
        return self.wealth_block.current_wealth if self.wealth_block else 0

    @property
    def special_total(self) -> int:
        """ 特殊支出总和 """
        return self.extra_block.get_total() if self.extra_block else 0

    @property
    def disposable_wealth(self) -> int:
        """ 可支配财富 """
        return self.allocation_block.disposable_wealth if self.allocation_block else 0

    # ----- 重建 -------------------- #

    def recalculate(self, segments_total: int):
        """ 根据segments总和重建所有计算值 """
        if self.wealth_block:
            new_current = self.wealth_block.calc_current_wealth(segments_total)
            self.wealth_block.set_current_wealth(new_current)

        if self.allocation_block:
            new_disposable = self.allocation_block.calc_disposable_wealth(
                self.current_wealth,
                self.special_total
            )
            self.allocation_block.set_disposable_wealth(new_disposable)
            self.allocation_block.recalculate()

    # ----- 验证 -------------------- #

    def checksum(self, segments_total: int) -> bool:
        """ 验证所有计算值 """
        if self.wealth_block:
            if not self.wealth_block.checksum(segments_total):
                return False
        if self.allocation_block:
            if not self.allocation_block.checksum(self.current_wealth, self.special_total):
                return False
        return True

    # ----- 序列化 -------------------- #

    def _parse_sub_blocks(self) -> None:
        lines = self.lines
        i, n = 0, len(lines)

        # ---------- seg1：找第一个 [DELIM...DELIM] ----------
        block_lines_1: list[Line] = None
        while i < n and lines[i].type != LineType.DELIMITER:
            i += 1
        if i < n:                          # 找到开头 DELIMITER
            start = i
            i += 1
            while i < n and lines[i].type != LineType.DELIMITER:
                i += 1
            if i < n:                      # 找到结尾 DELIMITER
                block_lines_1 = lines[start : i + 1]
                i += 1
        self._assign_wealth_blocks(block_lines_1)

        # ---------- seg2：到下一个 DELIMITER 之前 ----------
        seg2_start = i
        while i < n and lines[i].type != LineType.DELIMITER:
            i += 1
        block_lines_2 = lines[seg2_start : i]
        self._assign_extra_block(block_lines_2)

        # ---------- seg3：剩余的 [DELIM...DELIM] ----------
        block_lines_3: list[Line] = None
        if i < n:                          # 当前位置是开头 DELIMITER
            start = i
            i += 1
            while i < n and lines[i].type != LineType.DELIMITER:
                i += 1
            if i < n:                      # 找到结尾 DELIMITER
                block_lines_3 = lines[start : i + 1]
        self._assign_allocation_blocks(block_lines_3)


    def _assign_wealth_blocks(self, block_lines: list[Line]) -> None:
        if block_lines is not None:
            self.wealth_block = WealthBlock(lines=block_lines)
    

    def _assign_extra_block(self, block_lines: list[Line]) -> None:
        if any(ln.type != LineType.BLANK for ln in block_lines):
            self.extra_block = ExtraBlock(lines=block_lines)


    def _assign_allocation_blocks(self, block_lines: list[Line]) -> None:
        if block_lines is not None:
            self.allocation_block = AllocationBlock(lines=block_lines)


    def to_lines(self) -> List[Line]:
        out = []
        if self.title_line:
            out.append(self.title_line)
        out.extend(self.lines)
        return out


# ======================================== #
#    General Factory
# ======================================== #

def make_general(title_line: Line, lines: List[Line]) -> GeneralSection:
    general = GeneralSection(title_line=title_line, lines=lines)
    general._parse_sub_blocks()
    return general
