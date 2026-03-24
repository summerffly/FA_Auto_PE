from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType


# ======================================== #
#    BaseMiniSection
# ======================================== #

@dataclass
class BaseMiniSection:
    title_line: Line
    summary_lines: List[Line] = field(default_factory=list)

    @property
    def name(self) -> str:
        if self.title_line is None:
            return ""
        raw = self.title_line.raw.strip()
        if raw.startswith("## "):
            return raw[3:].strip()
        return raw

    def to_lines(self) -> List[Line]:
        out = []
        if self.title_line:
            out.append(self.title_line)
        out.extend(self.summary_lines)
        return out

    def validate(self) -> bool:
        return True


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

    def validate(self) -> bool:
        return self.income + self.expense == self.balance


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

    def validate(self) -> bool:
        xs = [x for x in self.summary_lines if x.ltype != LineType.BLANK]
        return len(xs) == 1 and xs[0].ltype == LineType.TITLE_SUM


# ----- MiniSection Factory -------------------- #

def make_minisection(title_line: Line, lines: List[Line]) -> BaseMiniSection:
    """
    只负责 MonthMiniSection 和 TitleMiniSection。
    ## Summary 由 SumLedger.flush_block 直接走 make_block，不会到这里。
    """
    name = title_line.raw.strip()

    if ".M" in name:
        return MonthMiniSection(title_line=title_line, summary_lines=lines)

    # 所有其他带标题的非-Summary 块
    return TitleMiniSection(title_line=title_line, summary_lines=lines)
