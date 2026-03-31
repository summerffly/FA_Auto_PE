# File:        Summary.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-25
# LastEdit:    2026-03-25
# Description: 

from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType


# ======================================== #
#    SubScetion of Summary
# ======================================== #

@dataclass
class UnitSection:
    lines: List[Line]

    def total(self) -> int:
        return sum(x.value for x in self.lines if x.type == LineType.UNIT)


@dataclass
class AllocationSection:
    lines: List[Line]

    def total(self) -> int:
        vals = [x.value for x in self.lines if x.type == LineType.AGGR]
        return vals[0] if vals else 0

    def children_sum(self) -> int:
        vals = [x.value for x in self.lines if x.type == LineType.AGGR]
        return sum(vals[1:]) if len(vals) > 1 else 0

    def validate(self) -> bool:
        return self.total() == self.children_sum()


# ======================================== #
#    SummarySection
# ======================================== #

@dataclass
class SummarySection:
    title_line: Optional[Line] = None
    lines: List[Line] = field(default_factory=list)

    curr_block: Optional[AllocationSection] = None
    unit_block: Optional[UnitSection] = None
    allocation_block: Optional[AllocationSection] = None

    @property
    def name(self) -> str:
        if self.title_line is None:
            return ""
        raw = self.title_line.raw.strip()
        if raw.startswith("## "):
            return raw[3:].strip()
        return raw

    def to_lines(self) -> List[Line]:
        out = []
        if self.title_line:
            out.append(self.title_line)
        out.extend(self.lines)
        return out

    def validate(self) -> bool:
        if self.allocation_block:
            if not self.allocation_block.validate():
                return False
        return True

    def _parse_sub_blocks(self) -> None:
        """
        把 self.lines 中的平铺行按 DELIMITER 边界切分成子块，
        依次填入 curr_block / unit_block / allocation_block。

        切分规则：
          - DELIMITER 开始 / 结束的行段 → AllocationSection（按出现顺序：
            第一段 → curr_block，第三段 → allocation_block）
          - 两段 DELIMITER 之间的裸行段 → UnitSection（unit_block）
        """
        segments: List[List[Line]] = []   # 每个元素是一段行
        is_delimited: List[bool] = []     # 对应 segment 是否被 ``` 包裹

        buf: List[Line] = []
        inside_delim = False

        for ln in self.lines:
            if ln.type == LineType.DELIMITER:
                if not inside_delim:
                    # 把之前的裸行先存起来
                    if buf:
                        segments.append(buf)
                        is_delimited.append(False)
                        buf = []
                    buf = [ln]
                    inside_delim = True
                else:
                    buf.append(ln)
                    segments.append(buf)
                    is_delimited.append(True)
                    buf = []
                    inside_delim = False
            else:
                buf.append(ln)

        if buf:
            segments.append(buf)
            is_delimited.append(False)

        # 按顺序分配
        alloc_idx = 0
        for seg, delimited in zip(segments, is_delimited):
            if delimited:
                # DELIMITER 包裹的段 → AllocationSection
                if alloc_idx == 0:
                    self.curr_block = AllocationSection(lines=seg)
                elif alloc_idx == 1:
                    self.allocation_block = AllocationSection(lines=seg)
                alloc_idx += 1
            else:
                # 裸行段（非空） → UnitSection
                non_blank = [l for l in seg if l.type != LineType.BLANK]
                if non_blank:
                    self.unit_block = UnitSection(lines=seg)


# ======================================== #
#    Summary Factory
# ======================================== #

def make_summary(title_line: Line, lines: List[Line]) -> SummarySection:
    summary = SummarySection(title_line=title_line, lines=lines)
    summary._parse_sub_blocks()
    return summary
