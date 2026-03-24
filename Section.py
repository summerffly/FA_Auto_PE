"""
Section.py
月度 Section 抽象

支持三类 Section
1. LifeSection
    - 适用于 life.M
    - summary_lines 为 3 行

2. MonthSection
    - 适用于 DGtler.M
    - summary_lines 为 1 行

3. TitleSection
    - 适用于 DK
    - summary_lines 为 1 行
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType


RE_MONTH_NAME = re.compile(r'^## (.+\.M\d{2})$')


# ======================================== #
#    BaseSection
# ======================================== #

@dataclass
class BaseSection(ABC):
    """
    Section 基类：
    - title_line
    - summary_lines
    - body_lines

    其中：
    - summary_lines 由子类决定具体规则
    - body_lines 保留空行、明细和其他内容
    """
    title_line: Line
    summary_lines: List[Line] = field(default_factory=list)
    body_lines: List[Line] = field(default_factory=list)

    def __post_init__(self):
        if self.title_line.ltype != LineType.MONTH_TITLE and self.title_line.ltype != LineType.SUB_TAG:
            raise ValueError("Section.title_line 必须是 MONTH_TITLE 或 SUB_TAG 类型")

    @property
    def name(self) -> str:
        """
        返回 section 名称，例如 life.M02 / DGtler.M03
        """
        m = RE_MONTH_NAME.match(self.title_line.raw)
        if m:
            return m.group(1)
        return self.title_line.raw[3:].strip()

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
        return [self.title_line] + self.summary_lines + self.body_lines

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

    @property
    def amount_lines(self) -> List[Line]:
        """
        返回 section 内所有带金额行
        """
        result: List[Line] = []
        result.extend([ln for ln in self.summary_lines if ln.is_amount])
        result.extend([ln for ln in self.body_lines if ln.is_amount])
        return result

    def add_line(self, line: Line):
        """
        自动分发：
        - summary 行 -> summary_lines
        - 其他行     -> body_lines
        """
        if self.is_summary_line(line):
            self.summary_lines.append(line)
        else:
            self.body_lines.append(line)

    def add_unit(self, value: int, content: str):
        self.body_lines.append(Line.make_unit(value, content))

    def insert_body_line(self, index: int, line: Line):
        self.body_lines.insert(index, line)

    def insert_unit(self, index: int, value: int, content: str):
        self.body_lines.insert(index, Line.make_unit(value, content))

    def extend(self, lines: List[Line]):
        for line in lines:
            self.add_line(line)

    def total_units(self) -> int:
        """
        所有 UNIT 行求和
        """
        return sum(ln.value for ln in self.unit_lines)

    def total_amounts(self) -> int:
        """
        所有带金额行求和
        """
        return sum(ln.value for ln in self.amount_lines)

    def find_summary(self, keyword: str) -> Optional[Line]:
        """
        按关键字查找 summary 行
        """
        for ln in self.summary_lines:
            if keyword in ln.content:
                return ln
        return None

    def first_detail_index(self) -> Optional[int]:
        for i, ln in enumerate(self.body_lines):
            if ln.ltype == LineType.UNIT:
                return i
        return None

    def last_detail_index(self) -> Optional[int]:
        for i in range(len(self.body_lines) - 1, -1, -1):
            if self.body_lines[i].ltype == LineType.UNIT:
                return i
        return None

    def append_unit_after_details(self, value: int, content: str):
        """
        把 UNIT 插到最后一条明细后面
        """
        new_line = Line.make_unit(value, content)
        idx = self.last_detail_index()

        if idx is None:
            self.body_lines.append(new_line)
        else:
            self.body_lines.insert(idx + 1, new_line)

    def replace_summary_lines(self, new_summary_lines: List[Line]):
        self.summary_lines = list(new_summary_lines)

    def to_raw_lines(self) -> List[str]:
        return [ln.to_raw() for ln in self.lines]

    def to_raw(self) -> str:
        return "\n".join(self.to_raw_lines())

    @abstractmethod
    def is_summary_line(self, line: Line) -> bool:
        """
        判断某行是否属于当前 Section 的 summary 行
        """
        raise NotImplementedError

    @abstractmethod
    def rebuild_summary(self):
        """
        重建 summary_lines
        """
        raise NotImplementedError

    @abstractmethod
    def validate_summary(self) -> bool:
        """
        校验当前 summary 是否正确
        """
        raise NotImplementedError


# ======================================== #
#    LifeSection
# ======================================== #

@dataclass
class LifeSection(BaseSection):
    """
    三行月汇总：
    > 03月薪资 : +800
    > 03月支出 : -3990
    > 03月结余 : -3190
    """

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
            raise ValueError(f"{self.name} 缺少 '薪资'，无法重建 summary")

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
    """
    单行汇总：
    > -300
    """

    def is_summary_line(self, line: Line) -> bool:
        return line.ltype == LineType.TITLE_SUM

    def rebuild_summary(self):
        """
        规则: summary = 所有 UNIT 求和
        """
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
    """
    单行汇总：
    >> -300
    """

    def is_summary_line(self, line: Line) -> bool:
        return line.ltype == LineType.SUB_TITLE_SUM

    def rebuild_summary(self):
        """
        规则: summary = 所有 UNIT 求和
        """
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


# ----- MiniSection Factory -------------------- #

def make_section(title_line: Line) -> BaseSection:
    raw = title_line.raw.strip()

    # Type1
    if raw.startswith("## life."):
        return LifeSection(title_line=title_line)
    
    # Type2
    if raw.startswith("##") and ".M" in raw:
        return MonthSection(title_line=title_line)
    
    # Type3
    if raw.startswith("###"):
        return TitleSection(title_line=title_line)
    
    raise ValueError(f"未知 section 类型，无法创建 Section: {raw}")
