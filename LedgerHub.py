# File:        LedgerHub.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-23
# LastEdit:    2026-04-07
# Description: Ledger合集

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
from pathlib import Path
import tomllib

from LedgerProtocol import LedgerProtocol
from Ledger import (
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
    alias:    str                        # 快捷命令
    name:     str                        # 正式名称
    filepath: str                        # 文件路径
    ledger:   Optional[LedgerProtocol]   # 账目对象


# ======================================== #
#    LedgerHub
# ======================================== #

class LedgerHub:

    # ----- 初始化 -------------------- #

    def __init__(self, config_path: str):
        self._entries:     Dict[str, LedgerEntry] = {}
        self._initialized: bool = False

        self._config_path = Path(config_path)
        self._registries = None
        self._backup_dir: Optional[Path] = None
        self._load_config()

    def init(self):
        if self._initialized:
            return
        self.load_all()
        self._initialized = True

    def _load_config(self):
        if not self._config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self._config_path}")

        with open(self._config_path, "rb") as file:
            cfg = tomllib.load(file)

        # Config Entries
        entries = cfg.get("entries")
        if not isinstance(entries, list) or not entries:
            raise ValueError("配置错误: 缺失 [[entries]]")

        registries = []
        alias_set = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"配置错误: 对象格式错误: {entry}")

            alias = entry.get("alias")
            name = entry.get("name")
            filepath = entry.get("filepath")
            if not all(isinstance(x, str) and x.strip() for x in (alias, name, filepath)):
                raise ValueError(f"配置错误: [[entries]] 存在非空字符串")
            if alias in alias_set:
                raise ValueError("配置错误: [[entries]] 存在重复对象")
            
            registries.append((alias, name, filepath))
            alias_set.add(alias)

        self._registries = registries

        # Config Backup
        backup = cfg.get("backup")
        if not isinstance(backup, dict):
            raise ValueError(f"配置错误: 对象格式错误: {backup}")

        backup_dir = backup.get("dir")
        if not isinstance(backup_dir, str) or not backup_dir.strip():
            raise ValueError("配置错误: [backup] 存在非空字符串")

        self._backup_dir = Path(backup_dir)

     # ----- 加载 -------------------- #

    def load_all(self):
        for alias, name, filepath in self._registries:
            ledger = create_ledger_from_file(filepath)
            if not isinstance(ledger, LedgerProtocol):
                raise TypeError(f"不符合LedgerProtocol: {type(ledger).__name__}")
            entry = LedgerEntry(alias=alias, name=name, filepath=filepath, ledger=ledger)
            self._entries[alias] = entry
    
    def reload_all(self):
        for entry in self.get_all_entries():
            ledger = create_ledger_from_file(entry.filepath)
            if not isinstance(ledger, LedgerProtocol):
                raise TypeError(f"不符合LedgerProtocol: {type(ledger).__name__}")
            entry.ledger = ledger
            print(f"  已重载: {entry.name:<9} <- {entry.filepath}")

    # ----- 保存 -------------------- #

    def save_all(self):
        for entry in self.get_all_entries():
            entry.ledger.refresh_timestamp()
            entry.ledger.save(entry.filepath)
            print(f"  已保存: {entry.name:<9} -> {entry.filepath}")

    def backup_all(self):
        if self._backup_dir is None:
            raise RuntimeError("备份目录未配置")
        backup_dir = Path(self._backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        for entry in self.get_all_entries():
            backup_path = backup_dir / entry.filepath
            entry.ledger.refresh_timestamp()
            entry.ledger.save(backup_path)
            print(f"  已备份: {entry.name:<9} -> {backup_path}")

    # ----- 访问 -------------------- #

    def get_entry(self, alias: str) -> LedgerEntry:
        entry = self._entries.get(alias)
        if entry is None:
            raise KeyError(f"账目不存在: {alias}")
        return entry
    
    def get_gen_entry(self) -> LedgerEntry:
        for entry in self._entries.values():
            if isinstance(entry.ledger, GeneralLedger):
                return entry
        raise RuntimeError("未找到General账目")
    
    def get_life_entry(self) -> LedgerEntry:
        for entry in self._entries.values():
            if isinstance(entry.ledger, LifeLedger):
                return entry
        raise RuntimeError("未找到Life账目")
    
    def get_month_entries(self) -> list[LedgerEntry]:
        month_entries = []
        for entry in self._entries.values():
            if isinstance(entry.ledger, MonthLedger):
                month_entries.append(entry)
        
        if not month_entries:
            raise RuntimeError("未找到任何Month账目")
        else:
            return month_entries
    
    def get_collect_entries(self) -> list[LedgerEntry]:
        collect_entries = []
        for entry in self._entries.values():
            if isinstance(entry.ledger, CollectLedger):
                collect_entries.append(entry)
        
        if not collect_entries:
            raise RuntimeError("未找到任何Collect账目")
        else:
            return collect_entries
    
    def get_non_gen_entries(self) -> list[LedgerEntry]:
        non_gen_entries = []
        for entry in self._entries.values():
            if not isinstance(entry.ledger, GeneralLedger):
                non_gen_entries.append(entry)
        
        if not non_gen_entries:
            raise RuntimeError("未找到任何Non-General账目")
        else:
            return non_gen_entries
    
    def get_all_entries(self) -> list[LedgerEntry]:
        return list(self._entries.values())

    def get_alias_list(self) -> list[str]:
        alias_list = []
        for entry in self._entries.values():
            alias_list.append(entry.alias)
        return alias_list
    
    # ----- END -------------------- #
