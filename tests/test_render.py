"""阅读记录渲染测试。"""

from __future__ import annotations

import unittest

from readinglog.model import Book, ReadinglogError
from readinglog.render import (
    COLUMNS,
    DEFAULT_ROWS,
    render_html,
    row_height_mm,
)


def make_books(count: int) -> list:
    return [
        Book(title="书 %d" % index, author="作者 %d" % index, pages=100 + index)
        for index in range(1, count + 1)
    ]


class RowHeightTest(unittest.TestCase):
    def test_decreases_with_more_rows(self) -> None:
        self.assertGreaterEqual(row_height_mm(6), row_height_mm(18))
        self.assertGreater(row_height_mm(18), row_height_mm(24))

    def test_rejects_bad_rows(self) -> None:
        for rows in (5, 25, True, 6.5):
            with self.assertRaises(ReadinglogError):
                row_height_mm(rows)  # type: ignore[arg-type]


class RenderHtmlTest(unittest.TestCase):
    def test_blank_log(self) -> None:
        page = render_html([])
        self.assertEqual(page.count('class="sheet"'), 1)
        self.assertEqual(page.count('class="idx"'), DEFAULT_ROWS)
        self.assertIn("共 0 本书 · 合计 0 页", page)
        self.assertIn("第 1 / 1 页", page)

    def test_single_page(self) -> None:
        page = render_html(make_books(3))
        self.assertEqual(page.count('class="sheet"'), 1)
        self.assertEqual(page.count('class="idx"'), DEFAULT_ROWS)
        self.assertIn("书 1", page)
        self.assertIn("作者 1", page)
        self.assertIn("101", page)
        self.assertIn("共 3 本书 · 合计 %d 页" % (101 + 102 + 103), page)

    def test_paginates_and_repeats_header(self) -> None:
        page = render_html(make_books(19), rows=18)
        self.assertEqual(page.count('class="sheet"'), 2)
        self.assertEqual(page.count('class="idx"'), 36)
        self.assertIn("阅读记录（续）", page)
        self.assertIn("第 2 / 2 页", page)
        self.assertIn("书 19", page)

    def test_rows_setting(self) -> None:
        page = render_html(make_books(8), rows=6)
        self.assertEqual(page.count('class="sheet"'), 2)
        self.assertEqual(page.count('class="idx"'), 12)
        self.assertIn("第 1 / 2 页", page)
        self.assertIn("第 2 / 2 页", page)

    def test_column_labels(self) -> None:
        page = render_html([])
        for label, _ in COLUMNS:
            self.assertIn("<th>%s</th>" % label, page)

    def test_info_line(self) -> None:
        page = render_html([])
        for label in ("姓名", "班级", "日期"):
            self.assertIn("<b>%s</b>" % label, page)

    def test_escapes_title_and_book(self) -> None:
        books = [Book(title="<书>", pages=100)]
        page = render_html(books, title="<记录>")
        self.assertIn("&lt;书&gt;", page)
        self.assertIn("&lt;记录&gt;", page)
        self.assertNotIn("<书>", page)

    def test_print_css(self) -> None:
        page = render_html([])
        self.assertIn("A4 portrait", page)
        self.assertIn("@media print", page)
        self.assertIn('lang="zh-CN"', page)

    def test_row_height_in_css(self) -> None:
        page = render_html([], rows=6)
        self.assertIn("height: 12mm", page)
        page = render_html([], rows=24)
        self.assertIn("height: 9mm", page)

    def test_rejects_empty_title(self) -> None:
        with self.assertRaises(ReadinglogError):
            render_html([], title="  ")

    def test_rejects_bad_rows(self) -> None:
        for rows in (5, 25, True, 6.5):
            with self.assertRaises(ReadinglogError):
                render_html([], rows=rows)  # type: ignore[arg-type]

    def test_rejects_non_sequence(self) -> None:
        with self.assertRaises(ReadinglogError):
            render_html("书")  # type: ignore[arg-type]

    def test_rejects_non_book_items(self) -> None:
        with self.assertRaises(ReadinglogError):
            render_html(["书"])  # type: ignore[list-item]


if __name__ == "__main__":
    unittest.main()
