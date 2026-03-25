# File:        LedgerHub.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-23
# LastEdit:    2026-03-25
# Description: 所有账本合集

from __future__ import annotations
from typing import Dict, Optional
from Ledger import Ledger
from SumLedger import SumLedger


LEDGERS: Dict[str, Ledger] = {}
SUM_LEDGER: Optional[SumLedger] = None
LEDGER_FILES: Dict[str, str] = {}


def init_ledger_hub():
    """
    初始化LedgerHub
    加载所有账本
    """
    load_sum_ledger("FA_SUM.md")
    load_ledger("life", "life.M.md")
    load_ledger("dg", "DGtler.M.md")
    load_ledger("keep", "KEEP.M.md")
    load_ledger("tb", "TB.M.md")
    load_ledger("dk", "DK.md")
    load_ledger("ns", "NS.md")
    load_ledger("travel", "travel.md")
    load_ledger("box", "BOX.md")

def register_ledger(name: str, ledger: Ledger, filepath: str | None = None) -> None:
    """
    注册一个已解析好的账本对象。
    """
    LEDGERS[name] = ledger
    if filepath is not None:
        LEDGER_FILES[name] = filepath


def load_ledger(name: str, filepath: str) -> Ledger:
    """
    从文件加载账本
    """
    ledger = Ledger.parse_file(filepath)
    LEDGERS[name] = ledger
    LEDGER_FILES[name] = filepath
    return ledger


def load_sum_ledger(filepath: str) -> SumLedger:
    """
    从文件加载汇总账本
    """
    global SUM_LEDGER
    ledger = SumLedger.parse_file(filepath)
    SUM_LEDGER = ledger
    LEDGER_FILES["sum"] = filepath
    return ledger


def get_ledger(name: str) -> Ledger:
    """
    获取指定账本
    """
    if name not in LEDGERS:
        raise KeyError(f"账本不存在: {name}")
    return LEDGERS[name]


def get_sum_ledger() -> SumLedger:
    """
    获取指定汇总账本
    """
    global SUM_LEDGER
    if SUM_LEDGER is None:
        raise ValueError("汇总账本未加载")
    return SUM_LEDGER


def has_ledger(name: str) -> bool:
    """
    判断账本是否存在
    """
    return name in LEDGERS


def has_sum_ledger() -> bool:
    """
    判断汇总账本是否已加载
    """
    return SUM_LEDGER is not None


def list_ledgers() -> list[str]:
    """
    返回所有账本名称
    """
    return sorted(LEDGERS.keys())


def remove_ledger(name: str) -> None:
    """
    移除指定账本
    """
    LEDGERS.pop(name, None)
    LEDGER_FILES.pop(name, None)


def reload_ledger(name: str) -> Ledger:
    """
    重新从磁盘加载指定账本
    """
    if name not in LEDGER_FILES:
        raise KeyError(f"账本没有绑定文件路径: {name}")

    filepath = LEDGER_FILES[name]
    ledger = Ledger.parse_file(filepath)
    LEDGERS[name] = ledger
    return ledger


def reload_sum_ledger() -> SumLedger:
    """
    重新从磁盘加载汇总账本
    """
    global SUM_LEDGER
    if "sum" not in LEDGER_FILES:
        raise KeyError("汇总账本没有绑定文件路径")
    
    filepath = LEDGER_FILES["sum"]
    ledger = SumLedger.parse_file(filepath)
    SUM_LEDGER = ledger
    return ledger


def reload_all() -> None:
    """
    重新从磁盘加载所有账本
    """
    for name in list(LEDGER_FILES.keys()):
        reload_ledger(name)

    if "sum" in LEDGER_FILES:
        reload_sum_ledger()


def save_ledger(name: str, filepath: str | None = None) -> None:
    """
    保存指定账本
    """
    ledger = get_ledger(name)

    if filepath is None:
        filepath = LEDGER_FILES.get(name)

    if not filepath:
        raise ValueError(f"账本 {name} 没有可用的保存路径")

    ledger.save(filepath)


def save_sum_ledger(filepath: str | None = None) -> None:
    """
    保存汇总账本
    """
    global SUM_LEDGER
    if SUM_LEDGER is None:
        raise ValueError("汇总账本未加载")
    
    if filepath is None:
        filepath = LEDGER_FILES.get("sum")
    
    if not filepath:
        raise ValueError("汇总账本没有可用的保存路径")
    
    SUM_LEDGER.save(filepath)


def save_all() -> None:
    """
    保存所有账本
    """
    for name in list_ledgers():
        if name in LEDGER_FILES:
            LEDGERS[name].save(LEDGER_FILES[name])

    if "sum" in LEDGER_FILES:
        save_sum_ledger()
