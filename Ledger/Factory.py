# File:        Ledger/Factory.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-04-03
# Description: Ledger工厂函数

import os
from typing import Union

from Line import Line, LineType
from .Life import LifeLedger
from .Month import MonthLedger
from .Collect import CollectLedger
from .General import GeneralLedger


def detect_ledger_type(lines: list) -> str:
    """ 检测账目类型 """
    has_life_title = False
    has_month_title = False
    has_collect_title = False
    has_general_title = False
    
    for line in lines:
        if line.type == LineType.LIFE_TITLE:
            has_life_title = True
        elif line.type == LineType.MONTH_TITLE:
            has_month_title = True
        elif line.type == LineType.COLLECT_TITLE:
            has_collect_title = True
        elif line.type == LineType.GENERAL_TITLE:
            has_general_title = True
        else:
            continue
    
    # 检测逻辑
    if has_life_title and not has_general_title:
        return 'life'
    elif has_month_title and not has_general_title:
        return 'month'
    elif has_collect_title and not has_general_title:
        return 'collect'
    elif has_general_title:
        return 'general'
    else:
        return ''


def create_ledger_from_lines(lines) -> Union[LifeLedger, MonthLedger, CollectLedger, GeneralLedger]:
    """ 从Line对象列表创建账目 """
    ledger_type = detect_ledger_type(lines)
    
    if ledger_type == 'life':
        return LifeLedger.parse_lines(lines)
    elif ledger_type == 'collect':
        return CollectLedger.parse_lines(lines)
    elif ledger_type == 'month':
        return MonthLedger.parse_lines(lines)
    elif ledger_type == 'general':
        return GeneralLedger.parse_lines(lines)
    else:
        raise ValueError("无法识别的账目类型")


def create_ledger_from_text(text: str) -> Union[LifeLedger, MonthLedger, CollectLedger, GeneralLedger]:
    """ 从文本创建账目 """
    raw_lines = text.splitlines()
    lines = [Line.parse(raw) for raw in raw_lines]
    return create_ledger_from_lines(lines)


def create_ledger_from_file(filepath: str, encoding: str = "utf-8") -> Union[LifeLedger, MonthLedger, CollectLedger, GeneralLedger]:
    """ 从文件创建账目 """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")
    with open(filepath, "r", encoding=encoding) as f:
        text = f.read()
    return create_ledger_from_text(text)
