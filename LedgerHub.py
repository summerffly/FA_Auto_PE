# File:        LedgerHub.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-23
# LastEdit:    2026-04-03
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

    def load_all(self):
        alias, name, filepath = self._GEN_REGISTRY
        ledger = create_ledger_from_file(filepath)
        self._gen_entry = LedgerEntry(alias=alias, name=name, filepath=filepath, ledger=ledger)

        for alias, name, filepath in self._REGISTRY:
            ledger = create_ledger_from_file(filepath)
            entry = LedgerEntry(alias=alias, name=name, filepath=filepath, ledger=ledger)
            self._entries[alias] = entry

    # ----- 重载 -------------------- #
    
    def reload_all(self):
        if self._gen_entry is not None:
            ledger = create_ledger_from_file(self._gen_entry.filepath)
            self._gen_entry.ledger = ledger
            print(f"  已重载: {self._gen_entry.name:<9} <- {self._gen_entry.filepath}")

        for entry in self.get_entries():
            ledger = create_ledger_from_file(entry.filepath)
            entry.ledger = ledger
            print(f"  已重载: {entry.name:<9} <- {entry.filepath}")

    # ----- 保存 -------------------- #

    def save_all(self):
        if self._gen_entry is not None:
            self._gen_entry.ledger.refresh_timestamp()
            self._gen_entry.ledger.save(self._gen_entry.filepath)
            print(f"  已保存: {self._gen_entry.name:<9} -> {self._gen_entry.filepath}")
        
        for entry in self.get_entries():
            entry.ledger.refresh_timestamp()
            entry.ledger.save(entry.filepath)
            print(f"  已保存: {entry.name:<9} -> {entry.filepath}")

    # ----- 访问 -------------------- #

    def _get_any_entry(self, alias: str) -> Optional[LedgerEntry]:
        """ 统一查找gen和普通账目 """
        if alias == "fa":
            return self._gen_entry
        return self._entries.get(alias)

    def get_gen_entry(self) -> LedgerEntry:
        if self._gen_entry is None:
            raise RuntimeError("账目未加载")
        return self._gen_entry
    
    def get_life_entry(self) -> LedgerEntry:
        entry = self._get_any_entry("life")
        if entry is None:
            raise RuntimeError("账目未加载")
        return entry
    
    def get_month_entries(self) -> list[LedgerEntry]:
        month_entries = []
        for entry in self._entries.values():
            if isinstance(entry.ledger, MonthLedger):
                month_entries.append(entry)
        return month_entries
    
    def get_collect_entries(self) -> list[LedgerEntry]:
        collect_entries = []
        for entry in self._entries.values():
            if isinstance(entry.ledger, CollectLedger):
                collect_entries.append(entry)
        return collect_entries
    
    def get_entries(self) -> list[LedgerEntry]:
        return list(self._entries.values())

    def get_entry(self, alias: str) -> LedgerEntry:
        entry = self._get_any_entry(alias)
        if entry is None:
            raise KeyError(f"账目不存在: {alias}")
        return entry

    def get_alias_list(self) -> list[str]:
        alias_list = []
        for entry in self.get_entries():
            alias_list.append(entry.alias)
        return alias_list
    
    # ----- END -------------------- #
