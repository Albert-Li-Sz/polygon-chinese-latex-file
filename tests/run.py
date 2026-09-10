#!/usr/bin/env python3
"""Render real FreeMarker templates and assert observable PDF behavior."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request

import pdfplumber
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
FREEMARKER_VERSION = "2.3.34"
FREEMARKER_SHA256 = "9a9fb91cd64199232eb1ca9766148a5d30ef8944be5fac051018f96c70c8f6a3"
FREEMARKER_URL = (
    "https://repo.maven.apache.org/maven2/org/freemarker/freemarker/"
    f"{FREEMARKER_VERSION}/freemarker-{FREEMARKER_VERSION}.jar"
)


def run(command: list[str], cwd: Path, output: Path | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=180)
    if output:
        output.write_text(result.stdout, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n"
                           + result.stdout[-12000:])


def java_tool(name: str) -> str:
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        executable = Path(java_home) / "bin" / name
        if executable.is_file():
            return str(executable)
    executable = shutil.which(name)
    if not executable:
        raise RuntimeError(f"{name} is required. Install Java 17+ and set JAVA_HOME.")
    return executable


def freemarker_jar(build: Path) -> Path:
    override = os.environ.get("FREEMARKER_JAR")
    jar = Path(override).resolve() if override else build / "deps" / f"freemarker-{FREEMARKER_VERSION}.jar"
    if not jar.exists():
        if override:
            raise RuntimeError(f"FREEMARKER_JAR does not exist: {jar}")
        jar.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading Apache FreeMarker {FREEMARKER_VERSION}", flush=True)
        with urllib.request.urlopen(FREEMARKER_URL, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != FREEMARKER_SHA256:
            raise RuntimeError("FreeMarker download checksum mismatch")
        jar.write_bytes(data)
    if hashlib.sha256(jar.read_bytes()).hexdigest() != FREEMARKER_SHA256:
        raise RuntimeError(f"Expected unmodified Apache FreeMarker {FREEMARKER_VERSION}: {jar}")
    return jar


def property_escape(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class PDF:
    def __init__(self, directory: Path):
        self.directory = directory
        self.reader = PdfReader(directory / "document.pdf")
        # pdfplumber understands the Adobe-GB1 CMaps used by Fandol; pypdf's
        # reader still independently validates the document and page count.
        with pdfplumber.open(directory / "document.pdf") as document:
            self.pages = [page.extract_text() or "" for page in document.pages]
        require(len(self.pages) == len(self.reader.pages), "PDF readers disagree on page count")
        self.text = "\n".join(self.pages)

    def contains(self, *texts: str) -> None:
        for text in texts:
            require(text in self.text, f"{self.directory.name}: missing PDF content {text!r}")

    def page_count(self, count: int) -> None:
        require(len(self.pages) == count,
                f"{self.directory.name}: expected {count} pages, found {len(self.pages)}")


def render_case(build: Path, classpath: str, name: str,
                problems: list[list[tuple[str, str]]], *, contest: bool = False,
                print_mode: bool = False, cover: bool = True, tab_size: int = 4,
                language: str = "chinese", empty_logo: bool = False,
                two_page_cover: bool = False) -> PDF:
    directory = build / name
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    shutil.copy2(ROOT / "olymp.sty", directory / "olymp.sty")
    properties: dict[str, object] = {"count": len(problems), "contest": str(contest).lower(), "language": language}
    for index, samples in enumerate(problems):
        properties[f"problem.{index}.name"] = f"题目 {chr(65 + index)}"
        properties[f"problem.{index}.samples"] = len(samples)
        destination = directory / f"problems/{chr(65 + index)}" if contest else directory
        destination.mkdir(parents=True, exist_ok=True)
        for sample, (input_text, output_text) in enumerate(samples):
            (destination / f"sample{sample}.in").write_text(input_text, encoding="utf-8")
            (destination / f"sample{sample}.ans").write_text(output_text, encoding="utf-8")
    (directory / "fixture.properties").write_text(
        "\n".join(f"{key}={property_escape(value)}" for key, value in properties.items()) + "\n",
        encoding="utf-8")
    run([java_tool("java"), "-cp", classpath, "RenderTemplates", str(ROOT), str(directory)], directory)
    document_path = directory / "document.tex"
    document = document_path.read_text(encoding="utf-8")
    if print_mode:
        require(document.count(r"\ContestPrintfalse") == 1, "Cannot locate print configuration")
        document = document.replace(r"\ContestPrintfalse", r"\ContestPrinttrue")
    if not cover:
        require(document.count(r"\ContestCovertrue") == 1, "Cannot locate cover configuration")
        document = document.replace(r"\ContestCovertrue", r"\ContestCoverfalse")
    if tab_size != 4:
        document = document.replace(r"\begin {document}",
                                    rf"\renewcommand{{\ExampleTabSize}}{{{tab_size}}}" + "\n" + r"\begin {document}")
    if empty_logo:
        logo_definition = r"\newcommand{\ContestLogo}{statements-logo.png}"
        require(logo_definition in document, "Cannot locate logo configuration")
        document = document.replace(logo_definition, r"\newcommand{\ContestLogo}{}")
    if two_page_cover:
        notice_definition = r"\newcommand{\ContestNotice}{请勿使用生成式人工智能参加本竞赛}"
        require(notice_definition in document, "Cannot locate notice configuration")
        document = document.replace(notice_definition,
                                    r"\newcommand{\ContestNotice}{First cover page\newpage Cover continuation}")
    require("<#" not in document and "${" not in document, "Unexpanded FreeMarker syntax")
    document_path.write_text(document, encoding="utf-8")
    for pass_number in (1, 2):
        run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "document.tex"],
            directory, directory / f"xelatex-pass-{pass_number}.txt")
    log = (directory / "document.log").read_text(encoding="utf-8")
    for warning in ("Missing character:", "Overfull \\hbox", "Overfull \\vbox", "LaTeX Font Warning:", "undefined references"):
        require(warning not in log, f"{name}: unexpected {warning!r}; inspect {directory / 'document.log'}")
    result = PDF(directory)
    result.contains("ENDPROBLEMA")
    return result


def check_long_rows(pdf: PDF) -> None:
    require(len(pdf.pages) >= 3, "Long sample did not span multiple pages")
    for marker, total in (("IN", 130), ("OUT", 23)):
        for number in range(1, total + 1):
            token = f"{marker}{number:04d}"
            require(pdf.text.count(token) == 1, f"Missing or duplicated sample row: {token}")
    # Headers must be repeated on each page that carries sample input rows.
    for page in pdf.pages:
        if re.search(r"IN\d{4}", page):
            require("输入" in page and "输出" in page, "A continued sample page lacks table headers")


def input_column_bounds(page: pdfplumber.page.Page) -> tuple[float, float]:
    positions = sorted({round(line["x0"], 2) for line in page.lines
                        if abs(line["x1"] - line["x0"]) < 0.01 and line["bottom"] - line["top"] > 2})
    edges = []
    for position in positions:
        if not edges or position - edges[-1] > 1:
            edges.append(position)
    require(len(edges) >= 3, "Cannot find the sample table's three vertical borders")
    return edges[0], edges[1]


def sample_rows(page: pdfplumber.page.Page) -> list[list[dict]]:
    # Group by baseline rather than trusting whitespace reconstruction, which
    # varies among PDF text readers. Detect the actual table column borders.
    left, right = input_column_bounds(page)
    groups: dict[float, list[dict]] = {}
    for char in page.chars:
        if left < char["x0"] < right:
            groups.setdefault(round(char["top"], 1), []).append(char)
    return [sorted(group, key=lambda char: char["x0"]) for group in groups.values()]


def row_containing(rows: list[list[dict]], text: str) -> list[dict]:
    for row in rows:
        if "".join(char["text"] for char in row).replace(" ", "") == text.replace(" ", ""):
            return row
    raise AssertionError(f"Cannot locate sample row {text!r}")


def check_spacing(pdf: PDF, tab_size: int) -> None:
    with pdfplumber.open(pdf.directory / "document.pdf") as document:
        rows = sample_rows(document.pages[0])
        baseline = row_containing(rows, "ABCDEFGH")
        origin = baseline[0]["x0"]
        advance = baseline[1]["x0"] - origin

        def check_row(text: str, positions: dict[str, int]) -> None:
            row = row_containing(rows, text)
            for letter, column in positions.items():
                char = next(char for char in row if char["text"] == letter)
                measured = (char["x0"] - origin) / advance
                require(abs(measured - column) < 0.08,
                        f"{pdf.directory.name}: {letter!r} at column {measured:.2f}, expected {column}")

        check_row("A B C", {"A": 0, "B": tab_size, "C": 2 * tab_size})
        check_row("ABCD E", {"A": 0, "E": (4 // tab_size + 1) * tab_size})
        check_row("F", {"F": tab_size})
        check_row("J K L M", {"J": 0, "K": 2, "L": 5, "M": 9})
        check_row("N P", {"N": 2, "P": 6})
        previous = row_containing(rows, "N P")[0]
        final = row_containing(rows, "ENDSPACE")[0]
        normal = row_containing(rows, "J K L M")[0]
        require(abs((final["top"] - previous["top"]) / (previous["top"] - normal["top"]) - 2) < 0.03,
                "Blank sample line did not preserve one row of vertical space")


def check_long_line(pdf: PDF, count: int) -> None:
    require(len(pdf.pages) >= 3, "One logical sample line should continue over several pages")
    with pdfplumber.open(pdf.directory / "document.pdf") as document:
        payload = [(page, char) for page in document.pages for char in page.chars if char["text"] == "q"]
        require(len(payload) == count, f"Long sample line lost characters: {len(payload)} of {count}")
        boundaries = {page.page_number: input_column_bounds(page)
                      for page in document.pages if any(char["text"] == "q" for char in page.chars)}
        for page, char in payload:
            left, right = boundaries[page.page_number]
            require(left < char["x0"] < char["x1"] < right,
                    f"Long sample crossed the input column boundary: {char['x0']}, {char['x1']}")
        require(any(char["text"] in {"↪", "→"} for page in document.pages for char in page.chars),
                "Wrapped sample does not show a continuation arrow")
        pair_positions = {}
        for page_number, page in enumerate(document.pages):
            for word in page.extract_words():
                if word["text"] in {"PAIRINPUT", "PAIROUTPUT"}:
                    pair_positions[word["text"]] = (page_number, word["top"])
        require(set(pair_positions) == {"PAIRINPUT", "PAIROUTPUT"}, "Missing following logical sample pair")
        left, right = pair_positions["PAIRINPUT"], pair_positions["PAIROUTPUT"]
        require(left[0] == right[0] and abs(left[1] - right[1]) < 0.1,
                "The next logical input/output pair is misaligned after wrapping")
    pdf.contains("LONGEND", "SINGLEOUTPUT", "PAIRINPUT", "PAIROUTPUT")


def check_mixed_script(pdf: PDF) -> None:
    expected = {"中": 50, "A": 50, "（": 50, "a": 50, "）": 50}
    actual: Counter[str] = Counter()
    with pdfplumber.open(pdf.directory / "document.pdf") as document:
        for page in document.pages:
            left, right = input_column_bounds(page)
            borders = [line for line in page.lines
                       if abs(line["x0"] - left) < 0.1 and abs(line["x1"] - left) < 0.1
                       and line["bottom"] - line["top"] > 2]
            top = min(line["top"] for line in borders)
            bottom = max(line["bottom"] for line in borders)
            for char in page.chars:
                if top <= char["top"] and char["bottom"] <= bottom and char["text"] in expected:
                    actual[char["text"]] += 1
                    # xeCJK compresses punctuation sidebearings; PDF character
                    # advance boxes still include those blank half-em spaces.
                    # Their centers track the visible punctuation position.
                    within = (left < (char["x0"] + char["x1"]) / 2 < right
                              if char["text"] in "（）"
                              else left < char["x0"] < char["x1"] < right)
                    require(within,
                            "Mixed CJK/Latin sample crossed the input column boundary")
    require(dict(actual) == expected, f"Mixed-script sample characters changed: {dict(actual)}")


def check_contest(pdf: PDF, print_mode: bool, cover: bool) -> None:
    expected = (2 if print_mode else 1) * (2 + int(cover))
    pdf.page_count(expected)
    body_start = (2 if print_mode else 1) if cover else 0
    for index, letter in enumerate("AB"):
        page = body_start + index * (2 if print_mode else 1)
        require(f"ENDPROBLEM{letter}" in pdf.pages[page], f"Problem {letter} starts on wrong page")
        require(f"CASE{letter}" in pdf.pages[page], f"Imported sample file for {letter} missing")
        if print_mode:
            require("ENDPROBLEM" not in pdf.pages[page + 1], "Expected a blank page after the problem")
    if cover:
        first_page = pdf.pages[0]
        require("题目 A" in first_page and "题目 B" in first_page, "Cover table of contents is incomplete after two passes")
        require("ENDPROBLEM" not in first_page, "Cover contains problem content")
        with pdfplumber.open(pdf.directory / "document.pdf") as document:
            for page in document.pages[:body_start]:
                require(not any(char["top"] > page.height - 45 for char in page.chars),
                        "Cover pages should not display a page-number footer")
    # Printed numbering restarts at 1 after the cover and remains sequential.
    # Auxiliary Page labels vary by engine, so check the visible Chinese footer.
    require(re.search(r"第\s*1\s*页", pdf.pages[body_start]) is not None,
            "The first problem page should be numbered 1")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=ROOT / "tests" / ".build",
                        help="Keep generated sources, PDFs and logs here")
    args = parser.parse_args()
    build = args.build_dir.resolve()
    build.mkdir(parents=True, exist_ok=True)
    require(shutil.which("xelatex") is not None, "XeLaTeX is required")
    jar = freemarker_jar(build)
    classes = build / "classes"
    classes.mkdir(exist_ok=True)
    run([java_tool("javac"), "-encoding", "UTF-8", "-cp", str(jar), "-d", str(classes),
         str(ROOT / "tests" / "RenderTemplates.java")], ROOT)
    classpath = os.pathsep.join((str(classes), str(jar)))
    completed = 0

    def render(name: str, problems: list[list[tuple[str, str]]], **options) -> PDF:
        nonlocal completed
        print(f"Rendering {name} ...", flush=True)
        pdf = render_case(build, classpath, name, problems, **options)
        completed += 1
        return pdf

    short = [[("2 3\n", "5\n")]]
    pdf = render("short", short)
    pdf.page_count(1)
    pdf.contains("标准输入", "标准输出", "输入格式", "输出格式", "样例", "1 秒", "256 MB")
    require("standard input" not in pdf.text, "Chinese template has an English standard input label")
    pdf = render("english", short, language="english")
    pdf.contains("standard input", "standard output", "1 Second", "256 megabytes")
    pdf = render("long-rows", [[("".join(f"IN{number:04d}\n" for number in range(1, 131)),
                                  "".join(f"OUT{number:04d}\n" for number in range(1, 24)))]])
    check_long_rows(pdf)
    format_input = "ABCDEFGH\nA\tB\tC\nABCD\tE\n\tF\nJ K  L   M\n  N   P\n\nENDSPACE\n"
    for tab_size in (4, 8):
        pdf = render(f"spacing-tab-{tab_size}", [[(format_input, "SPACINGOUTPUT\n")]], tab_size=tab_size)
        check_spacing(pdf, tab_size)
    special = r"\{}%#_$&~^\"<>|"  # These must be literal sample characters, never TeX commands.
    pdf = render("special-characters", [[("SPECIAL" + special + "\n", "SPECIALRESULT\n")]])
    pdf.contains("SPECIAL" + special, "SPECIALRESULT")
    pdf = render("mixed-script", [[("中A" * 50 + "\n" + "（a）" * 50 + "\n", "MIXEDRESULT\n")]])
    check_mixed_script(pdf)
    pdf = render("empty", [[("", "EMPTYINPUT\n"), ("EMPTYOUTPUT\n", ""), ("", ""), ("\n\n", "\n")]])
    pdf.contains("EMPTYINPUT", "EMPTYOUTPUT")
    pdf.page_count(1)
    long_count = 9000
    pdf = render("long-line", [[("q" * long_count + "LONGEND\nPAIRINPUT\n", "SINGLEOUTPUT\nPAIROUTPUT\n")]])
    check_long_line(pdf, long_count)
    pdf = render("single-print", short, print_mode=True)
    pdf.page_count(2)
    require("ENDPROBLEM" not in pdf.pages[1], "Print mode should insert a blank back page")
    for print_mode in (False, True):
        for cover in (False, True):
            name = f"contest-{'print' if print_mode else 'electronic'}-{'cover' if cover else 'no-cover'}"
            pdf = render(name, [[("CASEA\n", "RESULTA\n")], [("CASEB\n", "RESULTB\n")]],
                         contest=True, print_mode=print_mode, cover=cover)
            require(not (pdf.directory / "statements-logo.png").exists(), "Missing-logo fixture unexpectedly has a logo")
            check_contest(pdf, print_mode, cover)
    pdf = render("contest-empty-logo", [[("CASEA\n", "RESULTA\n")], [("CASEB\n", "RESULTB\n")]],
                 contest=True, empty_logo=True)
    check_contest(pdf, False, True)
    pdf = render("contest-print-two-page-cover", [[("CASEA\n", "RESULTA\n")], [("CASEB\n", "RESULTB\n")]],
                 contest=True, print_mode=True, two_page_cover=True)
    check_contest(pdf, True, True)
    require("Cover continuation" in pdf.pages[1], "Expected a two-page cover")
    print(f"PASS: {completed} fixtures rendered with FreeMarker {FREEMARKER_VERSION}, compiled twice and checked.\nArtifacts: {build}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
