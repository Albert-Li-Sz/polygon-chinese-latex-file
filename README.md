# Polygon 中文题面模板

为 Codeforces Polygon 生成中文单题 PDF 和整场比赛题册，包含中文栏目、赛事封面、题目目录，以及可跨页的文件样例。

## 在 Polygon 中使用

1. 在题目或竞赛的文件管理中，用本仓库的 `olymp.sty`、`problem.tex` 和 `statements.ftl` 替换对应的同名模板文件。
2. 按需要修改 `statements.ftl` 顶部的配置。比赛名称、地点、日期和题目内容由 Polygon 的模板数据提供。
3. 如需封面 Logo，将 `statements-logo.png` 放在与主 `statements.ftl` 模板一起供编译使用的位置，也可以修改 `\ContestLogo` 指定文件名。Logo 是可选的；文件不存在时会跳过图片。
4. 重新生成 PDF，检查中文字体、目录、样例及分页。题目目录和总页数依赖辅助文件，至少需要编译两遍；若编译日志仍提示重新运行，再编译一次。

| 文件 | 作用 |
| --- | --- |
| `statements.ftl` | FreeMarker 文档入口：宏包、配置、封面及题目引入。 |
| `problem.tex` | FreeMarker 单题模板：标题、限制、题意、样例等。虽然扩展名为 `.tex`，它不能直接用 XeLaTeX 编译。 |
| `olymp.sty` | LaTeX 排版宏包：题目环境、中文栏目、样例表格、页眉页脚和目录。 |
| `examples/minimal.tex` | 可直接编译的本地示例，不依赖 Polygon 或 FreeMarker。 |

## 常用配置

以下配置位于 `statements.ftl` 顶部，修改已有设置即可。

| 设置 | 默认行为 | 修改方式 |
| --- | --- | --- |
| `\ContestPrintfalse` | 电子版，不自动补空白页。 | 改为 `\ContestPrinttrue`，用于双面打印，让题目从奇数页开始；末题之后也可能补空白页。 |
| `\ContestCovertrue` | 整场比赛题册显示封面和题目目录；单题无封面。 | 改为 `\ContestCoverfalse` 关闭封面。 |
| `\ContestLogo` | 可选图片 `statements-logo.png`。 | 修改文件名，或将命令内容设为空以隐藏图片。 |
| `\ContestNotice` | “请勿使用生成式人工智能参加本竞赛”。 | 修改文字，或将命令内容设为空。 |
| `\ContestStartWarning` | “请勿在比赛正式开始前打开题面！”。 | 修改文字，或将命令内容设为空。 |
| `\ExampleTabSize` | 文件样例按每 4 个字符一处的制表位展开 Tab。 | 例如 `\renewcommand{\ExampleTabSize}{8}`；使用正整数。 |

需要隐藏输入文件、输出文件、时间限制或空间限制时，分别取消 `\NoInputFileName`、`\NoOutputFileName`、`\NoTimeLimit`、`\NoMemoryLimit` 对应定义的注释。

标题样式由 `olymp.sty` 中的 `\problemtitlefont` 控制，不会全局改写 `\textbf`。默认使用 Fandol 中文字体；若改用其他字体，请确认编译环境安装了对应字体，并提供常规与粗体字形。

## 样例排版

Polygon 的默认单题模板使用 `example` 环境和 `\exmpfile{输入文件}{输出文件}`。这条路径支持：

- 保留空行与连续空格，按制表位展开 Tab。
- 将过长的原始行按列宽折行，并在续行前显示箭头。箭头和视觉换行仅用于排版，不属于原始样例数据。
- 在单栏文档中跨页排版，续页重复输入、输出表头；输入与输出行数不同时，较短的一侧留空。

`examplewide`、`examplethree` 和直接在模板内书写的 `\exmp` 保持原有行为，不具备上述完整处理能力。双栏文档中的 `example` 使用普通 `tabular`，不能跨页。需要完整保留样例字节时，应使用原始 `.in` / `.ans` 文件，不要从 PDF 中复制还原。

## 本地编译示例

建议安装较新的完整 TeX Live，使用 **XeLaTeX** 编译。基础依赖包括 `ctex`、Fandol 字体、`amsmath`、`amssymb`、`lastpage`、`longtable`、`booktabs` 和 `etoolbox`。完整 Polygon 模板还使用 `graphicx`、`listings`、`hyperref`、`import`、`siunitx` 等宏包。

在 Debian / Ubuntu 中，可用以下包准备模板和回归测试所需的 TeX 环境：

```sh
sudo apt-get install texlive-xetex texlive-lang-chinese texlive-latex-extra texlive-science
```

从**仓库根目录**运行以下命令；示例中的样例路径也相对于仓库根目录：

```sh
mkdir -p /tmp/polygon-chinese-example
xelatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/polygon-chinese-example examples/minimal.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/polygon-chinese-example examples/minimal.tex
```

结果为 `/tmp/polygon-chinese-example/minimal.pdf`。该示例直接使用 `olymp.sty` 的题目环境，并展示两遍编译后生成的目录和总页数；它不替代 Polygon 对 FreeMarker 模板的展开过程。

## 回归测试

测试实际展开 FreeMarker 模板并用 XeLaTeX 编译，覆盖配置、目录、分页、中文标准输入输出，以及样例中的空文件、空行、空格、Tab 和长行。准备好 Python、Java 和 TeX 依赖后运行：

```sh
python3 -m pip install -r tests/requirements.txt
python3 tests/run.py
```

首次运行会下载固定版本的 FreeMarker JAR，也可以设置 `FREEMARKER_JAR` 使用本地文件。完整依赖、离线用法和输出位置见 [测试说明](tests/README.md)。自动测试验证本地模板与排版行为；发布前仍应在 Polygon 中生成最终题册检查。
