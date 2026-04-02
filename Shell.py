# File:        Shell.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-04-01
# Description: 交互式命令行

import cmd
import shlex
from colorama import Fore, Style

from LedgerHub import LedgerHub
from Engine import Engine


# ======================================== #
#    工具函数
# ======================================== #

def _parse(arg: str) -> list[str]:
    """把arg字符串安全拆分成token列表"""
    try:
        return shlex.split(arg)
    except ValueError as e:
        raise ValueError(f"参数解析出错: {e}") from e


def _require(parts: list[str], n: int, usage: str):
    """检查参数数量"""
    if len(parts) < n:
        raise ValueError(f"参数不足 用法: {usage}")


# ======================================== #
#    Shell
# ======================================== #

class Shell(cmd.Cmd):

    intro  = " "
    prompt = "CMD > "

    def __init__(self, hub: LedgerHub, engine: Engine):
        super().__init__()
        self._hub    = hub
        self._engine = engine

    # ----- 内部辅助 -------------------- #

    def _run(self, fn):
        try:
            fn()
        except ValueError as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} {e}")
        except KeyError as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} 找不到账目: {e}")
        except Exception as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} 执行出错: {e}")

    def emptyline(self):
        pass

    def default(self, line):
        print(f"{Fore.RED}[!]{Style.RESET_ALL} 未知命令: {line.split()[0]}")

    # ----- 查看 -------------------- #

    def do_ts(self, _):
        """ts"""
        def run():
            sum_ledger = self._hub.get_sum_ledger()
            filepath   = self._hub.get_filepath("sum")
            timestamp  = sum_ledger.tail.timestamp
            print(f"  {filepath:<14} {timestamp if timestamp else 'NONE'}")

            for name in self._hub.list_ledger_alias():
                ledger    = self._hub.get_ledger(name)
                filepath  = self._hub.get_filepath(name)
                timestamp = ledger.tail.timestamp
                print(f"  {filepath:<14} {timestamp if timestamp else 'NONE'}")
        self._run(run)

    def do_ls(self, _):
        """ls"""
        def run():
            alias_list = self._hub.list_ledger_alias()
            for alias in alias_list:
                ledger = self._hub.get_ledger(alias)
                name   = self._hub.get_name(alias)
                print(f"\n── {name} ──")
                for seg in ledger.segments:
                    print(f"  {seg.name}")
        self._run(run)

    def do_print(self, arg):
        """print <账目别名> [分段名]"""
        def run():
            parts = _parse(arg)
            _require(parts, 1, "print <账目别名> [分段名]")
            ledger = self._hub.get_ledger(parts[0])

            if len(parts) == 1:
                print(ledger.to_raw())
            else:
                seg = ledger.get_segment(parts[1])
                if seg is None:
                    raise ValueError(f"找不到区间: {parts[1]}")
                print(seg.to_raw())
        self._run(run)

    def do_aggr(self, arg):
        """aggr [<账目别名> [分段名]]"""
        def run():
            parts = _parse(arg)

            if not parts:
                for alias in self._hub.list_ledger_alias():
                    self._engine.show_ledger_aggr(alias)
                return

            alias = parts[0]
            ledger = self._hub.get_ledger(alias)

            if len(parts) == 1:
                self._engine.show_ledger_aggr(alias)
            else:
                self._engine.show_segment_aggr(alias, parts[1])
        self._run(run)

    # ----- 校验 -------------------- #

    def do_check(self, arg):
        """check [账目]"""
        def run():
            parts = _parse(arg)
            alias_list = [parts[0]] if parts else self._hub.list_ledger_alias()

            for alias in alias_list:
                ledger = self._hub.get_ledger(alias)
                name = self._hub.get_name(alias)
                for seg in ledger.segments:
                    ok = seg.validate_aggr()
                    flag = (f"{Fore.GREEN}OK{Style.RESET_ALL}"
                            if ok else
                            f"{Fore.RED}FAIL{Style.RESET_ALL}")
                    print(f"  [{flag}] {name} / {seg.name}")
        self._run(run)

    # ----- 操作 -------------------- #

    def do_rebuild(self, arg):
        """rebuild [账目]"""
        def run():
            parts = _parse(arg)
            alias = parts[0] if parts and parts[0] in self._hub.list_ledger_alias() else None

            if not parts:
                self._engine.rebuild()
            elif parts[0] == "sum":
                self._hub.get_sum_ledger().rebuild_ledger()
            elif parts[0] in self._hub.list_ledger_alias():
                self._hub.get_ledger(alias).rebuild_ledger()
            else:
                raise ValueError(f"未知账目: {parts[0]}")
        self._run(run)

    def do_sync(self, arg):
        """sync <month|life|collect>"""
        def run():
            parts = _parse(arg)
            #_require(parts, 1, "sync <month|life|collect>")

            if not parts:
                self._engine.sync_all()
                print(f"  所有账目已同步")
            elif parts[0] == "month":
                self._engine.sync_month()
                print(f"  Month 已同步")
            elif parts[0] == "life":
                self._engine.sync_life()
                print(f"  Life 已同步")
            elif parts[0] == "collect":
                self._engine.sync_collect()
                print(f"  Collect 已同步")
            else:
                raise ValueError(f"未知同步目标: {parts[0]}")
        self._run(run)

    def do_update(self, _):
        """update"""
        def run():
            self._engine.update()
        self._run(run)

    def do_save(self, arg):
        """save [账目]"""
        def run():
            parts = _parse(arg)
            if parts:
                if parts[0] == "sum":
                    self._hub.save_sum_ledger()
                    print(f"  汇总账目已保存")
                else:
                    self._hub.save_ledger(parts[0])
                    print(f"  {parts[0]} 已保存")
            else:
                self._hub.save_all()
        self._run(run)

    def do_reload(self, arg):
        """reload [账目]"""
        def run():
            parts = _parse(arg)
            if parts:
                if parts[0] == "sum":
                    self._hub.reload_sum_ledger()
                    print(f"  汇总账目已重载")
                else:
                    self._hub.reload_ledger(parts[0])
                    print(f"  {parts[0]} 已重载")
            else:
                self._hub.reload_all()
                print("  所有账目已重载")
        self._run(run)

    # ----- Debug -------------------- #

    def do_dump(self, arg):
        """dump [账目]"""
        def run():
            parts = _parse(arg)
            if parts and parts[0] == "sum":
                self._hub.get_sum_ledger().dump()
            elif parts:
                self._hub.get_ledger(parts[0]).dump()
            else:
                for name in self._hub.list_ledger_alias():
                    print(f"\nLedger: {name}")
                    self._hub.get_ledger(name).dump()
        self._run(run)

    def do_repr(self, arg):
        """repr [账目]"""
        def run():
            parts = _parse(arg)
            if parts and parts[0] == "sum":
                print(self._hub.get_sum_ledger().__repr__())
            elif parts:
                print(self._hub.get_ledger(parts[0]).__repr__())
            else:
                name = self._hub.get_name("sum")
                print(f"\n── {name} ──")
                print(self._hub.get_sum_ledger().__repr__())
                for alias in self._hub.list_ledger_alias():
                    name = self._hub.get_name(alias)
                    print(f"\n── {name} ──")
                    print(self._hub.get_ledger(alias).__repr__())
        self._run(run)

    def do_test(self, _):
        """test"""
        def run():
            month_list = self._engine._get_month_list()
            print(f"Month List: {month_list}")
        self._run(run)

    # ----- 退出 -------------------- #

    def do_quit(self, _):
        """quit"""
        return self._quit()

    def do_q(self, _):
        """q"""
        return self._quit()

    def _quit(self):
        print("Bye!")
        return True
    
    # ----- END -------------------- #
