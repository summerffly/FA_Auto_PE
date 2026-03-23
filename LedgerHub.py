"""
LedgerHub.py
整个账本文件抽象
"""

from __future__ import annotations
from typing import Dict
from Ledger import Ledger


LEDGERS: Dict[str, Ledger] = {}
LEDGER_FILES: Dict[str, str] = {}


def init_ledger_hub():
    """
    初始化 LedgerHub
    加载所有账本
    """
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
    从文件加载账本并注册。
    """
    ledger = Ledger.parse_file(filepath)
    LEDGERS[name] = ledger
    LEDGER_FILES[name] = filepath
    return ledger


def get_ledger(name: str) -> Ledger:
    """
    获取指定账本；不存在则抛异常。
    """
    if name not in LEDGERS:
        raise KeyError(f"账本不存在: {name}")
    return LEDGERS[name]


def has_ledger(name: str) -> bool:
    return name in LEDGERS


def list_ledgers() -> list[str]:
    return sorted(LEDGERS.keys())


def remove_ledger(name: str) -> None:
    LEDGERS.pop(name, None)
    LEDGER_FILES.pop(name, None)


def reload_ledger(name: str) -> Ledger:
    """
    重新从磁盘加载指定账本。
    """
    if name not in LEDGER_FILES:
        raise KeyError(f"账本没有绑定文件路径: {name}")

    filepath = LEDGER_FILES[name]
    ledger = Ledger.parse_file(filepath)
    LEDGERS[name] = ledger
    return ledger


def reload_all() -> None:
    """
    重新从磁盘加载所有已绑定路径的账本。
    """
    for name in list(LEDGER_FILES.keys()):
        reload_ledger(name)


def save_ledger(name: str, filepath: str | None = None) -> None:
    """
    保存指定账本。
    """
    ledger = get_ledger(name)

    if filepath is None:
        filepath = LEDGER_FILES.get(name)

    if not filepath:
        raise ValueError(f"账本 {name} 没有可用的保存路径")

    ledger.save(filepath)


def save_all() -> None:
    """
    保存所有已绑定路径的账本。
    """
    for name in list_ledgers():
        if name in LEDGER_FILES:
            LEDGERS[name].save(LEDGER_FILES[name])
