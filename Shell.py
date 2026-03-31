# File:        Shell.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-30
# Description: 交互式命令行

import cmd
import shlex
from unicodedata import name
from colorama import Fore, Style
from wcwidth import wcswidth

import LedgerHub as hub
import Engine as engine


# ----- 工具函数 -------------------- #

def _parse(arg: str) -> list[str]:
    """把 arg 字符串安全拆分成 token 列表（支持引号包裹的描述）。"""
    try:
        return shlex.split(arg)
    except ValueError as e:
        raise ValueError(f"参数解析出错: {e}") from e


def _require(parts: list[str], n: int, usage: str):
    """检查参数数量，不足时抛 ValueError。"""
    if len(parts) < n:
        raise ValueError(f"参数不足 用法: {usage}")


def _print_section_summary(ledger, sec_name: str):
    sec = ledger.get_segment(sec_name)
    if sec is None:
        print(f"  [!] 找不到区间: {sec_name}")
        return
    total = sec.calc_units_sum()
    sign  = "+" if total >= 0 else ""
    print(f"  {sec.name:<20} {sign}{total}")


def _pad_right(text: str, width: int) -> str:
    w = wcswidth(text)
    if w >= width:
        return text
    return text + " " * (width - w)


def _print_ledger_summary(name: str):
    ledger = hub.get_ledger(name)
    print(f"\n── {hub.LEDGER_FILES[name]} ──")
    for seg in ledger.segments:
        total = seg.calc_units_sum()
        sign  = "+" if total >= 0 else ""
        seg_name = _pad_right(seg.name, 15)
        print(f"  {seg_name} {sign}{total}")


# ======================================== #
#    Shell
# ======================================== #

class Shell(cmd.Cmd):

    #intro = f"{Fore.CYAN}Start Shell{Style.RESET_ALL}"
    intro = f" "
    prompt = "CMD > "

    # ----- 内部辅助 -------------------- #

    def _run(self, fn):
        try:
            fn()
        except ValueError as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} {e}")
        except KeyError as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} 找不到账本: {e}")
        except Exception as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} 执行出错: {e}")

    def emptyline(self):
        pass

    def default(self, line):
        print(f"{Fore.RED}[!]{Style.RESET_ALL} 未知命令: {line.split()[0]}")

    # ----- 查看 -------------------- #

    def do_ls(self, _):
        """ls"""
        def run():
            names = hub.list_ledgers()
            if not names:
                print("（无已加载账本）")
                return
            for name in names:
                ledger = hub.get_ledger(name)
                print(f"  {hub.LEDGER_FILES[name]:<14} {len(ledger.segments)} 个分段")
        self._run(run)

    def do_ts(self, _):
        """ts"""
        def run():
            for name in hub.list_ledgers():
                ledger = hub.get_ledger(name)
                timestamp = ledger.tail.timestamp
                if timestamp:
                    print(f"  {hub.LEDGER_FILES[name]:<14} {timestamp}")
                else:
                    print(f"  {hub.LEDGER_FILES[name]:<14} NONE")
        self._run(run)

    def do_show(self, arg):
        """show <账本> [月份]  显示账本内容，月份可选（如 life.M03）"""
        def run():
            parts = _parse(arg)
            _require(parts, 1, "show <账本> [月份]")
            ledger = hub.get_ledger(parts[0])

            if len(parts) == 1:
                # 显示全部
                print(ledger.to_raw())
            else:
                # 显示指定 segment
                seg = ledger.get_segment(parts[1])
                if seg is None:
                    raise ValueError(f"找不到区间: {parts[1]}")
                print(seg.to_raw())
        self._run(run)

    def do_summary(self, arg):
        """summary [<账本> [月份|all]]  收支汇总；不带参数则汇总所有账本所有区间"""
        def run():
            parts = _parse(arg)

            if not parts:
                # 汇总所有
                for name in hub.list_ledgers():
                    _print_ledger_summary(name)
                return

            name = parts[0]
            ledger = hub.get_ledger(name)

            if len(parts) == 1 or parts[1].lower() == "all":
                _print_ledger_summary(name)
            else:
                _print_section_summary(ledger, parts[1])
        self._run(run)

    # ----- 校验 -------------------- #

    def do_check(self, arg):
        """check [ledger]"""
        def run():
            parts  = _parse(arg)
            names  = [parts[0]] if parts else hub.list_ledgers()
            ok_all = True
            for name in names:
                ledger = hub.get_ledger(name)
                for seg in ledger.segments:
                    ok = seg.validate_summary()
                    flag = f"{Fore.GREEN}OK{Style.RESET_ALL}" if ok else f"{Fore.RED}FAIL{Style.RESET_ALL}"
                    if not ok:
                        ok_all = False
                    print(f"  [{flag}] {name} / {seg.name}")
            if ok_all:
                print("  全部校验通过")
        self._run(run)

    # ----- 汇总重建 -------------------- #

    def do_rebuild(self, arg):
        """rebuild [ledger]"""
        def run():
            parts = _parse(arg)
            names = [parts[0]] if parts else hub.list_ledgers()
            for name in names:
                hub.get_ledger(name).rebuild_ledger()
                print(f"  {name} 重建完成")
        self._run(run)

    def do_sync(self, arg):
        """sync <month|life|title>"""
        def run():
            parts = _parse(arg)
            _require(parts, 1, "sync <month|life|title>")
            if parts[0] == "month":
                engine.sync_month()
                print(f"  Month 已同步")
            elif parts[0] == "life":
                engine.sync_life()
                print(f"  Life 已同步")
            elif parts[0] == "title":
                engine.sync_title()
                print(f"  Title 已同步")
        self._run(run)

    # ----- 保存 -------------------- #

    def do_save(self, arg):
        """save [ledger]"""
        def run():
            parts = _parse(arg)
            if parts:
                hub.save_ledger(parts[0])
                print(f"  {parts[0]} 已保存")
            else:
                hub.save_all()
                print("  所有账本已保存")
        self._run(run)

    def do_reload(self, arg):
        """reload [ledger]"""
        def run():
            parts = _parse(arg)
            if parts:
                hub.reload_ledger(parts[0])
                print(f"  {parts[0]} 已重载")
            else:
                hub.reload_all()
                print("  所有账本已重载")
        self._run(run)

    # ----- Debug -------------------- #

    def do_dump(self, arg):
        """dump [ledger]"""
        def run():
            parts = _parse(arg)
            if parts and parts[0] == "sum":
                hub.get_sum_ledger().dump()
            elif parts:
                hub.get_ledger(parts[0]).dump()
            else:
                for name in hub.list_ledgers():
                    print(f"\nLedger: {name}")
                    hub.get_ledger(name).dump()
        self._run(run)

    def do_repr(self, arg):
        """repr [ledger]"""
        def run():
            parts = _parse(arg)
            if parts and parts[0] == "sum":
                print(hub.get_sum_ledger().__repr__())
            if parts:
                print(hub.get_ledger(parts[0]).__repr__())
            else:              
                for name in hub.list_ledgers():
                    print(f"\nLedger: {name}")
                    print(hub.get_ledger(name).__repr__())
        self._run(run)

    def do_test(self, _):
        """test"""
        def run():
            print(f"Month List: {engine.month_list}")
        self._run(run)

    # ----- Quit -------------------- #

    def do_quit(self, _):
        """quit"""
        return self._quit()

    def do_q(self, _):
        """q"""
        return self._quit()

    def do_exit(self, _):
        """exit"""
        return self._quit()

    def _quit(self):
        print("Bye!")
        return True
    
    # ----- END -------------------- #
