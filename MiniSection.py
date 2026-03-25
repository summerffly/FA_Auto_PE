# File:        MiniSection.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-25
# Description: 

from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType
from Line import LineRegex as RE


# ======================================== #
#    BaseMiniSection
# ======================================== #

@dataclass
class BaseMiniSection():
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

    def to_lines(self) -> List[Line]:
        out = []
        if self.head_line:
            out.append(self.head_line)
        out.extend(self.summary_lines)
        return out


# ======================================== #
#    MonthMiniSection
# ======================================== #

@dataclass
class MonthMiniSection(BaseMiniSection):
    def get(self, key: str) -> Optional[Line]:
        for ln in self.summary_lines:
            if ln.ltype == LineType.MONTH_SUM and key in ln.content:
                return ln
        return None

    @property
    def income(self) -> int:
        ln = self.get("薪资")
        return ln.value if ln else 0

    @property
    def expense(self) -> int:
        ln = self.get("支出")
        return ln.value if ln else 0

    @property
    def balance(self) -> int:
        ln = self.get("结余")
        return ln.value if ln else 0


# ======================================== #
#    TitleMiniSection
# ======================================== #

@dataclass
class TitleMiniSection(BaseMiniSection):
    def summary_line(self) -> Optional[Line]:
        for ln in self.summary_lines:
            if ln.ltype == LineType.TITLE_SUM:
                return ln
        return None

    @property
    def value(self) -> int:
        ln = self.summary_line()
        return ln.value if ln else 0


# ======================================== #
#    TotalMiniSection
# ======================================== #
@dataclass
class TotalMiniSection(BaseMiniSection):
    def value_line(self) -> Optional[Line]:
        """查找 AGGR 类型的行（Total : -1680）"""
        for ln in self.summary_lines:
            if ln.ltype == LineType.AGGR:
                return ln
        return None

    @property
    def value(self) -> int:
        ln = self.value_line()
        return ln.value if ln else 0

    def to_lines(self) -> List[Line]:
        """
        重写 to_lines 确保输出格式正确
        """
        out = []
        if self.head_line:
            out.append(self.head_line)
        out.extend(self.summary_lines)
        return out


# ----- MiniSection Factory -------------------- #

def make_minisection(headline: Line, lines: List[Line]) -> BaseMiniSection:
    raw = headline.raw.strip()
    ltype = headline.ltype

    # MonthMiniSection
    if ltype == LineType.MONTH_TITLE:
        return MonthMiniSection(head_line=headline, summary_lines=lines)
    
    # TitleMiniSection
    if ltype == LineType.SUB_TITLE:
        return TitleMiniSection(head_line=headline, summary_lines=lines)
    
    # TotalMiniSection
    if ltype == LineType.TOTAL:
        return TotalMiniSection(head_line=headline, summary_lines=lines)

    raise ValueError(f"未知 MiniSection 类型: {raw}")
