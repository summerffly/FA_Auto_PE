# File:        LedgerHub.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-23
# LastEdit:    2026-04-02
# Description: 所有账目合集

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
from colorama import Fore, Style

from Ledger import (
    BaseLedger,
    LifeLedger,
    MonthLedger,
    CollectLedger,
    GeneralLedger,
    create_ledger_from_file
)


# ======================================== #
#    LedgerEntry
# ======================================== #

@dataclass
class LedgerEntry:
    alias:    str                    # 快捷命令
    name:     str                    # 正式名称
    filepath: str                    # 文件路径
    ledger:   Optional[BaseLedger]   # 账目对象


# ======================================== #
#    LedgerHub
# ======================================== #

class LedgerHub:

    # ----- 账目注册表 -------------------- #

    _GEN_REGISTRY = ("fa", "FA", "FA.md")
    _REGISTRY = [
        ("life",   "life.M",   "life.M.md"),
        ("dgtler", "DGtler.M", "DGtler.M.md"),
        ("keep",   "KEEP.M",   "KEEP.M.md"),
        ("tb",     "TB.M",     "TB.M.md"),
        ("dk",     "DK",       "DK.md"),
        ("ns",     "NS",       "NS.md"),
        ("travel", "travel",   "travel.md"),
        ("box",    "BOX",      "BOX.md"),
    ]

    # ----- 初始化 -------------------- #

    def __init__(self):
        self._gen_entry:   Optional[LedgerEntry] = None
        self._entries:     Dict[str, LedgerEntry] = {}
        self._initialized: bool = False

    def init(self):
        if self._initialized:
            return
        self.load_all()
        self._initialized = True

     # ----- 加载 -------------------- #

    def load_gen_ledger(self, alias: str, name: str, filepath: str) -> GeneralLedger:
        ledger = GeneralLedger.parse_file(filepath)
        self._gen_entry = LedgerEntry(alias=alias, name=name, filepath=filepath, ledger=ledger)
        return ledger

    def load_ledger(self, alias: str, name: str, filepath: str) -> BaseLedger:
        ledger = create_ledger_from_file(filepath)
        entry  = LedgerEntry(alias=alias, name=name, filepath=filepath, ledger=ledger)
        self._entries[alias] = entry
        return ledger

    def load_all(self):
        alias, name, filepath = self._GEN_REGISTRY
        self.load_gen_ledger(alias, name, filepath)

        for alias, name, filepath in self._REGISTRY:
            self.load_ledger(alias, name, filepath)

    # ----- 访问 -------------------- #

    def _get_any_entry(self, alias: str) -> Optional[LedgerEntry]:
        """ 统一查找gen和普通账目 """
        if alias == "fa":
            return self._gen_entry
        return self._entries.get(alias)

    def get_gen_entry(self) -> LedgerEntry:
        entry = self._get_any_entry("fa")
        if entry is None:
            raise RuntimeError("汇总账目未加载")
        return entry

    def get_entry(self, alias: str) -> LedgerEntry:
        entry = self._get_any_entry(alias)
        if entry is None:
            raise KeyError(f"账目不存在: {alias}")
        return entry

    def get_gen_ledger(self) -> GeneralLedger:
        return self.get_gen_entry().ledger

    def get_ledger(self, alias: str) -> BaseLedger:
        return self.get_entry(alias).ledger

    def get_name(self, alias: str) -> str | None:
        entry = self._get_any_entry(alias)
        return entry.name if entry else None

    def get_filepath(self, alias: str) -> str | None:
        entry = self._get_any_entry(alias)
        return entry.filepath if entry else None

    def list_ledger_alias(self) -> list[str]:
        """返回所有账目alias列表"""
        return list(self._entries.keys())
    
    def list_ledger_entry(self) -> list[LedgerEntry]:
        """返回所有账目entry列表"""
        return self._entries.values()

    # ----- 重载 -------------------- #

    def reload_gen_ledger(self) -> GeneralLedger:
        if self._gen_entry is None:
            raise RuntimeError("汇总账目未加载")
        ledger = GeneralLedger.parse_file(self._gen_entry.filepath)
        self._gen_entry.ledger = ledger
        return ledger

    def reload_ledger(self, alias: str) -> BaseLedger:
        if alias not in self._entries:
            raise KeyError(f"账目不存在: {alias}")
        entry  = self._entries[alias]
        ledger = create_ledger_from_file(entry.filepath)
        entry.ledger = ledger
        return ledger

    def reload_all(self):
        if self._gen_entry is not None:
            self.reload_gen_ledger()
        
        for alias in list(self._entries.keys()):
            self.reload_ledger(alias)

    # ----- 保存 -------------------- #

    def save_gen_ledger(self, filepath: str | None = None):
        if self._gen_entry is None:
            raise RuntimeError("汇总账目未加载")

        target = filepath or self._gen_entry.filepath
        if not target:
            raise ValueError("汇总账目没有可用的保存路径")

        self._gen_entry.ledger.refresh_timestamp()
        self._gen_entry.ledger.save(target)

    def save_ledger(self, alias: str, filepath: str | None = None):
        entry = self.get_entry(alias)

        target = filepath or entry.filepath
        if not target:
            raise ValueError(f"账目 {alias} 没有可用的保存路径")

        entry.ledger.refresh_timestamp()
        entry.ledger.save(target)

    def save_all(self):
        if self._gen_entry is not None:
            self.save_gen_ledger()
            print(f"  保存账目: {self._gen_entry.name:<9} -> {self._gen_entry.filepath}")
        
        for entry in self._entries.values():
            entry.ledger.refresh_timestamp()
            entry.ledger.save(entry.filepath)
            print(f"  保存账目: {entry.name:<9} -> {entry.filepath}")
    
    # ----- END -------------------- #
