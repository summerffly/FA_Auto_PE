# File:        Segment/MiniSection.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-04-01
# Description: MiniSection分段模块

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from colorama import Fore, Style

from Line import Line, LineType
from Line import LineRegex as RE


# ======================================== #
#    BaseMiniSection
# ======================================== #

@dataclass
class BaseMiniSection(ABC):

    # ----- 属性 -------------------- #

    title_line: Line
    sum_lines: List[Line] = field(default_factory=list)
    _name: str = field(init=False)
    _month_no: Optional[str] = field(init=False)

    def __post_init__(self):        
        self._name = ""
        self._month_no = None
        self._parse_title()

    def _parse_title(self) -> str:
        if m := RE.LIFE_TITLE.match(self.title_line.raw):
            self._name = m.group(1) + m.group(2)
            self._month_no = m.group(2)
        if m := RE.COLLECT_TITLE.match(self.title_line.raw):
            self._name = m.group(1)
        if m := RE.TOTAL_TITLE.match(self.title_line.raw):
            self._name = m.group(1)

    @property
    def name(self) -> str:
        return self._name

    @property
    def month_no(self) -> Optional[str]:
        return self._month_no

    def to_lines(self) -> List[Line]:
        return [self.title_line] + self.sum_lines

    # ----- 抽象方法 -------------------- #

    @abstractmethod
    def validate(self) -> List[str]:
        raise NotImplementedError


# ======================================== #
#    LifeMiniSection
# ======================================== #

@dataclass
class LifeMiniSection(BaseMiniSection):
    def validate(self) -> List[str]:
        errors = []
        sum_line_count = sum(1 for ln in self.sum_lines if ln.type == LineType.MONTH_SUM)
        if sum_line_count != 3:
            errors.append(f"包含 {sum_line_count} SummaryLines")
        return errors
    
    def get_line(self, key: str) -> Optional[Line]:
        for ln in self.sum_lines:
            if ln.type == LineType.MONTH_SUM and key in ln.content:
                return ln
        return None

    @property
    def income(self) -> int:
        ln = self.get_line("收入")
        return ln.value if ln else 0

    @property
    def expense(self) -> int:
        ln = self.get_line("支出")
        return ln.value if ln else 0

    @property
    def balance(self) -> int:
        ln = self.get_line("结余")
        return ln.value if ln else 0
    
    def set_income(self, value: int):
        ln = self.get_line("收入")
        if ln:
            ln.value = value

    def set_expense(self, value: int):
        ln = self.get_line("支出")
        if ln:
            ln.value = value

    def set_balance(self, value: int):
        ln = self.get_line("结余")
        if ln:
            ln.value = value


# ======================================== #
#    CollectMiniSection
# ======================================== #

@dataclass
class CollectMiniSection(BaseMiniSection):
    def validate(self) -> List[str]:
        errors = []
        sum_line_count = sum(1 for ln in self.sum_lines if ln.type == LineType.SECTION_SUM)
        if sum_line_count != 1:
            errors.append(f"包含 {sum_line_count} SummaryLines")
        return errors

    def get_sum_line(self) -> Optional[Line]:
        for ln in self.sum_lines:
            if ln.type == LineType.SECTION_SUM:
                return ln
        return None

    def get_sum(self) -> int:
        ln = self.get_sum_line()
        return ln.value if ln else 0
    
    def set_sum(self, value: int):
        ln = self.get_sum_line()
        if ln:
            ln.value = value


# ======================================== #
#    TotalMiniSection
# ======================================== #

@dataclass
class TotalMiniSection(BaseMiniSection):
    def validate(self) -> List[str]:
        errors = []
        sum_line_count = sum(1 for ln in self.sum_lines if ln.type == LineType.TOTAL)
        delimiter_count = sum(1 for ln in self.sum_lines if ln.type == LineType.DELIMITER)
        
        if sum_line_count != 1:
            errors.append(f"包含 {sum_line_count} SummaryLines")
        if delimiter_count != 2:
            errors.append(f"包含 {delimiter_count} 分隔符行")
        
        return errors

    def get_total_line(self) -> Optional[Line]:
        for ln in self.sum_lines:
            if ln.type == LineType.TOTAL:
                return ln
        return None

    def get_total(self) -> int:
        ln = self.get_total_line()
        return ln.value if ln else 0
    
    def set_total(self, value: int):
        ln = self.get_total_line()
        if ln:
            ln.value = value


# ======================================== #
#    MiniSection Factory
# ======================================== #

def make_minisection(titleline: Line, lines: List[Line]) -> BaseMiniSection:
    raw = titleline.raw.strip()
    ltype = titleline.type
    
    if ltype == LineType.LIFE_TITLE:
        return LifeMiniSection(title_line=titleline, sum_lines=lines)
    elif ltype == LineType.COLLECT_TITLE:
        return CollectMiniSection(title_line=titleline, sum_lines=lines)
    elif ltype == LineType.TOTAL_TITLE:
        return TotalMiniSection(title_line=titleline, sum_lines=lines)
    else:
        raise ValueError(f"未知 MiniSection 类型: {raw}")
