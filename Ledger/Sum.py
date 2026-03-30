# File:        SumLedger.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-29
# Description: 汇总账本对象

from dataclasses import dataclass, field
from typing import List, Optional, Union
from colorama import Fore, Style

from Line import Line, LineType
from Segment import (
    BaseMiniSection, make_minisection, 
    SummarySection, make_summary, 
    BaseBlock, TailBlock, make_tail_block
)


# ======================================== #
#    SumLedger
# ======================================== #

@dataclass
class SumLedger:
    header: List[Line] = field(default_factory=list)
    segments: List[BaseMiniSection] = field(default_factory=list)
    summary: Optional[SummarySection] = None
    tail: Optional[TailBlock] = None

    # ----- 解析方法 -------------------- #

    @classmethod
    def parse_file(cls, filepath: str, encoding: str = "utf-8") -> "SumLedger":
        with open(filepath, "r", encoding=encoding) as f:
            text = f.read()
        return cls.parse_text(text)

    @classmethod
    def parse_text(cls, text: str) -> "SumLedger":
        raw_lines = text.splitlines()
        lines = [Line.parse(raw) for raw in raw_lines]
        return cls.parse_lines(lines)

    @classmethod
    def parse_lines(cls, lines: List[Line]) -> "SumLedger":
        parser = _SumLedgerParser(lines)
        return parser.parse()

    # ----- 数据访问方法 -------------------- #

    def get_segment_names(self) -> List[str]:
        """ 获取所有分段名称 """
        return [blk.name for blk in self.segments]

    def find_segment(self, name: str) -> Optional[Union[BaseBlock, BaseMiniSection]]:
        """ 按名称查找分段 """
        for blk in self.segments:
            if blk.name == name:
                return blk
        return None

    def add_segment(self, segment: BaseMiniSection):
        """ 添加新分段 """
        self.segments.append(segment)

    # ----- 验证方法 -------------------- #

    def validate(self) -> bool:
        """验证所有区块"""
        return all(blk.validate() for blk in self.segments)

    # ----- 序列化方法 -------------------- #

    def update_timestamp(self):
        if self.tail:
            self.tail.update_timestamp()

    def to_lines(self) -> List[Line]:
        all_lines: List[Line] = []
        all_lines.extend(self.header)
        for seg in self.segments:
            all_lines.extend(seg.lines)
        if self.summary:
            all_lines.extend(self.summary.to_lines())
        if self.tail:
            all_lines.extend(self.tail.lines)
        return all_lines

    def to_raw(self) -> str:
        lines = self.to_lines()
        raw_lines = [ln.to_raw() for ln in lines]
        raw_text = "\n".join(raw_lines)
        if not raw_text.endswith("\n"):
            raw_text += "\n"
        return raw_text

    def save(self, filepath: str, encoding: str = "utf-8"):
        text = self.to_raw()
        with open(filepath, "w", encoding=encoding) as f:
            f.write(text)

    def save_as(self, filepath: str, encoding: str = "utf-8"):
        self.save(filepath, encoding)

    # ----- Debug -------------------- #

    def validate_struct(self) -> List[str]:
        """验证账本结构，返回错误信息列表"""
        errors = []
        
        # 检查重复的分段名称
        names = self.get_segment_names()
        if len(names) != len(set(names)):
            errors.append("存在重复的分段名称")

        # 逐个检查每个 section 的结构
        for sec in self.segments:
            sec_errors = sec.validate_struct()
            errors.extend([f"section '{sec.name}': {err}" for err in sec_errors])
        
        # 检查 tail 是否包含必要元素
        if self.tail:
            tail_errors = self.tail.validate_struct()
            errors.extend([f"tail: {err}" for err in tail_errors])
        
        return errors

    def dump(self):
        """ 打印账本结构信息 """
        print("=== SumLedger Dump ===")
        
        print("\n[HEAD]")
        for ln in self.header:
            print(f"  {ln.raw}")
        
        print(f"\n[SEGMENTS]")
        for idx, blk in enumerate(self.segments, 1):
            print(f"  Segment {idx}: {blk.name} ({blk.__class__.__name__})")
            for ln in blk.lines:
                print(f"    {ln.raw}")
        
        print("\n[SUMMARY]")
        if self.summary:
            for ln in self.summary.to_lines():
                print(f"  {ln.raw}")
        else:
            print("  None")
        
        print("\n[TAIL]")
        if self.tail:
            for ln in self.tail.lines:
                print(f"  {ln.raw}")
        else:
            print("  None")

    def __repr__(self):
        return (
            f"SumLedger(header={len(self.header)}, "
            f"segments={len(self.segments)}, "
            f"summary={self.summary.name if self.summary else 'None'}, "
            f"tail={len(self.tail.lines) if self.tail else 0})"
        )


# ======================================== #
#    SumLedger Parser
# ======================================== #

@dataclass
class _SumLedgerParser:
    lines: List[Line]
    ledger: SumLedger = field(default_factory=SumLedger)
    index: int = 0
    curr_head: Optional[Line] = None
    curr_lines: List[Line] = field(default_factory=list)
    
    def parse(self) -> SumLedger:
        while self.index < len(self.lines):
            line = self.lines[self.index]
            
            # 处理新分段
            if line.ltype in (LineType.MONTH_TITLE, LineType.SUB_TITLE, LineType.SUMMARY):
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
        elif self.curr_head.ltype == LineType.SUMMARY:
            self.ledger.summary = make_summary(self.curr_head, self.curr_lines)
        else:
            minisection = make_minisection(self.curr_head, self.curr_lines)
            self.ledger.segments.append(minisection)
        
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
