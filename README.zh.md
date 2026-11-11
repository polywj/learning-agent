# 学习工作区

[English](README.md) | 中文

一个用于学习任意主题的辅导型工作区。把学习资料（PDF、PPTX 等）放进
`materials/`，AI 助教就可以基于资料为你讲解和测验；你也可以直接提问。
学习进度记录在 `progress.md` 中。

- **本文件** —— 面向你（学习者），说明工作区如何搭建和使用。
- **`AGENTS.md`** —— AI 助教的规则手册：辅导风格、会话编排和环境说明。

你可以先从单次提问、测验或资料导入开始，也可以随时设置学习者档案和课程。
你也可以修改 `AGENTS.md` 中的辅导行为。

## 前置条件

| 需求 | 用途 |
|---|---|
| **Node.js**（包含 `npx`） | 运行 DSH 启动命令。 |
| **DeepSeek Harness (DSH)** —— `npx @deepseek-ai/dsh web`，它会自动在浏览器中打开网页 GUI。 | 运行 AI 助教和网页界面。 |
| **Python 3.10 – 3.14** | MarkItDown（文档转 Markdown 工具）要求 `>=3.10, <3.15`。本工作区的 venv 使用 3.14。 |
| **PowerPoint**（Windows 桌面版；仅导入 PPTX/PPT 时需要） | 导入演示文稿时将幻灯片渲染成图片。 |

## 搭建步骤

### 1. 配置模型（DSH 网页 GUI 设置）

在 GUI 设置的 **Models**（模型）中声明：

- **导师模型（tutor model）** —— 你的主 AI 助教；
- **子代理模型（subagent models）** —— 助教可以委派任务的路由（它会自动
  发现这些路由，图像分析默认使用 `deepseek-flash`；详见 `ingest` 技能）。

负责读取页面/幻灯片图片的模型，务必在其 **Input types**（输入类型）中
勾选 **Image**（图像，与 Text 并列）。否则图像分析会报错
*"model does not declare image input"*。

### 2. Python 虚拟环境（`.venv/`）

直接吩咐助教即可——说一句 *"帮我搭建 venv"*。
也可以手动执行：

```powershell
python -m venv .venv
& .venv\Scripts\python.exe -m pip install "markitdown[all]" pymupdf comtypes
```

已验证版本：Python 3.14、markitdown 0.1.9、PyMuPDF 2.0、comtypes 1.4.17。

## 快速上手

从你当前需要的方式开始即可：

- **提问或学习：** *"教我 [主题]"*。
- **测验：** *"考考我 [主题]"*。
- **导入资料：** 把文件放进 `materials/`，对助教说 *"导入 <文件名>"*。
  助教会将文档转换为 Markdown 并保存到 `materials/md/`；PDF 和
  PowerPoint 文件还会附带页面/幻灯片图片。如果有支持图像输入的模型，
  助教会分析生成的图片；此外还会提供内容概览。无需先建立学习计划。

如果你想制定个性化的长期计划，可以请助教帮你设置。助教会简要询问你的
学习主题、目标、经验和偏好，然后提出一份适量的课程计划。你确认后，助教
会在 `progress.md` 中补充你的档案、目标和课程。你也可以在导入资料或参加
测验之后再设置计划。

## 模式

| 模式 | 说明 |
|---|---|
| **给我讲 X** | 结构化讲解，穿插理解检查；结尾做一次复述检验（explain-back）。 |
| **考考我** | 针对你指定的主题或已导入资料测验；如果已有确认的课程计划，也会据此调整。遵循 `quiz-me` 技能。 |
| **深入探讨** | 深入讨论进阶主题、权衡、设计决策或失败案例。 |
| **复习** | 回顾 `progress.md`，重访薄弱点，对旧主题做间隔重复。 |
| **导入资料** | 转换并索引新的培训材料——即 `ingest` 技能——随后给出简短的内容概览。 |
| **自由问答** | 随问随答；`AGENTS.md` 中的辅导原则同样适用。 |

不确定该用哪个模式时，直接说出你的需求即可——助教会帮你选。

## 目录结构

```
materials/          # 原始培训资料，按放入时的样子保存（PDF、PPTX、DOCX 等）——只读，永不修改
materials/md/       # Markdown 转换结果，文件名与源文件一致（另有 <name>_media/ 页面图片）
notes/              # 学习小结与概念笔记
tools/              # 转换与工作区工具脚本（用 .venv 运行；说明见 AGENTS.md）
.venv/              # 工作区 Python 虚拟环境
.agents/            # 工作区技能，AI 助教按需加载
progress.md         # 可选：学习者档案、目标、课程、资料索引、测验与会话记录（格式见 progress-log 技能）
AGENTS.md           # AI 助教规则手册
README.md           # 英文版说明
README.zh.md        # 本文件
```

## 许可证

本项目采用 GNU Affero 通用公共许可证第 3 版（AGPL-3.0）。详见 [LICENSE](LICENSE)。
