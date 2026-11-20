"""把阅读记录渲染成可打印的 A4 纵向表格。"""

from __future__ import annotations

import html
from typing import List, Optional, Sequence, Tuple

from .model import Book, ReadinglogError, paginate, total_pages

PAGE_WIDTH_MM = 210.0
PAGE_HEIGHT_MM = 297.0
MIN_ROWS = 6
MAX_ROWS = 24
DEFAULT_ROWS = 18

COLUMNS: List[Tuple[str, str]] = [
    ("序号", "7%"),
    ("书名", "31%"),
    ("作者", "17%"),
    ("页数", "8%"),
    ("开始", "13%"),
    ("完成", "13%"),
    ("签字", "11%"),
]


def row_height_mm(rows: int) -> float:
    """按每页行数计算行高，行数多时自动压缩。"""
    if isinstance(rows, bool) or not isinstance(rows, int):
        raise ReadinglogError("每页行数必须是整数")
    if not MIN_ROWS <= rows <= MAX_ROWS:
        raise ReadinglogError(
            "每页行数必须在 %d~%d 之间，当前是 %d" % (MIN_ROWS, MAX_ROWS, rows)
        )
    return min(12.0, 216.0 / rows)


def _num(value: float) -> str:
    text = "%.2f" % value
    return text.rstrip("0").rstrip(".") if "." in text else text


def _info_markup() -> str:
    return (
        '<div class="info">'
        "<span><b>姓名</b><i></i></span>"
        "<span><b>班级</b><i></i></span>"
        "<span><b>日期</b><i></i></span>"
        "</div>"
    )


def _table_markup(
    books: Sequence[Book],
    start: int,
    rows: int,
) -> str:
    heads = "".join("<th>%s</th>" % label for label, _ in COLUMNS)
    widths = "".join(
        '<col style="width:%s">' % width for _, width in COLUMNS
    )

    body: List[str] = []
    for slot in range(rows):
        position = start + slot
        book: Optional[Book] = books[position] if position < len(books) else None
        number = position + 1
        if book is None:
            cells = (
                '<td class="idx">%d</td><td></td><td></td><td></td>'
                "<td></td><td></td><td></td>"
            ) % number
        else:
            cells = (
                '<td class="idx">%d</td>'
                '<td class="title">%s</td>'
                '<td class="author">%s</td>'
                '<td class="num">%d</td>'
                "<td></td><td></td><td></td>"
            ) % (
                number,
                html.escape(book.title),
                html.escape(book.author),
                book.pages,
            )
        body.append("<tr>%s</tr>" % cells)

    return (
        '<table class="log">'
        "<colgroup>%s</colgroup>"
        "<thead><tr>%s</tr></thead>"
        "<tbody>%s</tbody>"
        "</table>"
        % (widths, heads, "".join(body))
    )


def render_html(
    books: Sequence[Book],
    title: str = "阅读记录",
    rows: int = DEFAULT_ROWS,
) -> str:
    """生成完整 HTML；书目跨页，末页补空行。"""
    if not isinstance(books, (list, tuple)):
        raise ReadinglogError("books 必须是书目列表")
    for book in books:
        if not isinstance(book, Book):
            raise ReadinglogError("书目列表里出现了非 Book 对象")
    if not isinstance(title, str) or not title.strip():
        raise ReadinglogError("标题不能为空")
    if isinstance(rows, bool) or not isinstance(rows, int):
        raise ReadinglogError("每页行数必须是整数")
    if not MIN_ROWS <= rows <= MAX_ROWS:
        raise ReadinglogError(
            "每页行数必须在 %d~%d 之间，当前是 %d" % (MIN_ROWS, MAX_ROWS, rows)
        )

    height = row_height_mm(rows)
    pages = paginate(books, rows)
    total = len(pages)
    count = len(books)
    pages_total = total_pages(books)

    sheets: List[str] = []
    for page_index in range(total):
        start = page_index * rows
        table = _table_markup(books, start, rows)
        label = html.escape(title.strip())
        if page_index:
            label += "（续）"
        head = '<header class="head"><h1>%s</h1>' % label
        if page_index == 0:
            head += _info_markup()
        head += "</header>"
        footer = (
            '<footer class="foot"><span>共 %d 本书 · 合计 %d 页</span>'
            "<span>第 %d / %d 页</span></footer>"
            % (count, pages_total, page_index + 1, total)
        )
        sheets.append(
            '<section class="sheet">%s%s%s</section>' % (head, table, footer)
        )

    toolbar = (
        '<div class="toolbar"><strong>%s</strong>'
        "<span>共 %d 本书 · 合计 %d 页 · 每页 %d 行 · 共 %d 页</span></div>"
        % (
            html.escape(title.strip()),
            count,
            pages_total,
            rows,
            total,
        )
    )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n%s\n</body>\n</html>\n"
        % (
            html.escape(title.strip()),
            _style(height),
            toolbar,
            "\n".join(sheets),
        )
    )


def _style(height: float) -> str:
    template = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 8mm 0 12mm;
    background: #e2e8f0;
    color: #0f172a;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  }
  .toolbar {
    width: 210mm;
    margin: 0 auto 6mm;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    color: #334155;
    font-size: 13px;
  }
  .toolbar strong { font-size: 15px; letter-spacing: 1px; }
  .toolbar span { color: #64748b; font-size: 12px; }
  .sheet {
    width: 210mm;
    height: 297mm;
    margin: 0 auto 8mm;
    padding: 14mm 15mm 10mm;
    background: #fff;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.14);
    display: flex;
    flex-direction: column;
    page-break-after: always;
    break-after: page;
    overflow: hidden;
  }
  .sheet:last-child { page-break-after: auto; break-after: auto; }
  .head { text-align: center; margin-bottom: 4mm; }
  .head h1 {
    margin: 0 0 3mm;
    font-size: 22pt;
    font-weight: 600;
    letter-spacing: 6pt;
  }
  .info {
    display: flex;
    justify-content: space-between;
    font-size: 11pt;
    color: #334155;
  }
  .info span {
    flex: 0 0 31%;
    display: flex;
    align-items: flex-end;
    gap: 2mm;
  }
  .info b { font-weight: 400; white-space: nowrap; }
  .info i {
    flex: 1;
    height: 4.5mm;
    border-bottom: 0.3mm solid #94a3b8;
  }
  table.log {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    font-size: 11pt;
  }
  table.log th,
  table.log td {
    border: 0.25mm solid #94a3b8;
    padding: 1mm 1.5mm;
    text-align: center;
    vertical-align: middle;
    overflow: hidden;
    overflow-wrap: anywhere;
  }
  table.log th {
    height: 9mm;
    background: #f1f5f9;
    font-weight: 600;
  }
  table.log tbody td { height: __ROW_HEIGHT__mm; }
  table.log td.title,
  table.log td.author { text-align: left; }
  .foot {
    margin-top: auto;
    padding-top: 2mm;
    display: flex;
    justify-content: space-between;
    font-size: 9pt;
    color: #64748b;
    border-top: 0.2mm solid #e2e8f0;
  }
  @page { size: A4 portrait; margin: 0; }
  @media print {
    body { background: #fff; padding: 0; }
    .toolbar { display: none; }
    .sheet { margin: 0; box-shadow: none; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""
    return template.replace("__ROW_HEIGHT__", _num(height))
