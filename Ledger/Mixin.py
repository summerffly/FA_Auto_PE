# File:        Ledger/Mixin.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-31
# LastEdit:    2026-04-01
# Description: Ledger通用混入基类

from __future__ import annotations
from Line import Line


class LedgerMixin:

    # ----- 解析账目 -------------------- #

    @classmethod
    def parse_file(cls, filepath: str, encoding: str = "utf-8"):
        with open(filepath, "r", encoding=encoding) as f:
            text = f.read()
        return cls.parse_text(text)

    @classmethod
    def parse_text(cls, text: str):
        raw_lines = text.splitlines()
        lines = [Line.parse(raw) for raw in raw_lines]
        return cls.parse_lines(lines)
    
    @classmethod
    def parse_lines(cls, lines):
        raise NotImplementedError(f"{cls.__name__} 未实现 parse_lines()")

    # ----- 序列化 -------------------- #

    def refresh_timestamp(self):
        if self.tail:
            self.tail.refresh_timestamp()

    def to_lines(self):
        raise NotImplementedError(f"{self.__class__.__name__} 未实现 to_lines()")

    def to_raw(self) -> str:
        raw_lines = [ln.to_raw() for ln in self.to_lines()]
        raw_text = "\n".join(raw_lines)
        if not raw_text.endswith("\n"):
            raw_text += "\n"
        return raw_text

    def save(self, filepath: str, encoding: str = "utf-8"):
        text = self.to_raw()
        with open(filepath, "w", encoding=encoding) as f:
            f.write(text)

    # ----- END -------------------- #
