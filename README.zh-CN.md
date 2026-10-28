# IAC 字幕格式

IAC（Inline Annotation Container，内联标注容器）是一种按行组织的纯文本字幕格式：一条音轨占一行，字幕文本与时间轴内联书写。

**状态：** 1.0.0，稳定版，2026-10-29 打标签，尚未公开发布。规范正文见 [spec/iac-1.0.md](spec/iac-1.0.md)。

## 一条记录的形状

```text
AudioName : { "text"|HH:MM:SS:CC-HH:MM:SS:CC|, ... } : [#RRGGBB] [ : Type ]
```

三个必填字段加一个可选字段。时间写作 `HH:MM:SS:CC`，`CC` 是百分秒，不是帧；区间是半开的 `[start, stop)`。

下面取自 [examples/music.iac](examples/music.iac) 的第一条记录（文件中它是一条物理行，此处为便于阅读折行，并从 19 条字幕里只显示前 3 条）：

```iac
music_KnewBefore : {"I've forgot the way to be myself"|00:00:08:58-00:00:17:20|,
                    "I don't know who I was the night before"|00:00:17:20-00:00:25:99|,
                    "The shadows in the air, they haunt me still"|00:00:25:99-00:00:40:62|,
                    ...,
                    "The one I knew before"|00:02:17:84-00:03:12:02|} : [#FFFFFF] : Music
```

## 为什么

- **时间跟着文本走。** 一行自带它的字幕条目，翻译一行就是改一处，时间不会和句子走散。
- **没有转义地狱。** 记录只在顶层、引号外、括号外按 ` : ` 切分，所以 `"Chapter : The Fall"` 和 `"他说 : 你好"` 都是普通文本。
- **纯文本，可 diff。** 一行一条记录，有确定的规范形式，没有二进制块。废弃的行写成 `#!cut` 注释：留在文件里、继续被检查、永远不会显示。

## 60 秒上手

```bash
python tools/iac_lint.py validate examples/single-subtitle.iac
python tools/iac_lint.py validate examples/          # 目录会被递归遍历
python tools/iac_lint.py fmt --check examples        # 每个文件都是规范形式吗？
```

退出码 `0` 表示没有发现，且不打印任何内容；`1` 只有警告；`2` 有错误。加 `--json` 得到机器可读输出。没有安装步骤，也没有已发布的包：校验器就是一个只用标准库的文件，从 checkout 直接跑。

## 各部分在哪

| 路径 | 是什么 |
|---|---|
| [spec/](spec/) | 规范层：[规范正文](spec/iac-1.0.md)、[语法](spec/iac.abnf)、[注册表](spec/registry.md)，以及[设计理由](spec/rationale.md)和[安全说明](spec/security.md) |
| [testdata/](testdata/) | 38 个一致性用例和 [conformance.json](testdata/conformance.json)，后者规定每个用例应产生哪些码 |
| [tools/](tools/) | 参考实现：校验、格式化、SRT 导入、草案迁移 |
| [docs/](docs/) | 五篇指南：[快速上手](docs/quickstart.md)、[写作](docs/authoring.md)、[解析器实现](docs/parsing.md)、[格式转换](docs/conversion.md)、[错误码](docs/errors.md) |
| [rfcs/](rfcs/) | [RFC 0001](rfcs/0001-standardize-iac-1.0.md)：格式为什么长这样 |
| [examples/](examples/) | 三个规范样例：一首歌、多轨含废弃行、一段中文对白 |

## 什么时候不该用 IAC

IAC 描述的是**说了什么、什么时候说**，不是长什么样。如果你需要：

- 定位、字体、富文本样式或动画——用 ASS 或 WebVTT + CSS；
- 卡拉 OK 或逐字时间轴——用 ASS；
- 每条字幕单独配色或透明度——IAC 只有轨道级颜色，没有 alpha；
- 和现有字幕管线无损互转——IAC 是创作源格式，转出是有损的（[spec §1.1](spec/iac-1.0.md)）。

## 兼容承诺

实现次要版本 `x` 的解析器必须能读取任意 `y <= x` 的合规文件，且不丢失含义。文件声明更新的次要版本不是致命错误：解析器报 W007 后继续。只有更新的主版本才致命（E015）。破坏性变更需要主版本号提升，并至少经过一个次要版本的弃用期；流程见 [GOVERNANCE.md](GOVERNANCE.md)。

## 许可

| 部分 | 许可 |
|---|---|
| 规范正文、文档、注册表、RFC、本 README | CC BY 4.0 |
| `tools/` 中的参考代码 | Apache-2.0 |
| 示例与一致性语料中的 `.iac` 文件 | CC0-1.0 |

按目录的完整划分见 [LICENSE](LICENSE)。

English： [README.md](README.md)
