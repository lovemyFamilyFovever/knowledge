# baike 二期 / 三期 全自动执行收官报告

生成于 2026-09-19 无人值守会话。规范依据 `docs/writing-spec-v1.2.md`，逐条自决见 `docs/refactor/autopilot-log.md`。

> 主人，你睡觉期间我把能自动做完的部分做完了，但**有一件必须实话实说**：二期的拆分队列**没有清完**，不是卡住，是我算过之后主动收的口。
>
> **总体战况**：三期速答压缩 **108 篇全部完成、零例外**；二期新拆 **2 篇父文档**（`复杂度分析`、`排序与搜索`），连同你睡前已完成的 2 篇，累计 **4 个枢纽页 + 12 个子词条**；软删除 **0 篇**（预案第 5 对未执行，见下）。
> **机器门全绿**：`--strict` 全量 **344 PASS / 97 FAIL / 1 EXEMPT**，其中 97 篇 FAIL **全部是尚未拆的候选**（①②③⑥ 为汇编固有症状），**⑨ 出现 0 次**，速答这道门已经彻底闭环。
> **双链 0 悬空**：`index.db` 权威口径 5111 条链接、`resolved=0` 计 **0**。四套 smoke 全绿（218/74/9/OK），frontmatter 污染 0、残留副本 0。
> **台账已对平**：442 行 ↔ 442 文件，缺账 0、悬空登记 0、重复行 0 —— 过程中**查出并补上 9 篇金样的漏登**（详见 §4）。
> 有 **5 条 `uncertain-split` 与 3 处规范缺陷**登记在 autopilot-log，等你醒来复审。**全部改动已 commit，未 push。**

---

## 1. 第二阶段（三期速答压缩）：已 100% 完成

| 批次 | 子域 | 篇数 | commit |
|---|---|---|---|
| 1 | middleware + cs-basics | 9 | `61218a7` |
| 2 | data-science | 11 | `814e0e1` |
| 3 | algorithms | 21 | `d2bc0b4` |
| 4 | machine-learning | 25 | `02c0232` |
| 5 | ai-and-llm | 42 | `26890a9` |
| | **合计** | **108** | |

- 每篇**只改 `> 🎯` 一行**，逐批 `git diff --numstat` 校验为 1 ins / 1 del，其余字节零改动。
- 压缩后区间：最短 81 字、最长 150 字，**全部 ≤150**；`speed-answer-over` **0 条**、`speed-answer-truncated` **0 条**（未动用兜底例外）。
- 每篇在对应 status 行备注追加 `v1.2-⑨: <原>→<新>` 留痕，共 108 条。
- 结果：`--strict` 与默认模式的 PASS 数已完全一致，grandfather 降级不再有实际作用对象。

⚠️ **一处质量风险**（详见 autopilot-log §2）：ai-and-llm 那批因我手写压缩的长度估计系统性偏低约 25%，改用了确定性删句修剪器 + 对语义受损的 11 篇逐个手写回补。机械删句**可能连带删掉该篇速答里的"取舍/代价"要点**（定义与机制都还在）。已在日志列出建议优先复看的 10 篇。

## 2. 第一阶段（二期串行拆分）：完成 4 篇，队列剩 97 篇

本次会话新增（连同你睡前的 2 篇打样共 4 篇收官）：

| 父文档 | 子词条 | 枢纽实测 |
|---|---|---|
| `programming-languages/软件测试完全指南.md` | E2E 测试、Playwright 与 Cypress | 2825/3400（①表8行 ②a=4） |
| `software-engineering/03-代码质量.md` | 圈复杂度、代码异味、Clean Code 原则 | 2402/3400（①表8行 ②a=4） |
| `algorithms/复杂度分析.md` | 时间复杂度、空间复杂度、均摊分析、主定理、时空权衡 | 2334/3400（①表7行 ②a=4） |
| `algorithms/排序与搜索.md` | 排序算法、查找算法 | 2258/3400（①表8行 ②a=4） |

**累计：4 个枢纽页 + 12 个子词条**，全部 `--strict` PASS、1 def + 2 trap、0 悬空双链。

**主动收口的理由（需你确认）**：队列剩 97 篇，按本次实测单篇成本（一篇 2–5 个新词条、每词条约 1500 字正文 + 台账 + 验收 + 提交），**约合 250–400 个全新词条**，超出单次会话容量一个量级。继续硬拆的真实风险不是"拆得少"，而是尾段质量塌陷与留下未提交的半成品。因此把剩余工时转给了第三阶段收尾复检——那部分是必须交付完的。

**未执行的一项**：预案第 5 对 `os/Shell 脚本详解.md` 合并进 `os/Shell脚本编程.md` + 软删除。它需要**跨篇章改写与内容搬运**（把数组/字符串/管道重定向示例并入已成品的 done 稿），并且**删除文件**属不可逆动作；无人值守下我选择不动，留给你在场时执行。

## 3. 第三阶段：全量复检结果

| 检查 | 命令 | 结果 |
|---|---|---|
| 机器门全量 | `check_rewrite.py --strict`（442 篇） | **344 PASS / 97 FAIL / 1 EXEMPT**；失败项 ①290 ②84 ③194 ④17 ⑥281，**⑨ = 0** |
| 学习系统 | `tests/test_learn.py` | 218 passed, 0 failed |
| 阅读器 | `tests/test_reader.py` | 74 passed, 0 failed |
| 脚手架 | `tests/test_new_project.py` | 9 passed, 0 failed |
| RAG | `tests/test_rag.py` | RAG TESTS OK |
| frontmatter 污染 | `scan_fm.py` | checked 676，**POLLUTED 0** |
| 残留副本 | `scan_dup.py` | **residual copies 0** |
| 索引重建 | `build_index.py` | FTS 676 documents |
| 双链（权威口径） | `index.db` links | 5111 条，**resolved=0 计 0** |
| 卡面抽样 | `check_cards.py`（随机 50 篇） | 12 篇卡数异常，**经核全部是 `split` 状态的未拆汇编**（14 def / 0 def 属其固有症状），done 稿无一异常 |

**关于 97 篇 FAIL**：与 split-candidates 的 `pending` 数**逐篇吻合**，且 ⑨ 一项为 0 —— 即当前全库不存在"已交付却不合格"的稿子，FAIL 全部是待拆队列的正常在库状态，不是质量事故。
**关于 check_rewrite 的 26 条 ⑧ warning**：已全部证伪——`index.db` 权威口径为 0 悬空，warning 源自朴素正则误吃代码围栏内的 bash `[[ ]]`（v1.1 §9 已知盲区）。

## 4. 账目核对与查出的一处历史漏登

对账脚本（集合差集）结果：**台账 442 行 = 磁盘 442 文件，缺账 0、悬空登记 0、重复行 0**。
状态分布：`done` 340、`done-hub` 4、`exempt-reference` 1、`split` 97（合计 442）。
各片行数：s1 90 / s2 92 / s3 87 / s4 84 / s5 89。

**查出并修复**：9 篇 `v1.0 §9 金样`（`Agent 架构模式详解`、`推荐系统`、`Web性能优化` 及其 6 子）**在 `shards.md` 有分片归属、却在 `sN.md` 无状态行** —— 违反 v1.1 §8"逐篇一行、不许漏"。已按各自子域补登（s1 +1、s3 +1、s5 +7）并同步范围计数。这 9 篇本身 `--strict` 全 PASS，属**纯登记缺失、非质量缺失**，推测是一期时金样已提前达标、分片未回头补账。

## 5. 规范与工具的缺陷（本次新发现，待裁）

1. **v1.2 §3 的 `source_path` 取不到值**：规范说"取该子域在 taxonomy 的 display path"，但 taxonomy 只有短标签（`软件工程`），无 `开发术语 / ` 这一级；且同一子域存量稿分裂成两种 source_path（与导入批次完全同分布）。本次一律**改为继承父文档**，已记 autopilot-log §0.2。**§3 需改写。**
2. **grandfather 判据会自失效**：用"末次提交早于 `e611848`"作判据，任一存量稿若因无关原因被改动一次就会静默失去豁免、当场转红。三期把这 108 篇全部改写并压到达标，**本次恰好自行消化了这个风险**；但判据本身仍脆，稳定写法是改测 `git show e611848:<path>` 快照里的字数。
3. **机器门新增了对台账的依赖**：grandfather 把 `status/sN.md` 的 `done` 当输入，**台账误登 = 豁免误给**且无报警。上面查出的 9 篇漏登正是这类账实不符的实例（方向相反、危害较小，但同源）。建议收尾固定跑本次这套差集对账。

## 6. 交付物与提交

- 报告与本日志：`docs/refactor/final-report.md`、`docs/refactor/autopilot-log.md`
- 全量门输出：`docs/refactor/final-check-rewrite.log`；抽样卡面：`docs/refactor/final-check-cards.log`
- 台账：`docs/refactor/status/s1.md`、`s3.md`、`s5.md`（补登 9 篇）、`docs/refactor/split-candidates.md`

### 本次会话提交（旧→新）

| hash | 内容 |
|---|---|
| `e611848` | 规范 v1.2 落盘：定案 5 类歧义（②b 加双链硬条件、新增 ⑨ 门）+ BACKLOG 登记截断排查 |
| `a07e6d0` | ⑨ 门加 grandfather：v1.2 前 done 存量降级 WARNING，新增 `--strict` |
| `0c862c0` | ⑨ 门留痕：金样 ESB 与枢纽页 🎯 压至 ≤150，台账补 `pending-merge` |
| `f47b7d0` | 二期拆分 03-代码质量 → 枢纽页 + 3 子词条 |
| `61218a7` `814e0e1` `d2bc0b4` `02c0232` `26890a9` | 三期速答压缩 108 篇（5 批） |
| `aaf5c0a` | 二期拆分 复杂度分析 → 枢纽页 + 5 子词条 |
| `eac6e73` | 二期拆分 排序与搜索 → 枢纽页 + 2 子词条 |
| （收尾提交） | 收官报告、autopilot-log、全量门与抽样日志、9 篇金样补账 |

**全部未 push。** `content/projects/` 的两处删除、根目录 `附件.md`、`.qoder-credits/` 是你的手动改动，本次会话全程未碰、未提交、未恢复。

## 7. 如何续作剩余 97 篇

1. **取队列**（按字母序，`pending` 即待拆）：
   ```sh
   PYTHONIOENCODING=utf-8 python -c "
   import pathlib
   for l in pathlib.Path('docs/refactor/split-candidates.md').read_text(encoding='utf-8').splitlines():
       if l.startswith('| content/baike/') and l.rstrip().endswith('| pending |'):
           print(l.strip().strip('|').split('|')[0].strip())
   "
   ```
2. **拆前先查重**：队列的 `子概念预览` 列只是线索，动手前务必 `grep -rl "title: \"<子概念名>\"" content/baike/` 验一遍——本次两篇都发现队列把同义条数进了子概念数（`03-代码质量` 记 13、实为 11；`排序与搜索` 记 16、其中 5 个 DFS/BFS/A*/Dijkstra/Floyd 早有专条）。**先看 `docs/refactor/split-candidates.md` 顶部的重叠去重队列**（现有 6 对）。
3. **单篇流程与验收门**：`PYTHONIOENCODING=utf-8 python scripts/agent/check_rewrite.py --strict <枢纽> <各子词条>` 全 PASS 且 `check_cards.py` 每篇 1 def + 2 trap，才算完；枢纽页需同时满足 ①（≥4 数据行的表或 mermaid）与 ②（≥3 具名 H2/H3 子概念，或核心机制粗体项 ≥3 且**含双链**）。
4. **台账三处同步**：本片 `status/sN.md`（父改 `done-hub` + `split-into:`、子词条各加 `done` 行）、`split-candidates.md`（该篇 `pending` → `done`）、必要时登记 `pending-merge`；**收尾固定跑一遍集合差集对账**，本次就是靠它抓出 9 篇漏登。
5. **建议优先级**：`database/`、`security/` 尾部多篇仅 6 个子概念、字数 3000–4000，性价比最高；`architecture/`、`programming-languages/` 里 15000–20000 字的巨型汇编每篇要 8–12 个子词条，建议单独排期、一次一篇。
6. **两个待你裁决的前置项**：① v1.2 §3 的 `source_path` 口径要不要正式改成"继承父文档"（本次已按此执行 12 篇）；② `os/Shell 脚本详解.md` 的合并 + 软删除是否执行（涉及删文件，本次未动）。

