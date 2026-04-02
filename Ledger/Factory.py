# File:        Ledger/Factory.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-04-01
# Description: Ledger工厂函数

from typing import Union

from Line import Line, LineType
from .Life import LifeLedger
from .Month import MonthLedger
from .Collect import CollectLedger


def detect_ledger_type(lines: list) -> str:
    """ 检测账目类型 """
    has_life_title = False
    has_month_title = False
    has_collect_title = False
    
    for line in lines:
        # 检查是否有life.Month标题
        if line.type == LineType.LIFE_TITLE:
            has_life_title = True
        # 检查是否有MONTH_TITLE
        if line.type == LineType.MONTH_TITLE:
            has_month_title = True
        # 检查是否有COLLECT_TITLE
        if line.type == LineType.COLLECT_TITLE:
            has_collect_title = True
    
    # 检测逻辑
    if has_life_title:
        return 'life'
    elif has_month_title:
        return 'month'
    elif has_collect_title:
        return 'collect'
    else:
        return ''


def create_ledger_from_lines(lines) -> Union[LifeLedger, MonthLedger, CollectLedger]:
    """ 从Line对象列表创建账目 """
    ledger_type = detect_ledger_type(lines)
    
    if ledger_type == 'life':
        return LifeLedger.parse_lines(lines)
    elif ledger_type == 'collect':
        return CollectLedger.parse_lines(lines)
    else:
        return MonthLedger.parse_lines(lines)


def create_ledger_from_text(text: str) -> Union[LifeLedger, MonthLedger, CollectLedger]:
    """ 从文本创建账目 """
    raw_lines = text.splitlines()
    lines = [Line.parse(raw) for raw in raw_lines]
    return create_ledger_from_lines(lines)


def create_ledger_from_file(filepath: str, encoding: str = "utf-8") -> Union[LifeLedger, MonthLedger, CollectLedger]:
    """ 从文件创建账目 """
    with open(filepath, "r", encoding=encoding) as f:
        text = f.read()
    return create_ledger_from_text(text)


# 向后兼容的别名
#Ledger = Union[LifeLedger, MonthLedger, CollectLedger]
