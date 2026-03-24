"""
Ledger.py
整个账本文件抽象
"""

from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType
from Section import BaseSection, make_section
from Block import BaseBlock, TailBlock, make_block, make_tail_block


@dataclass
class Ledger:
    """
    整个文件分为三部分：
    1. header  - 第一个 section 前面的内容
    2. segments    - 月度 segments
    3. tail_lines  - 最后一个 section 之后的内容
    """
    header: List[Line] = field(default_factory=list)
    segments: List[BaseSection] = field(default_factory=list)
    total: Optional[BaseBlock] = None
    tail: Optional[TailBlock] = None

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
        current_section: Optional[BaseSection] = None
        seen_section = False
        tail_lines: List[Line] = []  # 新增：临时存储tail行

        for ln in lines:
            if ln.ltype == LineType.MONTH_TITLE or ln.ltype == LineType.SUB_TAG:
                if current_section is not None:
                    ledger.segments.append(current_section)
                
                current_section = make_section(ln)
                seen_section = True
                continue
            
            if current_section is None:
                if not seen_section:
                    ledger.header.append(ln)
                else:
                    # 收集tail行，最后统一创建TailBlock
                    tail_lines.append(ln)
            else:
                if cls._is_tail_line(ln):
                    ledger.segments.append(current_section)
                    current_section = None
                    tail_lines.append(ln)  # 添加到tail_lines
                else:
                    current_section.add_line(ln)
        
        if current_section is not None:
            ledger.segments.append(current_section)
        
        # 最后统一创建TailBlock
        if tail_lines:
            ledger.tail = make_tail_block(tail_lines)
        
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
    def month_segments(self) -> List[BaseSection]:
        """
        所有月度 section
        """
        return self.segments

    def get_section(self, name: str) -> Optional[BaseSection]:
        """
        按 section 名称查找，例如 life.M02 / DGtler.M03
        """
        for sec in self.segments:
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
        self.segments.append(section)

    def section_names(self) -> List[str]:
        """
        返回所有 section 名称
        """
        return [sec.name for sec in self.segments]

    def all_lines(self) -> List[Line]:
        """
        返回整个文件的所有行
        """
        result: List[Line] = []
        result.extend(self.header)

        for sec in self.segments:
            result.extend(sec.lines)

        if self.tail:
            result.extend(self.tail.to_lines())
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
        for sec in self.segments:
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
        return all(sec.validate_summary() for sec in self.segments)

    # -------- 调试 -------- #

    def dump(self):
        """
        调试输出
        """
        print("=== Ledger ===")
        print(f"header: {len(self.header)}")
        print(f"segments  : {len(self.segments)}")
        print(f"tail: {len(self.tail.to_lines()) if self.tail else 0}")
        print()

        for i, sec in enumerate(self.segments, 1):
            print(f"[{i}] {sec.name}")
            print(f"    class      : {sec.__class__.__name__}")
            print(f"    summaries  : {len(sec.summary_lines)}")
            print(f"    body       : {len(sec.body_lines)}")
            print(f"    units      : {len(sec.unit_lines)}")
            print(f"    blanks     : {len(sec.blank_lines)}")
            print(f"    total_unit : {sec.total_units()}")

    def __repr__(self):
        return (
            f"Ledger(head={len(self.header)}, "
            f"segments={len(self.segments)}, "
            f"tail={len(self.tail.to_lines()) if self.tail else 0})"
        )
