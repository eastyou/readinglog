# readinglog

[![CI](https://github.com/eastyou/readinglog/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/readinglog/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

给学生用的阅读记录表：把书单整理成 CSV，一条命令生成 A4 可打印记录表，书名、作者、页数自动排好，留出开始、完成和签字栏。**零依赖，不联网，打印即用。**

不传书单也能生成空白表，直接打印发给学生手写。

## 特性

- **书目自动排版**：书名、作者、页数从 CSV 读入，序号连续编号
- **分页可控**：`--rows` 设置每页 6~24 行，书目跨页，末页自动补空行
- **空白表模式**：不传 `-i` 就生成一张空白阅读记录，适合统一打印
- **页脚统计**：每页显示「共 N 本书 · 合计 M 页」和页码
- **表头可选**：`书名,作者,页数` 可有可无，两列、三列都能用
- **编码兼容**：UTF-8（含 BOM）与 GBK 自动识别，Excel 导出的 CSV 可直接用
- **逐行校验**：空书名、缺页数、非正整数页数、多余列都会指出具体行号
- **59 个单元测试**：覆盖 CSV 解析、编码识别、分页、页脚统计、渲染与命令行

## 安装

```bash
pip install readinglog
```

也可以直接下载源码，在项目目录里运行：

```bash
python -m readinglog --help
```

## 用法

准备书单 `阅读书单.csv`：

```csv
书名,作者,页数
夏洛的网,E.B.怀特,192
城南旧事,林海音,164
西游记,吴承恩,620
```

生成阅读记录：

```bash
readinglog -i 阅读书单.csv -o 阅读记录.html
```

每页 24 行，适合高年级：

```bash
readinglog -i 阅读书单.csv --rows 24 -o 阅读记录.html
```

生成空白表：

```bash
readinglog -o 空白阅读记录.html
```

打开 HTML 后按 `Ctrl/Cmd + P`，纸张选 **A4 纵向**、边距选「无」即可打印。

## 书单格式

| 列 | 是否必填 | 长度上限 | 说明 |
| --- | --- | --- | --- |
| 书名 | 必填 | 60 字 | 表格左对齐，过长自动换行 |
| 作者 | 可选 | 20 字 | 留空也可以 |
| 页数 | 必填 | 1~10000 | 必须是正整数 |

## 表格结构

每页固定七列：**序号、书名、作者、页数、开始、完成、签字**。前四列由程序填好，后三列留白给学生手写日期和签名。

- 每页行数：`--rows`，范围 6~24，默认 18
- 书目超过一页时自动分页，标题变成「阅读记录（续）」
- 末页不足一整页时补空行，序号继续递增
- 页脚始终显示全部书目的总本数与总页数

## 命令行参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `-i, --input` | 不传则空白 | 书目 CSV 路径 |
| `-o, --output` | `阅读记录.html` | 输出 HTML 路径 |
| `--rows` | `18` | 每页行数，6~24 |
| `--title` | `阅读记录` | 表格标题 |

## 工作原理

1. **读取**：按 UTF-8（含 BOM）→ GBK 的顺序解码，识别可选表头。
2. **校验**：逐行检查列数、书名、页数，错误信息带行号。
3. **分页**：按 `--rows` 切片，序号跨页连续，空行补足末页。
4. **排版**：HTML 表格按 A4 纵向排版，行高随行数自动压缩，打印时隐藏工具栏。

核心接口：

```python
from readinglog import Book, paginate, render_html, total_pages

books = [Book(title="夏洛的网", author="E.B.怀特", pages=192)]
print(total_pages(books))        # 192
print(len(paginate(books, 18)))  # 1
page = render_html(books, rows=18)
```

## 项目结构

```
readinglog/
├── readinglog/
│   ├── model.py    # CSV 解析、字段校验、分页与统计
│   ├── render.py   # A4 纵向表格排版
│   └── cli.py      # 命令行入口
├── examples/       # 示例书单
├── tests/          # 59 个单元测试
└── pyproject.toml
```

## 开发

```bash
python -m unittest discover -s tests -v
python -m readinglog -i examples/阅读书单.csv --rows 6 -o 阅读记录.html
```

## 许可证

[MIT](LICENSE) © 2026 eastyou
