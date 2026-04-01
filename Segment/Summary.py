# File:        Segment/Summary.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-25
# LastEdit:    2026-03-31
# Description: Summary分段模块

from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType


# ======================================== #
#    块一：历史财富汇总
# ======================================== #

@dataclass
class WealthBlock:
    """
    对应MD结构：
    ```
    初始财富 : -122690
    当前财富 : -137580
    ```
    """
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

    def validate(self, segments_total: int) -> bool:
        """ 验证当前财富是否正确 """
        return self.current_wealth == self.calc_current_wealth(segments_total)


# ======================================== #
#    块二：特殊资金流水
# ======================================== #

@dataclass
class SpecialBlock:
    """
    对应MD结构：
    `- 4900` 公寓押金
    `+ 200000` HOME注资
    `- 20000` HOME派息
    `+ 50000` 蚂蚁借呗
    """
    lines: List[Line]

    @property
    def unit_lines(self) -> List[Line]:
        return [ln for ln in self.lines if ln.type == LineType.UNIT]

    def get_total(self) -> int:
        """ 特殊支出总和 """
        return sum(ln.value for ln in self.unit_lines)


# ======================================== #
#    块三：资产分配明细
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
        aggr_lines = self._get_primary_lines()
        if aggr_lines:
            aggr_lines[0].value = value

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

    def rebuild_allocation(self):
        """ 重建主分配行的值 """
        ln = self.primary_line
        if ln:
            ln.value = self.calc_primary_value()

    def validate(self, current_wealth: int, special_total: int) -> bool:
        """ 验证可支配财富是否正确 """
        expected = self.calc_disposable_wealth(current_wealth, special_total)
        return (
            self.disposable_wealth == expected and
            self.disposable_wealth == self.get_allocation_total()
        )


# ======================================== #
#    SummarySection
# ======================================== #

@dataclass
class SummarySection:
    title_line: Optional[Line] = None
    lines: List[Line] = field(default_factory=list)

    wealth_block: Optional[WealthBlock] = None
    special_block: Optional[SpecialBlock] = None
    allocation_block: Optional[AllocationBlock] = None

    @property
    def name(self) -> str:
        if self.title_line is None:
            return ""
        raw = self.title_line.raw.strip()
        if raw.startswith("## "):
            return raw[3:].strip()
        return raw

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
        return self.special_block.get_total() if self.special_block else 0

    @property
    def disposable_wealth(self) -> int:
        """ 可支配财富 """
        return self.allocation_block.disposable_wealth if self.allocation_block else 0

    # ----- 重建 -------------------- #

    def rebuild(self, segments_total: int):
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
            self.allocation_block.rebuild_allocation()

    # ----- 验证 -------------------- #

    def validate(self, segments_total: int) -> bool:
        """ 验证所有计算值 """
        if self.wealth_block:
            if not self.wealth_block.validate(segments_total):
                return False
        if self.allocation_block:
            if not self.allocation_block.validate(self.current_wealth, self.special_total):
                return False
        return True

    # ----- 序列化 -------------------- #

    def to_lines(self) -> List[Line]:
        out = []
        if self.title_line:
            out.append(self.title_line)
        out.extend(self.lines)
        return out

    def _parse_sub_blocks(self) -> None:
        """
        按 DELIMITER 边界切分 self.lines，
        依次填入 wealth_block / special_block / allocation_block
        """
        segments: List[List[Line]] = []
        is_delimited: List[bool] = []

        buf: List[Line] = []
        inside_delim = False

        for ln in self.lines:
            if ln.type == LineType.DELIMITER:
                if not inside_delim:
                    if buf:
                        segments.append(buf)
                        is_delimited.append(False)
                        buf = []
                    buf = [ln]
                    inside_delim = True
                else:
                    buf.append(ln)
                    segments.append(buf)
                    is_delimited.append(True)
                    buf = []
                    inside_delim = False
            else:
                buf.append(ln)

        if buf:
            segments.append(buf)
            is_delimited.append(False)

        delim_idx = 0
        for seg, delimited in zip(segments, is_delimited):
            if delimited:
                if delim_idx == 0:
                    self.wealth_block = WealthBlock(lines=seg)
                elif delim_idx == 1:
                    self.allocation_block = AllocationBlock(lines=seg)
                delim_idx += 1
            else:
                non_blank = [l for l in seg if l.type != LineType.BLANK]
                if non_blank:
                    self.special_block = SpecialBlock(lines=seg)


# ======================================== #
#    Summary Factory
# ======================================== #

def make_summary(title_line: Line, lines: List[Line]) -> SummarySection:
    summary = SummarySection(title_line=title_line, lines=lines)
    summary._parse_sub_blocks()
    return summary
