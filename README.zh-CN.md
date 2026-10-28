# IAC 字幕格式

IAC（Inline Annotation Container，内联标注容器）是一种按行组织的纯文本字幕格式：一条音轨占一行，字幕文本与时间轴内联书写。

**状态**：1.0.0，稳定版，2026-10-29 发布。规范正文见 [spec/iac-1.0.md](spec/iac-1.0.md)。

## 一条真实记录

下面取自 [examples/music.iac](examples/music.iac) 的第一条记录（文件中它是一条物理行，此处为便于阅读折行，并用 `...` 省略了其余 16 条字幕）：

```iac
music_KnewBefore : {"I've forgot the way to be myself"|00:00:08:58-00:00:17:20|,
                    "I don't know who I was the night before"|00:00:17:20-00:00:25:99|,
                    "The shadows in the air, they haunt me still"|00:00:25:99-00:00:40:62|,
                    ...,
                    "The one I knew before"|00:02:17:84-00:03:12:02|} : [#FFFFFF] : Music

# Song "Knew Before" from game BONELAB
# Copyright: Michael Wyckoff, Stress Level Zero
```

字段顺序为 `<AudioName> : {<条目>, <条目>, ...} : [#RRGGBB][ : <Type>]`：三个必填字段，外加可选的音轨类型。时间写作 `HH:MM:SS:CC`，其中 `CC` 是百分秒；时间区间为半开区间 `[start, stop)`。文件开头可以写 `#!iac 1.0`：它本身就是注释，对不识别它的旧解析器没有任何成本。

## 为什么

- **时间跟着文本走。** 一行记录自带全部时间信息，翻译一行就是改一处，时间点始终附着在它所属的那句台词上，不必另外维护一条时间轴。
- **不必和转义较劲。** 记录只在顶层、且不在引号和花括号内的地方按 ` : ` 切分，因此 `"Chapter : The Fall"`、`"他说 : 你好"` 都是合法文本——台词不用编码就能原样保留。
- **纯文本，可 diff。** 一条记录一行、规范形式唯一、没有二进制块也没有标记泥潭。本地化评审能直接读懂 diff，`iac_lint.py fmt` 还能让这份 diff 稳定不变。被删掉的台词写成 `#!cut` 注释：它留在文件里、照样被 linter 检查，但永远不渲染，记录里也不再有布尔字段要维护。

## 快速开始：60 秒

```bash
python tools/iac_lint.py validate examples/single-subtitle.iac
```

退出码 `0` 表示没有发现任何问题，`1` 表示只有警告，`2` 表示存在错误；干净的文件不会打印任何内容。加上 `--json` 可输出机器可读的诊断信息。

```bash
python tools/iac_lint.py validate examples/
python tools/iac_lint.py fmt examples/multi-subtitles.iac
python tools/iac_lint.py from-srt in.srt out.iac
python tools/iac_lint.py migrate old-draft.iac
```

`fmt` 把单个文件重写为规范形式，`from-srt` 用于导入 SRT 文件，`migrate` 把还带着 `: true` / `: false` 字段的草案期记录改写为新语法。完整流程见 [docs/quickstart.md](docs/quickstart.md)。

## 目录导航

| 内容 | 位置 |
|---|---|
| 规范正文 | [spec/iac-1.0.md](spec/iac-1.0.md) |
| 语法定义（ABNF） | [spec/iac.abnf](spec/iac.abnf) |
| 注册表 | [registry/types.md](registry/types.md)、[registry/directives.md](registry/directives.md) |
| 文档 | [docs/index.md](docs/index.md)——快速上手、书写指南、解析器指南、转换指南、错误码 |
| RFC 流程 | [rfcs/0000-template.md](rfcs/0000-template.md)、[GOVERNANCE.md](GOVERNANCE.md) |
| 治理 | [GOVERNANCE.md](GOVERNANCE.md)、[CONTRIBUTING.md](CONTRIBUTING.md) |
| 一致性测试集 | [testdata/](testdata/)，参考 linter [tools/iac_lint.py](tools/iac_lint.py) |
| 路线图 | [ROADMAP.md](ROADMAP.md) |

## 兼容性承诺

实现次版本 `x` 的解析器必须能无损读取次版本 `y <= x` 的合规文件。如果遇到声明了更新次版本的文件，解析器不得因为版本行本身而失败：报 W007，然后尽力继续解析。只有更高的**主**版本才是致命错误（E024）。不兼容的改动必须提升主版本，并至少经过一个次版本的弃用期——详见 [GOVERNANCE.md](GOVERNANCE.md)。

相对旧草案，1.0 的变化有：时间区间改为半开区间（结束时间不包含在内）、新增 `#!iac` 版本行、`Type` 取值改为注册制、错误码体系成文，以及记录只剩三个必填字段——草案里的第四个布尔字段已被删除，被删台词改用 `#!cut` 注释表达。`python tools/iac_lint.py migrate` 可以机械地改写草案期文件。

## 许可

| 部分 | 许可协议 |
|---|---|
| 规范文本（`spec/`、`docs/`、`registry/`、RFC、本 README） | CC BY 4.0 |
| 参考实现代码（`tools/` 及后续库） | Apache-2.0 |
| 示例 `.iac` 文件（`examples/`） | CC0-1.0 |

示例采用 CC0 是有意为之：可以直接粘进专有项目，不必处理署名问题。按目录划分的授权表与版权行见 [LICENSE](LICENSE)。

## 状态与路线

1.0.0 是首个稳定版本。目前尚未发布到 npm、PyPI 或 IANA：linter 需要从仓库检出后运行，`text/x-iac` 只是临时的未注册媒体类型，也还没有第三方实现可以列举。1.1 的候选内容见 [RFC 0001 §4](rfcs/0001-standardize-iac-1.0.md#4-deferred-work)，推广节奏见 [docs/adoption.md](docs/adoption.md)，排期清单见 [ROADMAP.md](ROADMAP.md)，发布记录见 [CHANGELOG.md](CHANGELOG.md)。

English: [README.md](README.md)
