# File:        Line.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-14
# LastEdit:    2026-04-01
# Description: Markdown单行解析模块

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import ClassVar


# ======================================== #
#    Line 类型枚举
# ======================================== #

class LineType(Enum):
    BLANK         = auto()
    DELIMITER     = auto()
    EOF           = auto()
    TIMESTAMP     = auto()

    HEADER        = auto()
    LIFE_TITLE    = auto()
    MONTH_TITLE   = auto()
    COLLECT_TITLE = auto()
    TOTAL_TITLE   = auto()
    SUMMARY_TITLE = auto()

    UNIT          = auto()
    PRIMARY       = auto()
    MONTH_AGGR    = auto()
    SECTION_AGGR  = auto()
    TOTAL         = auto()

    UNKNOWN       = auto()


# ======================================== #
#    Line 正则表达式
# ======================================== #

@dataclass(frozen=True)
class LineRegex:
    # 空行
    BLANK: ClassVar[re.Pattern] = re.compile(r'^\s*$')
    # ```
    DELIMITER: ClassVar[re.Pattern] = re.compile(r'^`{3}$')
    # ---
    EOF: ClassVar[re.Pattern] = re.compile(r'^-{3}$')
    # *Update Time : 2024-06-01 12:00:00*
    TIMESTAMP: ClassVar[re.Pattern] = re.compile(r'^\*Update Time : (.+)\*$')

    # # Digital Kingdom
    HEADER: ClassVar[re.Pattern] = re.compile(r'^# (.+)$')
    # ## life.M03
    LIFE_TITLE: ClassVar[re.Pattern] = re.compile(r'^## (life\.)(M\d{2})$')
    # ## DGtler.M03
    MONTH_TITLE: ClassVar[re.Pattern] = re.compile(r'^## (?!life)(.+\.)(M\d{2})$')
    # ## NGXP
    COLLECT_TITLE: ClassVar[re.Pattern] = re.compile(r'^## (?!.*\.M\d{2}$)(.+)$')
    # ### Total
    TOTAL_TITLE: ClassVar[re.Pattern] = re.compile(r'^### (Total)$')
    # ### Summary
    SUMMARY_TITLE: ClassVar[re.Pattern] = re.compile(r'^### (Summary)$')

    # `- 50` 猫罐头
    UNIT: ClassVar[re.Pattern] = re.compile(r'^`([+-])[ ]?(\d+)` (.*)$')
    # 币安货币 : +80000
    PRIMARY: ClassVar[re.Pattern] = re.compile(r'^(?!Total)(?!>)(.+) : ([+-])(\d+)$')
    # > 02月收入 : +1030
    MONTH_AGGR: ClassVar[re.Pattern] = re.compile(r'^> (\d{2}.+) : ([+-])(\d+)$')
    # > +100
    SECTION_AGGR: ClassVar[re.Pattern] = re.compile(r'^> ([+-])(\d+)$')
    # Total : +820
    TOTAL: ClassVar[re.Pattern] = re.compile(r'^Total : ([+-])(\d+)$')

    """
    # 金额层级
    UNIT      ->  基础项
    PRIMARY   ->  主级项
    AGGR      ->  合计项
    TOTAL     ->  总计项
    SUMMARY   ->  总结项
    """


# ======================================== #
#    Line
# ======================================== #

@dataclass
class Line:
    raw: str
    type: LineType = LineType.UNKNOWN
    value: int = 0
    content: str = ""

    # 内部引用
    RE = LineRegex

    @classmethod
    def parse(cls, raw: str) -> "Line":
        s = raw.rstrip("\n")
        ln = cls(raw=s)
        ln._parse()
        return ln

    @classmethod
    def make_unit(cls, value: int, content: str) -> "Line":
        sign = "+" if value >= 0 else "-"
        raw = f"`{sign} {abs(value)}` {content}"
        return cls(raw=raw, type=LineType.UNIT, value=value, content=content)

    @classmethod
    def make_blank(cls) -> "Line":
        return cls(raw="", type=LineType.BLANK)

    def _parse(self):
        s = self.raw
        RE = self.RE

        if RE.BLANK.match(s):
            self.type = LineType.BLANK
            return
        if RE.DELIMITER.match(s):
            self.type = LineType.DELIMITER
            return
        if RE.EOF.match(s):
            self.type = LineType.EOF
            return
        if RE.TIMESTAMP.match(s):
            self.type = LineType.TIMESTAMP
            self.content = RE.TIMESTAMP.match(s).group(1)
            return

        if RE.HEADER.match(s):
            self.type = LineType.HEADER
            return
        if RE.LIFE_TITLE.match(s):
            self.type = LineType.LIFE_TITLE
            return
        if RE.MONTH_TITLE.match(s):
            self.type = LineType.MONTH_TITLE
            return 
        if RE.COLLECT_TITLE.match(s):
            self.type = LineType.COLLECT_TITLE
            return
        if RE.TOTAL_TITLE.match(s):
            self.type = LineType.TOTAL_TITLE
            return
        if RE.SUMMARY_TITLE.match(s):
            self.type = LineType.SUMMARY_TITLE
            return

        m = RE.UNIT.match(s)
        if m:
            self.type = LineType.UNIT
            self.value = int(m.group(2)) if m.group(1) == "+" else -int(m.group(2))
            self.content = m.group(3)
            return
        
        m = RE.PRIMARY.match(s)
        if m:
            self.type = LineType.PRIMARY
            self.value = int(m.group(3)) if m.group(2) == "+" else -int(m.group(3))
            self.content = m.group(1)
            return

        m = RE.MONTH_AGGR.match(s)
        if m:
            self.type = LineType.MONTH_AGGR
            self.value = int(m.group(3)) if m.group(2) == "+" else -int(m.group(3))
            self.content = m.group(1)
            return

        m = RE.SECTION_AGGR.match(s)
        if m:
            self.type = LineType.SECTION_AGGR
            self.value = int(m.group(2)) if m.group(1) == "+" else -int(m.group(2))
            return

        m = RE.TOTAL.match(s)
        if m:
            self.type = LineType.TOTAL
            self.value = int(m.group(2)) if m.group(1) == "+" else -int(m.group(2))
            return

        # UNKNOWN
        self.type = LineType.UNKNOWN
        self.content = s


    # ----- 序列化 -------------------- #

    def to_raw(self) -> str:
        if self.type == LineType.UNIT:
            sign = "+" if self.value > 0 else "-"
            return f"`{sign} {abs(self.value)}` {self.content}"
        
        if self.type == LineType.PRIMARY:
            sign = "+" if self.value > 0 else "-"
            return f"{self.content} : {sign}{abs(self.value)}"
        
        if self.type == LineType.MONTH_AGGR:
            sign = "+" if self.value > 0 else "-"
            return f"> {self.content} : {sign}{abs(self.value)}"
        
        if self.type == LineType.SECTION_AGGR:
            sign = "+" if self.value > 0 else "-"
            return f"> {sign}{abs(self.value)}"
        
        if self.type == LineType.TOTAL:
            sign = "+" if self.value > 0 else "-"
            return f"Total : {sign}{abs(self.value)}"
        
        if self.type == LineType.TIMESTAMP:
            return f"*Update Time : {self.content}*"
        
        if self.type == LineType.BLANK:
            return ""
        
        return self.raw


    # ----- 辅助 -------------------- #

    @property
    def is_amount(self) -> bool:
        """ 是否包含金额 """
        return self.type in (
            LineType.UNIT, 
            LineType.PRIMARY, 
            LineType.MONTH_AGGR, 
            LineType.SECTION_AGGR, 
            LineType.TOTAL
        )

    def __repr__(self):
        return f"Line({self.type.value}, val={self.value}, content={self.content!r})"
