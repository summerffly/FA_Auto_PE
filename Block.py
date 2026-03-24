from dataclasses import dataclass, field
from typing import List, Optional
from Line import Line, LineType


# ======================================== #
#    BaseBlock
# ======================================== #

@dataclass
class BaseBlock:
    title_line: Optional[Line] = None
    lines: List[Line] = field(default_factory=list)

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
        return True


# ======================================== #
#    ValueBlock
# ======================================== #
"""
@dataclass
class ValueBlock(BaseBlock):
    def value_line(self) -> Optional[Line]:
        for ln in self.lines:
            if ln.ltype == LineType.AGGR:
                return ln
        return None

    @property
    def value(self) -> int:
        ln = self.value_line()
        return ln.value if ln else 0

    def validate(self) -> bool:
        xs = [x for x in self.lines if x.ltype != LineType.BLANK]

        if len(xs) != 3:
            return False

        return (
            xs[0].ltype == LineType.DELIMITER and
            xs[1].ltype == LineType.AGGR and
            xs[2].ltype == LineType.DELIMITER
        )
"""

# ======================================== #
#    子块（给 Summary 用）
# ======================================== #

@dataclass
class UnitBlock:
    lines: List[Line]

    def total(self) -> int:
        return sum(x.value for x in self.lines if x.ltype == LineType.UNIT)


@dataclass
class AllocationBlock:
    lines: List[Line]

    def total(self) -> int:
        vals = [x.value for x in self.lines if x.ltype == LineType.AGGR]
        return vals[0] if vals else 0

    def children_sum(self) -> int:
        vals = [x.value for x in self.lines if x.ltype == LineType.AGGR]
        return sum(vals[1:]) if len(vals) > 1 else 0

    def validate(self) -> bool:
        return self.total() == self.children_sum()


# ======================================== #
#    SummaryBlock
# ======================================== #

@dataclass
class SummaryBlock(BaseBlock):

    curr_block: Optional[AllocationBlock] = None
    unit_block: Optional[UnitBlock] = None
    allocation_block: Optional[AllocationBlock] = None

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
          - DELIMITER 开始 / 结束的行段 → AllocationBlock（按出现顺序：
            第一段 → curr_block，第三段 → allocation_block）
          - 两段 DELIMITER 之间的裸行段 → UnitBlock（unit_block）
        """
        segments: List[List[Line]] = []   # 每个元素是一段行
        is_delimited: List[bool] = []     # 对应 segment 是否被 ``` 包裹

        buf: List[Line] = []
        inside_delim = False

        for ln in self.lines:
            if ln.ltype == LineType.DELIMITER:
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
                # DELIMITER 包裹的段 → AllocationBlock
                if alloc_idx == 0:
                    self.curr_block = AllocationBlock(lines=seg)
                elif alloc_idx == 1:
                    self.allocation_block = AllocationBlock(lines=seg)
                alloc_idx += 1
            else:
                # 裸行段（非空） → UnitBlock
                non_blank = [l for l in seg if l.ltype != LineType.BLANK]
                if non_blank:
                    self.unit_block = UnitBlock(lines=seg)


# ======================================== #
#    TailBlock
# ======================================== #

@dataclass
class TailBlock(BaseBlock):
    """
    文档尾部元信息块，收录 Update Time 时间戳行与分隔线（---）。
    没有标题，不参与 validate 校验。

    典型内容：
        *Update Time : 2026-03-23 16:15:00*
        ---
    """

    @property
    def timestamp_line(self) -> Optional[Line]:
        for ln in self.lines:
            if ln.ltype == LineType.TIMESTAMP:
                return ln
        return None

    @property
    def timestamp(self) -> str:
        ln = self.timestamp_line
        return ln.content.strip() if ln else ""

    def validate(self) -> bool:
        return True


# ----- Block Factory -------------------- #

def make_block(title_line: Optional[Line], lines: List[Line]) -> BaseBlock:

    name = title_line.raw.strip()

    # Type2：Summary → SummaryBlock，并解析内部子块
    if name == "## Summary":
        blk = SummaryBlock(title_line=title_line, lines=lines)
        blk._parse_sub_blocks()
        return blk

    raise ValueError(f"make_block: 未知标题类型 '{name}'，请检查调用方是否应走 make_minisection")


def make_tail_block(lines: List[Line]) -> TailBlock:
    """把尾部行包装成 TailBlock，由 SumLedger 在解析结束后调用。"""
    return TailBlock(title_line=None, lines=lines)