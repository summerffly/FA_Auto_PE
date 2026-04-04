#!/usr/bin/env python3

import os
import sys
from colorama import Fore, Style

from LedgerHub import LedgerHub
from Engine import Engine
from Viewer import Viewer
from Shell import Shell
from __about__ import APP_VERSION, BUILD_DATE

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

def _get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        # PyInstaller打包后 sys.frozen = True
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


banner = rf"""
{'─'*57}
{'─'*57}
{'─'*2}                                                     {'─'*2}
{'─'*2}      {Style.BRIGHT}{Fore.YELLOW} ____   __         __    _    _____  ___ {Style.RESET_ALL}      {'─'*2}
{'─'*2}      {Style.BRIGHT}{Fore.YELLOW}| |_   / /\       / /\  | | |  | |  / / \{Style.RESET_ALL}      {'─'*2}
{'─'*2}      {Style.BRIGHT}{Fore.YELLOW}|_|   /_/--\     /_/--\ \_\_/  |_|  \_\_/{Style.RESET_ALL}      {'─'*2}
{'─'*2}                                                     {'─'*2}
{'─'*2}                                                     {'─'*2}
{'─'*2}   {'─'*47}   {'─'*2}
{'─'*2}                                                     {'─'*2}
{'─'*2}      Version: {Fore.CYAN}{APP_VERSION:<36}{Style.RESET_ALL}  {'─'*2}
{'─'*2}      Date:    {Fore.CYAN}{BUILD_DATE:<36}{Style.RESET_ALL}  {'─'*2}
{'─'*2}      Dir:     {_get_base_dir():<36}  {'─'*2}
{'─'*2}                                                     {'─'*2}
{'─'*57}
{'─'*57}
"""


bannner = rf"""
{Fore.CYAN}{'─'*50}{Style.RESET_ALL}
{Fore.YELLOW}
            ███████╗  █████╗
            ██╔════╝ ██╔══██╗
            █████╗   ███████║
            ██╔══╝   ██╔══██║
            ██║      ██║  ██║
            ╚═╝      ╚═╝  ╚═╝
{Style.RESET_ALL}
{Fore.CYAN}{'─'*50}{Style.RESET_ALL}

    Version: {Fore.CYAN}{APP_VERSION}{Style.RESET_ALL}
    Build:   {Fore.CYAN}{BUILD_DATE}{Style.RESET_ALL}
    Path:    {Fore.WHITE}{_get_base_dir()}{Style.RESET_ALL}

{Fore.CYAN}{'─'*50}{Style.RESET_ALL}
"""


# ======================================== #
#    Main Entry
# ======================================== #

def main():
    print(banner)

    # 切换工作目录
    base_dir = _get_base_dir()
    os.chdir(base_dir)

    # 创建实例
    hub = LedgerHub()
    engine = Engine(hub)
    viewer = Viewer(hub)

    # 初始化
    try:
        hub.init()
        engine.validate()
        print(f"\n{Fore.CYAN}{'-'*50}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!]{Style.RESET_ALL} 账目加载失败: {e}")
        return
    
    # 启动Shell
    Shell(hub, engine, viewer).cmdloop()


if __name__ == "__main__":
    main()
