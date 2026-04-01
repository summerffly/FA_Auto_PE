# File:        LedgerHub.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-23
# LastEdit:    2026-04-01
# Description: 所有账本合集

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
from colorama import Fore, Style

from Ledger import (
    BaseLedger,
    LifeLedger,
    MonthLedger,
    CollectLedger,
    SumLedger,
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
    ledger:   Optional[BaseLedger]   # 账本对象


# ======================================== #
#    LedgerHub
# ======================================== #

class LedgerHub:

    # 账本注册表
    # 顺序即加载顺序
    _SUM_REGISTRY = ("sum", "FA_SUM", "FA_SUM.md")
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

    def __init__(self):
        self._sum_entry:   Optional[LedgerEntry] = None
        self._entries:     Dict[str, LedgerEntry] = {}
        self._initialized: bool = False

    # ----- 初始化 -------------------- #

    def init(self):
        if self._initialized:
            return
        self._load_all()
        self._initialized = True

    def _load_all(self):
        """按注册表加载所有账本文件"""
        alias, name, filepath = self._SUM_REGISTRY
        self.load_sum_ledger(alias, name, filepath)

        for alias, name, filepath in self._REGISTRY:
            self.load_ledger(alias, name, filepath)

    # ----- 加载 -------------------- #

    def load_sum_ledger(self, alias: str, name: str, filepath: str) -> SumLedger:
        ledger = SumLedger.parse_file(filepath)
        self._sum_entry = LedgerEntry(alias=alias, name=name, filepath=filepath, ledger=ledger)
        print(f"Load Ledger:  {alias:<8} {name:<10} SumLedger")
        return ledger

    def load_ledger(self, alias: str, name: str, filepath: str) -> BaseLedger:
        ledger = create_ledger_from_file(filepath)
        entry  = LedgerEntry(alias=alias, name=name, filepath=filepath, ledger=ledger)
        self._entries[alias] = entry

        if isinstance(ledger, LifeLedger):
            print(f"Load Ledger:  {alias:<8} {name:<10} LifeLedger")
        elif isinstance(ledger, MonthLedger):
            print(f"Load Ledger:  {alias:<8} {name:<10} MonthLedger")
        elif isinstance(ledger, CollectLedger):
            print(f"Load Ledger:  {alias:<8} {name:<10} CollectLedger")
        else:
            print(f"Load Ledger:  {alias:<8} {name:<10} Unknown Ledger")

        return ledger

    # ----- 验证 -------------------- #

    def validate(self):
        """验证所有账本结构"""
        if self._sum_entry is not None:
            errors = self._sum_entry.ledger.validate_struct()
            label  = self._sum_entry.name
            if errors:
                for error in errors:
                    print(f"{label:<10} {Fore.RED}[!]{Style.RESET_ALL} {error}")
            else:
                print(f"{label:<10} {Fore.GREEN}✓✓✓{Style.RESET_ALL}")

        for entry in self._entries.values():
            errors = entry.ledger.validate_struct()
            if errors:
                for error in errors:
                    print(f"{entry.name:<10} {Fore.RED}[!]{Style.RESET_ALL} {error}")
            else:
                print(f"{entry.name:<10} {Fore.GREEN}✓✓✓{Style.RESET_ALL}")

    # ----- 访问 -------------------- #

    def _get_any_entry(self, alias: str) -> Optional[LedgerEntry]:
        """统一查找sum和普通账本 找不到返回None"""
        if alias == "sum":
            return self._sum_entry
        return self._entries.get(alias)

    def get_sum_entry(self) -> LedgerEntry:
        entry = self._get_any_entry("sum")
        if entry is None:
            raise RuntimeError("汇总账本未加载")
        return entry

    def get_entry(self, alias: str) -> LedgerEntry:
        entry = self._get_any_entry(alias)
        if entry is None:
            raise KeyError(f"账本不存在: {alias}")
        return entry

    def get_sum_ledger(self) -> SumLedger:
        return self.get_sum_entry().ledger

    def get_ledger(self, alias: str) -> BaseLedger:
        return self.get_entry(alias).ledger

    def get_name(self, alias: str) -> str | None:
        entry = self._get_any_entry(alias)
        return entry.name if entry else None

    def get_filepath(self, alias: str) -> str | None:
        entry = self._get_any_entry(alias)
        return entry.filepath if entry else None

    def list_ledger_alias(self) -> list[str]:
        """返回所有账本alias列表"""
        return list(self._entries.keys())

    # ----- 重载 -------------------- #

    def reload_sum_ledger(self) -> SumLedger:
        if self._sum_entry is None:
            raise RuntimeError("汇总账本未加载")
        ledger = SumLedger.parse_file(self._sum_entry.filepath)
        self._sum_entry.ledger = ledger
        return ledger

    def reload_ledger(self, alias: str) -> BaseLedger:
        if alias not in self._entries:
            raise KeyError(f"账本不存在: {alias}")
        entry  = self._entries[alias]
        ledger = create_ledger_from_file(entry.filepath)
        entry.ledger = ledger
        return ledger

    def reload_all(self):
        if self._sum_entry is not None:
            self.reload_sum_ledger()
        
        for alias in list(self._entries.keys()):
            self.reload_ledger(alias)

    # ----- 保存 -------------------- #

    def save_sum_ledger(self, filepath: str | None = None):
        if self._sum_entry is None:
            raise RuntimeError("汇总账本未加载")

        target = filepath or self._sum_entry.filepath
        if not target:
            raise ValueError("汇总账本没有可用的保存路径")

        self._sum_entry.ledger.refresh_timestamp()
        self._sum_entry.ledger.save(target)

    def save_ledger(self, alias: str, filepath: str | None = None):
        entry = self.get_entry(alias)

        target = filepath or entry.filepath
        if not target:
            raise ValueError(f"账本 {alias} 没有可用的保存路径")

        entry.ledger.refresh_timestamp()
        entry.ledger.save(target)

    def save_all(self):
        if self._sum_entry is not None:
            self.save_sum_ledger()
        
        for entry in self._entries.values():
            entry.ledger.refresh_timestamp()
            entry.ledger.save(entry.filepath)
