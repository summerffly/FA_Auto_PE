# File:        Segment/Section.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-22
# LastEdit:    2026-04-06
# Description: Section分段模块

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from colorama import Fore, Style

from Line import Line, LineType
from Line import LineRegex as RE


# ======================================== #
#    BaseSection
# ======================================== #

@dataclass
class BaseSection(ABC):

    # ----- 属性 -------------------- #

    title_line: Line
    sum_lines: List[Line] = field(init=False, default_factory=list)
    body_lines: List[Line] = field(init=False, default_factory=list)
    _raw_lines: List[Line] = field(default_factory=list)
    _name: str = field(init=False)
    _month_no: Optional[str] = field(init=False)

    def __post_init__(self):
        self._name = ""
        self._month_no = None
        self._parse_title()
        self._parse_lines()

    def _parse_title(self):
        if m := RE.LIFE_TITLE.match(self.title_line.raw):
            self._name = m.group(1) + m.group(2)
            self._month_no = m.group(2)
        elif m := RE.MONTH_TITLE.match(self.title_line.raw):
            self._name = m.group(1) + m.group(2)
            self._month_no = m.group(2)
        elif m := RE.COLLECT_TITLE.match(self.title_line.raw):
            self._name = m.group(1)

    def _parse_lines(self):
        for line in self._raw_lines:
            if self.is_sum_line(line):
                self.sum_lines.append(line)
            else:
                self.body_lines.append(line)

    @property
    def name(self) -> str:
        return self._name

    @property
    def month_no(self) -> Optional[str]:
        return self._month_no

    @property
    def unit_lines(self) -> List[Line]:
        return [ln for ln in self.body_lines if ln.type == LineType.UNIT]

    @property
    def blank_lines(self) -> List[Line]:
        return [ln for ln in self.body_lines if ln.type == LineType.BLANK]
    
    # ----- 序列化 -------------------- #

    def to_lines(self) -> List[Line]:
        raw_lines: List[Line] = []
        raw_lines.extend([self.title_line])
        raw_lines.extend(self.sum_lines)
        raw_lines.extend(self.body_lines)
        return raw_lines

    # ----- 抽象方法 -------------------- #

    @abstractmethod
    def is_sum_line(self, line: Line) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def sum(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def rebuild(self):
        raise NotImplementedError

    @abstractmethod
    def checksum(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def validate(self) -> List[str]:
        raise NotImplementedError


# ======================================== #
#    LifeSection
# ======================================== #

@dataclass
class LifeSection(BaseSection):

    def is_sum_line(self, line: Line) -> bool:
        return line.type == LineType.MONTH_SUM

    @property
    def sum(self) -> int:
        return self.balance

    def rebuild(self):
        expected_income = self.income
        expected_expense = sum(ln.value for ln in self.unit_lines)
        expected_balance = expected_income + expected_expense

        expense_line = self.get_sum_line("支出")
        if not expense_line:
            raise ValueError(f"LifeSection '{self.name}' 缺失支出行")
        else:
            expense_line.value = expected_expense

        balance_line = self.get_sum_line("结余")
        if not balance_line:
            raise ValueError(f"LifeSection '{self.name}' 缺失结余行")
        else:
            balance_line.value = expected_balance

    def checksum(self) -> bool:
        expected_income = self.income
        expected_expense = sum(ln.value for ln in self.unit_lines)
        expected_balance = expected_income + expected_expense

        return (
            self.expense == expected_expense and
            self.balance == expected_balance
        )

    def get_sum_line(self, keyword: str) -> Optional[Line]:
        for ln in self.sum_lines:
            if keyword in ln.content:
                return ln
        return None
    
    @property
    def income(self) -> int:
        income_line = self.get_sum_line("收入")
        if not income_line:
            raise ValueError(f"LifeSection '{self.name}' 缺失收入行")
        else:
            return income_line.value
    
    @property
    def expense(self) -> int:
        expense_line = self.get_sum_line("支出")
        if not expense_line:
            raise ValueError(f"LifeSection '{self.name}' 缺失支出行")
        else:
            return expense_line.value
    
    @property
    def balance(self) -> int:
        balance_line = self.get_sum_line("结余")
        if not balance_line:
            raise ValueError(f"LifeSection '{self.name}' 缺失结余行")
        else:
            return balance_line.value

    def validate(self) -> List[str]:
        errors = []
        if len(self.sum_lines) != 3:
            errors.append(f"包含 {len(self.sum_lines)} sum_lines")
        if not self.get_sum_line("收入"):
            errors.append(f"缺失 income_line")
        if not self.get_sum_line("支出"):
            errors.append(f"缺失 expense_line")
        if not self.get_sum_line("结余"):
            errors.append(f"缺失 balance_line")
        if not self.body_lines:
            errors.append(f"缺失 body_lines")
        return errors

    def __repr__(self):
        return (
            f"LifeSection(name={self.name!r}, "
            f"summary={len(self.sum_lines)}, "
            f"body={len(self.body_lines)}, "
            f"units={len(self.unit_lines)})"
        )


# ======================================== #
#    SingleAggrSection
# ======================================== #
 
@dataclass
class SingleAggrSection(BaseSection, ABC):

    def is_sum_line(self, line: Line) -> bool:
        return line.type == LineType.SECTION_SUM

    @property
    def sum(self) -> int:
        ln = self.sum_lines[0]
        return ln.value

    def rebuild(self):
        sum_value = sum(ln.value for ln in self.unit_lines)
        ln = self.sum_lines[0]
        ln.value = sum_value
    
    def checksum(self) -> bool:
        ln = self.sum_lines[0]
        return ln.value == sum(ln.value for ln in self.unit_lines)

    def validate(self) -> List[str]:
        errors = []
        if len(self.sum_lines) != 1:
            errors.append(f"包含 {len(self.sum_lines)} sum_lines")
        if not self.body_lines:
            errors.append(f"缺失 body_lines")
        return errors


# ======================================== #
#    MonthSection
# ======================================== #
 
@dataclass
class MonthSection(SingleAggrSection):

    def __repr__(self):
        return (
            f"MonthSection(name={self.name!r}, "
            f"sum={len(self.sum_lines)}, "
            f"body={len(self.body_lines)}, "
            f"units={len(self.unit_lines)})"
        )


# ======================================== #
#    CollectSection
# ======================================== #
 
@dataclass
class CollectSection(SingleAggrSection):

    def __repr__(self):
        return (
            f"CollectSection(name={self.name!r}, "
            f"sum={len(self.sum_lines)}, "
            f"body={len(self.body_lines)}, "
            f"units={len(self.unit_lines)})"
        )


# ======================================== #
#    Section Factory
# ======================================== #

def make_section(titleline: Line, lines: List[Line]) -> BaseSection:
    ltype = titleline.type

    if ltype == LineType.LIFE_TITLE:
        return LifeSection(title_line=titleline, _raw_lines=lines)
    elif ltype == LineType.MONTH_TITLE:
        return MonthSection(title_line=titleline, _raw_lines=lines)
    elif ltype == LineType.COLLECT_TITLE:
        return CollectSection(title_line=titleline, _raw_lines=lines)
    else:
        raise ValueError(f"未知 Section 类型: {titleline.raw.strip()}")
