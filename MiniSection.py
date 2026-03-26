# File:        MiniSection.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-26
# Description: 

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType
from Line import LineRegex as RE


# ======================================== #
#    BaseMiniSection
# ======================================== #

@dataclass
class BaseMiniSection(ABC):
    head_line: Line
    summary_lines: List[Line] = field(default_factory=list)

    @property
    def name(self) -> str:
        m = RE.MONTH_TITLE.match(self.head_line.raw)
        if m:
            return m.group(1) + m.group(2)
        m = RE.SUB_TITLE.match(self.head_line.raw)
        if m:
            return m.group(1)
        m = RE.TOTAL.match(self.head_line.raw)
        if m:
            return "Total"

    @property
    def lines(self) -> List[Line]:
        return [self.head_line] + self.summary_lines

    # ----- 抽象方法 -------------------- #

    @abstractmethod
    def validate_struct(self) -> List[str]:
        raise NotImplementedError


# ======================================== #
#    MonthMiniSection
# ======================================== #

@dataclass
class MonthMiniSection(BaseMiniSection):
    def validate_struct(self) -> List[str]:
        errors = []
        sum_line_count = sum(1 for ln in self.summary_lines if ln.ltype == LineType.MONTH_SUM)
        if sum_line_count != 3:
            errors.append(f"包含 {sum_line_count} SummaryLines")
        return errors
    
    def find_line(self, key: str) -> Optional[Line]:
        for ln in self.summary_lines:
            if ln.ltype == LineType.MONTH_SUM and key in ln.content:
                return ln
        return None

    @property
    def income(self) -> int:
        ln = self.find_line("薪资")
        return ln.value if ln else 0

    @property
    def expense(self) -> int:
        ln = self.find_line("支出")
        return ln.value if ln else 0

    @property
    def balance(self) -> int:
        ln = self.find_line("结余")
        return ln.value if ln else 0
    
    def set_income(self, value: int):
        ln = self.find_line("薪资")
        if ln:
            ln.value = value

    def set_expense(self, value: int):
        ln = self.find_line("支出")
        if ln:
            ln.value = value

    def set_balance(self, value: int):
        ln = self.find_line("结余")
        if ln:
            ln.value = value


# ======================================== #
#    TitleMiniSection
# ======================================== #

@dataclass
class TitleMiniSection(BaseMiniSection):
    def validate_struct(self) -> List[str]:
        errors = []
        sum_line_count = sum(1 for ln in self.summary_lines if ln.ltype == LineType.TITLE_SUM)
        if sum_line_count != 1:
            errors.append(f"包含 {sum_line_count} SummaryLines")
        return errors

    def get_summary_line(self) -> Optional[Line]:
        for ln in self.summary_lines:
            if ln.ltype == LineType.TITLE_SUM:
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
        sum_line_count = sum(1 for ln in self.summary_lines if ln.ltype == LineType.TOTAL_SUM)
        delimiter_count = sum(1 for ln in self.summary_lines if ln.ltype == LineType.DELIMITER)
        
        if sum_line_count != 1:
            errors.append(f"包含 {sum_line_count} SummaryLines")
        if delimiter_count != 2:
            errors.append(f"包含 {delimiter_count} 分隔符行")
        
        return errors

    def get_value_line(self) -> Optional[Line]:
        for ln in self.summary_lines:
            if ln.ltype == LineType.TOTAL_SUM:
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


# ----- MiniSection Factory -------------------- #

def make_minisection(headline: Line, lines: List[Line]) -> BaseMiniSection:
    raw = headline.raw.strip()
    ltype = headline.ltype
    
    if ltype == LineType.MONTH_TITLE:
        # MonthMiniSection
        return MonthMiniSection(head_line=headline, summary_lines=lines)
    elif ltype == LineType.SUB_TITLE:
         # TitleMiniSection
        return TitleMiniSection(head_line=headline, summary_lines=lines)
    elif ltype == LineType.TOTAL:
        # TotalMiniSection
        return TotalMiniSection(head_line=headline, summary_lines=lines)
    else:
        raise ValueError(f"未知 MiniSection 类型: {raw}")
