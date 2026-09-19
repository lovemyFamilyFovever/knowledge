---
title: "Playwright 与 Cypress"
tags: [测试与质量, E2E工具, 自动化测试]
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Playwright 与 Cypress

> 📌 **导航**：本文是 **Playwright 与 Cypress** 词条，属于 testing 术语集。相关枢纽：[[02 - 测试工具]]、[[E2E 测试]]、[[软件测试完全指南]]。

## 定义

**一句话定义：** Playwright 与 Cypress 是当前主流的两个前端 E2E 自动化测试框架，都以"自动等待"取代显式 sleep 来治异步时序导致的假失败；Playwright 由微软维护、经 CDP 等协议跨 Chromium/Firefox/WebKit 驱动浏览器，Cypress 则把运行器注入浏览器内、与被测应用同域执行。

**通俗类比：** Selenium 像隔着玻璃用遥控器指挥机器人点屏幕，你得自己等它动作做完；这两者像坐在浏览器里替你点，元素没准备好就自己等着。

## 为什么需要它

Selenium 时代 E2E 最大的痛是"时序"：命令与页面渲染异步赛跑，于是满屏 `sleep`，测试既慢又随机红，团队对红灯脱敏、资产随之腐烂。两者把等待内建进每次定位与断言——操作前自动等元素可见可点、断言轮询到超时——从根上削掉一大类假失败，并内建截图、录像、trace 与并行。

## 核心能力

- **定位**：Playwright 用 `page.locator()` 配 `data-testid`，内置可操作性检查；Cypress 用 `cy.get()` 链式命令，自带重试。
- **浏览器矩阵**：Playwright 原生覆盖 Chromium / Firefox / WebKit（含移动端模拟）；Cypress 长期以 Chromium 系为主。
- **并行**：Playwright 靠 `fullyParallel` + `workers`；Cypress 靠分片，历史上依赖付费 Dashboard 做负载均衡。
- **失败自证**：Playwright 的 `trace` 产出可回放时间线（DOM 快照 + 网络 + 控制台）；Cypress 主打"时间旅行"调试与失败录像。
- **组件测试与会话**：Cypress 内建 component testing、`cy.session()` 缓存登录态；Playwright 用 `webServer` 起被测应用、`storageState` 复用登录态。

## 具体示例

选型对比（「速度」一行由架构决定，不单列）：

| 特性 | Selenium | Cypress | Playwright |
|------|----------|---------|------------|
| 架构 | WebDriver 协议 | 浏览器内运行 | CDP 协议 |
| 等待机制 | 手动等待 | 自动等待 | 自动等待 |
| 调试体验 | 一般 | 时间旅行 | Trace Viewer |
| 多浏览器 | 支持 | 以 Chromium 为主 | Chromium/Firefox/WebKit |
| 并行测试 | 需第三方 | 内置 | 内置 |
| 多标签/多域 | 支持 | 受限 | 支持 |
| 语言绑定 | 多语言 | JS/TS | JS/TS/Python/Java/.NET |

一次典型配置即能力清单：`retries: process.env.CI ? 2 : 0` 让重试只发生在 CI、本地失败立刻暴露；`trace: 'on-first-retry'` 配 `screenshot: 'only-on-failure'` 让失败可回溯又不拖慢绿跑；`projects` 列出 chromium / firefox / webkit 即得三内核矩阵；`webServer` 给出 `command` 与 `url` 后框架自动拉起并等待被测应用就绪。

## 何时用与何时不用

- **用 Playwright**：要跨三内核或移动端模拟、多标签/多域流程、多语言栈（Python/Java/.NET），或要 trace 归档做失败回溯。
- **用 Cypress**：纯 JS/TS 前端团队、要最低上手成本与最好的交互式调试、需要组件测试且应用是单域 SPA。
- **都不用**：只测接口选 API 层工具（Postman/Newman、pytest + httpx）；只测性能选 [[性能测试]] 里的 JMeter/k6；拿 E2E 框架铺逻辑覆盖率是杀鸡用牛刀。

## 优劣与代价

✅ 自动等待大幅降低假失败率，E2E 结果重新可信；内建 trace/录像/截图/并行，失败可自证、CI 跑得动。
⚠️ 仍然慢、仍然脆：自动等待治的是时序，治不了测试数据污染与环境漂移。
⚠️ Cypress 跑在被测页面同一运行时，跨域与多标签受限。
⚠️ 引入即多一层基础设施成本（浏览器二进制、CI 镜像、flaky 治理），小项目未必划算。

## 与相关概念的区别

- **vs 单元测试框架**：Jest/pytest 测代码单元、毫秒级、不打桩就出不去；这两者测整条用户流、秒级、必须起真实浏览器。与 Selenium 的边界见上方选型对比表。
- **`data-testid` vs CSS 选择器**：前者是为测试预留的稳定契约，后者随样式重构而变——E2E 维护成本的大头就在这条选择上。

## 常见误区

- 换了 Playwright 或 Cypress，E2E 就不会再假失败了。
- Cypress 支持所有浏览器，所以跨浏览器兼容测试交给它就够了。
- E2E 用例越多越好，最好每个页面每个按钮都覆盖一遍。

## 面试速答

> 🎯 两者都以自动等待取代 sleep 治 E2E 假失败。Playwright 走 CDP、跨三内核、多语言绑定、trace 可回放；Cypress 运行器注入浏览器内、与被测应用同域、时间旅行调试，但跨域多标签受限。按浏览器矩阵与语言栈选型。
> 🔍 追问：Cypress 为什么在多标签/跨域场景吃力？
> 🔍 追问：自动等待能解决 flaky 的全部成因吗？

## 相关术语

[[E2E 测试]]、[[单元测试]]、[[集成测试]]、[[性能测试]]、[[02 - 测试工具]]

## 参考资料

建议人工核验：选型对比表沿用本库 [[02 - 测试工具]] 的 E2E 工具对比并补「多标签/多域」「语言绑定」两行；具体能力与配置项请以 Playwright（playwright.dev）与 Cypress（docs.cypress.io）官方文档当前版本为准。
