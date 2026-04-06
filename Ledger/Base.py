# File:        Ledger/Base.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-04-06
# Description: Ledger抽象基类

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from colorama import Fore, Style

from Line import Line, LineType
from Segment import (
    BaseSection, 
    TotalMiniSection, 
    TailBlock, make_tail_block
)
from .Mixin import LedgerMixin


# ======================================== #
#    BaseLedger
# ======================================== #

@dataclass
class BaseLedger(LedgerMixin, ABC):
    header: List[Line] = field(default_factory=list)
    segments: List[BaseSection] = field(default_factory=list)
    total_seg: Optional[TotalMiniSection] = None
    tail: Optional[TailBlock] = None

    # ----- 解析方法 -------------------- #

    @classmethod
    def parse_lines(cls, lines: List[Line]) -> "BaseLedger":
        parser = cls._create_parser(lines)
        return parser.parse()

    @classmethod
    @abstractmethod
    def _create_parser(cls, lines: List[Line]) -> "_LedgerParser":
        raise NotImplementedError

    # ----- 数据访问方法 -------------------- #

    @property
    def seg_names(self) -> List[str]:
        return [seg.name for seg in self.segments]

    # ----- 操作 -------------------- #

    @abstractmethod
    def rebuild(self):
        raise NotImplementedError

    def checksum(self) -> bool:
        return all(seg.checksum() for seg in self.segments)

    # ----- 序列化 -------------------- #

    def to_lines(self) -> List[Line]:
        all_lines: List[Line] = []
        all_lines.extend(self.header)
        for seg in self.segments:
            all_lines.extend(seg.to_lines())
        if self.total_seg:
            all_lines.extend(self.total_seg.to_lines())
        if self.tail:
            all_lines.extend(self.tail.to_lines())
        return all_lines

    # ----- 验证 -------------------- #

    @abstractmethod
    def validate(self) -> List[str]:
        raise NotImplementedError
    
    # ----- Debug -------------------- #

    def dump(self):
        print("=== Ledger Dump ===")
        print(f"class     : {self.__class__.__name__}")
        print(f"header    : {len(self.header)}")
        print(f"segments  : {len(self.segments)}")
        print(f"total_seg : {self.total_seg.name if self.total_seg else 'None'}")
        print(f"tail      : {len(self.tail.to_lines()) if self.tail else 0}")
        print()

        for i, seg in enumerate(self.segments, 1):
            print(f"[Segment {i}] {seg.name}")
            print(f"   class  : {seg.__class__.__name__}")
            print(f"   sum    : {len(seg.sum_lines)}")
            print(f"   body   : {len(seg.body_lines)}")
            print(f"   units  : {len(seg.unit_lines)}")
            print(f"   blanks : {len(seg.blank_lines)}")
            print()

        if self.total_seg:
            print(f"[Total] {self.total_seg.name}")
            print(f"   class : {self.total_seg.__class__.__name__}")
            print(f"   lines : {len(self.total_seg.sum_lines)}")
            print()

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"header={len(self.header)}, "
            f"segments={len(self.segments)}, "
            f"total_seg={self.total_seg.name if self.total_seg else 'None'}, "
            f"tail={len(self.tail.to_lines()) if self.tail else 0})"
        )


# ======================================== #
#    BaseLedger Parser
# ======================================== #

@dataclass
class _BaseLedgerParser(ABC):
    lines: List[Line]
    ledger: Optional[BaseLedger] = field(default=None)
    index: int = 0
    curr_head: Optional[Line] = None
    curr_lines: List[Line] = field(default_factory=list)
    
    def parse(self) -> BaseLedger:
        """ 通用解析流程 """
        while self.index < len(self.lines):
            line = self.lines[self.index]
            
            # 处理新分段
            if line.type in (LineType.LIFE_TITLE, LineType.MONTH_TITLE, LineType.COLLECT_TITLE, LineType.TOTAL_TITLE):
                self._finish_current_segment()
                self._start_new_segment(line)
                continue

            # 处理尾部行
            if line.type in (LineType.TIMESTAMP, LineType.EOF):
                self._finish_current_segment()
                self._parse_tail()
                break
                
            # 处理普通行
            self._process_normal_line(line)
            self.index += 1
        
        return self.ledger
    
    def _process_normal_line(self, line: Line):
        """ 处理普通行 """
        if self.curr_head is None:
            self.ledger.header.append(line)
        else:
            self.curr_lines.append(line)

    def _start_new_segment(self, title_line: Line):
        """ 开始新分段 """
        self.curr_head = title_line
        self.curr_lines = []
        self.index += 1

    @abstractmethod
    def _finish_current_segment(self):
        """ 结束当前分段 """
        raise NotImplementedError

    def _parse_tail(self):
        """ 解析尾部 """
        tail_lines = []
        while self.index < len(self.lines):
            tail_lines.append(self.lines[self.index])
            self.index += 1
        
        if tail_lines:
            self.ledger.tail = make_tail_block(tail_lines)
