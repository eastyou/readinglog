"""命令行入口：生成可打印的阅读记录表。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from .model import Book, ReadinglogError, load_books, total_pages
from .render import DEFAULT_ROWS, MAX_ROWS, MIN_ROWS, render_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readinglog",
        description="阅读记录表：从书目 CSV 生成 A4 可打印阅读记录",
    )
    parser.add_argument("--version", action="version", version="readinglog 0.1.0")
    parser.add_argument(
        "-i",
        "--input",
        default=None,
        help="书目 CSV（书名,作者,页数）；不传则生成空白表",
    )
    parser.add_argument(
        "-o", "--output", default="阅读记录.html", help="输出 HTML 路径"
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help="每页行数 %d~%d，默认 %d" % (MIN_ROWS, MAX_ROWS, DEFAULT_ROWS),
    )
    parser.add_argument("--title", default="阅读记录", help="页面标题")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        books: List[Book] = load_books(args.input) if args.input else []
        page = render_html(books, title=args.title, rows=args.rows)
    except ReadinglogError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("错误: 读取书目失败: %s" % exc, file=sys.stderr)
        return 1

    try:
        Path(args.output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    pages = max(1, (len(books) + args.rows - 1) // args.rows)
    print(
        "已生成 %s：共 %d 本书，合计 %d 页，每页 %d 行，共 %d 页"
        % (args.output, len(books), total_pages(books), args.rows, pages)
    )
    print("用浏览器打开后按 Ctrl/Cmd + P，纸张选 A4 纵向即可打印")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
