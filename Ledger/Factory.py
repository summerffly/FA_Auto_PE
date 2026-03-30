# File:        Ledger/Factory.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-30
# LastEdit:    2026-03-30
# Description: Ledger工厂函数

from typing import Union

from Line import Line, LineType
from .Life import LifeLedger
from .Month import MonthLedger
from .Title import TitleLedger


def detect_ledger_type(lines: list) -> str:
    """ 检测账本类型 """
    has_life = False
    has_month_title = False
    has_sub_tag = False
    
    for line in lines:
        # 检查是否有life.Month标题
        if line.ltype == LineType.HEAD_TITLE and "life" in line.raw.lower():
            has_life = True
        # 检查是否有life.M0x分段
        if line.ltype == LineType.MONTH_TITLE and "life" in line.raw.lower():
            has_life = True
        # 检查是否有MONTH_TITLE
        if line.ltype == LineType.MONTH_TITLE and "life" not in line.raw.lower():
            has_month_title = True
        # 检查是否有SUB_TAG
        if line.ltype == LineType.SUB_TAG:
            has_sub_tag = True
    
    # 检测逻辑
    if has_life:
        return 'life'
    elif has_sub_tag and not has_month_title:
        return 'title'
    else:
        return 'month'


def create_ledger_from_lines(lines) -> Union[LifeLedger, MonthLedger, TitleLedger]:
    """ 从Line对象列表创建账本 """
    ledger_type = detect_ledger_type(lines)
    
    if ledger_type == 'life':
        return LifeLedger.parse_lines(lines)
    elif ledger_type == 'title':
        return TitleLedger.parse_lines(lines)
    else:
        return MonthLedger.parse_lines(lines)


def create_ledger_from_text(text: str) -> Union[LifeLedger, MonthLedger, TitleLedger]:
    """ 从文本创建账本 """
    raw_lines = text.splitlines()
    lines = [Line.parse(raw) for raw in raw_lines]
    return create_ledger_from_lines(lines)


def create_ledger_from_file(filepath: str, encoding: str = "utf-8") -> Union[LifeLedger, MonthLedger, TitleLedger]:
    """ 从文件创建账本 """
    with open(filepath, "r", encoding=encoding) as f:
        text = f.read()
    return create_ledger_from_text(text)


# 向后兼容的别名
#Ledger = Union[LifeLedger, MonthLedger, TitleLedger]
