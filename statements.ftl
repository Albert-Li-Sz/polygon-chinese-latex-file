\documentclass [11pt, a4paper, oneside] {article}
% 使用 XeLaTeX；Fandol 字体随 TeX Live 提供，避免依赖操作系统字体。
\usepackage [UTF8, fontset=fandol]{ctex}
\usepackage {amsmath}
\usepackage {amssymb}
\usepackage [chinese]{olymp}
\usepackage {comment}
\usepackage {epigraph}
\usepackage {expdlist}
\usepackage {graphicx}
\usepackage {multirow}
\usepackage {siunitx}
\usepackage {ulem}
\usepackage {hyperref}
\usepackage {import}
\usepackage {ifpdf}
\usepackage {xparse}
\usepackage {color}
\usepackage {lastpage}
\usepackage {listings}
\usepackage {booktabs}
\usepackage {etoolbox}

% ---------- 用户配置 ----------
\newif\ifContestPrint
\ContestPrintfalse % 电子版；改为 \ContestPrinttrue 启用打印版补空白页。
\newif\ifContestCover
\ContestCovertrue % 比赛题册封面；改为 \ContestCoverfalse 关闭。
\newcommand{\ContestLogo}{statements-logo.png} % 图片不存在时自动省略。
\newcommand{\ContestNotice}{请勿使用生成式人工智能参加本竞赛}
\newcommand{\ContestStartWarning}{请勿在比赛正式开始前打开题面！}
\renewcommand{\ExampleTabSize}{4} % 样例的 Tab 按每 4 个字符一组的制表位展开。
% 长样例显示行以箭头开头表示续行；箭头不属于样例数据。
% \renewcommand{\ExampleContinuationMarker}{\ensuremath{\hookrightarrow}\,}
% 标题样式单独控制，不改变正文 \textbf 的含义。
% \renewcommand{\problemtitlefont}{\sffamily\bfseries}
% 如需隐藏输入文件、输出文件、时间限制、内存限制，取消对应行的注释。
% \def\NoInputFileName{}
% \def\NoOutputFileName{}
% \def\NoTimeLimit{}
% \def\NoMemoryLimit{}
% ---------- 用户配置结束 ----------

\ifContestPrint
  \intentionallyblankpagestrue
\else
  \intentionallyblankpagesfalse
\fi
\hypersetup{hidelinks}
 
\ifpdf
  \DeclareGraphicsRule{*}{mps}{*}{}
\fi
 
\definecolor{mygreen}{RGB}{28,172,0}
\definecolor{mylilas}{RGB}{170,55,241}
\definecolor{mygray}{RGB}{128,128,128}
\definecolor{mymauve}{RGB}{124,6,123}
\definecolor{myblue}{RGB}{14,84,175}
\definecolor{mybg}{RGB}{248,248,248}
 
\lstset{
	basicstyle=\ttfamily,
	columns=fixed,
	numbers=left,
	numberstyle=\small\color{mygray},
	numbersep=5pt,
	showspaces=false,
	showstringspaces=false,
	showtabs=false,
	frame=single,
	rulecolor=\color{black},
	tabsize=2,
	captionpos=t,
	breaklines=true,
	postbreak=\raisebox{0ex}[0ex][0ex]{\ensuremath{\hookrightarrow}\space},
	commentstyle=\color{mygreen},
	keywordstyle={\bfseries\color{blue}},
	stringstyle=\color{mymauve},
	deletekeywords={...},
	xleftmargin=2em,
	identifierstyle=\color{black},
}
 
\newif\ifmultistatements
 
\begin {document}
 
<#list statements as statement>
<#if statement.path??>
\multistatementstrue
</#if>
</#list>
 
\ifmultistatements
\ifContestCover
\begingroup
\pagestyle{empty}
 
% 封面不创建正文页码锚点，正文随后从第 1 页开始。
\hypersetup{pageanchor=false}
 
\title{\textbf{\Huge{${contest.name!}}}}
\date{${contest.date!}}
\author{${contest.location!}}
\maketitle
\thispagestyle{empty}
 
\ifdefempty{\ContestLogo}{}{%
  \IfFileExists{\ContestLogo}{%
    \begin{center}
    \includegraphics[width=3in]{\ContestLogo}
    \end{center}
  }{}
}
 
\vspace{2.5em}
 
\begin{center}
\Large
 
\makeproblemtoc
 
\vspace{1em}
 
\ContestNotice\par
\Large \textbf{\ContestStartWarning}

\end{center}
\thispagestyle{empty}
 
\clearpage
\ifContestPrint
\ifodd\value{page}
\else
\null
\thispagestyle{empty}
\clearpage
\fi
\fi
\endgroup
\setcounter{page}{1}
\hypersetup{pageanchor=true}

\fi
\fi
 
\contest
{${contest.name!}}%
{${contest.location!}}%
{${contest.date!}}%
 
\binoppenalty=10000
\relpenalty=10000
 
%\renewcommand{\thefootnote}{\fnsymbol{footnote}}
 
<#if shortProblemTitle?? && shortProblemTitle>
  \def\ShortProblemTitle{}
</#if>
 
<#list statements as statement>
<#if statement.path??>
\graphicspath{{${statement.path}}}
<#if statement.index??>
  \def\ProblemIndex{${statement.index}}
</#if>
\import{${statement.path}}{./${statement.file}}
<#else>
\input ${statement.file}
</#if>
</#list>
 
\end {document}
