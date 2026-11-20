"""阅读记录数据模型测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from readinglog.model import (
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


def make_books(count: int) -> list:
    return [
        Book(title="书 %d" % index, author="作者 %d" % index, pages=100 + index)
        for index in range(1, count + 1)
    ]


class BookTest(unittest.TestCase):
    def test_strips_and_normalizes(self) -> None:
        book = Book(title="  夏洛的网 ", author=" E.B.怀特 ", pages=192)
        self.assertEqual(book.title, "夏洛的网")
        self.assertEqual(book.author, "E.B.怀特")

    def test_rejects_empty_title(self) -> None:
        with self.assertRaises(ReadinglogError) as ctx:
            Book(title="  ", pages=100)
        self.assertIn("书名", str(ctx.exception))

    def test_rejects_long_title(self) -> None:
        with self.assertRaises(ReadinglogError):
            Book(title="书" * (MAX_TITLE + 1), pages=100)

    def test_rejects_long_author(self) -> None:
        with self.assertRaises(ReadinglogError):
            Book(title="夏洛的网", author="作" * (MAX_AUTHOR + 1), pages=100)

    def test_rejects_non_integer_pages(self) -> None:
        with self.assertRaises(ReadinglogError):
            Book(title="夏洛的网", pages="192")  # type: ignore[arg-type]
        with self.assertRaises(ReadinglogError):
            Book(title="夏洛的网", pages=True)

    def test_rejects_zero_and_negative_pages(self) -> None:
        for pages in (0, -1):
            with self.assertRaises(ReadinglogError):
                Book(title="夏洛的网", pages=pages)

    def test_rejects_pages_over_limit(self) -> None:
        with self.assertRaises(ReadinglogError):
            Book(title="夏洛的网", pages=MAX_PAGES + 1)


class ParseCsvTest(unittest.TestCase):
    def test_with_header(self) -> None:
        books = parse_csv("书名,作者,页数\n夏洛的网,E.B.怀特,192\n")
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].author, "E.B.怀特")
        self.assertEqual(books[0].pages, 192)

    def test_without_header(self) -> None:
        books = parse_csv("夏洛的网,E.B.怀特,192\n城南旧事,,164\n")
        self.assertEqual(len(books), 2)
        self.assertEqual(books[1].author, "")

    def test_skips_blank_lines(self) -> None:
        books = parse_csv("\n\n夏洛的网,E.B.怀特,192\n\n")
        self.assertEqual(len(books), 1)

    def test_handles_bom(self) -> None:
        books = parse_csv("\ufeff夏洛的网,E.B.怀特,192\n")
        self.assertEqual(books[0].title, "夏洛的网")

    def test_handles_quoted_comma(self) -> None:
        books = parse_csv('"夏洛的网, 插图版",E.B.怀特,192\n')
        self.assertEqual(books[0].title, "夏洛的网, 插图版")

    def test_rejects_extra_columns(self) -> None:
        with self.assertRaises(ReadinglogError) as ctx:
            parse_csv("夏洛的网,E.B.怀特,192,多余\n")
        self.assertIn("第 1 行", str(ctx.exception))
        self.assertIn("3 列", str(ctx.exception))

    def test_rejects_missing_title(self) -> None:
        with self.assertRaises(ReadinglogError) as ctx:
            parse_csv("夏洛的网,E.B.怀特,192\n,佚名,100\n")
        self.assertIn("第 2 行", str(ctx.exception))
        self.assertIn("书名", str(ctx.exception))

    def test_rejects_missing_pages(self) -> None:
        with self.assertRaises(ReadinglogError) as ctx:
            parse_csv("夏洛的网,E.B.怀特\n")
        self.assertIn("页数", str(ctx.exception))

    def test_rejects_non_numeric_pages(self) -> None:
        for value in ("12.5", "abc", "0", "-3"):
            with self.assertRaises(ReadinglogError) as ctx:
                parse_csv("夏洛的网,E.B.怀特,%s\n" % value)
            self.assertIn("第 1 行", str(ctx.exception))

    def test_rejects_too_long_title_with_row(self) -> None:
        with self.assertRaises(ReadinglogError) as ctx:
            parse_csv("夏洛的网,,192\n%s,,100\n" % ("书" * 61))
        self.assertIn("第 2 行", str(ctx.exception))

    def test_rejects_empty_content(self) -> None:
        for text in ("", "\n\n", "书名,作者,页数\n"):
            with self.assertRaises(ReadinglogError) as ctx:
                parse_csv(text)
            self.assertIn("没有有效", str(ctx.exception))

    def test_rejects_non_text(self) -> None:
        with self.assertRaises(ReadinglogError):
            parse_csv(b"abc")  # type: ignore[arg-type]


class DecodeTest(unittest.TestCase):
    def test_utf8_bom(self) -> None:
        data = "夏洛的网,E.B.怀特,192\n".encode("utf-8-sig")
        self.assertTrue(decode_bytes(data).startswith("夏洛的网"))

    def test_gbk(self) -> None:
        data = "夏洛的网,E.B.怀特,192\n".encode("gbk")
        self.assertIn("夏洛的网", decode_bytes(data))

    def test_invalid_bytes(self) -> None:
        with self.assertRaises(ReadinglogError) as ctx:
            decode_bytes(b"\xff\xff\xff")
        self.assertIn("编码", str(ctx.exception))


class TotalPagesTest(unittest.TestCase):
    def test_sum(self) -> None:
        self.assertEqual(total_pages(make_books(3)), 101 + 102 + 103)

    def test_empty(self) -> None:
        self.assertEqual(total_pages([]), 0)

    def test_rejects_non_book(self) -> None:
        with self.assertRaises(ReadinglogError):
            total_pages(["书"])  # type: ignore[list-item]


class PaginateTest(unittest.TestCase):
    def test_empty_has_one_blank_page(self) -> None:
        self.assertEqual(paginate([], 18), [[]])

    def test_exact_fit(self) -> None:
        self.assertEqual(len(paginate(make_books(18), 18)), 1)

    def test_one_more_makes_second_page(self) -> None:
        pages = paginate(make_books(19), 18)
        self.assertEqual(len(pages), 2)
        self.assertEqual(len(pages[0]), 18)
        self.assertEqual(len(pages[1]), 1)
        self.assertEqual(pages[1][0][0], 19)
        self.assertEqual(pages[1][0][1].title, "书 19")

    def test_numbering_is_continuous(self) -> None:
        pages = paginate(make_books(8), 6)
        self.assertEqual(len(pages), 2)
        numbers = [number for page in pages for number, _ in page]
        self.assertEqual(numbers, list(range(1, 9)))

    def test_rejects_bad_rows(self) -> None:
        for rows in (5, 25, 0, -1, True, 6.5):
            with self.assertRaises(ReadinglogError):
                paginate([], rows)  # type: ignore[arg-type]

    def test_rejects_non_book(self) -> None:
        with self.assertRaises(ReadinglogError):
            paginate([123], 18)  # type: ignore[list-item]


class FormatBooksTest(unittest.TestCase):
    def test_roundtrip(self) -> None:
        books = make_books(3)
        text = format_books(books)
        self.assertTrue(text.startswith("书名,作者,页数"))
        self.assertEqual(parse_csv(text), books)

    def test_rejects_empty(self) -> None:
        with self.assertRaises(ReadinglogError):
            format_books([])


class LoadBooksTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_reads_utf8_and_gbk(self) -> None:
        for encoding in ("utf-8-sig", "gbk"):
            path = self.tmp / ("书单_%s.csv" % encoding)
            path.write_bytes("夏洛的网,E.B.怀特,192\n".encode(encoding))
            self.assertEqual(load_books(str(path))[0].title, "夏洛的网")

    def test_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_books(str(self.tmp / "nope.csv"))


if __name__ == "__main__":
    unittest.main()
