"""阅读记录数据模型：CSV 解析、字段校验与统计。"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

MAX_TITLE = 60
MAX_AUTHOR = 20
MAX_PAGES = 10000

TITLE_HEADERS = {"书名", "图书", "阅读书目", "书目"}
AUTHOR_HEADERS = {"作者", "著者"}
PAGES_HEADERS = {"页数", "页码", "总页数"}


class ReadinglogError(ValueError):
    """阅读记录数据或参数不合法。"""


@dataclass(frozen=True)
class Book:
    """一本要读的书：书名、页数与可选的作者。"""

    title: str
    pages: int
    author: str = ""

    def __post_init__(self) -> None:
        title = _clean(self.title)
        author = _clean(self.author)
        if not title:
            raise ReadinglogError("书名不能为空")
        _check_length(title, MAX_TITLE, "书名")
        _check_length(author, MAX_AUTHOR, "作者")
        if isinstance(self.pages, bool) or not isinstance(self.pages, int):
            raise ReadinglogError("页数必须是整数")
        if not 1 <= self.pages <= MAX_PAGES:
            raise ReadinglogError(
                "页数必须在 1~%d 之间，当前是 %d" % (MAX_PAGES, self.pages)
            )
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "author", author)


def _clean(value: str) -> str:
    if not isinstance(value, str):
        raise ReadinglogError("字段必须是文本，当前是 %r" % (value,))
    return value.strip()


def _check_length(value: str, limit: int, label: str) -> None:
    if len(value) > limit:
        raise ReadinglogError(
            "%s最多 %d 个字符，当前 %d 个：%s" % (label, limit, len(value), value)
        )


def _is_header(cells: Sequence[str]) -> bool:
    if not cells or cells[0] not in TITLE_HEADERS:
        return False
    return len(cells) < 2 or cells[1] in AUTHOR_HEADERS


def decode_bytes(data: bytes) -> str:
    """按 UTF-8（含 BOM）优先、GBK 兜底的顺序解码。"""
    if not isinstance(data, (bytes, bytearray)):
        raise ReadinglogError("文件内容必须是字节")
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return bytes(data).decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ReadinglogError("无法识别文件编码，请另存为 UTF-8 或 GBK 后重试")


def _parse_pages(text: str) -> int:
    if not text.isdigit():
        raise ReadinglogError("页数必须是正整数：%s" % (text or "空"))
    return int(text)


def parse_csv(text: str, source: str = "输入内容") -> List[Book]:
    """解析 CSV 文本；表头可选，返回有效的书目列表。"""
    if not isinstance(text, str):
        raise ReadinglogError("CSV 内容必须是文本")
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text))
    books: List[Book] = []
    for line_no, row in enumerate(reader, start=1):
        cells = [cell.strip() for cell in row]
        if not any(cells):
            continue
        if not books and _is_header(cells):
            continue
        if len(cells) > 3:
            raise ReadinglogError(
                "%s 第 %d 行有 %d 列，最多 3 列（书名,作者,页数）"
                % (source, line_no, len(cells))
            )
        title = cells[0] if len(cells) > 0 else ""
        author = cells[1] if len(cells) > 1 else ""
        pages_text = cells[2] if len(cells) > 2 else ""
        if not title:
            raise ReadinglogError("%s 第 %d 行缺少书名" % (source, line_no))
        if not pages_text:
            raise ReadinglogError("%s 第 %d 行缺少页数" % (source, line_no))
        try:
            books.append(
                Book(title=title, author=author, pages=_parse_pages(pages_text))
            )
        except ReadinglogError as exc:
            raise ReadinglogError("%s 第 %d 行：%s" % (source, line_no, exc)) from exc
    if not books:
        raise ReadinglogError("%s 中没有有效的书目记录" % source)
    return books


def load_books(path: str) -> List[Book]:
    """读取 CSV 文件并解析；文件不存在或编码错误时抛出异常。"""
    target = Path(path)
    return parse_csv(decode_bytes(target.read_bytes()), source=str(target))


def total_pages(books: Sequence[Book]) -> int:
    """所有书目的页数合计。"""
    if not isinstance(books, (list, tuple)):
        raise ReadinglogError("books 必须是书目列表")
    total = 0
    for book in books:
        if not isinstance(book, Book):
            raise ReadinglogError("书目列表里出现了非 Book 对象")
        total += book.pages
    return total


def paginate(
    books: Sequence[Book], rows: int
) -> List[List[Tuple[int, Book]]]:
    """按每页行数分页；返回每页的（序号, 书目）列表，末页可不满。"""
    if not isinstance(books, (list, tuple)):
        raise ReadinglogError("books 必须是书目列表")
    if isinstance(rows, bool) or not isinstance(rows, int):
        raise ReadinglogError("每页行数必须是整数")
    if not 6 <= rows <= 24:
        raise ReadinglogError("每页行数必须在 6~24 之间，当前是 %d" % rows)
    for book in books:
        if not isinstance(book, Book):
            raise ReadinglogError("书目列表里出现了非 Book 对象")
    if not books:
        return [[]]
    pages: List[List[Tuple[int, Book]]] = []
    for start in range(0, len(books), rows):
        chunk = books[start : start + rows]
        pages.append(
            [(start + offset + 1, book) for offset, book in enumerate(chunk)]
        )
    return pages


def format_books(books: Sequence[Book]) -> str:
    """把书目排成 CSV 文本，方便回写或调试。"""
    if not books:
        raise ReadinglogError("没有可输出的书目")
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["书名", "作者", "页数"])
    for book in books:
        if not isinstance(book, Book):
            raise ReadinglogError("书目列表里出现了非 Book 对象")
        writer.writerow([book.title, book.author, book.pages])
    return buffer.getvalue()
