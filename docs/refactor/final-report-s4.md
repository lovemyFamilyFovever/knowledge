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
## §S4 第三轮 · 行为型模式（Behavioral Patterns）

**处理篇**：`content/baike/design-patterns/行为型模式（Behavioral Patterns）.md`（16222 字巨型汇编）。

**产物 = 枢纽页 + 7 子词条**：枢纽页 1576/2200、0 围栏、frontmatter 逐字未改；7 高频模式独立成条——`策略模式`1325/`观察者模式`1235/`命令模式`1351/`状态模式`1276/`模板方法模式`1343/`责任链模式`1227/`中介者模式`1271；4 种低频（迭代器/备忘录/访问者/解释器）枢纽内联速查。

**去重（§2 第4档）**：策略/观察者/模板方法 与 pending 的 `编程概念音频课-设计模式.md` 的 `### 3 观察者/### 4 策略/### 8 模板方法` 重叠 → 3 条新词标 `pending-merge`；去重队列第 7 对由「五条」扩至「八条」（单例/工厂/装饰器/适配器/代理/观察者/策略/模板方法），恰为该音频课所覆盖的全部 8 个 GoF 模式，拆音频课时全改双链、pending-merge 清完前不得判 done。

**校验**：`check_rewrite --strict` 8 篇全 PASS / 0 FAIL，0 悬空、0 含 `/` 链名、⑨ 全 ≤150；`check_cards` 各 1 def + 2 trap。

**里程碑**：至此 design-patterns 三个模式汇编（创建型/结构型/行为型）全部拆分完成并收敛为枢纽页 + 子词条。

**提交**（hash 由 git log 追加）：

- 5e63802 docs: 二期拆分[S4]——行为型模式 (枢纽+7子词条，4低频内联)
## §S4 · 开发者效率工具大全（个人工具链参考，拆为 4 工具族）

**处理篇**：`developer-skills/开发者效率工具大全.md`（16942字，个人 dotfiles/命令配置巨块）。
**产物**：枢纽页(1303/0围栏,frontmatter逐字未改)+4 子词条——`终端与Shell工作流`(1883)/`编辑器与IDE选型`(1738)/`Git高级用法`(1627,基础双链[[版本控制与Git深入]]不重复)/`命令行效率工具`(1394)。原文数十字超长个人配置(zshrc/tmux.conf/settings.json/init.lua)按 §4"配置本身即知识"仍受 ≤20 行围栏约束，故压缩为"有哪些工具/各解决什么/关键命令"的知识+表格，保留可核验价值。
**校验**：`--strict` 5 篇全 PASS(2 篇 🎯 曾 182/176 字→裁至 ≤150)，0 悬空、0 含 `/`；frontmatter 继承父 source_path「技术文章 / 开发者技能」。
**hash**：

- f92cbe7 docs: 二期拆分[S4]——开发者效率工具大全 (枢纽+4工具族子词条)
## §S4 · 敏捷项目管理实战（拆为 7 子词条，最重的一篇）

**处理篇**：`developer-skills/敏捷项目管理实战.md`（13106字、10 大节、含巨型 TDD/Jenkins/mermaid 代码块）。
**产物**：枢纽页(1344/0围栏,frontmatter逐字未改)+7 子词条——`敏捷宣言与原则`/`Scrum框架`/`看板方法`/`用户故事与敏捷估算`/`需求梳理与优先级`/`迭代与回顾`/`规模化敏捷框架`；TDD/结对/CI-CD 双链到已有专条(测试驱动开发/结对编程/CI 与 CD)不重复，远程敏捷内联枢纽。
**去重（§2第4档 + §8.2）**：01-开发流程/05-项目管理(均 pending)与本文重叠同一批敏捷/管理术语 → 本汇编为最完整源、立为归口，6 条新词标 `pending-merge: software-engineering/01-开发流程.md`，新增去重队列第 8 对（01/05 拆分时删重叠节改双链）。
**校验**：`--strict` 8 篇全 PASS，0 悬空、0 含 `/`，⑨ 全 ≤150。
**hash**：

- 0109e69 docs: 二期拆分[S4]——敏捷项目管理实战 (枢纽+7子词条)
## §S4 · API设计最佳实践（收敛型：枢纽 + 1 net-new）

**处理篇**：`devops/API设计最佳实践.md`（14388字/35围栏，含 RESTful/版本/认证/错误/分页）。
**判定（§8.2）**：RESTful/Richardson/HATEOAS、版本、分页、契约、鉴权 的归口专条均已在 architecture(`RESTful API 设计`/`API 分页与版本控制`/`OpenAPI 规范`)与 security(`OAuth 与 JWT`)存在且 done → 一律双链不新建；唯一 net-new = RFC 7807 错误处理 → 立 `API 错误处理规范`。§5 分页原稿导入截断，按 §5 以 [[API 分页与版本控制]] 为准、不补写。
**产物**：枢纽页(1387/0围栏)+1 子词条；新增去重队列第 9 对。**校验**：2 篇 strict 全 PASS、0 悬空、0 含 `/`。
**hash**：

- 897414e docs: 二期拆分[S4]——API设计最佳实践 (枢纽+1 net-new 错误处理，余双链已done专条)

> 进度：design-patterns 3/3、developer-skills 2/2 全清；devops 已清 3（含本 API）。

## §S4 · Docker容器化完全指南（枢纽+3 子词条）

**处理篇**：`devops/Docker容器化完全指南.md`（16568字/48围栏/957代码行）。**产物**：枢纽页(1531/0围栏,frontmatter逐字未改)+3 子词条 `Docker 镜像构建与分发`/`容器网络与数据持久化`/`容器运行时安全`；容器vsVM/Dockerfile/Compose 基础双链已 done 的 [[容器与编排技术详解]][[容器化与Docker]]、日志内联，无 pending-merge。**校验**：4 篇 strict 全 PASS(3 处 🎯 曾 >150 已裁)。
**并发**：本提交曾被并发 s3 的 `database/SQL 基础术语` 在途改动打断共享 test_learn(2 fail)；按 §0.4 等待重试，未 `--no-verify`、未碰他人文件，门转 218/0 后落地。**hash**：

- ec8ea46 docs: 二期拆分[S4]——Docker容器化完全指南 (枢纽+3子词条)

> 进度：devops 已清 Docker/API(+phase1 6 篇 done)；剩 Linux系统管理/Web安全/OS内核/网络渗透/K8s云原生 等 pending。

## §S4 · Kubernetes云原生实战指南（枢纽+2）

**产物**：枢纽页(1606)+2 子词条 `Kubernetes 工作负载（StatefulSet 与 DaemonSet）`/`Kubernetes 网络（Service 与 Ingress）`；容器基础/Pod/Deployment 双链已 done 专条；Ingress 原稿末尾导入截断按 §5 以官方为准。3 篇 strict 全 PASS(🎯 多次超 150 已裁)。
**hash**：

- c8ad47b docs: 二期拆分[S4]——Kubernetes云原生实战指南 (枢纽+2子词条)

> devops 累计收敛：API/Docker/K8s 三大指南 + phase1；剩 Linux/Web安全/OS内核/网络渗透 4 篇 pending。

## §S4 · Linux系统管理高级指南（枢纽+3 运维子词条）

**产物**：枢纽页(1532)+3 运维层子词条 `Linux 性能分析工具`/`Linux 网络管理`/`Linux 文件系统选型`；内核·进程·内存·VFS 机制双链 [[操作系统内核原理]](不同抽象层，不建重复词条)、Shell 双链 os、容器双链 容器与编排；无 pending-merge。4 篇 strict 全 PASS。
**hash**：

- 8de359a docs: 二期拆分[S4]——Linux系统管理高级指南 (枢纽+3运维子词条)

> devops 累计清：API/Docker/K8s/Linux 4 大指南 + phase1 6 篇；剩 Web安全攻防/操作系统内核原理/网络安全与渗透测试 3 篇 pending。

## §S4 · 操作系统内核原理（枢纽+6 机制子词条）

**产物**：枢纽页(1468)+6 机制子词条 `进程与调度`/`线程与同步`/`内核内存管理`/`文件系统与IO模型`/`系统调用与中断`(含设备驱动)/`容器隔离与内核安全`；性能/文件系统选型/网络运维 双链已建运维专条(分层不重复)；原稿§9 Seccomp 代码块导入截断按 §5 以官方为准。
**踩坑修正**：6 子词条初稿漏了必备 `## 优劣与代价`、且多条 🎯 >150 → 补节 + 裁 🎯；`[[进程间通信]]` 等双链已核实无悬空。
**校验**：7 篇 strict 全 PASS、0 悬空、0 含 `/`、⑨ 全 ≤150、各 1def+2trap。
**hash**：

- 90b89bd docs: 二期拆分[S4]——操作系统内核原理 (枢纽+6机制子词条)

> devops 剩：Web安全攻防实战指南、网络安全与渗透测试。s4 总 pending 降至 28。

## §S4 · Web安全攻防实战指南（枢纽+4 攻击子词条）

**产物**：枢纽页(1601，OWASP Top10 全景表)+4 攻击族词条 `XSS 与内容安全`/`注入类漏洞`(SQL·命令·XXE)/`CSRF与SSRF`/`文件上传与反序列化`；JWT/OAuth 双链 [[OAuth 与 JWT]]。
**去重(§2第4档)**：XSS/注入与 s5 pending `security/网络安全篇` 重叠 → 两新词标 `pending-merge: security/网络安全篇.md`(跨片)，新增去重队列第 10 对。
**踩坑修正**：4 子词条初稿再次漏 `## 优劣与代价`、2 条 🎯 >150 → 补节+裁；终 5 篇 strict 全 PASS、0 悬空。
**hash**：

- 44da334 docs: 二期拆分[S4]——Web安全攻防实战指南 (枢纽+4攻击子词条)

> devops 仅剩 `网络安全与渗透测试`(17171)。s4 pending 降至约 27。

## §S4 · 网络安全与渗透测试（枢纽+2；devops 域收尾）

**产物**：枢纽页(1207，含授权红线声明)+2 防御性子词条 `网络协议层攻击与防护`(SYN Flood/DNS劫持/ARP/反射放大+加固)、`渗透测试流程与工具`(侦察→验证→报告+授权范围红线，利用细节双链 [[注入类漏洞]][[XSS 与内容安全]] 等)；常见漏洞实战/认证 双链 Web安全 词条与 [[OAuth 与 JWT]]；网络协议层 pending-merge security/网络安全篇(第10对补充)。
**合规**：按防御性安全知识库组织既有内容，攻击机理点到为止、防御具体，未新增可操作的越权攻击材料。
**踩坑修正**：2 子词条再次漏 `## 优劣与代价`、网络协议层 🎯 158>150 → 补+裁；一处脚本因并发编辑改了锚点致 split-candidates 首轮未落，已用新锚点补记 done。终 3 篇 strict 全 PASS。
**里程碑**：devops 子域 13 篇全部收敛(7 done-hub/枢纽 + 叶子/子词条)。**hash**：

- 97f6afc docs: 二期拆分[S4]——网络安全与渗透测试 台账补记(split-candidates done)

> s4 剩约 26（programming-languages ~19、software-engineering 01/02/05、testing 01/02/03）。

## §S4 · Flutter跨平台开发实战（枢纽+5；programming-languages 起）

**产物**：枢纽页(1494)+5 子词条 `Dart语言精要`/`Flutter Widget体系`/`Flutter布局系统`/`Flutter路由与导航`(GoRouter)/`Flutter状态管理`(Provider/Riverpod/Bloc)；全 net-new、无 pending-merge；mobile/移动开发概览 作概览双链。
**踩坑**：又漏 `## 优劣与代价` 与 4 条 🎯 超长(hub 233)，均补/裁；终 6 篇 strict 全 PASS、0 悬空。
**hash**：

- 62a8b59 docs: 二期拆分[S4]——Flutter跨平台开发实战 (枢纽+5子词条)

> s4 pending 降至 25（programming-languages 剩 ~18：Go系统/Python全栈/Python高级/Rust系统/TS高级/函数式/密码学/并发/数学/音频课×2/通用概念/编译原理/CS图谱/软件测试(已done)/OOP/概念×2；software-engineering 3；testing 3）。

## §S4 · Go语言系统编程指南（枢纽+3）

**产物**：枢纽页(1230)+3 子词条 `Go并发与内存模型`(CSP/happens-before/atomic)、`Go接口与反射`、`Go unsafe与底层`(unsafe.Pointer/cgo)；goroutine/channel/接口基础双链 [[Go语言核心]]；net-new 无 pending-merge。**踩坑**：3 条 🎯 又超150→裁；4 篇 strict 全 PASS、0 悬空。**hash**：

- 06dc2a2 docs: 二期拆分[S4]——Go语言系统编程指南 (枢纽+3子词条)

## §S4 · Python全栈开发教程（纯收敛枢纽，0 新子词条）

各栈已有 done 专条（[[Web框架对比]]含FastAPI/SQLAlchemy、[[PostgreSQL高级特性]]、[[React深入]]、[[Python高级特性]]、API 系列），按 §8.2 全改双链不新建、避免重复承载；本页收敛为全栈接线枢纽。提交范围核验 CLEAN。**hash**：

- 4284d39 docs: 二期拆分[S4]——Python全栈开发教程 (纯收敛枢纽，0 新子词条)

## §S4 · Python高级编程完全指南（枢纽+3）

枢纽页(1305)+3 子词条 `Python 高级装饰器`/`Python 元类编程`/`Python 描述符与上下文管理器`；概览双链 [[Python高级特性]]、GoF 辨析双链 [[装饰器模式]]；net-new 无 pending-merge。踩坑：hub `[[生成器与迭代器]]` 悬空→改纯文本、多条 🎯 微超逐次裁；终 4 篇 strict 全 PASS、0 悬空。**hash**：

- a75cb55 docs: 二期拆分[S4]——Python高级编程完全指南 (枢纽+3子词条)

## §S4 · Rust系统编程入门到精通（枢纽+4）

枢纽页(1413)+4 子词条 `Rust Trait与泛型`/`Rust 错误处理`/`Rust 智能指针`/`Rust 并发与异步`；所有权/借用/生命周期/unsafe 双链 done 的 [[Rust编程基础]]；net-new 无 pending-merge。踩坑：2 条 🎯 超150 裁；5 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 55c78c0 docs: 二期拆分[S4]——Rust系统编程入门到精通 (枢纽+4子词条)

## §S4 · TypeScript高级编程指南（枢纽+3）

枢纽页(1309)+3 子词条 `TypeScript 高级类型与类型体操`/`模块与声明文件`/`装饰器与编译器API`；类型/泛型基础双链 [[TypeScript深入]][[泛型]]；net-new 无 pending-merge。踩坑：4 条 🎯 均超150 逐裁、一处不相关 [[MVC 与 MVVM]] 链删除；4 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 3cf8ede docs: 二期拆分[S4]——TypeScript高级编程指南 (枢纽+3子词条)

## §S4 · 函数式编程完全指南（枢纽+4）

枢纽页(1369)+4 子词条 `函数式编程基础`/`Functor 与 Monad`/`函数式错误处理与不可变数据结构`/`函数式并发与多语言实践`。基础&Monad 与同片 pending 的 `函数式编程（FP）概念`(14-def 汇编) 术语重叠→按 §2 第4档两新词标 pending-merge，新增去重队列第 11 对。踩坑：清理 [[Option 与 Result]]/[[Actor 模型]] 两处悬空链为既有专条、4 条 🎯 逐裁；5 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 769ddc3 docs: 二期拆分[S4]——函数式编程完全指南 (枢纽+4子词条)

## §S4 · 密码学与区块链技术指南（枢纽+2）

枢纽页(1253)+2 子词条 `密码学基础`(对称/非对称/哈希/签名/AES·RSA·ECC·SHA/KMS·HSM/TLS)、`区块链与比特币`(哈希链/PoW-PoS/P2P/UTXO/SegWit)。密码学基础与 s5 pending 的 security/密码学基础篇·加密技术篇·哈希算法篇 跨片重叠→标 pending-merge、新增去重队列第 12 对（归口宜统一 security，待 s5 收敛定夺）；区块链 net-new。踩坑：2 新链悬空(哈希算法与一致性哈希/去中心化身份)改纯文本、2 条 🎯 裁；一处 heredoc 脚本因 ASCII 引号语法错致 split-candidates 首轮未落，改用脚本文件补记。3 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- ade354c docs: 二期拆分[S4]——密码学与区块链 台账补记(split-candidates done + 第12对)

## §S4 · 并发编程模式与实践（枢纽+3）

枢纽页(1321)+3 子词条 `并发与并行及线程模型`/`同步原语与无锁并发`/`消息传递并发：CSP 与 Actor`；线程/协程/Go/Rust 并发双链既有专条；三条与同片 pending 的 `并发编程（CP）概念`(14-def) 重叠→pending-merge、新增去重队列第 13 对。4 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 248bc22 docs: 二期拆分[S4]——并发编程模式与实践 (枢纽+3子词条)

## §S4 · 程序员的数学基础（枢纽+2）

枢纽页(1116)+2 子词条 `离散数学与组合`(集合/逻辑/组合/图论结构)、`线性代数`(向量/矩阵/特征值/SVD)。图论/复杂度/ML 双链既有 done 专条([[图算法大全]][[复杂度分析]][[机器学习基础]])；修掉3处不存在链(大O与离散数学基础/梯度下降与优化算法/2.0,0.0 numpy 误判)。2 篇 net-new 无 pending-merge。3 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 5e7917d docs: 二期拆分[S4]——程序员的数学基础 (枢纽+2子词条)

## §S4 · 编程概念音频课-数据结构（枢纽+2）

枢纽页(1283)+2 net-new 子词条 `数组与链表`/`栈与队列`；哈希/树/图/堆双链 algorithms done 专条([[哈希表]][[二叉搜索树]][[图(数据结构)]][[堆与优先队列]])；修悬空链。3 篇 strict 全 PASS、0 悬空。**（s5 落库后 test_learn 门转 218/0，本提交随即落地）hash 见下：
- fca1354 docs: 二期拆分[S4]——编程概念音频课-数据结构 (枢纽+2子词条)
## §S4 · 编程概念音频课-设计模式（纯收敛 hub，闭环第7对）

枢纽页(1316，比喻速记+双链 8 个 design-patterns 专条)、0 新子词条；此步作为收尾复检：清除指向本汇编的 8 条 pending-merge(单例/工厂/装饰器/适配器/代理/观察者/策略/模板方法)、第7对标 ✅已执行。1 篇 strict PASS、0 悬空。提交 CLEAN。**hash**：

- 276a561 docs: 二期拆分[S4]——编程概念音频课-设计模式 (纯收敛hub，清8条pending-merge)

## §S4 · 编程语言通用概念（枢纽+3族）

枢纽页(1163，11术语归3族)+3 子词条 `变量与数据类型`/`控制流与函数`/`作用域与命名`；类型/闭包双链 done 专条；net-new 无 pending-merge。踩坑：控制流与函数 🎯 151 微超→按行裁。4 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- c042661 docs: 二期拆分[S4]——编程语言通用概念 (枢纽+3族子词条)

## §S4 · 编译原理与解释器实现（枢纽+2，闭环第4对）

枢纽页(1419,流水线总览+实战)+2 net-new 子词条 `语义分析`/`代码生成与LLVM`；词法/语法/AST/IR/优化/JIT/GC 全双链已 done 专条(第4对闭环)。3 篇 strict 首轮全 PASS(清单生效)、0 悬空。提交 CLEAN。**hash**：

- c4a0114 docs: 二期拆分[S4]——编译原理与解释器实现 (枢纽+2子词条)

## §S4 · 计算机科学完整知识图谱（纯收敛 hub，0 新条）

全景 hub(1320)：五大子系统+数学 全双链既有 done/existing 专条，0 新子词条；修1处悬空。1 篇 strict PASS、0 悬空。提交 CLEAN。**hash**：

- 4ff4b46 docs: 二期拆分[S4]——计算机科学完整知识图谱 (纯收敛hub)

## §S4 · 面向对象编程（OOP）概念（枢纽+3族）

枢纽页(1168,13术语归3族)+3 族子词条 `类与对象`/`封装与继承`/`多态与抽象`；泛型/设计原则双链既有专条；修2处悬空链(SOLID/开闭→设计原则)、多态🎯152→按行裁。net-new 无 pending-merge。4 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 4d16df7 docs: 二期拆分[S4]——面向对象编程（OOP）概念 (枢纽+3族子词条)

## §S4 · React Native移动应用开发（枢纽+4子词条）

枢纽页(1859，四层地图+子词条索引表)+4 net-new 子词条 `React Native 新架构与原生桥接`(JSI/Fabric/TurboModules/Codegen/原生模块)/`React Native 组件与布局`(Flexbox默认column/SafeAreaView/FlatList)/`React Native 导航与状态管理`(React Navigation嵌套深链/Zustand/Jotai)/`React Native 网络与数据缓存`(拦截器/TanStack Query staleTime·gcTime/MMKV)；原计划6层，实际收敛为4篇(原生桥接并入新架构、导航与状态合1篇)，见 split-candidates 行注。枢纽双链 [[React深入]][[TypeScript深入]][[Flutter跨平台开发实战]]。踩坑：枢纽首稿误按纯收敛页写→补全 §2 骨架(def/2误区/🎯)；修2处悬空链(RN组件布局→React Native 组件与布局)；枢纽🎯152·组件181·导航169·网络158 逐行裁至≤150。5 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 2d77163 docs: 二期拆分[S4]——React Native移动应用开发 (枢纽+4子词条)

## §S4 · Rust Web开发实战（枢纽+5子词条）

枢纽页(1798，五块技术栈索引表+框架选型 Actix/Axum/Rocket)+5 net-new 子词条 `Axum 路由与中间件`(类型安全 Router/extractor·tower layer·with_state·IntoResponse)/`Rust Web 数据库集成`(SQLx 编译期校验·Diesel·SeaORM·池·事务·migrate)/`serde 序列化与反序列化`(derive 解耦·rename/skip/default/with·Json<T>)/`Rust Web 认证与授权`(JWT 签验+Bearer 中间件·OAuth2 授权码+CSRF state)/`tokio 异步运行时实战`(工作窃取·spawn_blocking·信号量·通道)；原计划6块、框架选型入枢纽故落5子词条。语言层双链 done 的 [[Rust编程基础]][[Rust 错误处理]][[Rust 并发与异步]]，避免与系统层重复承载。踩坑：认证页误链[[API 鉴权与授权（…）]]→改[[API 错误处理规范]]；4 条🎯(Axum175/serde168/认证156/tokio188，英文标识符计入致估长)逐行裁至≤150。6 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- b4055af docs: 二期拆分[S4]——Rust Web开发实战 (枢纽+5子词条)

## §S4 · 函数式编程（FP）概念（收敛枢纽+1子词条 · 闭环去重第11对）

原 14-def 概念汇编收敛为枢纽页(1616)：纯函数/副作用/不可变/高阶/柯里化/组合/闭包/Functor/Applicative/Monad/错误处理 等 12 概念**已在既有专条承载**，故删除重复、改双链指向 [[函数式编程基础]][[Functor 与 Monad]][[函数式错误处理与不可变数据结构]][[闭包]]；仅 声明式vs命令式 + 惰性求值 两概念汇编独家、无归口 → net-new 1 子词条 `声明式风格与惰性求值`(1538)。枢纽核心机制为"概念→专条"归属表(6 行)。闭环：清掉 [[函数式编程基础]][[Functor 与 Monad]] 两行 pending-merge，去重队列第 11 对标 ✅已执行，`grep pending-merge:.*函数式编程（Functional` 复检为空。踩坑：新条 source 字段误填成 source_path→改回 "baike"；误链[[高阶函数与 Lambda]](不存在)→改[[闭包]]；2 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- fcb844b docs: 二期拆分[S4]——函数式编程（FP）概念 (收敛枢纽+1子词条，闭环去重第11对)

## §S4 · 并发编程（CP）概念（收敛枢纽+2子词条 · 闭环去重第13对）

原 14-def 概念汇编收敛为枢纽页(1650)：并发vs并行/线程vs进程/锁·读写锁·信号量·条件变量·原子·CAS·死锁·协程·消息传递 等 11 概念**已在既有专条承载**，改双链归口 [[并发与并行及线程模型]][[同步原语与无锁并发]][[消息传递并发：CSP 与 Actor]][[死锁]][[协程]]；汇编独家、无归口的 线程池 与 Future·Promise·事件循环 → net-new 2 子词条 `线程池`(1582，复用worker+队列/容量参数·拒绝策略/大小选型) + `异步结果与事件循环`(1804，Future vs Promise/链式组合/事件循环协作调度·禁阻塞红线)。闭环：清 [[并发与并行及线程模型]][[同步原语与无锁并发]][[消息传递并发：CSP 与 Actor]] 三行 pending-merge、并发编程模式与实践 hub 与去重队列第 13 对标 ✅已执行，`grep pending-merge:.*并发编程（Concurrent` 复检为空。踩坑：异步结果 leaf 🎯151→删 run_in_executor 括注过线。3 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 1a2c4bd docs: 二期拆分[S4]——并发编程（CP）概念 (收敛枢纽+2子词条，闭环去重第13对)

## §S4 · 01-开发流程（收敛枢纽+1子词条 · 闭环去重第8对之01侧）

原 13-def 术语汇编收敛为枢纽页(1513)：敏捷/Scrum/Kanban/Sprint/站会/回顾/用户故事/验收标准/故事点/计划扑克/产品待办/冲刺待办 等 12 术语**已在 developer-skills 承载**，改双链归口 [[敏捷宣言与原则]][[Scrum框架]][[看板方法]][[用户故事与敏捷估算]][[需求梳理与优先级]][[迭代与回顾]]；仅 瀑布模型 为软件工程侧独家、另立 1 net-new 子词条 `瀑布模型`(1374，线性阶段/Stage-Gate/变更控制/与增量·螺旋·敏捷对比)。核心机制为"术语→专条"归属表(7 行)。闭环：清 developer-skills 六行 pending-merge、去重队列第 8 对 01 侧标 ✅已执行(05 侧仍 pending、拆 05 时同双链看板/需求专条)，`grep pending-merge: software-engineering/01-开发流程` 复检为空。2 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- acff229 docs: 二期拆分[S4]——01-开发流程 (收敛枢纽+瀑布模型，闭环去重第8对之01侧)

## §S4 · 02-版本控制（纯收敛枢纽页，0 新条）

原 14-def 汇编收敛为纯索引枢纽(1735)：三区模型/add·commit·push·pull·fetch/分支·merge·rebase·冲突/cherry·stash·.gitignore/分支策略 全双链 [[版本控制与Git深入]]，Hooks·rebase-i 归 [[Git高级用法]]，PR·MR·CodeReview 归 [[代码评审]]——无一条未被既有 done 专条承载、故 0 net-new（避免造薄词条）。核心机制为"术语→专条"归属表(6 行)。踩坑：🎯152→去"暂存区→仓库"冗余括注+缩"择规模"两步裁至≤150。1 篇 strict PASS、0 悬空。提交 CLEAN。**hash**：

- 6d9e45f docs: 二期拆分[S4]——02-版本控制 (纯收敛枢纽页，0新条)

## §S4 · 05-项目管理（枢纽+5子词条 · 闭环去重第8对之05侧）

枢纽页(1587，四组主线:进度/目标/质量/协作 + 术语归属表)+5 net-new 子词条 `燃尽图与燃起图`(剩余↓vs完成↑·范围蔓延暴露)/`OKR与KPI`(目标对齐vs绩效水位·古德哈特防刷)/`里程碑与发布计划`(阶段检查点·release train·发布≠部署)/`缺陷生命周期与风险管理`(Bug状态机·Severity vs Priority·风险四应对)/`干系人管理与RACI`(权力×利益分级·唯一A·C双向I单向)。看板/需求管理 改双链归口 [[看板方法]][[需求梳理与优先级]]→**闭环去重第8对(01+05 两侧齐、整对 ✅)**；Jira 作工具速览不立条避免薄词条。踩坑：缺陷 leaf 🎯210→大幅精简状态名与括注两步裁至≤150。6 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 14e601a docs: 二期拆分[S4]——05-项目管理 (枢纽+5子词条，闭环去重第8对)

## §S4 · 01-测试基础（枢纽+5子词条）

枢纽页(1575，"概念→专条"归属表 9 行)+5 net-new 子词条 `测试金字塔与覆盖率`(三层70/20/10+语句·分支覆盖·高覆盖≠高质量)/`冒烟测试与回归测试`(构建后准入小集 vs 改动后全量重放)/`验收测试与探索性测试`(UAT 业务符合度 vs charter 时间盒挖隐藏 bug)/`断言与测试替身`(判对错/Stub·Spy·Mock·Fake·Dummy·state vs interaction·忌过度mock)/`BDD 与契约测试`(Gherkin 活文档 + Pact 消费者驱动·只验形状不验业务)；单元/集成/E2E/TDD 四概念改双链归口既有专条、**清 E2E 测试行的 pending-merge**(01 的 E2E 节已删除)。踩坑：BDD 页误链[[微服务架构设计]]→改[[微服务架构设计与实践]]；断言页 H2 手滑写成"## 面试速答>"→修回；断言🎯183·BDD🎯166→精简裁至≤150。6 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 6d3ee72 docs: 二期拆分[S4]——01-测试基础 (枢纽+5子词条)

## §S4 · 02-测试工具（枢纽+3子词条 · 清 Playwright/Cypress pending-merge）

工具选型枢纽(1745，"工具→用途→归口"表)+3 net-new 子词条 `单元测试框架`(pytest·JUnit5·Jest·Mocha+Chai/发现·断言·fixture·参数化·mock·CI)/`Postman 与接口测试`(Collection·Tests脚本·Environment·Runner+Newman CI·只验接口形状)/`测试数据与环境管理`(夹具·工厂·种子·隔离重置脱敏·本地/CI/临时容器/类生产·治 flaky 地基)；浏览器工具(Selenium/Cypress/Playwright)归口 [[Playwright 与 Cypress]][[E2E 测试]]、JMeter 归口 [[性能测试]]、Mockito/Mock.js 归口 [[断言与测试替身]]——均双链不重复。**清 [[Playwright 与 Cypress]] 行 pending-merge**(02 三节已删)。踩坑：4 条🎯(198/179/183/162)全需精简；提交首跑 pre-commit 崩在 OpenBLAS 内存分配失败(RAG 模型加载 OOM、非代码失败)，**未 --no-verify**、文件仍暂存，原样重试一次即全绿落库。6 篇 strict 全 PASS、0 悬空。提交 CLEAN。**hash**：

- 55c68cb docs: 二期拆分[S4]——02-测试工具 (枢纽+3子词条，清 Playwright/Cypress pending-merge)

## §S4 · Python全栈开发教程（纯收敛枢纽，0 新子词条）

各技术层均已存在 done 专条（[[Web框架对比]] 含 FastAPI/SQLAlchemy、[[PostgreSQL高级特性]]、[[React深入]]、[[Python高级特性]]、API 系列），按 §8.2 全部改双链、不新建；本页收敛为全栈接线枢纽。**hash**：

- 93646c3 docs: 二期拆分[S4]——Python全栈开发教程 (纯收敛枢纽，0 新子词条)

