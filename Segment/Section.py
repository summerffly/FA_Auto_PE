# File:        Section.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-22
# LastEdit:    2026-03-26
# Description: 

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from Line import LineType, Line
from Line import LineRegex as RE


# ======================================== #
#    BaseSection
# ======================================== #

@dataclass
class BaseSection(ABC):
    head_line: Line
    summary_lines: List[Line] = field(default_factory=list)
    body_lines: List[Line] = field(default_factory=list)

    def __post_init__(self):
        if self.head_line.ltype != LineType.LIFE_TITLE and self.head_line.ltype != LineType.MONTH_TITLE and self.head_line.ltype != LineType.SUB_TAG:
            raise ValueError("Section.head_line 必须是 MONTH_TITLE 或 SUB_TAG 类型")

    @property
    def name(self) -> str:
        m = RE.LIFE_TITLE.match(self.head_line.raw)
        if m:
            return "life" + m.group(1)
        m = RE.MONTH_TITLE.match(self.head_line.raw)
        if m:
            return m.group(1) + m.group(2)
        m = RE.SUB_TAG.match(self.head_line.raw)
        if m:
            return m.group(1)

    @property
    def month_no(self) -> Optional[str]:
        """
        返回月份编号，例如 M02 / M03
        """
        m = re.search(r'\.(M\d{2})$', self.name)
        if m:
            return m.group(1)
        return None

    @property
    def lines(self) -> List[Line]:
        return [self.head_line] + self.summary_lines + self.body_lines

    @property
    def unit_lines(self) -> List[Line]:
        return [ln for ln in self.body_lines if ln.ltype == LineType.UNIT]

    @property
    def blank_lines(self) -> List[Line]:
        return [ln for ln in self.body_lines if ln.ltype == LineType.BLANK]

    def add_line(self, line: Line):
        if self.is_summary_line(line):
            self.summary_lines.append(line)
        else:
            self.body_lines.append(line)

    def calc_units_sum(self) -> int:
        return sum(ln.value for ln in self.unit_lines)

    def find_summary_line(self, keyword: str) -> Optional[Line]:
        for ln in self.summary_lines:
            if keyword in ln.content:
                return ln
        return None

    def to_raw_lines(self) -> List[str]:
        return [ln.to_raw() for ln in self.lines]

    def to_raw(self) -> str:
        return "\n".join(self.to_raw_lines())
    

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
        if len(self.summary_lines) != 3:
            errors.append(f"包含 {len(self.summary_lines)} SummaryLines")
        if not self.body_lines:
            errors.append(f"缺失 BodyLines")
        return errors

    def is_summary_line(self, line: Line) -> bool:
        return line.ltype == LineType.MONTH_SUM

    def rebuild_summary(self):
        income_line = self.find_summary_line("薪资")
        if income_line is None:
            raise ValueError(f"{self.name} 缺少 '薪资'")

        income = income_line.value
        expense = sum(ln.value for ln in self.unit_lines if ln.value < 0)
        balance = income + expense

        month_no = self.month_no
        if month_no is None:
            raise ValueError(f"无法从 section 名称中解析月份: {self.name}")

        month_text = month_no[1:] + "月"

        self.summary_lines = [
            Line(
                raw="",
                ltype=LineType.MONTH_SUM,
                value=income,
                content=f"{month_text}薪资"
            ),
            Line(
                raw="",
                ltype=LineType.MONTH_SUM,
                value=expense,
                content=f"{month_text}支出"
            ),
            Line(
                raw="",
                ltype=LineType.MONTH_SUM,
                value=balance,
                content=f"{month_text}结余"
            ),
        ]

    def validate_summary(self) -> bool:
        income_line = self.find_summary_line("薪资")
        expense_line = self.find_summary_line("支出")
        balance_line = self.find_summary_line("结余")

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
        balance_line = self.find_summary_line("结余")
        return balance_line.value if balance_line else 0

    def __repr__(self):
        return (
            f"LifeSection(name={self.name!r}, "
            f"summary={len(self.summary_lines)}, "
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
        if len(self.summary_lines) != 1:
            errors.append(f"包含 {len(self.summary_lines)} SummaryLines")
        if not self.body_lines:
            errors.append(f"缺失 BodyLines")
        return errors

    def is_summary_line(self, line: Line) -> bool:
        return line.ltype == LineType.TITLE_SUM

    def rebuild_summary(self):
        total = self.calc_units_sum()
        self.summary_lines = [
            Line(
                raw="",
                ltype=LineType.TITLE_SUM,
                value=total,
                content=""
            )
        ]

    def validate_summary(self) -> bool:
        if len(self.summary_lines) != 1:
            return False

        ln = self.summary_lines[0]
        return (
            ln.ltype == LineType.TITLE_SUM and
            ln.value == self.calc_units_sum()
        )
    
    def get_summary(self) -> int:
        ln = self.summary_lines[0] if self.summary_lines else None
        return ln.value if ln and ln.ltype == LineType.TITLE_SUM else 0

    def __repr__(self):
        return (
            f"MonthSection(name={self.name!r}, "
            f"summary={len(self.summary_lines)}, "
            f"body={len(self.body_lines)}, "
            f"units={len(self.unit_lines)})"
        )


# ======================================== #
#    TitleSection
# ======================================== #

@dataclass
class TitleSection(BaseSection):
    def validate_struct(self) -> List[str]:
        errors = []
        if len(self.summary_lines) != 1:
            errors.append(f"包含 {len(self.summary_lines)} SummaryLines")
        if not self.body_lines:
            errors.append(f"缺失 BodyLines")
        return errors

    def is_summary_line(self, line: Line) -> bool:
        return line.ltype == LineType.SUB_TITLE_SUM

    def rebuild_summary(self):
        total = self.calc_units_sum()
        self.summary_lines = [
            Line(
                raw="",
                ltype=LineType.SUB_TITLE_SUM,
                value=total,
                content=""
            )
        ]

    def validate_summary(self) -> bool:
        if len(self.summary_lines) != 1:
            return False

        ln = self.summary_lines[0]
        return (
            ln.ltype == LineType.SUB_TITLE_SUM and
            ln.value == self.calc_units_sum()
        )

    def get_summary(self) -> int:
        ln = self.summary_lines[0] if self.summary_lines else None
        return ln.value if ln and ln.ltype == LineType.SUB_TITLE_SUM else 0

    def __repr__(self):
        return (
            f"TitleSection(name={self.name!r}, "
            f"summary={len(self.summary_lines)}, "
            f"body={len(self.body_lines)}, "
            f"units={len(self.unit_lines)})"
        )


# ----- Section Factory -------------------- #

def make_section(headline: Line, lines: List[Line]) -> BaseSection:
    raw = headline.raw.strip()
    ltype = headline.ltype
    section = None

    if ltype == LineType.LIFE_TITLE:
        # LifeSection
        section = LifeSection(head_line=headline)
    elif ltype == LineType.MONTH_TITLE:
        # MonthSection
        section = MonthSection(head_line=headline)
    elif ltype == LineType.SUB_TAG:
        # TitleSection
        section = TitleSection(head_line=headline)
    else:
        raise ValueError(f"未知 Section 类型: {raw}")
    
    if lines is not None:
        for line in lines:
            section.add_line(line)
    
    return section
