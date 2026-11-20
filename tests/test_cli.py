"""阅读记录命令行入口测试。"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import List, Tuple

from readinglog.cli import main


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.csv = self.tmp / "书单.csv"
        self.csv.write_text(
            "书名,作者,页数\n夏洛的网,E.B.怀特,192\n"
            "城南旧事,林海音,164\n西游记,吴承恩,620\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, argv: List[str]) -> Tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_generate_from_csv(self) -> None:
        output = self.tmp / "r.html"
        code, out, err = self.run_cli(["-i", str(self.csv), "-o", str(output)])
        self.assertEqual(code, 0, err)
        self.assertTrue(output.exists())
        self.assertIn("共 3 本书", out)
        self.assertIn("合计 976 页", out)
        page = output.read_text(encoding="utf-8")
        self.assertIn("夏洛的网", page)
        self.assertEqual(page.count('class="sheet"'), 1)

    def test_blank_log_without_input(self) -> None:
        output = self.tmp / "blank.html"
        code, out, err = self.run_cli(["-o", str(output)])
        self.assertEqual(code, 0, err)
        self.assertIn("共 0 本书", out)
        page = output.read_text(encoding="utf-8")
        self.assertEqual(page.count('class="idx"'), 18)

    def test_rows_option_paginates(self) -> None:
        output = self.tmp / "r.html"
        code, out, err = self.run_cli(
            ["-i", str(self.csv), "--rows", "6", "-o", str(output)]
        )
        self.assertEqual(code, 0, err)
        self.assertIn("共 1 页", out)
        page = output.read_text(encoding="utf-8")
        self.assertEqual(page.count('class="idx"'), 6)

    def test_custom_title(self) -> None:
        output = self.tmp / "r.html"
        code, _, err = self.run_cli(
            ["-i", str(self.csv), "--title", "寒假阅读", "-o", str(output)]
        )
        self.assertEqual(code, 0, err)
        self.assertIn("寒假阅读", output.read_text(encoding="utf-8"))

    def test_missing_input_file(self) -> None:
        code, _, err = self.run_cli(["-i", str(self.tmp / "nope.csv")])
        self.assertEqual(code, 1)
        self.assertIn("读取书目失败", err)

    def test_invalid_csv(self) -> None:
        bad = self.tmp / "bad.csv"
        bad.write_text("夏洛的网,E.B.怀特,12.5\n", encoding="utf-8")
        code, _, err = self.run_cli(["-i", str(bad)])
        self.assertEqual(code, 2)
        self.assertIn("页数", err)

    def test_invalid_rows(self) -> None:
        code, _, err = self.run_cli(["--rows", "5"])
        self.assertEqual(code, 2)
        self.assertIn("6~24", err)

    def test_write_failure(self) -> None:
        output = self.tmp / "missing" / "r.html"
        code, _, err = self.run_cli(["-o", str(output)])
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", err)

    def test_output_is_reproducible(self) -> None:
        first = self.tmp / "a.html"
        second = self.tmp / "b.html"
        for path in (first, second):
            code, _, err = self.run_cli(["-i", str(self.csv), "-o", str(path)])
            self.assertEqual(code, 0, err)
        self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
