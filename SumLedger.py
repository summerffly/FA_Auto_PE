"""
SumLedger.py
基于 Block / MiniSection 架构的账本解析
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union
from Line import Line, LineType
from MiniSection import BaseMiniSection, make_minisection
from Block import BaseBlock, TailBlock, make_block, make_tail_block

# Summary 标题常量，集中管理避免散落的魔法字符串
_SUMMARY_TITLE = "## Summary"


# ========================
# Ledger
# ========================

@dataclass
class SumLedger:
    header: List[Line] = field(default_factory=list)
    segments: List[BaseMiniSection] = field(default_factory=list)
    summary: Optional[BaseBlock] = None
    tail: Optional[TailBlock] = None

    # --------------------
    # Parse
    # --------------------

    @staticmethod
    def parse_text(text: str) -> "SumLedger":
        raw_lines = text.splitlines()
        lines = [Line.parse(raw) for raw in raw_lines]
        return SumLedger.parse_lines(lines)

    @staticmethod
    def parse_file(filepath: str, encoding: str = "utf-8") -> "SumLedger":
        with open(filepath, "r", encoding=encoding) as f:
            text = f.read()
        return SumLedger.parse_text(text)

    @staticmethod
    def parse_lines(lines: List[Line]) -> "SumLedger":
        ledger = SumLedger()

        i = 0
        n = len(lines)

        current_title: Optional[Line] = None
        current_lines: List[Line] = []

        def flush_block():
            nonlocal current_title, current_lines
            if current_title is None and not current_lines:
                return

            # -----------------------------------------------
            # 路由规则：
            #   - 无标题               → make_block(None, ...)  → ValueBlock
            #   - ## Summary           → make_block(title, ...) → SummaryBlock
            #   - 其他带标题（含 .M）  → make_minisection(...)  → Month / TitleMiniSection
            # -----------------------------------------------
            if current_title is None:
                blk: BaseMiniSection = make_block(None, current_lines)
            elif current_title.raw.strip() == _SUMMARY_TITLE:
                ledger.summary = make_block(current_title, current_lines)
            else:
                blk = make_minisection(current_title, current_lines)
                ledger.segments.append(blk)

            current_title = None
            current_lines = []

        while i < n:
            ln = lines[i]

            # --------------------
            # 尾部触发：TIMESTAMP 或 EOF
            # 遇到其中之一，结束当前 block，收集剩余所有行为 TailBlock
            # --------------------
            if ln.ltype in (LineType.TIMESTAMP, LineType.EOF):
                flush_block()
                tail_lines = lines[i:]
                ledger.tail = make_tail_block(tail_lines)
                break

            # --------------------
            # 顶层标题（新 Block / MiniSection）
            # --------------------
            if ln.ltype in (LineType.MONTH_TITLE, LineType.SUB_TITLE, LineType.SUB_TAG):
                flush_block()
                current_title = ln
                current_lines = []
                i += 1
                continue

            # --------------------
            # 没有标题的块（Type1 ValueBlock）
            # --------------------
            if current_title is None:
                if ln.ltype == LineType.DELIMITER:
                    current_lines = [ln]
                    i += 1
                    while i < n:
                        current_lines.append(lines[i])
                        if lines[i].ltype == LineType.DELIMITER:
                            i += 1
                            break
                        i += 1
                    flush_block()
                    continue
                else:
                    ledger.header.append(ln)
                    i += 1
                    continue

            # --------------------
            # 普通内容（Block / MiniSection 内）
            # 注意：## Summary 内的 ``` 行也走这里，交给
            # SummaryBlock._parse_sub_segments() 负责二次解析。
            # --------------------
            current_lines.append(ln)
            i += 1

        # 收尾（无尾部触发行时仍需 flush）
        flush_block()

        return ledger

    # --------------------
    # 查询
    # --------------------

    def block_names(self) -> List[str]:
        return [blk.name for blk in self.segments]

    def get_block(self, name: str) -> Optional[Union[BaseBlock, BaseMiniSection]]:
        for blk in self.segments:
            if blk.name == name:
                return blk
        return None

    # --------------------
    # 验证
    # --------------------

    def validate(self) -> bool:
        return all(blk.validate() for blk in self.segments)

    # --------------------
    # 输出
    # --------------------

    def to_lines(self) -> List[Line]:
        out: List[Line] = []
        out.extend(self.header)
        for blk in self.segments:
            out.extend(blk.to_lines())
        if self.tail:
            out.extend(self.tail.to_lines())
        return out

    def to_raw(self) -> str:
        return "\n".join(ln.to_raw() for ln in self.to_lines())

    # --------------------
    # 调试
    # --------------------

    def dump(self):
        print("=== Ledger Dump ===")

        print("\n[HEAD]")
        for ln in self.header:
            print(ln.raw)

        print("[SEGMENTS]")
        for idx, blk in enumerate(self.segments, 1):
            print(f"Segment {idx}: {blk.name} ({blk.__class__.__name__})")
            for ln in blk.to_lines():
                print(ln.raw)

        print("[SUMMARY]")
        if self.summary:
            for ln in self.summary.to_lines():
                print(ln.raw)

        print("[TAIL]")
        if self.tail:
            for ln in self.tail.to_lines():
                print(ln.raw)
