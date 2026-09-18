# BACKLOG · 待办与待决策（2026-09-18 由 docs 清理提炼）

> 规则：事项完成即删除条目；本文件只放「尚未做/待用户拍板」的事。

## 待用户拍板 / 操作

- [ ] **标签合并「AI → AI资产」**：`govern_tags.py similar` 报告的真重叠（涉及 9 篇文档写盘），已验证预览可用，留用户复核后执行：
  `python scripts\govern_tags.py merge --src "AI" --dst "AI资产" --apply`
- [ ] 抽读三篇补齐后的题库 md（llm 第二/第三部分、架构设计），最终确认权在用户（handoff-2026091801）。
- [ ] 启用每日自动备份：用户在场时按 `scripts/daily_backup.ps1` 注释里的 `schtasks /Create` 注册计划任务（AGENTS 约定 push 需用户在场）。

## 工具愿望清单（低优先，装了才生效）

- [ ] ImageMagick（`winget install ImageMagick`）——改动前后截图像素 diff，视觉回归。
- [ ] resvg / rsvg-convert——SVG 图标单独光栅化成 PNG 自检。
- [ ] ffmpeg——音视频处理（当前环境未装，HyperFrames 链路也因此不可用）。
- [ ] jq / pandoc——API JSON 查看 / 文档互转。
- [ ] Skill: superpowers-writing-plans——"设计→计划→实现"闭环（曾试调未装）。

## 来源说明

以上提炼自 `docs/工具能力清单.md`、`docs/标签治理与重命名-解决方案.md`、`docs/handoff-2026091801.md`（均已归档或删除，git 历史可查）。
