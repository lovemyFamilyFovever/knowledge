# S4 二期拆分收尾报告（工程线 · 分片4）

> 隔离说明：本会话仅写本文件 `docs/refactor/final-report-s4.md`，**未触碰** `docs/refactor/final-report.md` 及其他分片报告。（第一轮"创建型模式"拆分当时尚无报告隔离要求，其段落写在 `final-report.md`；自第二轮起统一落此文件。）

## §S4 第二轮 · 结构型模式（Structural Patterns）

**处理篇（1 篇，巨型汇编收手）**：`content/baike/design-patterns/结构型模式（Structural Patterns）.md`（原 16104 字 ≫ 8000 → 本会话仅此 1 篇）。

**拆分产物**：
- **枢纽页**（`done-hub`）：正文 1809/2200、0 围栏、1 def + 2 trap；核心机制改为「8 子词条索引表 + 选型判据」，§8.1 信息不重复承载（表格载"有什么"、散文载"怎么选/为什么"）；过滤器/Criteria 作非 GoF 说明枢纽内联，不单列；frontmatter 逐字未改（⑦ 与 HEAD 一致）。
- **新建 8 子词条**（§3 继承父 `source_path: 开发术语 / 设计模式`、`collected: 2026-09-05`、`tags: []`）：
  - `适配器模式.md` 1450/1围栏
  - `桥接模式.md` 1353/1围栏
  - `组合模式.md` 1484/1围栏
  - `装饰器模式.md` 1417/1围栏
  - `外观模式.md` 1301/1围栏
  - `享元模式.md` 1357/1围栏
  - `代理模式.md` 1428/1围栏
  - `MVC 与 MVVM.md` 1933/1围栏（族词条合并 MVC+MVVM；标注"属架构模式、非 GoF 设计模式"，并保留 Reenskaug 1979 / Gossman 2005 出处）

**概念级查重（§8.2）**：全库无同名或异名的结构型 pattern 专条（`云原生` 等文件里的"代理"是反向代理/RPC 义，非 GoF 代理模式，不构成重叠）。唯一重叠为 pending 的 `programming-languages/编程概念音频课-设计模式.md`——其 `### 5 装饰器 / ### 6 适配器 / ### 7 代理` 三节 → 按 §2 第 4 档先行立条，在 `装饰器模式`、`适配器模式`、`代理模式` 三行标 `pending-merge`，并把去重队列第 7 对由"两条"扩展为"五条"（累计 单例/工厂/装饰器/适配器/代理，拆该音频课前不得清）。本轮无删除/改名，不造悬空，未重建索引。

**check_rewrite --strict（本分片 9 篇）**：9 篇全 PASS / 0 FAIL；8 条 warning 均为「新文件不在 HEAD」；0 悬空双链、0 处含 `/` 的链名；⑨ 面试速答全部 ≤150 字硬判通过。`check_cards` 9 篇各 1 def + 2 trap。

**提交**（hash 由 `git log` 自动追加）：

- 0498f56 docs: 二期拆分[S4]——结构型模式 (枢纽+8子词条)

**剩余本分片 pending**：36 篇。**下一篇巨型汇编**：`content/baike/design-patterns/行为型模式（Behavioral Patterns）.md`（16222 字）。
