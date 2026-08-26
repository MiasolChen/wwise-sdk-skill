# Wwise SDK Skill

一个通过本地头文件、示例、帮助文档和源码准确检索不同版本 Wwise SDK 的
Agent Skill。

[English](README.md)

> [!IMPORTANT]
> 请先通过 **Wwise Launcher** 安装对应 Wwise 版本的 SDK 组件。本仓库不包含
> Wwise SDK。

## 功能

- 从本地头文件确认 API 签名、参数和返回值。
- 从示例、帮助文档和已有源码中查找实际用法。
- 标注所查询的 SDK 版本、相对文件路径和行号。
- 支持 Sound Engine、Spatial Audio、插件、WAAPI、回调和流式 I/O 等主题。

由于 Wwise API 会随版本变化，且 AI Agent 无法稳定访问官方网页文档，本 Skill
以用户实际安装的 SDK 为准。本 Skill 只在明确涉及 Wwise 的提问中激活，通用
游戏音频问题不会触发。

## 安装

将仓库克隆到 AI 工具支持的 Skill 目录：

| 工具 | 全局目录 | 项目目录 |
| --- | --- | --- |
| OpenCode | `~/.config/opencode/skills/wwise-sdk-skills/` | `.opencode/skills/wwise-sdk-skills/` |
| Claude Code | `~/.claude/skills/wwise-sdk-skills/` | `.claude/skills/wwise-sdk-skills/` |
| Codex / Agent Skills | `~/.agents/skills/wwise-sdk-skills/` | `.agents/skills/wwise-sdk-skills/` |

以 OpenCode 全局安装为例：

```sh
git clone https://github.com/MiasolChen/wwise-sdk-skills ~/.config/opencode/skills/wwise-sdk-skills
```

Windows PowerShell：

```powershell
git clone https://github.com/MiasolChen/wwise-sdk-skills "$HOME\.config\opencode\skills\wwise-sdk-skills"
```

安装后请重启或重新加载 AI 工具。

## 配置

打开 Skill 安装目录中的 `wwise-sdk.config.json`，手动填写 SDK 路径：

```json
{
  "sdk_roots": [
    "C:/path/to/Wwise/SDK"
  ],
  "help_roots": []
}
```

每一项可以是 SDK 目录、包含 `SDK` 子目录的 Wwise 安装目录，或包含多个 Wwise
安装目录的父目录。JSON 路径请使用正斜杠或转义后的反斜杠。Skill 不会从环境
变量读取 SDK 路径。

## 首次使用检查

配置好 SDK 路径后，可以让 AI 先检查文档是否缺失：

```text
检查我本地的 Wwise SDK 配置，并告诉我缺少哪些文档。
```

也可以直接运行：

```sh
python scripts/wwise_sdk.py check
```

该命令会报告识别到的 SDK 和版本、`include`、`samples`、`source` 是否存在、
已安装的 SDK 帮助 CHM 和 Authoring 帮助语言、是否有可用的 CHM 解包工具，以及
配置的 `help_roots` 目录是否有效。缺失项会集中列在末尾，并以非零状态码退出。

文档缺失不会导致 Skill 无法运行。只要 `include` 存在，API 查询就能正常工作，
缺失只会让能力不够全面。例如：

| 缺失项 | 影响 |
| --- | --- |
| SDK 帮助 CHM | 无法查询官方指南和概念说明，头文件查询不受影响。 |
| Authoring 帮助 | 无法将 Authoring 文档链接映射到本地页面。 |
| `samples` | 无法参考官方集成示例的用法。 |
| `source` | 无法查看实现细节，公开 API 契约不受影响。 |
| CHM 解包工具 | 帮助文档检索需要预先解包并配置 `help_roots`。 |

只有在需要对应能力时，才需要通过 Wwise Launcher 补装相应组件。

## CHM 帮助文档

项目同时支持两种处理方式：

- **临时解包：** `search --area help` 会查找所选 SDK 中的 CHM，并解包到临时
  目录。Windows 使用 `hh.exe`；所有系统也可使用已安装的 `7z`、`7zz`、
  `7za` 或 `extract_chmLib`。搜索结束后自动删除临时文件。
- **持久解包：** 将 CHM 一次性解包到某个目录，并登记到 `help_roots`。之后 AI
  可以用普通文件工具直接读取解包后的 HTML，速度更快，且兼容所有系统。

可以让 AI 帮你完成持久解包：

```text
把我的 Wwise SDK CHM 帮助文档解包到本地目录，并加入 help_roots。
```

也可以直接运行：

```sh
python scripts/wwise_sdk.py extract-help "C:/Wwise/Wwise2025/HelpExtracted" --language zh
```

该命令会解包 CHM、输出页面数量，并把目录追加到 `wwise-sdk.config.json` 的
`help_roots` 中。使用 `--no-config` 可跳过写入配置；不加 `--language` 则解包
全部语言。

得到的配置：

```json
{
  "sdk_roots": ["C:/Wwise/Wwise2025/SDK"],
  "help_roots": ["C:/Wwise/Wwise2025/HelpExtracted"]
}
```

常用解包命令：

```powershell
# Windows，使用 7-Zip
7z x "C:\Wwise\Wwise2025\SDK\Help\WwiseSDK-Windows.chm" -o"C:\Wwise\Wwise2025\HelpExtracted"
```

```sh
# macOS/Linux，使用 7-Zip
7zz x /path/to/WwiseSDK-Windows.chm -o/path/to/HelpExtracted

# Linux，使用 chmlib
extract_chmLib /path/to/WwiseSDK-Windows.chm /path/to/HelpExtracted
```

解包后请把输出目录填入 `help_roots`。请为不同 SDK 版本使用独立的解包目录，
并只配置与当前 SDK 版本对应的目录。不要将解包后的专有文档提交到本仓库。

## 使用

安装后直接向 AI 工具提问：

```text
根据我本地的 Wwise SDK，PostEvent 有哪些重载？

如何正确注册和注销 Game Object？请引用本地头文件。

比较两个本地 SDK 版本中的 Spatial Audio API 差异。
```

临时查询时也可以在提问中指定路径：

```text
请使用 D:\Wwise\Wwise2025\SDK，解释 PostEvent 回调并引用相关头文件行号。
```

## 官网文档链接

Wwise 官网会拦截自动访问，因此本 Skill 不会抓取网页，而是把官网链接映射到
对应的本地文档页面：

```sh
python scripts/wwise_sdk.py resolve-url "https://www.audiokinetic.com/zh/public-library/2025.1.8_9170/?source=SDK&id=soundengine_events"
```

```text
Page: soundengine_events
Library: sdk
Language: zh
Documentation version: 2025.1.8 build 9170
Local SDK: C:\Wwise\Wwise2025\SDK
Local version: 2025.1.8 build 9170
Local page: Help/zh/WwiseSDK-Windows.chm!/soundengine_events.html
```

链接中的 `id` 与本地 HTML 文件名一致，语言段用于选择对应语言的帮助文档，
版本段会与本地 SDK 版本比对并在不一致时给出提示。你也可以直接把链接贴进
提问，让 AI 自行解析。

## 可选 Python 工具

使用 Skill 不需要 Python。只有使用可选命令行工具时才需要 Python 3.9+：

```sh
python scripts/wwise_sdk.py locate
python scripts/wwise_sdk.py info
python scripts/wwise_sdk.py check
python scripts/wwise_sdk.py extract-help "/path/to/HelpExtracted" --language zh
python scripts/wwise_sdk.py search PostEvent --area include --context 3
python scripts/wwise_sdk.py search PostEvent --area help --ignore-case
python scripts/wwise_sdk.py resolve-url "https://www.audiokinetic.com/zh/public-library/2025.1.8_9170/?source=SDK&id=soundengine_events"
```

## 许可证

本仓库中的原创文件采用 [MIT License](LICENSE) 许可。Wwise 及其 SDK 仍受
Audiokinetic 相关许可条款约束。
