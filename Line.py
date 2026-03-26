# File:        Line.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-14
# LastEdit:    2026-03-26
# Description: Markdown行解析

import re
from datetime import datetime
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

    HEAD_TITLE    = auto()
    MONTH_TITLE   = auto()
    SUB_TITLE     = auto()
    SUB_TAG       = auto()
    TOTAL         = auto()
    SUMMARY       = auto()

    UNIT          = auto()
    AGGR          = auto()
    MONTH_SUM     = auto()
    TITLE_SUM     = auto()
    SUB_TITLE_SUM = auto()
    TOTAL_SUM     = auto()
    UNKNOWN       = auto()


# ======================================== #
#    Line 正则表达式
# ======================================== #

@dataclass(frozen=True)
class LineRegex:
    # 空行
    BLANK: ClassVar[re.Pattern] = re.compile(r'^\s*$')
    # 分隔线
    # ```
    DELIMITER: ClassVar[re.Pattern] = re.compile(r'^`{3}$')
    # EOF
    # ---
    EOF: ClassVar[re.Pattern] = re.compile(r'^-{3}$')
    # 更新时间戳
    # *Update Time : 2024-06-01 12:00:00*
    TIMESTAMP: ClassVar[re.Pattern] = re.compile(r'^\*Update Time : (.+)\*$')

    # 总标题
    # # DGtler.Month
    HEAD_TITLE: ClassVar[re.Pattern] = re.compile(r'^# (.+)$')
    # 月度标题
    # ## DGtler.M03
    MONTH_TITLE: ClassVar[re.Pattern] = re.compile(r'^## (.+)(\.M\d{2})$')
    # 分项标题
    # ## NGXP
    SUB_TITLE: ClassVar[re.Pattern] = re.compile(r'^## (?!Total$)(?!Summary$)(?!.*\.M\d{2}$)(.+)$')
    # 分项Tag
    # ### Apple
    SUB_TAG: ClassVar[re.Pattern] = re.compile(r'^### (.+)$')
    # 总计
    # ## Total
    TOTAL: ClassVar[re.Pattern] = re.compile(r'^## Total$')
    # 汇总
    # ## Summary
    SUMMARY: ClassVar[re.Pattern] = re.compile(r'^## Summary$')

    # 收支条目
    # `- 50` 猫罐头
    UNIT: ClassVar[re.Pattern] = re.compile(r'^`([+-])[ ]?(\d+)` (.*)$')
    # 聚合金额
    # 币安货币 : +80000
    AGGR: ClassVar[re.Pattern] = re.compile(r'^(?!Total)(?!>)(.+) : ([+-])(\d+)$')
    # 月度汇总金额
    # > 02月薪资 : +1030
    MONTH_SUM: ClassVar[re.Pattern] = re.compile(r'^> (\d{2}.+) : ([+-])(\d+)$')
    # 分项汇总金额
    # > +100
    TITLE_SUM: ClassVar[re.Pattern] = re.compile(r'^> ([+-])(\d+)$')
    # 分项Tag汇总金额
    # >> +100
    SUB_TITLE_SUM: ClassVar[re.Pattern] = re.compile(r'^>> ([+-])(\d+)$')
    # 总计金额
    # Total : +820
    TOTAL_SUM: ClassVar[re.Pattern] = re.compile(r'^Total : ([+-])(\d+)$')


# ======================================== #
#    Line
# ======================================== #

@dataclass
class Line:
    raw: str
    ltype: LineType = LineType.UNKNOWN
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
        return cls(raw=raw, ltype=LineType.UNIT, value=value, content=content)

    @classmethod
    def make_blank(cls) -> "Line":
        return cls(raw="", ltype=LineType.BLANK)

    def _parse(self):
        s = self.raw
        RE = self.RE

        if RE.BLANK.match(s):
            self.ltype = LineType.BLANK
            return
        if RE.DELIMITER.match(s):
            self.ltype = LineType.DELIMITER
            return
        if RE.EOF.match(s):
            self.ltype = LineType.EOF
            return
        if RE.TIMESTAMP.match(s):
            self.ltype = LineType.TIMESTAMP
            return

        if RE.HEAD_TITLE.match(s):
            self.ltype = LineType.HEAD_TITLE
            return
        if RE.MONTH_TITLE.match(s):
            self.ltype = LineType.MONTH_TITLE
            return 
        if RE.SUB_TITLE.match(s):
            self.ltype = LineType.SUB_TITLE
            return
        if RE.SUB_TAG.match(s):
            self.ltype = LineType.SUB_TAG
            return
        if RE.TOTAL.match(s):
            self.ltype = LineType.TOTAL
            return
        if RE.SUMMARY.match(s):
            self.ltype = LineType.SUMMARY
            return

        m = RE.UNIT.match(s)
        if m:
            self.ltype = LineType.UNIT
            self.value = int(m.group(2)) if m.group(1) == "+" else -int(m.group(2))
            self.content = m.group(3)
            return
        
        m = RE.AGGR.match(s)
        if m:
            self.ltype = LineType.AGGR
            self.value = int(m.group(3)) if m.group(2) == "+" else -int(m.group(3))
            self.content = m.group(1)
            return

        m = RE.MONTH_SUM.match(s)
        if m:
            self.ltype = LineType.MONTH_SUM
            self.value = int(m.group(3)) if m.group(2) == "+" else -int(m.group(3))
            self.content = m.group(1)
            return

        m = RE.TITLE_SUM.match(s)
        if m:
            self.ltype = LineType.TITLE_SUM
            self.value = int(m.group(2)) if m.group(1) == "+" else -int(m.group(2))
            return

        m = RE.SUB_TITLE_SUM.match(s)
        if m:
            self.ltype = LineType.SUB_TITLE_SUM
            self.value = int(m.group(2)) if m.group(1) == "+" else -int(m.group(2))
            return

        m = RE.TOTAL_SUM.match(s)
        if m:
            self.ltype = LineType.TOTAL_SUM
            self.value = int(m.group(2)) if m.group(1) == "+" else -int(m.group(2))
            return

        # UNKNOWN
        self.ltype = LineType.UNKNOWN
        self.content = s


    # ----- 序列化Markdown -------------------- #

    def to_raw(self) -> str:
        if self.ltype == LineType.UNIT:
            sign = "+" if self.value > 0 else "-"
            return f"`{sign} {abs(self.value)}` {self.content}"
        
        if self.ltype == LineType.AGGR:
            sign = "+" if self.value > 0 else "-"
            return f"{self.content} : {sign}{abs(self.value)}"
        
        if self.ltype == LineType.MONTH_SUM:
            sign = "+" if self.value > 0 else "-"
            return f"> {self.content} : {sign}{abs(self.value)}"
        
        if self.ltype == LineType.TITLE_SUM:
            sign = "+" if self.value > 0 else "-"
            return f"> {sign}{abs(self.value)}"
        
        if self.ltype == LineType.SUB_TITLE_SUM:
            sign = "+" if self.value > 0 else "-"
            return f">> {sign}{abs(self.value)}"
        
        if self.ltype == LineType.TOTAL_SUM:
            sign = "+" if self.value > 0 else "-"
            return f"Total : {sign}{abs(self.value)}"
        
        if self.ltype == LineType.TIMESTAMP:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"*Update Time : {now}*"
        
        if self.ltype == LineType.BLANK:
            return ""
        
        return self.raw


    # ----- 辅助 -------------------- #

    @property
    def is_amount(self) -> bool:
        """ 是否包含金额 """
        return self.ltype in (
            LineType.UNIT, 
            LineType.AGGR, 
            LineType.MONTH_SUM, 
            LineType.TITLE_SUM, 
            LineType.SUB_TITLE_SUM,
            LineType.TOTAL_SUM
        )

    def __repr__(self):
        return f"Line({self.ltype.value}, val={self.value}, content={self.content!r})"
