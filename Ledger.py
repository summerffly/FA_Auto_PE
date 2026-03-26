# File:        Ledger.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-22
# LastEdit:    2026-03-27
# Description: 独立账本对象

from dataclasses import dataclass, field
from typing import List, Optional
from colorama import Fore, Style
from Line import Line, LineType
from Section import BaseSection, make_section
from MiniSection import BaseMiniSection, make_minisection
from Block import TailBlock, make_tail_block


# ======================================== #
#    Ledger
# ======================================== #

@dataclass
class Ledger:
    header: List[Line] = field(default_factory=list)
    segments: List[BaseSection] = field(default_factory=list)
    total: Optional[BaseMiniSection] = None
    tail: Optional[TailBlock] = None

    # ----- 解析方法 -------------------- #

    @classmethod
    def parse_file(cls, filepath: str, encoding: str = "utf-8") -> "Ledger":
        with open(filepath, "r", encoding=encoding) as f:
            text = f.read()
        return cls.parse_text(text)

    @classmethod
    def parse_text(cls, text: str) -> "Ledger":
        raw_lines = text.splitlines()
        lines = [Line.parse(raw) for raw in raw_lines]
        return cls.parse_lines(lines)
    
    @classmethod
    def parse_lines(cls, lines: List[Line]) -> "Ledger":
        parser = _LedgerParser(lines)
        return parser.parse()

    # ----- 数据访问方法 -------------------- #

    @property
    def segment_names(self) -> List[str]:
        return [seg.name for seg in self.segments]

    def get_segment(self, name: str) -> Optional[BaseSection]:
        for seg in self.segments:
            if seg.name == name:
                return seg
        return None
    
    def get_all_lines(self) -> List[Line]:
        all_lines: List[Line] = []
        all_lines.extend(self.header)
        for seg in self.segments:
            all_lines.extend(seg.lines)
        if self.total:
            all_lines.extend(self.total.lines)
        if self.tail:
            all_lines.extend(self.tail.lines)
        return all_lines

    # ----- 汇总操作 -------------------- #

    def rebuild_segment_summary(self, name: str):
        seg = self.get_segment(name)
        if seg is None:
            raise ValueError(f"section 不存在: {name}")
        seg.rebuild_summary()

    def validate_segment_summary(self, name: str) -> bool:
        seg = self.get_segment(name)
        if seg is None:
            raise ValueError(f"segment 不存在: {name}")
        return seg.validate_summary()

    def validate_all_summaries(self) -> bool:
        return all(seg.validate_summary() for seg in self.segments)

    def validate_struct(self) -> List[str]:
        errors = []
        
        names = self.segment_names
        if len(names) != len(set(names)):
            errors.append("存在重复 Segment")

        for seg in self.segments:
            seg_errors = seg.validate_struct()
            errors.extend([f"segment '{seg.name}': {err}" for err in seg_errors])

        if self.total:
            total_errors = self.total.validate_struct()
            errors.extend([f"total: {err}" for err in total_errors])
        
        if self.tail:
            tail_errors = self.tail.validate_struct()
            errors.extend([f"tail: {err}" for err in tail_errors])
        
        return errors

    def rebuild_total(self):
        if self.total is None:
            return None
        
        total_sum = 0
        for sec in self.segments:
            segment_sum = sec.get_summary()
            total_sum += segment_sum

        self.total.set_value(total_sum)

    def rebuild_ledger(self):
        for seg in self.segments:
            seg.rebuild_summary()
        if self.total:
            self.rebuild_total()

    def get_total_value(self) -> Optional[int]:
        if self.total is None:
            return None
        else:
            return self.total.value

    def get_all_sections_sum(self) -> int:
        total_sum = 0
        for seg in self.segments:
            total_sum += seg.get_summary()
        return total_sum

    def validate_total(self) -> bool:
        if self.total is None:
            return True
        
        total_value = self.get_total_value()
        if total_value is None:
            return False
        
        all_sections_sum = self.get_all_sections_sum()
        return total_value == all_sections_sum

    # ----- 序列化方法 -------------------- #

    def to_raw_lines(self) -> List[str]:
        return [ln.to_raw() for ln in self.get_all_lines()]

    def to_raw(self) -> str:
        lines = self.to_raw_lines()
        result = "\n".join(lines)
        if not result.endswith("\n"):
            result += "\n"
        return result

    def save(self, filepath: str, encoding: str = "utf-8"):
        text = self.to_raw()
        with open(filepath, "w", encoding=encoding) as f:
            f.write(text)

    def save_as(self, filepath: str, encoding: str = "utf-8"):
        self.save(filepath, encoding)

    # ----- Dump -------------------- #

    def dump(self):
        print("=== Ledger Dump ===")
        print(f"header   : {len(self.header)}")
        print(f"segments : {len(self.segments)}")
        if self.total:
            print(f"total    : {len(self.total.lines) if self.total else 'None'}")
        print(f"tail     : {len(self.tail.lines) if self.tail else 0}")
        print()

        for i, sec in enumerate(self.segments, 1):
            print(f"[Segment {i}] {sec.name}")
            print(f"   class     : {sec.__class__.__name__}")
            print(f"   summaries : {len(sec.summary_lines)}")
            print(f"   body      : {len(sec.body_lines)}")
            print(f"   units     : {len(sec.unit_lines)}")
            print(f"   blanks    : {len(sec.blank_lines)}")
            print()

        if self.total:
            print(f"[Total] {self.total.name}")
            print(f"   class : {self.total.__class__.__name__}")
            print(f"   lines : {len(self.total.summary_lines)}")
            print()

    def __repr__(self):
        return (
            f"Ledger(header={len(self.header)}, "
            f"segments={len(self.segments)}, "
            f"total={self.total.name if self.total else 'None'}, "
            f"tail={len(self.tail.lines) if self.tail else 0})"
        )


# ======================================== #
#    Ledger Parser
# ======================================== #

@dataclass
class _LedgerParser:
    lines: List[Line]
    ledger: Ledger = field(default_factory=Ledger)
    index: int = 0
    curr_head: Optional[Line] = None
    curr_lines: List[Line] = field(default_factory=list)
    
    def parse(self) -> Ledger:
        while self.index < len(self.lines):
            line = self.lines[self.index]
            
            # 处理新分段
            if line.ltype in (LineType.MONTH_TITLE, LineType.SUB_TAG, LineType.TOTAL):
                self._finish_current_segment()
                self._start_new_segment(line)
                continue

            # 处理尾部行
            if line.ltype in (LineType.TIMESTAMP, LineType.EOF):
                self._finish_current_segment()
                self._parse_tail()
                break
                
            # 处理普通行
            self._process_normal_line(line)
            self.index += 1
        
        return self.ledger
    
    def _process_normal_line(self, line: Line):
        if self.curr_head is None:
            self.ledger.header.append(line)
        else:
            self.curr_lines.append(line)

    def _start_new_segment(self, head_line: Line):
        self.curr_head = head_line
        self.curr_lines = []
        self.index += 1

    def _finish_current_segment(self):
        if self.curr_head is None and not self.curr_lines:
            return
        
        if self.curr_head is None:
            pass
        elif self.curr_head.ltype == LineType.TOTAL:
            self.ledger.total = make_minisection(self.curr_head, self.curr_lines)
        else:
            section = make_section(self.curr_head, self.curr_lines)
            self.ledger.segments.append(section)
        
        # 重置状态
        self.curr_head = None
        self.curr_lines = []

    def _parse_tail(self):
        tail_lines = []
        while self.index < len(self.lines):
            tail_lines.append(self.lines[self.index])
            self.index += 1
        
        if tail_lines:
            self.ledger.tail = make_tail_block(tail_lines)
