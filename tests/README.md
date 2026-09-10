# 模板回归测试

测试使用 **Apache FreeMarker 2.3.34** 展开仓库里的 `problem.tex` 和 `statements.ftl`，然后用 XeLaTeX 连续编译两遍，再检查 PDF 的实际文本和字符位置。它不会用字符串替换模拟 FreeMarker。

## 本地运行

需要 Python 3.10+、Java/Javac 17+ 和 XeLaTeX。TeX 环境必须包含 `ctex`、Fandol 字体及模板依赖的宏包；完整的 TeX Live 或 MacTeX 可以满足要求。Ubuntu 可安装：

```sh
sudo apt-get install texlive-xetex texlive-lang-chinese texlive-latex-extra texlive-science
```

在仓库根目录运行：

```sh
python3 -m pip install -r tests/requirements.txt
python3 tests/run.py
```

如果 Java 不在 `PATH` 中，请设置 `JAVA_HOME`。首次运行会从 Maven Central 下载 FreeMarker，并校验固定 SHA-256。离线使用时，可通过 `FREEMARKER_JAR=/path/to/freemarker-2.3.34.jar` 指定相同版本的官方 JAR。

所有生成文件保存在已忽略的 `tests/.build/`，也可以使用 `--build-dir /path/to/output` 指定目录。每个测试目录保留展开后的 TeX、原始样例、PDF、两次编译输出及最终日志，便于检查排版。重复运行仅重建这些固定测试目录。

## 检查范围

- 中文标准输入输出、英文分支及短样例。
- 130 行输入、23 行输出跨页时的完整性与续页表头。
- 连续空格、行首空格和空行；默认 4 列及自定义 8 列 Tab 对齐，直接检查 PDF 字符坐标。
- LaTeX 特殊字符原样显示、输入/输出文件为空、多组样例。
- 中文和英文混排、中文标点的自动折行，检查字符数量和实际列边界。
- 超过一页的单行文本：9000 个字符无丢失、无越过输入列边界，并带续行箭头。
- 多题目录和子目录中的样例文件导入；缺少 Logo 或将 Logo 文件名设为空时仍能编译。
- 电子版、打印版、启用/关闭封面的页数、题目位置和正文从第 1 页开始。
- 打印版封面本身有两页时，正文仍从物理奇数页开始，不多插空白页；所有封面页隐藏页码。
- 第二次编译没有缺字、字体替代、未定义引用或 overfull box 警告。

GitHub Actions 使用同一入口运行，失败时仍上传生成的 PDF、TeX 和日志。这里验证的是本地 FreeMarker/XeLaTeX 流程，不能代替 Polygon 服务端最终导出检查。
