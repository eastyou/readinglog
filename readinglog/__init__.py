"""readinglog：A4 可打印阅读记录表。"""

from __future__ import annotations

from .model import (
    MAX_AUTHOR,
    MAX_PAGES,
    MAX_TITLE,
    Book,
    ReadinglogError,
    decode_bytes,
    format_books,
    load_books,
    paginate,
    parse_csv,
    total_pages,
)
from .render import (
    COLUMNS,
    DEFAULT_ROWS,
    MAX_ROWS,
    MIN_ROWS,
    render_html,
    row_height_mm,
)

__version__ = "0.1.0"

__all__ = [
    "COLUMNS",
    "DEFAULT_ROWS",
    "MAX_AUTHOR",
    "MAX_PAGES",
    "MAX_ROWS",
    "MAX_TITLE",
    "MIN_ROWS",
    "Book",
    "ReadinglogError",
    "decode_bytes",
    "format_books",
    "load_books",
    "paginate",
    "parse_csv",
    "render_html",
    "row_height_mm",
    "total_pages",
    "__version__",
]
