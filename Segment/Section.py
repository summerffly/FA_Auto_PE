# File:        Section.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-22
# LastEdit:    2026-04-01
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
    title_line: Line
    aggr_lines: List[Line] = field(default_factory=list)
    body_lines: List[Line] = field(default_factory=list)
    _name: str = field(init=False)
    _month_no: Optional[str] = field(init=False)

    def __post_init__(self):
        if self.title_line.type not in {
            LineType.LIFE_TITLE,
            LineType.MONTH_TITLE,
            LineType.COLLECT_TITLE
        }:
            raise ValueError(f"{Fore.RED}[!]{Style.RESET_ALL} Section.title_line 类型错误")

        self._name = ""
        self._month_no = None
        self._extract_name()
        self._extract_month_no()

    def _extract_name(self) -> str:
        if m := RE.LIFE_TITLE.match(self.title_line.raw):
            self._name = "life." + m.group(1)
        if m := RE.MONTH_TITLE.match(self.title_line.raw):
            self._name = m.group(1) + "." + m.group(2)
        if m := RE.COLLECT_TITLE.match(self.title_line.raw):
            self._name = m.group(1)
    
    def _extract_month_no(self) -> Optional[str]:
        if m := RE.LIFE_TITLE.match(self.title_line.raw):
            self._month_no = m.group(1)
        if m := RE.MONTH_TITLE.match(self.title_line.raw):
            self._month_no = m.group(2)

    @property
    def name(self) -> str:
        return self._name

    @property
    def month_no(self) -> Optional[str]:
        return self._month_no

    @property
    def lines(self) -> List[Line]:
        return [self.title_line] + self.aggr_lines + self.body_lines

    @property
    def unit_lines(self) -> List[Line]:
        return [ln for ln in self.body_lines if ln.type == LineType.UNIT]

    @property
    def blank_lines(self) -> List[Line]:
        return [ln for ln in self.body_lines if ln.type == LineType.BLANK]

    def parse_line(self, line: Line):
        if self.is_summary_line(line):
            self.aggr_lines.append(line)
        else:
            self.body_lines.append(line)

    def calc_units_sum(self) -> int:
        return sum(ln.value for ln in self.unit_lines)

    def get_aggr_line(self, keyword: str) -> Optional[Line]:
        for ln in self.aggr_lines:
            if keyword in ln.content:
                return ln
        return None
    
    # ----- 序列化方法 -------------------- #

    def to_lines(self) -> List[str]:
        return [ln.to_raw() for ln in self.lines]

    def to_raw(self) -> str:
        return "\n".join(self.to_lines())
    
    # ----- 抽象方法 -------------------- #

    @abstractmethod
    def validate_struct(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def is_summary_line(self, line: Line) -> bool:
        raise NotImplementedError

    @abstractmethod
    def rebuild_summary(self):
        raise NotImplementedError

    @abstractmethod
    def validate_summary(self) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    def get_summary(self) -> int:
        raise NotImplementedError


# ======================================== #
#    LifeSection
# ======================================== #

@dataclass
class LifeSection(BaseSection):
    def validate_struct(self) -> List[str]:
        errors = []
        if len(self.aggr_lines) != 3:
            errors.append(f"包含 {len(self.aggr_lines)} SummaryLines")
        if not self.body_lines:
            errors.append(f"缺失 BodyLines")
        return errors

    def is_summary_line(self, line: Line) -> bool:
        return line.type == LineType.MONTH_AGGR

    def rebuild_summary(self):
        income_line = self.get_aggr_line("收入")
        if income_line is None:
            raise ValueError(f"{self.name} 缺少 '收入'")

        income = income_line.value
        expense = sum(ln.value for ln in self.unit_lines if ln.value < 0)
        balance = income + expense

        month_no = self.month_no
        if month_no is None:
            raise ValueError(f"无法从 section 名称中解析月份: {self.name}")

        month_text = month_no[1:] + "月"

        self.aggr_lines = [
            Line(
                raw="",
                type=LineType.MONTH_AGGR,
                value=income,
                content=f"{month_text}收入"
            ),
            Line(
                raw="",
                type=LineType.MONTH_AGGR,
                value=expense,
                content=f"{month_text}支出"
            ),
            Line(
                raw="",
                type=LineType.MONTH_AGGR,
                value=balance,
                content=f"{month_text}结余"
            ),
        ]

    def validate_summary(self) -> bool:
        income_line = self.get_aggr_line("收入")
        expense_line = self.get_aggr_line("支出")
        balance_line = self.get_aggr_line("结余")

        if income_line is None or expense_line is None or balance_line is None:
            return False

        income = income_line.value
        expense = sum(ln.value for ln in self.unit_lines if ln.value < 0)
        balance = income + expense

        return (
            expense_line.value == expense and
            balance_line.value == balance
        )
    
    def get_summary(self) -> int:
        balance_line = self.get_aggr_line("结余")
        return balance_line.value if balance_line else 0
    
    def get_income(self) -> int:
        income_line = self.get_aggr_line("收入")
        return income_line.value if income_line else 0
    
    def get_expense(self) -> int:
        expense_line = self.get_aggr_line("支出")
        return expense_line.value if expense_line else 0
    
    def get_balance(self) -> int:
        balance_line = self.get_aggr_line("结余")
        return balance_line.value if balance_line else 0

    def __repr__(self):
        return (
            f"LifeSection(name={self.name!r}, "
            f"summary={len(self.aggr_lines)}, "
            f"body={len(self.body_lines)}, "
            f"units={len(self.unit_lines)})"
        )


# ======================================== #
#    MonthSection
# ======================================== #

@dataclass
class MonthSection(BaseSection):
    def validate_struct(self) -> List[str]:
        errors = []
        if len(self.aggr_lines) != 1:
            errors.append(f"包含 {len(self.aggr_lines)} SummaryLines")
        if not self.body_lines:
            errors.append(f"缺失 BodyLines")
        return errors

    def is_summary_line(self, line: Line) -> bool:
        return line.type == LineType.SECTION_AGGR

    def rebuild_summary(self):
        total = self.calc_units_sum()
        self.aggr_lines = [
            Line(
                raw="",
                type=LineType.SECTION_AGGR,
                value=total,
                content=""
            )
        ]

    def validate_summary(self) -> bool:
        if len(self.aggr_lines) != 1:
            return False

        ln = self.aggr_lines[0]
        return (
            ln.type == LineType.SECTION_AGGR and
            ln.value == self.calc_units_sum()
        )
    
    def get_summary(self) -> int:
        ln = self.aggr_lines[0] if self.aggr_lines else None
        return ln.value if ln and ln.type == LineType.SECTION_AGGR else 0

    def __repr__(self):
        return (
            f"MonthSection(name={self.name!r}, "
            f"summary={len(self.aggr_lines)}, "
            f"body={len(self.body_lines)}, "
            f"units={len(self.unit_lines)})"
        )


# ======================================== #
#    CollectSection
# ======================================== #

@dataclass
class CollectSection(BaseSection):
    def validate_struct(self) -> List[str]:
        errors = []
        if len(self.aggr_lines) != 1:
            errors.append(f"包含 {len(self.aggr_lines)} SummaryLines")
        if not self.body_lines:
            errors.append(f"缺失 BodyLines")
        return errors

    def is_summary_line(self, line: Line) -> bool:
        return line.type == LineType.SECTION_AGGR

    def rebuild_summary(self):
        total = self.calc_units_sum()
        self.aggr_lines = [
            Line(
                raw="",
                type=LineType.SECTION_AGGR,
                value=total,
                content=""
            )
        ]

    def validate_summary(self) -> bool:
        if len(self.aggr_lines) != 1:
            return False

        ln = self.aggr_lines[0]
        return (
            ln.type == LineType.SECTION_AGGR and
            ln.value == self.calc_units_sum()
        )

    def get_summary(self) -> int:
        ln = self.aggr_lines[0] if self.aggr_lines else None
        return ln.value if ln and ln.type == LineType.SECTION_AGGR else 0

    def __repr__(self):
        return (
            f"CollectSection(name={self.name!r}, "
            f"summary={len(self.aggr_lines)}, "
            f"body={len(self.body_lines)}, "
            f"units={len(self.unit_lines)})"
        )


# ======================================== #
#    Section Factory
# ======================================== #

def make_section(titleline: Line, lines: List[Line]) -> BaseSection:
    raw = titleline.raw.strip()
    type = titleline.type
    section = None

    if type == LineType.LIFE_TITLE:
        section = LifeSection(title_line=titleline)
    elif type == LineType.MONTH_TITLE:
        section = MonthSection(title_line=titleline)
    elif type == LineType.COLLECT_TITLE:
        section = CollectSection(title_line=titleline)
    else:
        raise ValueError(f"未知 Section 类型: {raw}")
    
    if lines is not None:
        for line in lines:
            section.parse_line(line)
    
    return section
