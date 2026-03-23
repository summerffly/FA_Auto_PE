"""
Ledger.py
整个账本文件抽象
"""

from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType
from Section import BaseSection, make_section_by_title_line


@dataclass
class Ledger:
    """
    整个文件分为三部分：
    1. head_lines  - 第一个 section 前面的内容
    2. sections    - 月度 sections
    3. tail_lines  - 最后一个 section 之后的内容
    """
    head_lines: List[Line] = field(default_factory=list)
    sections: List[BaseSection] = field(default_factory=list)
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
        """
        从 Line 列表解析 Ledger

        规则：
        - MONTH_TITLE 开启一个新的 Section
        - Section 类型由标题决定（通过工厂函数）
        - TIMESTAMP / EOF 视为 tail_lines 起点
        """
        ledger = cls()

        current_section: Optional[BaseSection] = None
        seen_section = False

        for ln in lines:
            if ln.ltype == LineType.MONTH_TITLE or ln.ltype == LineType.SUB_TAG:
                if current_section is not None:
                    ledger.sections.append(current_section)

                current_section = make_section_by_title_line(ln)
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
    def month_sections(self) -> List[BaseSection]:
        """
        所有月度 section
        """
        return self.sections

    def get_section(self, name: str) -> Optional[BaseSection]:
        """
        按 section 名称查找，例如 life.M02 / DGtler.M03
        """
        for sec in self.sections:
            if sec.name == name:
                return sec
        return None

    def has_section(self, name: str) -> bool:
        """
        判断 section 是否存在
        """
        return self.get_section(name) is not None

    def add_section(self, section: BaseSection):
        """
        追加一个新的 section
        """
        self.sections.append(section)

    def section_names(self) -> List[str]:
        """
        返回所有 section 名称
        """
        return [sec.name for sec in self.sections]

    def all_lines(self) -> List[Line]:
        """
        返回整个文件的所有行
        """
        result: List[Line] = []
        result.extend(self.head_lines)

        for sec in self.sections:
            result.extend(sec.lines)

        result.extend(self.tail_lines)
        return result

    def to_raw_lines(self) -> List[str]:
        """
        序列化为 markdown 行列表
        """
        return [ln.to_raw() for ln in self.all_lines()]

    def to_raw(self) -> str:
        """
        序列化为完整 markdown 文本
        """
        return "\n".join(self.to_raw_lines())

    def save(self, filepath: str, encoding: str = "utf-8"):
        """
        回写到 markdown 文件
        """
        text = self.to_raw()
        with open(filepath, "w", encoding=encoding) as f:
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")

    def save_as(self, filepath: str, encoding: str = "utf-8"):
        """
        另存为新文件
        """
        self.save(filepath, encoding=encoding)

    # -------- summary 重建 / 校验 -------- #

    def rebuild_section_summary(self, name: str):
        """
        重建指定 section 的 summary
        """
        sec = self.get_section(name)
        if sec is None:
            raise ValueError(f"section 不存在: {name}")

        sec.rebuild_summary()

    def rebuild_all_summaries(self):
        """
        重建所有 section 的 summary
        """
        for sec in self.sections:
            sec.rebuild_summary()

    def validate_section_summary(self, name: str) -> bool:
        """
        校验指定 section 的 summary 是否正确
        """
        sec = self.get_section(name)
        if sec is None:
            raise ValueError(f"section 不存在: {name}")

        return sec.validate_summary()

    def validate_all_summaries(self) -> bool:
        """
        校验所有 section 的 summary 是否正确
        """
        return all(sec.validate_summary() for sec in self.sections)

    # -------- 调试 -------- #

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
            print(f"    class      : {sec.__class__.__name__}")
            print(f"    summaries  : {len(sec.summary_lines)}")
            print(f"    body       : {len(sec.body_lines)}")
            print(f"    units      : {len(sec.unit_lines)}")
            print(f"    blanks     : {len(sec.blank_lines)}")
            print(f"    total_unit : {sec.total_units()}")

    def __repr__(self):
        return (
            f"Ledger(head={len(self.head_lines)}, "
            f"sections={len(self.sections)}, "
            f"tail={len(self.tail_lines)})"
        )
