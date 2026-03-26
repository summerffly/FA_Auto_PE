# File:        Ledger.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-22
# LastEdit:    2026-03-26
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
        """从文件解析 Ledger"""
        with open(filepath, "r", encoding=encoding) as f:
            text = f.read()
        return cls.parse_text(text)

    @classmethod
    def parse_text(cls, text: str) -> "Ledger":
        """从文本解析 Ledger"""
        raw_lines = text.splitlines()
        lines = [Line.parse(raw) for raw in raw_lines]
        return cls.parse_lines(lines)
    
    @classmethod
    def parse_lines(cls, lines: List[Line]) -> "Ledger":
        """从行列表解析 Ledger - 简洁入口"""
        parser = _LedgerParser(lines)
        return parser.parse()

    # ----- 数据访问方法 -------------------- #

    @property
    def all_segments(self) -> List[BaseSection]:
        """获取所有 segments"""
        return self.segments

    def get_section(self, name: str) -> Optional[BaseSection]:
        """按名称查找 section"""
        for sec in self.segments:
            if sec.name == name:
                return sec
        return None

    def has_section(self, name: str) -> bool:
        """判断 section 是否存在"""
        return self.get_section(name) is not None

    def add_section(self, section: BaseSection):
        """添加新的 section"""
        self.segments.append(section)

    def section_names(self) -> List[str]:
        """获取所有 section 名称"""
        return [sec.name for sec in self.segments]

    def all_lines(self) -> List[Line]:
        """获取所有行（用于序列化）"""
        out_lines: List[Line] = []
        out_lines.extend(self.header)
        
        for sec in self.segments:
            out_lines.extend(sec.lines)
            
        if self.total:
            out_lines.extend(self.total.to_lines())
            
        if self.tail:
            out_lines.extend(self.tail.to_lines())
            
        return out_lines

    # ----- 汇总操作 -------------------- #

    def rebuild_section_summary(self, name: str):
        """重建指定 section 的汇总"""
        sec = self.get_section(name)
        if sec is None:
            raise ValueError(f"section 不存在: {name}")
        sec.rebuild_summary()

    def rebuild_all_summaries(self):
        """重建所有 sections 的汇总"""
        for sec in self.segments:
            sec.rebuild_summary()

    def validate_section_summary(self, name: str) -> bool:
        """验证指定 section 的汇总"""
        sec = self.get_section(name)
        if sec is None:
            raise ValueError(f"section 不存在: {name}")
        return sec.validate_summary()

    def validate_all_summaries(self) -> bool:
        """验证所有 sections 的汇总"""
        return all(sec.validate_summary() for sec in self.segments)

    def validate_total(self) -> bool:
        """验证 Total 区块"""
        if self.total is None:
            return True
        # TotalMiniSection 需要有 validate 方法
        # 如果没有，可以添加一个默认实现或使用 hasattr 检查
        if hasattr(self.total, 'validate'):
            return self.total.validate()
        return True

    def validate_structure(self) -> List[str]:
        errors = []
        
        # 检查重复的 section 名称
        names = self.section_names()
        if len(names) != len(set(names)):
            errors.append("存在重复的 section 名称")

        # 逐个检查每个 section 的结构
        for sec in self.segments:
            sec_errors = sec.validate_structure()
            errors.extend([f"section '{sec.name}': {err}" for err in sec_errors])

        # 检查 total 是否存在且有效
        if self.total:
            total_errors = self.total.validate_structure()
            errors.extend([f"total: {err}" for err in total_errors])
        
        # 检查 tail 是否包含必要元素
        if self.tail:
            tail_errors = self.tail.validate_structure()
            errors.extend([f"tail: {err}" for err in tail_errors])
        
        return errors

    # ----- 序列化方法 -------------------- #

    def to_raw_lines(self) -> List[str]:
        """转换为原始 Markdown 行列表"""
        return [ln.to_raw() for ln in self.all_lines()]

    def to_raw(self) -> str:
        """转换为完整 Markdown 文本"""
        lines = self.to_raw_lines()
        result = "\n".join(lines)
        # 确保最后有换行符
        if not result.endswith("\n"):
            result += "\n"
        return result

    def save(self, filepath: str, encoding: str = "utf-8"):
        text = self.to_raw()
        with open(filepath, "w", encoding=encoding) as f:
            f.write(text)

    def save_as(self, filepath: str, encoding: str = "utf-8"):
        self.save(filepath, encoding)

    # ----- Debug -------------------- #

    def dump(self):
        """ 打印账本结构信息 """
        print("=== Ledger Dump ===")
        print(f"header: {len(self.header)}")
        print(f"segments: {len(self.segments)}")
        if self.total:
            print(f"total: {len(self.total.to_lines()) if self.total else 'None'}")
        print(f"tail: {len(self.tail.lines) if self.tail else 0}")
        print()

        for i, sec in enumerate(self.segments, 1):
            print(f"[Segment {i}] {sec.name}")
            print(f"   class      : {sec.__class__.__name__}")
            print(f"   summaries  : {len(sec.summary_lines)}")
            print(f"   body       : {len(sec.body_lines)}")
            print(f"   units      : {len(sec.unit_lines)}")
            print(f"   blanks     : {len(sec.blank_lines)}")
            print(f"   total_unit : {sec.calc_units_sum()}")
            print()

        if self.total:
            print(f"[Total] {self.total.name}")
            print(f"   class : {self.total.__class__.__name__}")
            print(f"   lines : {len(self.total.summary_lines)}")
            print(f"   value : {self.total.value}")

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
