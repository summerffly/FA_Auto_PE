# File:        Ledger/Base.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-03-30
# Description: Ledger抽象基类

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from colorama import Fore, Style

from Line import Line, LineType
from Segment import (
    BaseSection, 
    BaseMiniSection, 
    TailBlock, make_tail_block
)


# ======================================== #
#    BaseLedger
# ======================================== #

@dataclass
class BaseLedger(ABC):
    header: List[Line] = field(default_factory=list)
    segments: List[BaseSection] = field(default_factory=list)
    total: Optional[BaseMiniSection] = None
    tail: Optional[TailBlock] = None

    # ----- 工厂方法 -------------------- #

    @classmethod
    def parse_file(cls, filepath: str, encoding: str = "utf-8") -> "BaseLedger":
        """ 从文件解析账本 """
        with open(filepath, "r", encoding=encoding) as f:
            text = f.read()
        return cls.parse_text(text)

    @classmethod
    def parse_text(cls, text: str) -> "BaseLedger":
        """ 从文本解析账本 """
        raw_lines = text.splitlines()
        lines = [Line.parse(raw) for raw in raw_lines]
        return cls.parse_lines(lines)

    @classmethod
    def parse_lines(cls, lines: List[Line]) -> "BaseLedger":
        """ 从Line对象列表解析账本 """
        parser = cls._create_parser(lines)
        return parser.parse()

    @classmethod
    @abstractmethod
    def _create_parser(cls, lines: List[Line]) -> "_LedgerParser":
        """ 创建本类型解析器 """
        raise NotImplementedError

    # ----- 数据访问方法 -------------------- #

    @property
    def segment_names(self) -> List[str]:
        """ 获取所有分段名称 """
        return [seg.name for seg in self.segments]

    def get_segment(self, name: str) -> Optional[BaseSection]:
        """ 获取指定分段 """
        for seg in self.segments:
            if seg.name == name:
                return seg
        return None

    def get_segment_line(self, name: str, key: str) -> Optional[Line]:
        """ 获取指定分段+行 """
        seg = self.get_segment(name)
        if seg is None:
            return None
        
        for ln in seg.body_lines:
            if ln.ltype == LineType.UNIT and ln.key == key:
                return ln
        return None

    def mod_segment_line(self, name: str, key: str, new_value: int) -> bool:
        """ 修改指定分段+行 """
        ln = self.get_segment_line(name, key)
        if ln is None:
            return False
        ln.value = new_value
        return True

    # ----- 汇总操作 -------------------- #

    def rebuild_segment_summary(self, name: str):
        """ 重建指定分段汇总 """
        seg = self.get_segment(name)
        if seg is None:
            raise ValueError(f"segment 不存在: {name}")
        seg.rebuild_summary()

    def validate_segment_summary(self, name: str) -> bool:
        """ 验证指定分段汇总 """
        seg = self.get_segment(name)
        if seg is None:
            raise ValueError(f"segment 不存在: {name}")
        return seg.validate_summary()

    def validate_all_summaries(self) -> bool:
        """ 验证所有分段汇总 """
        return all(seg.validate_summary() for seg in self.segments)

    def get_all_segments_sum(self) -> int:
        """获取所有分段的总和"""
        total_sum = 0
        for seg in self.segments:
            total_sum += seg.get_summary()
        return total_sum

    @abstractmethod
    def rebuild_ledger(self):
        """重建整个账本（抽象方法）"""
        raise NotImplementedError

    # ----- 序列化方法 -------------------- #

    def update_timestamp(self):
        """更新时间戳"""
        if self.tail:
            self.tail.update_timestamp()

    def to_lines(self) -> List[Line]:
        """转换为Line对象列表"""
        all_lines: List[Line] = []
        all_lines.extend(self.header)
        for seg in self.segments:
            all_lines.extend(seg.lines)
        if self.total:
            all_lines.extend(self.total.lines)
        if self.tail:
            all_lines.extend(self.tail.lines)
        return all_lines

    def to_raw(self) -> str:
        """转换为原始文本"""
        lines = self.to_lines()
        raw_lines = [ln.to_raw() for ln in lines]
        raw_text = "\n".join(raw_lines)
        if not raw_text.endswith("\n"):
            raw_text += "\n"
        return raw_text

    def save(self, filepath: str, encoding: str = "utf-8"):
        """保存到文件"""
        text = self.to_raw()
        with open(filepath, "w", encoding=encoding) as f:
            f.write(text)

    def save_as(self, filepath: str, encoding: str = "utf-8"):
        """另存为文件"""
        self.save(filepath, encoding)

    # ----- 验证和调试 -------------------- #

    def validate_struct(self) -> List[str]:
        """验证账本结构"""
        errors = []
        
        # 检查重复的Segment名称
        names = self.segment_names
        if len(names) != len(set(names)):
            errors.append("存在重复Segment")

        # 验证每个分段
        for seg in self.segments:
            seg_errors = seg.validate_struct()
            errors.extend([f"segment '{seg.name}': {err}" for err in seg_errors])

        # 验证总计
        if self.total:
            total_errors = self.total.validate_struct()
            errors.extend([f"total: {err}" for err in total_errors])
        
        # 验证尾部
        if self.tail:
            tail_errors = self.tail.validate_struct()
            errors.extend([f"tail: {err}" for err in tail_errors])
        
        return errors

    def dump(self):
        """打印账本结构"""
        print("=== Ledger Dump ===")
        print(f"Type     : {self.__class__.__name__}")
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
            f"{self.__class__.__name__}("
            f"header={len(self.header)}, "
            f"segments={len(self.segments)}, "
            f"total={self.total.name if self.total else 'None'}, "
            f"tail={len(self.tail.lines) if self.tail else 0})"
        )


# ======================================== #
#    BaseLedger Parser
# ======================================== #

@dataclass
class _BaseLedgerParser(ABC):
    lines: List[Line]
    ledger: BaseLedger = field(default_factory=lambda: None)
    index: int = 0
    curr_head: Optional[Line] = None
    curr_lines: List[Line] = field(default_factory=list)
    
    def parse(self) -> BaseLedger:
        """ 通用解析流程 """
        while self.index < len(self.lines):
            line = self.lines[self.index]
            
            # 处理新分段
            if line.ltype in (LineType.LIFE_TITLE, LineType.MONTH_TITLE, LineType.SUB_TAG, LineType.TOTAL):
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
        """ 处理普通行 """
        if self.curr_head is None:
            self.ledger.header.append(line)
        else:
            self.curr_lines.append(line)

    def _start_new_segment(self, head_line: Line):
        """ 开始新分段 """
        self.curr_head = head_line
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
