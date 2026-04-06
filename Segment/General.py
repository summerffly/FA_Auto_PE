# File:        Segment/General.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-25
# LastEdit:    2026-04-06
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

    def get_primary_line(self, keyword: str) -> Optional[Line]:
        for ln in self.lines:
            if ln.type == LineType.PRIMARY and keyword in ln.content:
                return ln
        return None

    @property
    def initial_wealth(self) -> int:
        ln = self.get_primary_line("初始财富")
        return ln.value if ln else 0

    @property
    def current_wealth(self) -> int:
        ln = self.get_primary_line("当前财富")
        return ln.value if ln else 0

    def set_current_wealth(self, value: int):
        ln = self.get_primary_line("当前财富")
        if ln:
            ln.value = value

    def checksum(self, segments_total: int) -> bool:
        return self.current_wealth == self.initial_wealth + segments_total
    
    def validate(self) -> List[str]:
        errors = []
        if not self.get_primary_line("初始财富"):
            errors.append("缺失 初始财富 行")
        if not self.get_primary_line("当前财富"):
            errors.append("缺失 当前财富 行")
        return errors


# ======================================== #
#    ExtraBlock
# ======================================== #

@dataclass
class ExtraBlock:

    lines: List[Line]

    @property
    def unit_lines(self) -> List[Line]:
        return [ln for ln in self.lines if ln.type == LineType.UNIT]

    def get_extra_sum(self) -> int:
        return sum(ln.value for ln in self.unit_lines)
    
    def validate(self) -> List[str]:
        errors = []
        if not self.unit_lines:
            errors.append("缺失 Unit 行")
        return errors


# ======================================== #
#    ComboBlock
# ======================================== #

@dataclass
class ComboBlock:

    lines: List[Line]

    @property
    def primary_lines(self) -> List[Line]:
        return [ln for ln in self.lines if ln.type == LineType.PRIMARY]

    @property
    def combo_lines(self) -> List[Line]:
        return self.primary_lines[1:]

    @property
    def disposable_wealth(self) -> int:
        ln = self.primary_lines if self.primary_lines else None
        return ln[0].value if ln else 0

    def set_disposable_wealth(self, value: int):
        lines = self.primary_lines if self.primary_lines else None
        if lines:
            lines[0].value = value

    @property
    def principal_line(self) -> Optional[Line]:
        """ 主分配行（第一行）"""
        lines = self.combo_lines
        return lines[0] if lines else None

    @property
    def secondary_lines(self) -> List[Line]:
        """ 次要分配行（第二行起）"""
        return self.combo_lines[1:]

    def get_combo_sum(self) -> int:
        return sum(ln.value for ln in self.combo_lines)

    def get_secondary_sum(self) -> int:
        return sum(ln.value for ln in self.secondary_lines)

    def rebuild(self):
        ln = self.principal_line
        if ln:
            ln.value = self.disposable_wealth - self.get_secondary_sum()

    def checksum(self, current_wealth: int, extra_sum: int) -> bool:
        expected_value = current_wealth + extra_sum
        return (
            self.disposable_wealth == expected_value and
            self.disposable_wealth == self.get_combo_sum()
        )
    
    def validate(self) -> List[str]:
        errors = []
        if not self.primary_lines:
            errors.append("缺失主分配行")
        elif len(self.primary_lines) < 2:
            errors.append(f"包含 {len(self.primary_lines)} 主分配行")
        return errors


# ======================================== #
#    GeneralSection
# ======================================== #

@dataclass
class GeneralSection:
    title_line: Optional[Line] = None
    wealth_block: Optional[WealthBlock] = None
    extra_block: Optional[ExtraBlock] = None
    combo_block: Optional[ComboBlock] = None
    _raw_lines: List[Line] = field(default_factory=list)

    def __post_init__(self):        
        self._name = ""
        self._parse_title()
        self._parse_sub_blocks()

    def _parse_title(self) -> str:
        if not self.title_line:
            return
        if m := RE.GENERAL_TITLE.match(self.title_line.raw):
            self._name = m.group(1)

    def _parse_sub_blocks(self) -> None:
        lines = self._raw_lines
        i, n = 0, len(lines)

        # ----- Seg1 -------------------- #
        block_lines_1: list[Line] = None
        while i < n and lines[i].type != LineType.DELIMITER:
            i += 1
        if i < n:
            start = i
            i += 1
            while i < n and lines[i].type != LineType.DELIMITER:
                i += 1
            if i < n:
                i += 1
                block_lines_1 = lines[start : i]
        self._assign_wealth_blocks(block_lines_1)

        # ----- Seg2 -------------------- #
        block_lines_2: list[Line] = None
        seg2_start = i
        while i < n and lines[i].type != LineType.DELIMITER:
            i += 1
        block_lines_2 = lines[seg2_start : i]
        self._assign_extra_block(block_lines_2)

        # ----- Seg3 -------------------- #
        block_lines_3: list[Line] = None
        seg3_start = i
        if seg3_start < n:
            block_lines_3 = lines[seg3_start:]
        else:
            block_lines_3 = []
        self._assign_combo_blocks(block_lines_3)

    def _assign_wealth_blocks(self, block_lines: list[Line]) -> None:
        if block_lines is not None:
            self.wealth_block = WealthBlock(lines=block_lines)

    def _assign_extra_block(self, block_lines: list[Line]) -> None:
        if any(ln.type != LineType.BLANK for ln in block_lines):
            self.extra_block = ExtraBlock(lines=block_lines)

    def _assign_combo_blocks(self, block_lines: list[Line]) -> None:
        if block_lines is not None:
            self.combo_block = ComboBlock(lines=block_lines)

    @property
    def name(self) -> str:
        return self._name

    # ----- 数据访问 -------------------- #

    @property
    def initial_wealth(self) -> int:
        return self.wealth_block.initial_wealth if self.wealth_block else 0

    @property
    def current_wealth(self) -> int:
        return self.wealth_block.current_wealth if self.wealth_block else 0

    @property
    def extra_sum(self) -> int:
        return self.extra_block.get_extra_sum() if self.extra_block else 0

    @property
    def disposable_wealth(self) -> int:
        return self.combo_block.disposable_wealth if self.combo_block else 0
    
    @property
    def principal_line(self) -> int:
        return self.combo_block.principal_line if self.combo_block else 0
    
    @property
    def secondary_lines(self) -> List[Line]:
        return self.combo_block.secondary_lines if self.combo_block else []

    # ----- 验证方法 -------------------- #

    def validate(self) -> List[str]:
        errors = []
        if not self.title_line:
            errors.extend([f"缺失标题行"])

        if not self.wealth_block:
            errors.extend([f"缺失 wealth_block"])
        else:
            wealth_errors = self.wealth_block.validate()
            errors.extend([f"wealth_block: {err}" for err in wealth_errors])

        if not self.extra_block:
            errors.extend([f"缺失 extra_block"])
        else:
            extra_errors = self.extra_block.validate()
            errors.extend([f"extra_block: {err}" for err in extra_errors])

        if not self.combo_block:
            errors.extend([f"缺失 combo_block"])
        else:
            combo_errors = self.combo_block.validate()
            errors.extend([f"combo_block: {err}" for err in combo_errors])

        return errors

    # ----- 重建 -------------------- #

    def rebuild(self, segments_total: int):
        if self.wealth_block:
            new_current = self.wealth_block.initial_wealth + segments_total
            self.wealth_block.set_current_wealth(new_current)

        if self.combo_block:
            new_disposable = self.current_wealth + self.extra_sum
            self.combo_block.set_disposable_wealth(new_disposable)
            self.combo_block.rebuild()

    # ----- 验证 -------------------- #

    def checksum(self, segments_total: int) -> bool:
        """ 验证所有计算值 """
        if self.wealth_block:
            if not self.wealth_block.checksum(segments_total):
                return False
        if self.combo_block:
            if not self.combo_block.checksum(self.current_wealth, self.extra_sum):
                return False
        return True

    # ----- 序列化 -------------------- #

    def to_lines(self) -> List[Line]:
        raw_lines: List[Line] = []
        raw_lines.extend([self.title_line])
        if self.wealth_block:
            raw_lines.extend(self.wealth_block.lines)
        if self.extra_block:
            raw_lines.extend(self.extra_block.lines)
        if self.combo_block:
            raw_lines.extend(self.combo_block.lines)
        return raw_lines


# ======================================== #
#    General Factory
# ======================================== #

def make_general(title_line: Line, lines: List[Line]) -> GeneralSection:
    return GeneralSection(title_line=title_line, _raw_lines=lines)
