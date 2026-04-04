# File:        Ledger/Mixin.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-31
# LastEdit:    2026-04-01
# Description: Ledger通用混入基类

from __future__ import annotations
from Line import Line


class LedgerMixin:

    # ----- 解析方法 -------------------- #

    @classmethod
    def parse_file(cls, filepath: str, encoding: str = "utf-8"):
        """ 从文件解析账目 """
        with open(filepath, "r", encoding=encoding) as f:
            text = f.read()
        return cls.parse_text(text)

    @classmethod
    def parse_text(cls, text: str):
        """ 从文本解析账目 """
        raw_lines = text.splitlines()
        lines = [Line.parse(raw) for raw in raw_lines]
        return cls.parse_lines(lines)
    
    @classmethod
    def parse_lines(cls, lines):
        """ 子类实现方法 """
        """ 从Line对象列表解析账目 """
        raise NotImplementedError(f"{cls.__name__} 未实现 parse_lines()")

    # ----- 序列化 -------------------- #

    def refresh_timestamp(self):
        """ 刷新时间戳 """
        if self.tail:
            self.tail.refresh_timestamp()

    def to_lines(self):
        """ 子类实现方法 """
        raise NotImplementedError(f"{self.__class__.__name__} 未实现 to_lines()")

    def to_raw(self) -> str:
        """ 转换为原始文本 """
        raw_lines = [ln.to_raw() for ln in self.to_lines()]
        raw_text = "\n".join(raw_lines)
        if not raw_text.endswith("\n"):
            raw_text += "\n"
        return raw_text

    def save(self, filepath: str, encoding: str = "utf-8"):
        """ 保存文件 """
        text = self.to_raw()
        with open(filepath, "w", encoding=encoding) as f:
            f.write(text)

    # ----- END -------------------- #
