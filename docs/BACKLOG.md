# BACKLOG · 待办与待决策（2026-09-18 建立）

> 规则：事项完成即删除条目；本文件是 docs/ 唯一保留的"活文档"（另有 ADR 架构决策记录）。

## 工具审查定案（2026-09-18 用户拍板）

- ✅ ImageMagick：2026-09-18 已装（官方源 7.1.2-31），配套 `scripts/agent/imgdiff.mjs` + AGENTS「UI 回归纪律」接线。
- ✅ writing-plans skill：2026-09-18 已装（obra/superpowers，MIT，落到 `~/.box-agent/skills/writing-plans/`）。
- ❌ resvg / jq / pandoc：审查否决，不再考虑（Python/沙箱与 shot.mjs 已覆盖；pandoc 等导出需求出现时再议）。
- ⏸ ffmpeg：未装。有视频需求（HyperFrames 链路）时再装。

## 已完成（留档一次，下轮清理删除）

- ~~标签合并「AI → AI资产」~~：2026-09-18 复核确认已生效（全库已无 AI 标签，AI资产 10 篇）。
