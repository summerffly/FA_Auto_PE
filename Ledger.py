"""
Ledger.py
整个账本文件抽象
"""

from dataclasses import dataclass, field
from typing import List, Optional

from Line import Line, LineType
from Section import Section


@dataclass
class Ledger:
    """
    整个文件分为三部分：
    1. head_lines  - section 前面的内容
    2. sections    - 月度 sections
    3. tail_lines  - 最后一个 section 之后的内容
    """
    head_lines: List[Line] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    tail_lines: List[Line] = field(default_factory=list)

    @classmethod
    def parse_text(cls, text: str) -> "Ledger":
        """
        从完整文本解析 Ledger
        """
        raw_lines = text.splitlines()
        lines = [Line.parse(raw) for raw in raw_lines]
        return cls.parse_lines(lines)

    @classmethod
    def parse_file(cls, filepath: str, encoding: str = "utf-8") -> "Ledger":
        """
        从文件解析 Ledger
        """
        with open(filepath, "r", encoding=encoding) as f:
            text = f.read()
        return cls.parse_text(text)

    @classmethod
    def parse_lines(cls, lines: List[Line]) -> "Ledger":
        ledger = cls()

        current_section: Optional[Section] = None
        seen_section = False

        for ln in lines:
            if ln.ltype == LineType.MONTH_TITLE:
                if current_section is not None:
                    ledger.sections.append(current_section)
                current_section = Section(title_line=ln)
                seen_section = True
                continue

            if current_section is None:
                if not seen_section:
                    ledger.head_lines.append(ln)
                else:
                    ledger.tail_lines.append(ln)
            else:
                if cls._is_tail_line(ln):
                    ledger.sections.append(current_section)
                    current_section = None
                    ledger.tail_lines.append(ln)
                else:
                    current_section.add_line(ln)

        if current_section is not None:
            ledger.sections.append(current_section)

        return ledger

    @staticmethod
    def _is_tail_line(line: Line) -> bool:
        """
        定义哪些行应视为文件尾部内容
        当前规则：
        - TIMESTAMP
        - EOF
        """
        return line.ltype in (LineType.TIMESTAMP, LineType.EOF)

    @property
    def month_sections(self) -> List[Section]:
        return self.sections

    def get_section(self, name: str) -> Optional[Section]:
        """
        按 section 名称查找，例如 life.M02
        """
        for sec in self.sections:
            if sec.name == name:
                return sec
        return None

    def has_section(self, name: str) -> bool:
        return self.get_section(name) is not None

    def add_section(self, section: Section):
        self.sections.append(section)

    def section_names(self) -> List[str]:
        return [sec.name for sec in self.sections]

    def all_lines(self) -> List[Line]:
        result: List[Line] = []
        result.extend(self.head_lines)
        for sec in self.sections:
            result.extend(sec.lines)
        result.extend(self.tail_lines)
        return result

    def rebuild_section_summary(self, name: str):
        """
        重算指定 section 的 summary 并回写
        """
        sec = self.get_section(name)
        if sec is None:
            raise ValueError(f"section 不存在: {name}")

        if not hasattr(sec, "rebuild_summary_lines"):
            raise AttributeError(
                "Section 缺少 rebuild_summary_lines() 方法，请先在 Section.py 中实现"
            )

        sec.rebuild_summary_lines()

    def rebuild_all_summaries(self):
        """
        重算所有 section 的 summary 并回写
        """
        for sec in self.sections:
            if not hasattr(sec, "rebuild_summary_lines"):
                raise AttributeError(
                    "Section 缺少 rebuild_summary_lines() 方法，请先在 Section.py 中实现"
                )
            sec.rebuild_summary_lines()

    def validate_section_summary(self, name: str) -> bool:
        """
        校验指定 section 当前 summary 是否正确
        """
        sec = self.get_section(name)
        if sec is None:
            raise ValueError(f"section 不存在: {name}")

        income = sum(ln.value for ln in sec.unit_lines if ln.value > 0)
        expense = sum(ln.value for ln in sec.unit_lines if ln.value < 0)
        balance = income + expense

        s_income = sec.find_summary("薪资")
        s_expense = sec.find_summary("支出")
        s_balance = sec.find_summary("结余")

        if s_income is None or s_expense is None or s_balance is None:
            return False

        return (
            s_income.value == income and
            s_expense.value == expense and
            s_balance.value == balance
        )

    def validate_all_summaries(self) -> bool:
        """
        校验所有 section 的 summary 是否正确
        """
        for sec in self.sections:
            if not self.validate_section_summary(sec.name):
                return False
        return True

    def to_raw_lines(self) -> List[str]:
        return [ln.to_raw() for ln in self.all_lines()]

    def to_raw(self) -> str:
        return "\n".join(self.to_raw_lines())

    def dump(self):
        """
        调试输出
        """
        print("=== Ledger ===")
        print(f"head_lines: {len(self.head_lines)}")
        print(f"sections  : {len(self.sections)}")
        print(f"tail_lines: {len(self.tail_lines)}")
        print()

        for i, sec in enumerate(self.sections, 1):
            print(f"[{i}] {sec.name}")
            print(f"    summaries : {len(sec.summary_lines)}")
            print(f"    units     : {len(sec.unit_lines)}")
            print(f"    total_unit: {sec.total_units()}")

    def save(self, filepath: str, encoding: str = "utf-8"):
        """
        回写到 markdown 文件
        """
        with open(filepath, "w", encoding=encoding) as f:
            f.write(self.to_raw())

    def save_as(self, filepath: str, encoding: str = "utf-8"):
        """
        另存为新文件
        """
        self.save(filepath, encoding=encoding)

    def __repr__(self):
        return (
            f"Ledger(head={len(self.head_lines)}, "
            f"sections={len(self.sections)}, "
            f"tail={len(self.tail_lines)})"
        )
