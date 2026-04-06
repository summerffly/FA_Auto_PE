# Segment/__init__.py

from .Section import BaseSection, LifeSection, MonthSection, CollectSection, make_section
from .MiniSection import BaseMiniSection, LifeMiniSection, CollectMiniSection, TotalMiniSection, make_minisection
from .Block import BaseBlock, TailBlock, make_tail_block
from .General import WealthBlock, ExtraBlock, ComboBlock, GeneralSection, make_general

__all__ = [
    'BaseSection', 'LifeSection', 'MonthSection', 'CollectSection', 'make_section',
    'BaseMiniSection', 'LifeMiniSection', 'CollectMiniSection', 'TotalMiniSection', 'make_minisection',
    'BaseBlock', 'TailBlock', 'make_tail_block',
    'WealthBlock', 'ExtraBlock', 'ComboBlock', 'GeneralSection', 'make_general'
]
