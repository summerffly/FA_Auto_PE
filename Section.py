# File:        Section.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-22
# LastEdit:    2026-03-25
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
        if self.head_line.ltype != LineType.MONTH_TITLE and self.head_line.ltype != LineType.SUB_TAG:
            raise ValueError("Section.head_line 必须是 MONTH_TITLE 或 SUB_TAG 类型")

    @property
    def name(self) -> str:
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
        """
        返回完整 section 行
        """
        return [self.head_line] + self.summary_lines + self.body_lines

    @property
    def unit_lines(self) -> List[Line]:
        """
        body_lines 中的 UNIT 行
        """
        return [ln for ln in self.body_lines if ln.ltype == LineType.UNIT]

    @property
    def detail_lines(self) -> List[Line]:
        return self.unit_lines

    @property
    def blank_lines(self) -> List[Line]:
        """
        body_lines 中的空行
        """
        return [ln for ln in self.body_lines if ln.ltype == LineType.BLANK]

    @property
    def other_lines(self) -> List[Line]:
        """
        body_lines 中除 UNIT / BLANK 之外的其他行
        """
        return [
            ln for ln in self.body_lines
            if ln.ltype not in (LineType.UNIT, LineType.BLANK)
        ]

    def add_line(self, line: Line):
        if self.is_summary_line(line):
            self.summary_lines.append(line)
        else:
            self.body_lines.append(line)

    def total_units(self) -> int:
        """
        所有 UNIT 行求和
        """
        return sum(ln.value for ln in self.unit_lines)

    def find_summary(self, keyword: str) -> Optional[Line]:
        """
        按关键字查找 summary 行
        """
        for ln in self.summary_lines:
            if keyword in ln.content:
                return ln
        return None

    def to_raw_lines(self) -> List[str]:
        return [ln.to_raw() for ln in self.lines]

    def to_raw(self) -> str:
        return "\n".join(self.to_raw_lines())

    @abstractmethod
    def is_summary_line(self, line: Line) -> bool:
        raise NotImplementedError

    @abstractmethod
    def rebuild_summary(self):
        raise NotImplementedError

    @abstractmethod
    def validate_summary(self) -> bool:
        raise NotImplementedError


# ======================================== #
#    LifeSection
# ======================================== #

@dataclass
class LifeSection(BaseSection):
    def is_summary_line(self, line: Line) -> bool:
        return line.ltype == LineType.MONTH_SUM

    def rebuild_summary(self):
        """
        规则：
        - 薪资保留原值
        - 支出 = 所有负数 UNIT 求和
        - 结余 = 薪资 + 支出
        """
        s_income = self.find_summary("薪资")
        if s_income is None:
            raise ValueError(f"{self.name} 缺少 '薪资'")

        income = s_income.value
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
        s_income = self.find_summary("薪资")
        s_expense = self.find_summary("支出")
        s_balance = self.find_summary("结余")

        if s_income is None or s_expense is None or s_balance is None:
            return False

        income = s_income.value
        expense = sum(ln.value for ln in self.unit_lines if ln.value < 0)
        balance = income + expense

        return (
            s_expense.value == expense and
            s_balance.value == balance
        )

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
    def is_summary_line(self, line: Line) -> bool:
        return line.ltype == LineType.TITLE_SUM

    def rebuild_summary(self):
        total = self.total_units()
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
            ln.value == self.total_units()
        )

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
    def is_summary_line(self, line: Line) -> bool:
        return line.ltype == LineType.SUB_TITLE_SUM

    def rebuild_summary(self):
        total = self.total_units()
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
            ln.value == self.total_units()
        )

    def __repr__(self):
        return (
            f"TitleSection(name={self.name!r}, "
            f"summary={len(self.summary_lines)}, "
            f"body={len(self.body_lines)}, "
            f"units={len(self.unit_lines)})"
        )


# ----- Section Factory -------------------- #

def make_section(headline: Line) -> BaseSection:
    raw = headline.raw.strip()
    ltype = headline.ltype

    # LifeSection
    if ltype == LineType.MONTH_TITLE and "life" in raw:
        return LifeSection(head_line=headline)
    
    # MonthSection
    if ltype == LineType.MONTH_TITLE and "life" not in raw:
        return MonthSection(head_line=headline)
    
    # TitleSection
    if ltype == LineType.SUB_TAG:
        return TitleSection(head_line=headline)
    
    raise ValueError(f"未知 Section 类型: {raw}")
