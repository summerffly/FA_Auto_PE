# File:        LedgerProtocol.py
# Author:      summer@SummerStudio
# CreateDate:  2026-04-07
# LastEdit:    2026-04-07
# Description: Ledger统一接口协议

from __future__ import annotations
from typing import Protocol, List, runtime_checkable

from Line import Line


# ======================================== #
#    LedgerProtocol
# ======================================== #

@runtime_checkable
class LedgerProtocol(Protocol):

    # ----- 核心方法 -------------------- #

    def validate(self) -> List[str]: ...
    def checksum(self) -> bool: ...
    def rebuild(self) -> None: ...

    # ----- 序列化 -------------------- #

    def refresh_timestamp(self) -> None: ...
    def to_lines(self) -> List[Line]: ...
    def to_raw(self) -> str: ...
    def save(self, filepath: str, encoding: str = "utf-8") -> None: ...

    # ----- END -------------------- #
