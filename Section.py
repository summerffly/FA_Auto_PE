"""
Section.py
月度 Section 抽象（三段结构版）

结构：
1. title_line
2. summary_lines  - 仅保存 MONTH_SUM，通常为 3 行
3. body_lines     - 保存明细、空行、其他内容，需保留空行
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType


RE_MONTH_NAME = re.compile(r'^## (.+\.M\d{2})$')


@dataclass
class Section:
    """
    一个月度块，例如：

    ## life.M02
    > 02月薪资 : +1030
    > 02月支出 : -5440
    > 02月结余 : -4410

    `- 1000` 02月_生活费
    `- 100`  02月_通勤费
    """
    title_line: Line
    summary_lines: List[Line] = field(default_factory=list)
    body_lines: List[Line] = field(default_factory=list)

    def __post_init__(self):
        if self.title_line.ltype != LineType.MONTH_TITLE:
            raise ValueError("Section.title_line 必须是 MONTH_TITLE")

    @property
    def name(self) -> str:
        """
        返回 section 名称，例如 life.M02
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
        返回该 section 的完整行（含标题）

        输出顺序：
        1. title_line
        2. summary_lines
        3. body_lines
        """
        result: List[Line] = [self.title_line]
        result.extend(self.summary_lines)
        result.extend(self.body_lines)
        return result

    @property
    def detail_lines(self) -> List[Line]:
        """
        body_lines 中的明细行（UNIT）
        """
        return [ln for ln in self.body_lines if ln.ltype == LineType.UNIT]

    @property
    def unit_lines(self) -> List[Line]:
        """
        兼容旧接口
        """
        return self.detail_lines

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
        返回该 section 内所有带金额的行
        顺序与输出一致
        """
        result: List[Line] = []
        result.extend([ln for ln in self.summary_lines if ln.is_amount])
        result.extend([ln for ln in self.body_lines if ln.is_amount])
        return result

    def add_line(self, line: Line):
        """
        自动分发：
        - MONTH_SUM -> summary_lines
        - 其他      -> body_lines

        注意：
        - 空行进入 body_lines
        - 明细进入 body_lines
        """
        if line.ltype == LineType.MONTH_SUM:
            self.summary_lines.append(line)
        else:
            self.body_lines.append(line)

    def add_summary(self, value: int, content: str):
        """
        添加一条月汇总行
        """
        self.summary_lines.append(
            Line(
                raw="",
                ltype=LineType.MONTH_SUM,
                value=value,
                content=content
            )
        )

    def add_unit(self, value: int, content: str):
        """
        在 body_lines 末尾追加一条 UNIT
        """
        self.body_lines.append(Line.make_unit(value, content))

    def insert_body_line(self, index: int, line: Line):
        """
        在 body_lines 指定位置插入一行
        """
        self.body_lines.insert(index, line)

    def insert_unit(self, index: int, value: int, content: str):
        """
        在 body_lines 指定位置插入一条 UNIT
        """
        self.body_lines.insert(index, Line.make_unit(value, content))

    def extend(self, lines: List[Line]):
        """
        批量追加，按 add_line 规则自动分发
        """
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
        注意：通常你更常用 total_units()
        """
        return sum(ln.value for ln in self.amount_lines)

    def find_summary(self, keyword: str) -> Optional[Line]:
        """
        按关键字找月汇总行，例如 keyword='薪资'
        """
        for ln in self.summary_lines:
            if keyword in ln.content:
                return ln
        return None

    def first_detail_index(self) -> Optional[int]:
        """
        返回第一条 UNIT 在 body_lines 中的位置
        """
        for i, ln in enumerate(self.body_lines):
            if ln.ltype == LineType.UNIT:
                return i
        return None

    def last_detail_index(self) -> Optional[int]:
        """
        返回最后一条 UNIT 在 body_lines 中的位置
        """
        for i in range(len(self.body_lines) - 1, -1, -1):
            if self.body_lines[i].ltype == LineType.UNIT:
                return i
        return None

    def append_unit_after_details(self, value: int, content: str):
        """
        尽量把 UNIT 插到明细区最后一条 UNIT 后面。
        如果没有明细，则追加到 body_lines 末尾。

        不主动处理空行，保持 body_lines 现有布局。
        """
        new_line = Line.make_unit(value, content)
        idx = self.last_detail_index()

        if idx is None:
            self.body_lines.append(new_line)
        else:
            self.body_lines.insert(idx + 1, new_line)

    def replace_summary_lines(self, new_summary_lines: List[Line]):
        """
        整体替换 summary_lines

        约束：
        - new_summary_lines 中应全部为 MONTH_SUM
        - 数量通常为 3 行
        """
        for ln in new_summary_lines:
            if ln.ltype != LineType.MONTH_SUM:
                raise ValueError("replace_summary_lines 只接受 MONTH_SUM 行")
        self.summary_lines = list(new_summary_lines)

    def rebuild_summary_lines(self):
        """
        回写 summary_lines：
        - 薪资：保留原值（如果存在）
        - 支出：根据 UNIT<0 计算
        - 结余：薪资 + 支出
        """

        # ===== 1. 找现有 summary =====
        s_income = self.find_summary("薪资")
        s_expense = self.find_summary("支出")
        s_balance = self.find_summary("结余")

        # ===== 2. 计算支出 =====
        expense = sum(ln.value for ln in self.unit_lines if ln.value < 0)

        # ===== 3. 薪资必须存在 =====
        if s_income is None:
            raise ValueError(f"{self.name} 缺少 '薪资'，无法计算结余")

        income = s_income.value
        balance = income + expense

        # ===== 4. 生成月前缀 =====
        month_no = self.month_no
        if month_no is None:
            raise ValueError(f"无法从 section 名称中解析月份: {self.name}")

        month_text = month_no[1:] + "月"

        # ===== 5. 回写（只改支出 & 结余）=====
        # 支出
        if s_expense:
            s_expense.value = expense
        else:
            self.summary_lines.append(
                Line(
                    raw="",
                    ltype=LineType.MONTH_SUM,
                    value=expense,
                    content=f"{month_text}支出"
                )
            )

        # 结余
        if s_balance:
            s_balance.value = balance
        else:
            self.summary_lines.append(
                Line(
                    raw="",
                    ltype=LineType.MONTH_SUM,
                    value=balance,
                    content=f"{month_text}结余"
                )
            )

        # ===== 6. 保证顺序（可选，但强烈建议）=====
        # 按：薪资 -> 支出 -> 结余 排序
        order = ["薪资", "支出", "结余"]

        def sort_key(ln: Line):
            for i, k in enumerate(order):
                if k in ln.content:
                    return i
            return 99

        self.summary_lines.sort(key=sort_key)

    def to_raw_lines(self) -> List[str]:
        return [ln.to_raw() for ln in self.lines]

    def to_raw(self) -> str:
        return "\n".join(self.to_raw_lines())

    def __repr__(self):
        return (
            f"Section(name={self.name!r}, "
            f"summary={len(self.summary_lines)}, "
            f"body={len(self.body_lines)}, "
            f"units={len(self.unit_lines)})"
        )
