#!/usr/bin/env python3

import sys
from Line import Line


def main():
    while True:
        print("> ", end="", flush=True)
        raw = sys.stdin.readline()
        if not raw:
            break
        raw = raw.rstrip("\n")
        
        if raw == "exit":
            break

        try:
            line = Line.parse(raw)
        except Exception as e:
            print(f"解析错误: {e}")
            continue

        print("TYPE:", line.type.name)

        if line.is_amount:
            print("value:", line.value)
            print("content:", line.content)


if __name__ == "__main__":
    main()
