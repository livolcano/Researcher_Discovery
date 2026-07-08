# Researcher Discovery MVP

面向非软件工程同事的交接文档。这个项目用于从公开论文站点的官方 API 检索论文元数据，整理出可供 Sales / FAE 初筛的 researcher candidate 列表。

如果你会用 Copilot，但不想自己读源码，这份 README 已经尽量写成可直接交给 Copilot 执行的操作说明。

## 1. 这个项目是做什么的

这个 MVP 解决的是“先把相关研究者找出来”这一步，而不是完整销售流程自动化。

它会做这些事：

- 从 OpenAlex、arXiv、IEEE Xplore 检索论文元数据。
- 依据配置好的关键词批量查询。
- 提取论文、作者、作者机构等字段。
- 把不同来源的作者记录做去重和合并。
- 按简单规则打分，生成 researcher candidate 清单。
- 导出 Excel 给业务同事复核。
- 保存中间 JSON 和 source log，便于追查数据来源。

它明确不做这些事：

- 不发邮件。
- 不做 Google Scholar scraping。
- 不采集私人邮箱。
- 不判断 buying intent。
- 不写回 CRM。
- 不依赖 LLM API 或其他外部 AI API。

## 2. 适合谁接手

这份交接是按以下假设写的：

- 接手同事不是专业软件工程师。
- 接手同事会使用 Copilot / AI Agent 辅助完成环境搭建和问题排查。
- 接手同事愿意按文档一步一步执行，不直接改核心代码逻辑。

如果你满足上面 3 条，通常不需要先理解全部 Python 代码，也可以把项目跑起来。

## 3. 你需要准备什么

最少需要：

- 一台可以联网的 Windows 电脑。
- Python 3.11 或 3.12。
- VS Code。
- Copilot 可用。
- 能访问公开论文网站 API。

建议你先让 Copilot 帮你检查本机环境，再开始。

可以直接把下面这段话发给 Copilot：

```text
请把当前文件夹 build/researcher_discovery_mvp 当成一个需要交接的 Python 项目。
目标不是重构代码，而是帮我确认本机是否具备运行条件，并按 README 的步骤带我完成：
1. 检查 Python 版本。
2. 创建虚拟环境。
3. 安装 requirements.txt。
4. 指导我配置 .env。
5. 运行一次项目。
6. 检查输出 Excel 和日志文件是否生成。
如果出错，请优先给出最小修复步骤，不要重写整个项目。
```

## 4. 数据安全和合规边界

这个项目的数据安全风险较低，原因如下：

- 数据源是公开论文站点的官方 API。
- 处理的是论文元数据，不是内部客户数据。
- 输出保存到本地文件，不自动上传第三方系统。
- 项目不采集私人邮箱，不做自动触达。

但仍然有 2 个边界要注意：

- API key 仍然是凭据，必须保存在本地 `.env`，不要发到群里，不要提交到 Git。
- 输出结果虽然是公开元数据整理，但业务判断和后续触达仍要人工复核。

## 5. 项目目录说明

你只需要先认识这几个位置：

- `README.md`：当前交接文档。
- `requirements.txt`：Python 依赖清单。
- `config/keywords.yaml`：检索关键词。
- `config/settings.yaml`：数据源开关、年份、结果上限、输出路径。
- `src/main.py`：主入口。
- `data/researcher_discovery_output/`：Excel 和运行日志输出目录。
- `data/interim/`：中间 JSON 文件，便于排查问题。
- `tests/`：基础自动化测试。

## 6. API 说明和申请方法

本项目当前接了 3 个来源，但不是 3 个都需要你先申请账号。

### 6.1 arXiv

- 用的是 arXiv 官方 API。
- 不需要申请 API key。
- 官方建议连续请求之间至少间隔 3 秒。
- 当前项目已经在配置里按 3 秒节流。

你可以把 arXiv 当成“开箱即可用”的来源。

### 6.2 OpenAlex

- 用的是 OpenAlex 官方 API。
- 不带 key 也能用，但免费额度较低。
- 建议申请一个免费的 API key，稳定性和可用额度更好。
- 官方文档说明可以在 OpenAlex 账号设置页生成 key。

建议动作：

1. 打开 OpenAlex 官网并注册账号。
2. 登录后进入 API settings 页面。
3. 复制 API key。
4. 写入本地 `.env` 的 `OPENALEX_API_KEY`。
5. 同时填写 `CONTACT_EMAIL`，让请求更符合官方 polite pool 建议。

如果一开始你不想申请，也可以先把 `OPENALEX_API_KEY` 留空，项目通常仍可运行。

### 6.3 IEEE Xplore

- 用的是 IEEE Xplore Metadata API。
- 这个来源需要 API key。
- 没有 key 时，代码会自动跳过 IEEE，不会导致整个项目失败。

申请建议步骤：

1. 打开 IEEE Developer Portal。
2. 注册开发者账号。
3. 找到 IEEE Xplore Metadata API。
4. 按页面流程申请或订阅可用访问权限。
5. 获取 API key 后，写入本地 `.env` 的 `IEEE_API_KEY`。
6. 首次调用后，确认返回不是权限错误或配额错误。

如果暂时拿不到 IEEE key，建议先把 `config/settings.yaml` 里的 `ieee.enabled` 改为 `false`，先跑通 OpenAlex + arXiv。

## 7. 一次性安装步骤

以下步骤默认你在 Windows + PowerShell + VS Code 环境下操作。

### 7.1 打开项目目录

项目根目录是：

```text
build/researcher_discovery_mvp
```

### 7.2 创建虚拟环境

在项目根目录打开终端后执行：

```powershell
python -m venv .venv
```

### 7.3 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 阻止执行脚本，可以先执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

然后再执行激活命令。

### 7.4 安装依赖

```powershell
pip install -r requirements.txt
```

### 7.5 创建本地 `.env`

先复制模板：

```powershell
Copy-Item .env.example .env
```

然后打开 `.env`，按你自己的实际信息填写。

推荐最小写法：

```text
OPENALEX_API_KEY=
IEEE_API_KEY=
CONTACT_EMAIL=your.name@your-company.com
```

说明：

- `OPENALEX_API_KEY`：可选，建议填写。
- `IEEE_API_KEY`：只有要启用 IEEE Xplore 时才需要。
- `CONTACT_EMAIL`：建议填写真实工作邮箱。

## 8. 首次运行前要改哪两个配置

### 8.1 关键词配置

文件：`config/keywords.yaml`

每条 query 至少要有：

- `id`：查询编号，例如 `Q01`
- `text`：查询语句
- `topic_cluster`：该 query 属于哪个主题组

如果你不确定怎么写 query，不要先改代码，直接让 Copilot 帮你改 YAML。

可以对 Copilot 说：

```text
请只修改 config/keywords.yaml，不改 Python 代码。
目标主题是 <你的主题>。
请保留现有 YAML 结构，为我生成 8 到 12 条适合 researcher discovery 的英文检索语句，避免过宽泛。
```

### 8.2 运行参数配置

文件：`config/settings.yaml`

你最常改的是：

- 哪些 source 开启或关闭。
- 每个 query 最多取多少条结果。
- 从哪一年开始筛选。
- Excel 输出路径。
- 打分阈值。

首次建议：

- 保持 `max_results_per_query: 50`。
- 保持 `from_publication_year: 2022`。
- 如果 IEEE key 还没申请好，把 `ieee.enabled` 改成 `false`。

## 9. 如何运行

在项目根目录执行：

```powershell
python -m src.main
```

运行完成后，终端通常会打印：

- query 数量
- paper record 数量
- author relation 数量
- researcher candidate 数量
- Excel 输出文件路径

如果终端没有报错，但数字全是 0，优先检查：

## 10. 简易 UI

如果你不想改 YAML，可以直接用一个极简页面输入关键词和地理范围。

先安装依赖：

```powershell
pip install -r requirements.txt
```

启动页面：

```powershell
streamlit run ui_app.py
```

页面里只保留 4 个必要输入：

- `关键词`：每行一个关键词或检索语句。
- `国家`：可选，例如 `Japan`。
- `Continent`：可选，只支持 `APAC`、`EMEA`、`AMER`。
- `开始搜索`：执行搜索并生成结果。

运行后页面会显示：

- query 数量
- paper 数量
- author relation 数量
- researcher candidate 数量
- 候选人简表
- Excel 下载按钮

## 11. Desktop App Packaging

如果你想把这个项目做成可直接点击运行的桌面应用，而不是手动执行 `streamlit run`，项目里已经补了桌面启动器和打包脚本。

相关文件：

- `desktop_launcher.py`：桌面入口。双击后的本地应用会从这里启动。
- `ResearcherDiscovery.spec`：macOS 打包配置。
- `build_mac_app.sh`：macOS 构建脚本。
- `build_windows_exe.ps1`：Windows `exe` 构建脚本。
- `requirements-desktop.txt`：桌面打包额外依赖。

### 11.1 macOS

在项目根目录执行：

```bash
chmod +x build_mac_app.sh
./build_mac_app.sh
```

构建完成后，产物会在：

```text
dist/ResearcherDiscovery.app
```

### 11.2 Windows

在 PowerShell 中执行：

```powershell
.\build_windows_exe.ps1
```

构建完成后，产物会在：

```text
dist\ResearcherDiscovery\
```

说明：

- Windows `exe` 需要在 Windows 环境下构建，不能在 macOS 上直接产出原生 Windows `exe`。
- macOS `.app` 需要在 macOS 环境下构建。
- 如果是首次打开 macOS `.app`，系统可能会提示来源未验证，需要在系统设置里允许打开，或使用右键 `Open`。
- 本地文件夹选择功能适用于桌面本地运行，不适用于部署到公网域名后的浏览器访问场景。

- 关键词是否太窄。
- 网络是否可访问目标站点。
- `from_publication_year` 是否过新。
- IEEE 是否因为没有 key 被跳过。

## 10. 成功运行后你应该看到什么

### 10.1 Excel 主输出

默认输出文件：

```text
data/researcher_discovery_output/researcher_discovery_mvp.xlsx
```

主要 sheet 含义：

- `README`：结果使用提醒，不是数据本身。
- `Query_Plan`：本次执行的 query 清单。
- `Paper_Results`：论文级结果。
- `Author_Paper_Relation`：作者和论文关系表。
- `Researcher_Candidates`：去重后的候选研究者清单。
- `Data_Source_Log`：各 source 各 query 的成功或失败记录。

### 10.2 中间 JSON

这些文件主要用于排查问题：

- `data/interim/paper_results.json`
- `data/interim/author_relations.json`
- `data/interim/researcher_candidates.json`
- `data/interim/source_logs.json`

### 10.3 日志目录

运行日志会写到：

```text
data/researcher_discovery_output/logs
```

## 11. 结果怎么读

最重要的是 `Researcher_Candidates` 这个 sheet。

优先看这些列：

- `researcher_name`
- `primary_institution`
- `country_or_region`
- `related_paper_count`
- `latest_publication_year`
- `top_evidence_papers`
- `topic_clusters`
- `evidence_urls`
- `relevance_score`
- `relevance_level`

请注意：

- 这个分数只是规则打分，不代表真实商机价值。
- 同名作者在机构信息缺失时，仍可能被误合并。
- arXiv 的机构和作者标识覆盖率通常弱于 OpenAlex。
- 有些空字段不是程序坏了，而是源站本来就没给结构化字段。

## 12. 推荐接手方式

对非工程同事，最稳妥的接手顺序是：

1. 先不改代码，只跑通默认配置。
2. 再只改 `config/keywords.yaml`。
3. 再决定是否启用 IEEE。
4. 最后才考虑调整打分逻辑。

不要一开始就让 Copilot 重构整个项目。这个项目是一个可运行 MVP，不是要你重新设计架构。

## 13. 常见问题

### Q1. 没有 IEEE key，可以先用吗

可以。把 `config/settings.yaml` 里的 IEEE 开关关掉，先跑 OpenAlex 和 arXiv。

### Q2. 为什么 Excel 里有些机构或国家为空

因为源站元数据不完整，尤其 arXiv 常见。项目会尽量保留 `affiliation_raw` 之类的原始线索。

### Q3. 为什么输出不是 prospect list

因为这个项目只证明“这个研究者在公开论文上和主题相关”，不证明他有采购需求、预算、项目窗口或合作意愿。

### Q4. 为什么要保留 JSON 中间文件

因为业务同事如果怀疑某个候选人是否被误判，可以回看原始 paper / author 结构，而不必直接读源码。

### Q5. 如果出错，先让 Copilot 做什么

优先让 Copilot 做这几件事：

1. 检查 Python 版本。
2. 检查虚拟环境是否已激活。
3. 检查 `pip install -r requirements.txt` 是否成功。
4. 检查 `.env` 是否存在以及 key 是否为空。
5. 检查 `config/settings.yaml` 里的 source 开关。
6. 检查 `data/researcher_discovery_output/logs` 和 `data/interim/source_logs.json`。

## 14. 建议给 Copilot 的排障提示词

如果项目运行失败，可以直接把下面这段话发给 Copilot：

```text
请在 build/researcher_discovery_mvp 目录下帮助我排查运行失败问题。
前提：不要大改架构，不要重写项目。
请按下面顺序排查：
1. Python 版本是否合适。
2. 虚拟环境是否激活。
3. requirements.txt 是否已安装。
4. .env 是否存在，哪些变量缺失。
5. config/settings.yaml 是否把某个 source 配错。
6. 运行 python -m src.main 后，去看 data/researcher_discovery_output/logs 和 data/interim/source_logs.json。
请给我最小修复步骤，并解释修复后我应该再次执行什么命令。
```

## 15. 交接完成的最低验收标准

把项目移交给其他同事时，至少要满足下面 5 条：

1. 同事知道这个项目只做 researcher discovery，不做 outreach。
2. 同事能自己申请 IEEE Xplore API key，或知道如何先关闭 IEEE。
3. 同事能自己创建 `.env` 并填写必要变量。
4. 同事能自己运行 `python -m src.main`。
5. 同事能找到 Excel、JSON 和日志，并知道先看哪个 sheet。

## 16. 当前已知限制

- arXiv 元数据经常缺机构、国家和稳定 author ID。
- OpenAlex 覆盖质量取决于其索引数据。
- IEEE Xplore 返回字段可能不完整，尤其机构结构化程度不总是一致。
- 去重是启发式规则，不是 author disambiguation 专业系统。
- 打分规则是轻量规则，适合初筛，不适合直接外呼决策。

## 17. 如果你要继续增强项目

建议优先级：

1. 增加更稳的 DOI 校验。
2. 增加更多公开学术数据源。
3. 增加更清晰的 reviewer workflow。
4. 增加面向业务同事的结果摘要页。

在这些增强之前，先确保当前交付链路稳定可复现：配置可改、API 可用、Excel 可出、日志可追。
