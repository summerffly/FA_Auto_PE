# File:        LedgerHub.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-23
# LastEdit:    2026-04-04
# Description: 所有账目合集

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
from colorama import Fore, Style
from pathlib import Path
import tomllib

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

    # ----- 初始化 -------------------- #

    def __init__(self, config_path: str):
        self._gen_entry:   Optional[LedgerEntry] = None
        self._entries:     Dict[str, LedgerEntry] = {}
        self._initialized: bool = False

        self._config_path = Path(config_path)
        self._gen_registry = None
        self._registries = None
        self._backup_dir: Optional[Path] = None
        self._load_config_toml()

    def init(self):
        if self._initialized:
            return
        self.load_all()
        self._initialized = True

    def _load_config_toml(self):
        # 检查配置文件
        if not self._config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self._config_path}")

        # 读取配置文件
        with open(self._config_path, "rb") as f:
            cfg = tomllib.load(f)

        # 解析 gen_entry
        gen_entry = cfg.get("gen_entry")
        if not isinstance(gen_entry, dict):
            raise ValueError("配置错误: 缺失 [gen_entry]")

        gen_alias = gen_entry.get("alias")
        gen_name = gen_entry.get("name")
        gen_filepath = gen_entry.get("filepath")

        if not all(isinstance(x, str) and x.strip() for x in (gen_alias, gen_name, gen_filepath)):
            raise ValueError("配置错误: [gen_entry] 存在非空字符")

        # 解析 entries
        entries = cfg.get("entries")
        if not isinstance(entries, list) or not entries:
            raise ValueError("配置错误: 缺失 [[entries]]")

        registries = []
        alias_set = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"配置错误: 表对象格式错误: {entry}")

            alias = entry.get("alias")
            name = entry.get("name")
            filepath = entry.get("filepath")

            if not all(isinstance(x, str) and x.strip() for x in (alias, name, filepath)):
                raise ValueError(f"配置错误: [[entries]] 存在非空字符串")

            if alias in alias_set:
                raise ValueError("配置错误: [[entries]] 重复")

            alias_set.add(alias)
            registries.append((alias, name, filepath))

        self._gen_registry = (gen_alias, gen_name, gen_filepath)
        self._registries = registries

        # backup
        backup = cfg.get("backup")
        if not isinstance(backup, dict):
            raise ValueError("配置错误: 缺失 [backup]")

        backup_dir = backup.get("dir")
        if not isinstance(backup_dir, str) or not backup_dir.strip():
            raise ValueError("配置错误: [backup] 存在非空字符串")

        self._backup_dir = Path(backup_dir)

     # ----- 加载 -------------------- #

    def load_all(self):
        alias, name, filepath = self._gen_registry
        ledger = create_ledger_from_file(filepath)
        self._gen_entry = LedgerEntry(alias=alias, name=name, filepath=filepath, ledger=ledger)

        for alias, name, filepath in self._registries:
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

    def backup_all(self):
        if self._backup_dir is None:
            raise RuntimeError("备份目录未配置")

        backup_dir = Path(self._backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        if self._gen_entry is not None:
            backup_path = backup_dir / self._gen_entry.filepath
            self._gen_entry.ledger.refresh_timestamp()
            self._gen_entry.ledger.save(backup_path)
            print(f"  已备份: {self._gen_entry.name:<9} -> {backup_path}")
        
        for entry in self.get_entries():
            backup_path = backup_dir / entry.filepath
            entry.ledger.refresh_timestamp()
            entry.ledger.save(backup_path)
            print(f"  已备份: {entry.name:<9} -> {backup_path}")

    # ----- 访问 -------------------- #

    def _get_any_entry(self, alias: str) -> Optional[LedgerEntry]:
        """ 统一查找gen和普通账目 """
        if alias == "fa":
            return self._gen_entry
        return self._entries.get(alias)

    def get_gen_entry(self) -> LedgerEntry:
        if self._gen_entry is None:
            raise RuntimeError("账目未加载")
        elif not isinstance(self._gen_entry.ledger, GeneralLedger):
            raise TypeError(f"FA账目类型错误: {type(self._gen_entry.ledger).__name__}")
        else:
            return self._gen_entry
    
    def get_life_entry(self) -> LedgerEntry:
        entry = self._get_any_entry("life")
        if entry is None:
            raise RuntimeError("账目未加载")
        elif not isinstance(entry.ledger, LifeLedger):
            raise TypeError(f"life账目类型错误: {type(entry.ledger).__name__}")
        else:
            return entry
    
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
