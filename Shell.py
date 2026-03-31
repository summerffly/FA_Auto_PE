# File:        Shell.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-31
# Description: 交互式命令行

import cmd
import shlex
from colorama import Fore, Style
from wcwidth import wcswidth

from LedgerHub import LedgerHub
from Engine import Engine


# ======================================== #
#    工具函数
# ======================================== #

def _parse(arg: str) -> list[str]:
    """把arg字符串安全拆分成token列表（支持引号包裹的描述）"""
    try:
        return shlex.split(arg)
    except ValueError as e:
        raise ValueError(f"参数解析出错: {e}") from e


def _require(parts: list[str], n: int, usage: str):
    """检查参数数量，不足时抛ValueError"""
    if len(parts) < n:
        raise ValueError(f"参数不足 用法: {usage}")


def _pad_right(text: str, width: int) -> str:
    w = wcswidth(text)
    if w >= width:
        return text
    return text + " " * (width - w)


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

    # ======================================== #
    #    内部辅助
    # ======================================== #

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

    def _print_section_summary(self, ledger, sec_name: str):
        sec = ledger.get_segment(sec_name)
        if sec is None:
            print(f"  [!] 找不到区间: {sec_name}")
            return
        total = sec.calc_units_sum()
        sign  = "+" if total >= 0 else ""
        print(f"  {sec.name:<20} {sign}{total}")

    def _print_ledger_summary(self, name: str):
        ledger = self._hub.get_ledger(name)
        name = self._hub.get_name(name)
        print(f"\n── {name} ──")
        for seg in ledger.segments:
            total    = seg.calc_units_sum()
            sign     = "+" if total >= 0 else ""
            seg_name = _pad_right(seg.name, 15)
            print(f"  {seg_name} {sign}{total}")

    # ======================================== #
    #    查看命令
    # ======================================== #

    def do_ls(self, _):
        """ls"""
        def run():
            names = self._hub.list_ledger_alias()
            for name in names:
                ledger = self._hub.get_ledger(name)
                name   = self._hub.get_name(name)
                print(f"  {name:<10} {len(ledger.segments)} 个分段")
        self._run(run)

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

    def do_show(self, arg):
        """show <账本别名> [分段名]"""
        def run():
            parts = _parse(arg)
            _require(parts, 1, "show <账本别名> [分段名]")
            ledger = self._hub.get_ledger(parts[0])

            if len(parts) == 1:
                print(ledger.to_raw())
            else:
                seg = ledger.get_segment(parts[1])
                if seg is None:
                    raise ValueError(f"找不到区间: {parts[1]}")
                print(seg.to_raw())
        self._run(run)

    def do_summary(self, arg):
        """summary [<账本别名> [分段名|all]]"""
        def run():
            parts = _parse(arg)

            if not parts:
                for name in self._hub.list_ledger_alias():
                    self._print_ledger_summary(name)
                return

            name   = parts[0]
            ledger = self._hub.get_ledger(name)

            if len(parts) == 1 or parts[1].lower() == "all":
                self._print_ledger_summary(name)
            else:
                self._print_section_summary(ledger, parts[1])
        self._run(run)

    # ======================================== #
    #    校验命令
    # ======================================== #

    def do_check(self, arg):
        """check [账本]
        验证汇总行数值是否正确，不带参数则验证所有账本
        """
        def run():
            parts  = _parse(arg)
            names  = [parts[0]] if parts else self._hub.list_ledger_alias()
            ok_all = True

            for name in names:
                ledger = self._hub.get_ledger(name)
                for seg in ledger.segments:
                    ok   = seg.validate_summary()
                    flag = (f"{Fore.GREEN}OK{Style.RESET_ALL}"
                            if ok else
                            f"{Fore.RED}FAIL{Style.RESET_ALL}")
                    if not ok:
                        ok_all = False
                    print(f"  [{flag}] {name} / {seg.name}")

            if ok_all:
                print("  全部校验通过")
        self._run(run)

    # ======================================== #
    #    操作命令
    # ======================================== #

    def do_rebuild(self, arg):
        """rebuild [账本]
        重建汇总行数值，不带参数则重建所有账本
        """
        def run():
            parts = _parse(arg)
            names = [parts[0]] if parts else self._hub.list_ledger_alias()

            for name in names:
                self._hub.get_ledger(name).rebuild_ledger()
                print(f"  {name} 重建完成")

            self._hub.get_sum_ledger().rebuild_summary()
            print(f"  汇总账本重建完成")
        self._run(run)

    def do_sync(self, arg):
        """sync <month|life|title|all>
        同步数据：
          month — 将DGtler/KEEP/TB月账汇总写入life账本
          life  — 将life账本月度数据写入汇总账本
          title — 将DK/NS/travel/BOX项目账写入汇总账本
          all   — 依次执行 month → life → title
        """
        def run():
            parts = _parse(arg)
            _require(parts, 1, "sync <month|life|title|all>")

            if parts[0] == "month":
                self._engine.sync_month()
                print(f"  Month 已同步")
            elif parts[0] == "life":
                self._engine.sync_life()
                print(f"  Life 已同步")
            elif parts[0] == "title":
                self._engine.sync_title()
                print(f"  Title 已同步")
            elif parts[0] == "all":
                self._engine.sync_month()
                print(f"  [1/3] Month 已同步")
                self._engine.sync_life()
                print(f"  [2/3] Life 已同步")
                self._engine.sync_title()
                print(f"  [3/3] Title 已同步")
            else:
                raise ValueError(f"未知同步目标: {parts[0]}")
        self._run(run)

    def do_update(self, _):
        """update"""
        def run():
            self._engine.update()
        self._run(run)

    def do_save(self, arg):
        """save [账本]
        保存指定账本，不带参数则保存所有账本
        """
        def run():
            parts = _parse(arg)
            if parts:
                if parts[0] == "sum":
                    self._hub.save_sum_ledger()
                    print(f"  汇总账本已保存")
                else:
                    self._hub.save_ledger(parts[0])
                    print(f"  {parts[0]} 已保存")
            else:
                self._hub.save_all()
                print("  所有账本已保存")
        self._run(run)

    def do_reload(self, arg):
        """reload [账本]
        重载指定账本，不带参数则重载所有账本
        """
        def run():
            parts = _parse(arg)
            if parts:
                if parts[0] == "sum":
                    self._hub.reload_sum_ledger()
                    print(f"  汇总账本已重载")
                else:
                    self._hub.reload_ledger(parts[0])
                    print(f"  {parts[0]} 已重载")
            else:
                self._hub.reload_all()
                print("  所有账本已重载")
        self._run(run)

    # ======================================== #
    #    Debug命令
    # ======================================== #

    def do_dump(self, arg):
        """dump [账本|sum]
        打印账本内部结构，不带参数则打印所有账本
        """
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
        """repr [账本|sum]
        打印账本repr，不带参数则打印所有账本
        """
        def run():
            parts = _parse(arg)
            if parts and parts[0] == "sum":
                print(self._hub.get_sum_ledger().__repr__())
            elif parts:
                print(self._hub.get_ledger(parts[0]).__repr__())
            else:
                for name in self._hub.list_ledger_alias():
                    print(f"\nLedger: {name}")
                    print(self._hub.get_ledger(name).__repr__())
        self._run(run)

    def do_test(self, _):
        """test
        测试输出
        """
        def run():
            month_list = self._engine._get_month_list()
            print(f"Month List: {month_list}")
        self._run(run)

    # ======================================== #
    #    退出命令
    # ======================================== #

    def do_quit(self, _):
        """quit  退出程序"""
        return self._quit()

    def do_q(self, _):
        """q  退出程序"""
        return self._quit()

    def do_exit(self, _):
        """exit  退出程序"""
        return self._quit()

    def _quit(self):
        print("Bye!")
        return True
