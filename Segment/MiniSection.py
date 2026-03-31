# File:        MiniSection.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-30
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
    head_line: Line
    summary_lines: List[Line] = field(default_factory=list)
    _name: str = field(init=False)
    _month_no: Optional[str] = field(init=False)

    def __post_init__(self):
        if self.head_line.type not in {
            LineType.LIFE_TITLE,
            LineType.SUB_TITLE,
            LineType.TOTAL,
        }:
            raise ValueError(f"{Fore.RED}[!]{Style.RESET_ALL} MiniSection.head_line 类型错误")
        
        self._name = ""
        self._month_no = None
        self._extract_name()
        self._extract_month_no()

    def _extract_name(self) -> str:
        if m := RE.LIFE_TITLE.match(self.head_line.raw):
            self._name = "life." + m.group(1)
        if m := RE.SUB_TITLE.match(self.head_line.raw):
            self._name = m.group(1)
        if m := RE.TOTAL.match(self.head_line.raw):
            self._name = "Total"
    
    def _extract_month_no(self) -> Optional[str]:
        if m := RE.LIFE_TITLE.match(self.head_line.raw):
            self._month_no = m.group(1)

    @property
    def name(self) -> str:
        return self._name

    @property
    def month_no(self) -> Optional[str]:
        return self._month_no

    @property
    def lines(self) -> List[Line]:
        return [self.head_line] + self.summary_lines

    # ----- 抽象方法 -------------------- #

    @abstractmethod
    def validate_struct(self) -> List[str]:
        raise NotImplementedError


# ======================================== #
#    LifeMiniSection
# ======================================== #

@dataclass
class LifeMiniSection(BaseMiniSection):
    def validate_struct(self) -> List[str]:
        errors = []
        sum_line_count = sum(1 for ln in self.summary_lines if ln.type == LineType.MONTH_SUM)
        if sum_line_count != 3:
            errors.append(f"包含 {sum_line_count} SummaryLines")
        return errors
    
    def get_line(self, key: str) -> Optional[Line]:
        for ln in self.summary_lines:
            if ln.type == LineType.MONTH_SUM and key in ln.content:
                return ln
        return None

    @property
    def income(self) -> int:
        ln = self.get_line("薪资")
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
        ln = self.get_line("薪资")
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
#    TitleMiniSection
# ======================================== #

@dataclass
class TitleMiniSection(BaseMiniSection):
    def validate_struct(self) -> List[str]:
        errors = []
        sum_line_count = sum(1 for ln in self.summary_lines if ln.type == LineType.TITLE_SUM)
        if sum_line_count != 1:
            errors.append(f"包含 {sum_line_count} SummaryLines")
        return errors

    def get_summary_line(self) -> Optional[Line]:
        for ln in self.summary_lines:
            if ln.type == LineType.TITLE_SUM:
                return ln
        return None

    @property
    def value(self) -> int:
        ln = self.get_summary_line()
        return ln.value if ln else 0
    
    def set_value(self, value: int):
        ln = self.get_summary_line()
        if ln:
            ln.value = value


# ======================================== #
#    TotalMiniSection
# ======================================== #

@dataclass
class TotalMiniSection(BaseMiniSection):
    def validate_struct(self) -> List[str]:
        errors = []
        sum_line_count = sum(1 for ln in self.summary_lines if ln.type == LineType.TOTAL_SUM)
        delimiter_count = sum(1 for ln in self.summary_lines if ln.type == LineType.DELIMITER)
        
        if sum_line_count != 1:
            errors.append(f"包含 {sum_line_count} SummaryLines")
        if delimiter_count != 2:
            errors.append(f"包含 {delimiter_count} 分隔符行")
        
        return errors

    def get_value_line(self) -> Optional[Line]:
        for ln in self.summary_lines:
            if ln.type == LineType.TOTAL_SUM:
                return ln
        return None

    @property
    def value(self) -> int:
        ln = self.get_value_line()
        return ln.value if ln else 0
    
    def set_value(self, value: int):
        ln = self.get_value_line()
        if ln:
            ln.value = value


# ======================================== #
#    MiniSection Factory
# ======================================== #

def make_minisection(headline: Line, lines: List[Line]) -> BaseMiniSection:
    raw = headline.raw.strip()
    type = headline.type
    
    if type == LineType.LIFE_TITLE:
        return LifeMiniSection(head_line=headline, summary_lines=lines)
    elif type == LineType.SUB_TITLE:
        return TitleMiniSection(head_line=headline, summary_lines=lines)
    elif type == LineType.TOTAL:
        return TotalMiniSection(head_line=headline, summary_lines=lines)
    else:
        raise ValueError(f"未知 MiniSection 类型: {raw}")
