# BACKLOG · 待办与待决策（2026-09-18 建立）

> 规则：事项完成即删除条目；本文件是 docs/ 唯一保留的"活文档"（另有 ADR 架构决策记录）。

## 待用户操作 / 拍板

- [ ] 抽读三篇补齐后的题库 md（llm 第二/第三部分、架构设计），内容经双轮核对，最终确认权在用户。
- [ ] 启用每日自动备份：用户在场时按 `scripts/daily_backup.ps1` 注释里的 `schtasks /Create` 注册计划任务（AGENTS 约定 push 需用户在场）。

## 工具愿望清单（低优先，装了才生效）

- [ ] ImageMagick（`winget install ImageMagick`）——改动前后截图像素 diff，视觉回归。
- [ ] resvg / rsvg-convert——SVG 图标单独光栅化成 PNG 自检。
- [ ] ffmpeg——音视频处理（当前环境未装，HyperFrames 视频链路也因此不可用）。
- [ ] jq / pandoc——API JSON 查看 / 文档互转。
- [ ] Skill: superpowers-writing-plans——"设计→计划→实现"闭环（曾试调未装）。

## 已完成（留档一次，下轮清理删除）

- ~~标签合并「AI → AI资产」~~：2026-09-18 复核确认已生效（全库已无 AI 标签，AI资产 10 篇）。
