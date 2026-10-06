# baike 批量重写分片清单（5 片）

生成方式：扫描 `content/baike/*/`（排除 `_` 前缀目录与已落地试点），按主题相近聚合。
判据：每片 75–95 篇。执行规范见 `docs/writing-spec-v1.0.md`，交付门 `scripts/agent/check_rewrite.py`。

- baike 子域：28 个；词条总数 430 篇，其中待重写 421 篇
- 已落地试点（不再重做）：9 篇

## 一、分片汇总

| 片 | 主题 | 篇数 | 子域 |
|---|---|---|---|
| s1 | AI 线 | 89 | `ai-and-llm`、`machine-learning` |
| s2 | 系统线 | 81 | `distributed`、`os`、`network`、`hardware` |
| s3 | 数据线 | 79 | `database`、`data-science`、`algorithms`、`middleware` |
| s4 | 工程线 | 79 | `programming-languages`、`devops`、`software-engineering`、`testing`、`tools`、`developer-skills`、`design-patterns` |
| s5 | Web 与其余 | 93 | `security`、`architecture`、`frontend-concepts`、`frontend-frameworks`、`graphics-multimedia`、`hci`、`cs-basics`、`blockchain`、`iot`、`mobile`、`web-backend` |
| | **合计** | **421** | |

## 二、排除清单（已落地试点，禁止重复改写）

- `content/baike/ai-and-llm/Agent 架构模式详解.md`
- `content/baike/data-science/推荐系统.md`
- `content/baike/frontend-frameworks/CSS渲染性能.md`
- `content/baike/frontend-frameworks/Core Web Vitals.md`
- `content/baike/frontend-frameworks/JS执行性能.md`
- `content/baike/frontend-frameworks/Web性能优化.md`
- `content/baike/frontend-frameworks/图片优化.md`
- `content/baike/frontend-frameworks/字体优化.md`
- `content/baike/frontend-frameworks/资源加载优化.md`

## 三、逐片工作清单

### s1｜AI 线（89 篇）

| 子域 | 相对路径 | 篇数 |
|---|---|---|
| ai-and-llm | `content/baike/ai-and-llm/` | 54 |
| machine-learning | `content/baike/machine-learning/` | 35 |

<details><summary>展开文件清单</summary>

**`content/baike/ai-and-llm/`**

- `content/baike/ai-and-llm/AI Agent 开发最佳实践.md`
- `content/baike/ai-and-llm/AI Agent 概述与核心架构.md`
- `content/baike/ai-and-llm/AI 应用详解.md`
- `content/baike/ai-and-llm/Agent 安全与对齐.md`
- `content/baike/ai-and-llm/Agent 编排框架对比.md`
- `content/baike/ai-and-llm/Agent 规划与推理.md`
- `content/baike/ai-and-llm/Agent 记忆系统.md`
- `content/baike/ai-and-llm/Agent 评估与基准.md`
- `content/baike/ai-and-llm/AutoGPT 与自主 Agent.md`
- `content/baike/ai-and-llm/BERT模型详解.md`
- `content/baike/ai-and-llm/Code Agent.md`
- `content/baike/ai-and-llm/Computer Use Agent.md`
- `content/baike/ai-and-llm/CrewAI 多 Agent 框架.md`
- `content/baike/ai-and-llm/Diffusion扩散模型.md`
- `content/baike/ai-and-llm/Embedding 技术详解.md`
- `content/baike/ai-and-llm/Function Calling 与 Tool Use.md`
- `content/baike/ai-and-llm/GPT系列模型演进.md`
- `content/baike/ai-and-llm/LLM 微调技术.md`
- `content/baike/ai-and-llm/LLM 推理优化.md`
- `content/baike/ai-and-llm/LangChain 框架全解析.md`
- `content/baike/ai-and-llm/LlamaIndex 框架指南.md`
- `content/baike/ai-and-llm/MCP（Model Context Protocol）.md`
- `content/baike/ai-and-llm/MoE 混合专家模型.md`
- `content/baike/ai-and-llm/NeRF与3D生成.md`
- `content/baike/ai-and-llm/Prompt Engineering 高级技巧.md`
- `content/baike/ai-and-llm/Prompt 工程与 Agent 详解.md`
- `content/baike/ai-and-llm/RAG 与检索技术详解.md`
- `content/baike/ai-and-llm/RAG 检索增强生成.md`
- `content/baike/ai-and-llm/Research Agent.md`
- `content/baike/ai-and-llm/Scaling Law.md`
- `content/baike/ai-and-llm/Tokenizer 技术.md`
- `content/baike/ai-and-llm/Transformer架构深度解析.md`
- `content/baike/ai-and-llm/Web Agent.md`
- `content/baike/ai-and-llm/Workflow Agent.md`
- `content/baike/ai-and-llm/向量数据库技术.md`
- `content/baike/ai-and-llm/图神经网络.md`
- `content/baike/ai-and-llm/多 Agent 协作系统.md`
- `content/baike/ai-and-llm/多模态 Agent.md`
- `content/baike/ai-and-llm/多模态大模型.md`
- `content/baike/ai-and-llm/大模型基础术语详解.md`
- `content/baike/ai-and-llm/大模型预训练技术.md`
- `content/baike/ai-and-llm/大语言模型架构演进.md`
- `content/baike/ai-and-llm/小模型与端侧 Agent.md`
- `content/baike/ai-and-llm/强化学习基础.md`
- `content/baike/ai-and-llm/微调与训练技术详解.md`
- `content/baike/ai-and-llm/机器学习基础.md`
- `content/baike/ai-and-llm/注意力机制.md`
- `content/baike/ai-and-llm/深度强化学习.md`
- `content/baike/ai-and-llm/知识图谱与 LLM 结合.md`
- `content/baike/ai-and-llm/联邦学习.md`
- `content/baike/ai-and-llm/词向量.md`
- `content/baike/ai-and-llm/词袋模型.md`
- `content/baike/ai-and-llm/语音AI技术.md`
- `content/baike/ai-and-llm/长上下文技术.md`

**`content/baike/machine-learning/`**

- `content/baike/machine-learning/2026年AI技术全景图.md`
- `content/baike/machine-learning/AI是否会取代人类辩论.md`
- `content/baike/machine-learning/Dropout.md`
- `content/baike/machine-learning/K均值聚类.md`
- `content/baike/machine-learning/K近邻算法.md`
- `content/baike/machine-learning/LLM应用开发完全指南.md`
- `content/baike/machine-learning/MLOps机器学习工程化.md`
- `content/baike/machine-learning/Prompt Engineering高级指南.md`
- `content/baike/machine-learning/RAG系统工程化实践.md`
- `content/baike/machine-learning/《AI时代生存指南》第一章.md`
- `content/baike/machine-learning/《AI时代生存指南》第三章.md`
- `content/baike/machine-learning/《AI时代生存指南》第二章.md`
- `content/baike/machine-learning/主成分分析.md`
- `content/baike/machine-learning/交叉验证.md`
- `content/baike/machine-learning/决策树.md`
- `content/baike/machine-learning/反向传播.md`
- `content/baike/machine-learning/强化学习从入门到实践.md`
- `content/baike/machine-learning/批归一化.md`
- `content/baike/machine-learning/损失函数.md`
- `content/baike/machine-learning/支持向量机.md`
- `content/baike/machine-learning/朴素贝叶斯.md`
- `content/baike/machine-learning/梯度下降.md`
- `content/baike/machine-learning/梯度提升树.md`
- `content/baike/machine-learning/梯度消失与梯度爆炸.md`
- `content/baike/machine-learning/深度学习从零到精通.md`
- `content/baike/machine-learning/混淆矩阵.md`
- `content/baike/machine-learning/激活函数.md`
- `content/baike/machine-learning/特征缩放.md`
- `content/baike/machine-learning/自然语言处理NLP完全指南.md`
- `content/baike/machine-learning/计算机视觉入门到实战.md`
- `content/baike/machine-learning/迁移学习.md`
- `content/baike/machine-learning/过拟合与正则化.md`
- `content/baike/machine-learning/逻辑回归.md`
- `content/baike/machine-learning/随机森林.md`
- `content/baike/machine-learning/集成学习.md`

</details>

### s2｜系统线（81 篇）

| 子域 | 相对路径 | 篇数 |
|---|---|---|
| distributed | `content/baike/distributed/` | 23 |
| os | `content/baike/os/` | 21 |
| network | `content/baike/network/` | 22 |
| hardware | `content/baike/hardware/` | 15 |

<details><summary>展开文件清单</summary>

**`content/baike/distributed/`**

- `content/baike/distributed/BASE 理论.md`
- `content/baike/distributed/CAP 定理.md`
- `content/baike/distributed/MapReduce.md`
- `content/baike/distributed/Saga 与 TCC.md`
- `content/baike/distributed/一致性哈希.md`
- `content/baike/distributed/一致性算法.md`
- `content/baike/distributed/分布式 ID.md`
- `content/baike/distributed/分布式ID与缓存术语百科.md`
- `content/baike/distributed/分布式事务.md`
- `content/baike/distributed/分布式基础术语百科.md`
- `content/baike/distributed/分布式存储术语百科.md`
- `content/baike/distributed/分布式缓存.md`
- `content/baike/distributed/分布式锁.md`
- `content/baike/distributed/幂等性.md`
- `content/baike/distributed/异地多活.md`
- `content/baike/distributed/微服务治理术语百科.md`
- `content/baike/distributed/心跳检测.md`
- `content/baike/distributed/最终一致性.md`
- `content/baike/distributed/服务发现.md`
- `content/baike/distributed/服务网格.md`
- `content/baike/distributed/熔断与降级.md`
- `content/baike/distributed/负载均衡.md`
- `content/baike/distributed/限流.md`

**`content/baike/os/`**

- `content/baike/os/Linux 命令速查手册.md`
- `content/baike/os/Shell 脚本详解.md`
- `content/baike/os/Shell脚本编程.md`
- `content/baike/os/上下文切换.md`
- `content/baike/os/中断.md`
- `content/baike/os/信号量与互斥锁.md`
- `content/baike/os/实时操作系统.md`
- `content/baike/os/容器运行时.md`
- `content/baike/os/操作系统基础术语.md`
- `content/baike/os/操作系统核心.md`
- `content/baike/os/文件系统.md`
- `content/baike/os/死锁.md`
- `content/baike/os/用户态与内核态.md`
- `content/baike/os/系统调用.md`
- `content/baike/os/线程.md`
- `content/baike/os/虚拟内存.md`
- `content/baike/os/进程管理详解.md`
- `content/baike/os/进程调度.md`
- `content/baike/os/进程间通信.md`
- `content/baike/os/银行家算法.md`
- `content/baike/os/页面置换算法.md`

**`content/baike/network/`**

- `content/baike/network/DNS深入解析.md`
- `content/baike/network/HTTP 状态码.md`
- `content/baike/network/HTTPS 与 TLS.md`
- `content/baike/network/HTTP协议.md`
- `content/baike/network/IP 协议.md`
- `content/baike/network/OSI 参考模型.md`
- `content/baike/network/QUIC.md`
- `content/baike/network/TCP深入.md`
- `content/baike/network/WebSocket.md`
- `content/baike/network/三次握手与四次挥手.md`
- `content/baike/network/内容分发网络.md`
- `content/baike/network/动态主机配置协议.md`
- `content/baike/network/地址解析协议.md`
- `content/baike/network/应用层协议.md`
- `content/baike/network/拥塞控制.md`
- `content/baike/network/滑动窗口.md`
- `content/baike/network/用户数据报协议.md`
- `content/baike/network/组播与广播.md`
- `content/baike/network/网络地址转换.md`
- `content/baike/network/网络基础.md`
- `content/baike/network/网络安全协议.md`
- `content/baike/network/路由协议.md`

**`content/baike/hardware/`**

- `content/baike/hardware/CPU 缓存.md`
- `content/baike/hardware/CPU与处理器架构.md`
- `content/baike/hardware/RAID 磁盘阵列.md`
- `content/baike/hardware/主板与总线.md`
- `content/baike/hardware/内存与存储系统.md`
- `content/baike/hardware/内存屏障.md`
- `content/baike/hardware/冯·诺依曼结构.md`
- `content/baike/hardware/分支预测.md`
- `content/baike/hardware/指令流水线.md`
- `content/baike/hardware/指令集架构.md`
- `content/baike/hardware/显卡与GPU.md`
- `content/baike/hardware/直接内存访问.md`
- `content/baike/hardware/缓存一致性.md`
- `content/baike/hardware/超标量与乱序执行.md`
- `content/baike/hardware/输入输出与外设.md`

</details>

### s3｜数据线（79 篇）

| 子域 | 相对路径 | 篇数 |
|---|---|---|
| database | `content/baike/database/` | 23 |
| data-science | `content/baike/data-science/` | 19 |
| algorithms | `content/baike/algorithms/` | 27 |
| middleware | `content/baike/middleware/` | 10 |

<details><summary>展开文件清单</summary>

**`content/baike/database/`**

- `content/baike/database/B+树.md`
- `content/baike/database/ElasticSearch搜索.md`
- `content/baike/database/LSM 树.md`
- `content/baike/database/MongoDB实践.md`
- `content/baike/database/MySQL从入门到架构师.md`
- `content/baike/database/MySQL深入.md`
- `content/baike/database/NoSQL 数据库术语.md`
- `content/baike/database/PostgreSQL高级特性.md`
- `content/baike/database/Redis深入.md`
- `content/baike/database/Redis深度解析与实战指南.md`
- `content/baike/database/SQL 基础术语.md`
- `content/baike/database/事务与并发控制术语.md`
- `content/baike/database/事务隔离级别.md`
- `content/baike/database/分库分表.md`
- `content/baike/database/多版本并发控制.md`
- `content/baike/database/存储过程与触发器.md`
- `content/baike/database/搜索引擎技术详解.md`
- `content/baike/database/数据库内核原理深度解析.md`
- `content/baike/database/数据库范式.md`
- `content/baike/database/数据库设计术语.md`
- `content/baike/database/数据库连接池.md`
- `content/baike/database/索引与查询优化术语.md`
- `content/baike/database/读写分离.md`

**`content/baike/data-science/`**

- `content/baike/data-science/A B测试与实验设计.md`
- `content/baike/data-science/ETL.md`
- `content/baike/data-science/MLOps实践.md`
- `content/baike/data-science/RNN LSTM GRU.md`
- `content/baike/data-science/卷积神经网络(CNN).md`
- `content/baike/data-science/可解释AI(XAI).md`
- `content/baike/data-science/因果推断.md`
- `content/baike/data-science/大数据技术栈.md`
- `content/baike/data-science/数据仓库.md`
- `content/baike/data-science/数据分析与可视化.md`
- `content/baike/data-science/数据分析与可视化实战.md`
- `content/baike/data-science/数据增强技术.md`
- `content/baike/data-science/数据湖.md`
- `content/baike/data-science/时间序列分析.md`
- `content/baike/data-science/模型压缩与部署.md`
- `content/baike/data-science/深度学习基础.md`
- `content/baike/data-science/特征工程进阶.md`
- `content/baike/data-science/生成对抗网络(GAN).md`
- `content/baike/data-science/自监督学习.md`

**`content/baike/algorithms/`**

- `content/baike/algorithms/AVL 树.md`
- `content/baike/algorithms/KMP 算法.md`
- `content/baike/algorithms/二分查找.md`
- `content/baike/algorithms/二叉搜索树.md`
- `content/baike/algorithms/位运算.md`
- `content/baike/algorithms/分治算法.md`
- `content/baike/algorithms/前缀树.md`
- `content/baike/algorithms/动态规划.md`
- `content/baike/algorithms/哈希表.md`
- `content/baike/algorithms/回溯算法.md`
- `content/baike/algorithms/图(数据结构).md`
- `content/baike/algorithms/图算法大全.md`
- `content/baike/algorithms/基础数据结构.md`
- `content/baike/algorithms/堆与优先队列.md`
- `content/baike/algorithms/堆排序.md`
- `content/baike/algorithms/复杂度分析.md`
- `content/baike/algorithms/字符串算法.md`
- `content/baike/algorithms/并查集.md`
- `content/baike/algorithms/拓扑排序.md`
- `content/baike/algorithms/排序与搜索.md`
- `content/baike/algorithms/最小生成树.md`
- `content/baike/algorithms/最短路径算法.md`
- `content/baike/algorithms/算法思想.md`
- `content/baike/algorithms/红黑树.md`
- `content/baike/algorithms/贪心算法.md`
- `content/baike/algorithms/递归.md`
- `content/baike/algorithms/高级数据结构.md`

**`content/baike/middleware/`**

- `content/baike/middleware/ESB 与服务网格（Service Mesh）.md`
- `content/baike/middleware/GraphQL实践.md`
- `content/baike/middleware/Kafka深入.md`
- `content/baike/middleware/RabbitMQ vs Kafka vs Pulsar.md`
- `content/baike/middleware/gRPC深入.md`
- `content/baike/middleware/任务调度（Task Scheduling）.md`
- `content/baike/middleware/死信队列.md`
- `content/baike/middleware/消息投递语义.md`
- `content/baike/middleware/消息队列（Message Queue）.md`
- `content/baike/middleware/消息顺序性.md`

</details>

### s4｜工程线（79 篇）

| 子域 | 相对路径 | 篇数 |
|---|---|---|
| programming-languages | `content/baike/programming-languages/` | 38 |
| devops | `content/baike/devops/` | 13 |
| software-engineering | `content/baike/software-engineering/` | 11 |
| testing | `content/baike/testing/` | 8 |
| tools | `content/baike/tools/` | 4 |
| developer-skills | `content/baike/developer-skills/` | 2 |
| design-patterns | `content/baike/design-patterns/` | 3 |

<details><summary>展开文件清单</summary>

**`content/baike/programming-languages/`**

- `content/baike/programming-languages/Flutter跨平台开发实战.md`
- `content/baike/programming-languages/Go语言核心.md`
- `content/baike/programming-languages/Go语言系统编程指南.md`
- `content/baike/programming-languages/Python全栈开发教程.md`
- `content/baike/programming-languages/Python高级特性.md`
- `content/baike/programming-languages/Python高级编程完全指南.md`
- `content/baike/programming-languages/React Native移动应用开发.md`
- `content/baike/programming-languages/Rust Web开发实战.md`
- `content/baike/programming-languages/Rust系统编程入门到精通.md`
- `content/baike/programming-languages/Rust编程基础.md`
- `content/baike/programming-languages/TypeScript深入.md`
- `content/baike/programming-languages/TypeScript高级编程指南.md`
- `content/baike/programming-languages/中间表示.md`
- `content/baike/programming-languages/内存管理.md`
- `content/baike/programming-languages/函数式编程完全指南.md`
- `content/baike/programming-languages/函数式编程（Functional Programming）概念.md`
- `content/baike/programming-languages/协程.md`
- `content/baike/programming-languages/即时编译.md`
- `content/baike/programming-languages/垃圾回收.md`
- `content/baike/programming-languages/密码学与区块链技术指南.md`
- `content/baike/programming-languages/并发编程模式与实践.md`
- `content/baike/programming-languages/并发编程（Concurrent Programming）概念.md`
- `content/baike/programming-languages/抽象语法树.md`
- `content/baike/programming-languages/泛型.md`
- `content/baike/programming-languages/程序员的数学基础.md`
- `content/baike/programming-languages/类型系统.md`
- `content/baike/programming-languages/编程概念音频课-数据结构.md`
- `content/baike/programming-languages/编程概念音频课-设计模式.md`
- `content/baike/programming-languages/编程语言通用概念.md`
- `content/baike/programming-languages/编译优化.md`
- `content/baike/programming-languages/编译原理与解释器实现.md`
- `content/baike/programming-languages/计算机科学完整知识图谱.md`
- `content/baike/programming-languages/词法分析.md`
- `content/baike/programming-languages/语法分析.md`
- `content/baike/programming-languages/软件测试完全指南.md`
- `content/baike/programming-languages/闭包.md`
- `content/baike/programming-languages/静态链接与动态链接.md`
- `content/baike/programming-languages/面向对象编程（OOP）概念.md`

**`content/baike/devops/`**

- `content/baike/devops/API设计最佳实践.md`
- `content/baike/devops/Docker容器化完全指南.md`
- `content/baike/devops/Kubernetes云原生实战指南.md`
- `content/baike/devops/Kubernetes深入.md`
- `content/baike/devops/Linux系统管理高级指南.md`
- `content/baike/devops/Web安全攻防实战指南.md`
- `content/baike/devops/云服务详解.md`
- `content/baike/devops/基础设施即代码详解.md`
- `content/baike/devops/容器与编排技术详解.md`
- `content/baike/devops/操作系统内核原理.md`
- `content/baike/devops/监控与日志详解.md`
- `content/baike/devops/网络安全与渗透测试.md`
- `content/baike/devops/蓝绿部署与灰度发布.md`

**`content/baike/software-engineering/`**

- `content/baike/software-engineering/01-开发流程.md`
- `content/baike/software-engineering/02-版本控制.md`
- `content/baike/software-engineering/03-代码质量.md`
- `content/baike/software-engineering/04-CI CD.md`
- `content/baike/software-engineering/05-项目管理.md`
- `content/baike/software-engineering/UML.md`
- `content/baike/software-engineering/代码评审.md`
- `content/baike/software-engineering/技术债务.md`
- `content/baike/software-engineering/结对编程.md`
- `content/baike/software-engineering/重构.md`
- `content/baike/software-engineering/需求工程.md`

**`content/baike/testing/`**

- `content/baike/testing/01 - 测试基础.md`
- `content/baike/testing/02 - 测试工具.md`
- `content/baike/testing/03 - 性能测试.md`
- `content/baike/testing/单元测试.md`
- `content/baike/testing/性能测试.md`
- `content/baike/testing/测试驱动开发.md`
- `content/baike/testing/混沌工程.md`
- `content/baike/testing/集成测试.md`

**`content/baike/tools/`**

- `content/baike/tools/包管理器与构建工具.md`
- `content/baike/tools/容器化与Docker.md`
- `content/baike/tools/版本控制与Git深入.md`
- `content/baike/tools/调试与性能分析.md`

**`content/baike/developer-skills/`**

- `content/baike/developer-skills/开发者效率工具大全.md`
- `content/baike/developer-skills/敏捷项目管理实战.md`

**`content/baike/design-patterns/`**

- `content/baike/design-patterns/创建型模式（Creational Patterns）.md`
- `content/baike/design-patterns/结构型模式（Structural Patterns）.md`
- `content/baike/design-patterns/行为型模式（Behavioral Patterns）.md`

</details>

### s5｜Web 与其余（93 篇）

| 子域 | 相对路径 | 篇数 |
|---|---|---|
| security | `content/baike/security/` | 22 |
| architecture | `content/baike/architecture/` | 18 |
| frontend-concepts | `content/baike/frontend-concepts/` | 8 |
| frontend-frameworks | `content/baike/frontend-frameworks/` | 4 |
| graphics-multimedia | `content/baike/graphics-multimedia/` | 12 |
| hci | `content/baike/hci/` | 10 |
| cs-basics | `content/baike/cs-basics/` | 11 |
| blockchain | `content/baike/blockchain/` | 2 |
| iot | `content/baike/iot/` | 2 |
| mobile | `content/baike/mobile/` | 1 |
| web-backend | `content/baike/web-backend/` | 3 |

<details><summary>展开文件清单</summary>

**`content/baike/security/`**

- `content/baike/security/OAuth 与 JWT.md`
- `content/baike/security/SQL注入与XSS.md`
- `content/baike/security/Web安全攻防.md`
- `content/baike/security/中间人攻击.md`
- `content/baike/security/供应链安全.md`
- `content/baike/security/公钥基础设施.md`
- `content/baike/security/分布式拒绝服务攻击.md`
- `content/baike/security/加密技术篇.md`
- `content/baike/security/哈希算法篇.md`
- `content/baike/security/密码学基础篇.md`
- `content/baike/security/密码学实用指南.md`
- `content/baike/security/对称加密与非对称加密.md`
- `content/baike/security/数字签名.md`
- `content/baike/security/数字证书.md`
- `content/baike/security/端到端加密.md`
- `content/baike/security/缓冲区溢出.md`
- `content/baike/security/网络安全篇.md`
- `content/baike/security/认证与授权篇.md`
- `content/baike/security/访问控制.md`
- `content/baike/security/防火墙.md`
- `content/baike/security/零信任安全架构.md`
- `content/baike/security/零知识证明.md`

**`content/baike/architecture/`**

- `content/baike/architecture/API设计.md`
- `content/baike/architecture/DDD领域驱动设计.md`
- `content/baike/architecture/SaaS产品技术架构.md`
- `content/baike/architecture/事件驱动架构.md`
- `content/baike/architecture/云原生与多云架构实战指南.md`
- `content/baike/architecture/分布式系统设计完全指南.md`
- `content/baike/architecture/可观测性工程实战.md`
- `content/baike/architecture/微服务架构.md`
- `content/baike/architecture/微服务架构设计与实践.md`
- `content/baike/architecture/性能优化.md`
- `content/baike/architecture/推荐系统设计与实现.md`
- `content/baike/architecture/数据工程完全指南.md`
- `content/baike/architecture/数据库选型指南.md`
- `content/baike/architecture/架构模式.md`
- `content/baike/architecture/系统设计.md`
- `content/baike/architecture/设计原则.md`
- `content/baike/architecture/领域驱动设计DDD完全指南.md`
- `content/baike/architecture/高并发系统设计.md`

**`content/baike/frontend-concepts/`**

- `content/baike/frontend-concepts/HTML & CSS 核心概念.md`
- `content/baike/frontend-concepts/JavaScript 基础核心概念.md`
- `content/baike/frontend-concepts/React深入.md`
- `content/baike/frontend-concepts/Vue3核心.md`
- `content/baike/frontend-concepts/前端工程化.md`
- `content/baike/frontend-concepts/前端工程化核心概念.md`
- `content/baike/frontend-concepts/前端框架核心概念.md`
- `content/baike/frontend-concepts/响应式设计.md`

**`content/baike/frontend-frameworks/`**

- `content/baike/frontend-frameworks/GraphQL从入门到精通.md`
- `content/baike/frontend-frameworks/Next.js全栈开发实战.md`
- `content/baike/frontend-frameworks/WebAssembly完全指南.md`
- `content/baike/frontend-frameworks/现代前端工程化完全指南.md`

**`content/baike/graphics-multimedia/`**

- `content/baike/graphics-multimedia/光栅化.md`
- `content/baike/graphics-multimedia/光线追踪.md`
- `content/baike/graphics-multimedia/全局光照.md`
- `content/baike/graphics-multimedia/图像压缩.md`
- `content/baike/graphics-multimedia/图形渲染管线.md`
- `content/baike/graphics-multimedia/抗锯齿.md`
- `content/baike/graphics-multimedia/流媒体.md`
- `content/baike/graphics-multimedia/着色器.md`
- `content/baike/graphics-multimedia/纹理映射.md`
- `content/baike/graphics-multimedia/视频编解码器.md`
- `content/baike/graphics-multimedia/颜色空间.md`
- `content/baike/graphics-multimedia/骨骼动画.md`

**`content/baike/hci/`**

- `content/baike/hci/交互设计.md`
- `content/baike/hci/人机交互.md`
- `content/baike/hci/信息架构.md`
- `content/baike/hci/可用性.md`
- `content/baike/hci/可用性测试.md`
- `content/baike/hci/心智模型.md`
- `content/baike/hci/无障碍访问.md`
- `content/baike/hci/用户体验.md`
- `content/baike/hci/认知负荷.md`
- `content/baike/hci/费茨定律.md`

**`content/baike/cs-basics/`**

- `content/baike/cs-basics/P 与 NP.md`
- `content/baike/cs-basics/信息论基础.md`
- `content/baike/cs-basics/图灵机.md`
- `content/baike/cs-basics/布尔逻辑与逻辑门.md`
- `content/baike/cs-basics/形式语言与文法.md`
- `content/baike/cs-basics/数制与编码.md`
- `content/baike/cs-basics/有限状态机.md`
- `content/baike/cs-basics/正则表达式.md`
- `content/baike/cs-basics/离散数学基础.md`
- `content/baike/cs-basics/计算理论.md`
- `content/baike/cs-basics/量子计算.md`

**`content/baike/blockchain/`**

- `content/baike/blockchain/区块链基础.md`
- `content/baike/blockchain/智能合约.md`

**`content/baike/iot/`**

- `content/baike/iot/MQTT.md`
- `content/baike/iot/物联网与嵌入式基础.md`

**`content/baike/mobile/`**

- `content/baike/mobile/移动开发概览.md`

**`content/baike/web-backend/`**

- `content/baike/web-backend/Web框架对比.md`
- `content/baike/web-backend/缓存策略.md`
- `content/baike/web-backend/认证与安全实践.md`

</details>
