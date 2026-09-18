---
title: "Shell脚本编程"
tags: [计算机体系结构, 操作系统, Linux, Shell]
source: "baike"
source_path: "开发术语 / 操作系统与Linux"
collected: "2026-09-05"
status: "imported"
---

# Shell脚本编程


> 📌 **导航**：本文是 **Shell脚本编程** 词条，属于 os 术语集。相关枢纽：[[Shell 脚本详解]]、[[操作系统基础术语]]、[[操作系统核心]]、[[进程管理详解]]。

## 定义

**一句话定义：** Shell 脚本是把一系列 Shell 命令与流程控制（变量、条件、循环、函数）写入文件、由 Shell 解释执行的自动化脚本，常用于运维、批处理与任务编排。

**通俗类比：** 就像把"每天要重复的一串操作"录成一个宏——写一次，之后一句 `./script.sh` 就能自动跑完，免去反复敲命令。

> 多义说明：本文是 Shell 脚本的快速入门；系统完整的语法、文本三剑客与脚本模板见 [[Shell 脚本详解]]，常用命令见 [[Linux 命令速查手册]]。

## 为什么需要它

运维里有大量"重复、多步、要判断"的任务（备份、日志切割、批量改名、健康巡检）。逐个手敲慢且易错，Shell 把命令 + 流程控制固化成脚本，可复用、可定时（cron）、可组合管道，是 Linux 上最快的胶水层。

## 做法

脚本以 shebang 指定解释器、用 `set -euo pipefail` 让出错即停更健壮；变量赋值等号两边不能有空格、引用要加双引号防分词；条件用 `[ ]` / `[[ ]]`，循环 for / while，函数复用逻辑。最小骨架：

```bash
#!/usr/bin/env bash
set -euo pipefail
name="world"
echo "Hello, $name"
if [[ -f "$file" ]]; then
    echo "文件存在"
elif [[ -d "$file" ]]; then
    echo "是目录"
fi
for i in {1..10}; do echo "$i"; done
while IFS= read -r line; do echo "$line"; done < file.txt
```

文本处理靠三剑客组合：`grep -r` 递归搜、`sed 's/old/new/g'` 替换、`awk '{print $1}'` 提列，用管道串起来即可完成统计；变量替换（如 `${f%.jpg}` 去后缀）支撑批量改名等实战。

## 具体示例

统计访问量 Top 10 的 IP：`awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10`——各命令经管道流水作业，比手写循环短得多。

## 何时用与何时不用

- **用：** 运维自动化、批处理、任务编排、把多条命令与流程粘成脚本。
- **不用：** 大型复杂程序（弱类型、错误处理繁琐、性能有限）改用 Python / Go；跨平台要注意 bash / sh / zsh / dash 语法差异。

## 优劣与代价

✅ 无需编译、贴近系统命令、写运维胶水逻辑极快、几乎所有 Unix / Linux 环境自带。
⚠️ 不适合大型复杂逻辑；shell 方言差异使跨平台需谨慎（推荐 `#!/usr/bin/env bash`）。

## 与相关概念的区别

vs [[Linux 命令速查手册]]：那是单条命令的用法索引，本文讲把命令组织成带流程控制的脚本；vs 编程语言：Shell 强在编排现有命令，弱在复杂数据结构与工程化。

## 常见误区

- 变量赋值写成 `name = "x"`（等号两边加了空格）。
- 引用变量不加引号，写成 `$file` 而非 `"$file"`。
- 漏写 shebang 或不加执行权限 `chmod +x`。

## 面试速答

> 🎯 Shell 脚本 = 把命令 + 流程控制（变量 / 条件 / 循环 / 函数）写成文件由解释器跑，`set -euo pipefail` 增健壮、赋值无空格且引用加引号，配 grep/sed/awk 管道做文本处理，最适合运维胶水而非大型程序。
> 🔍 追问：为什么脚本里引用变量要加双引号？
> 🔍 追问：Shell 脚本不适合什么场景？

## 相关术语

[[Shell 脚本详解]]、[[Linux 命令速查手册]]、[[进程管理详解]]、[[操作系统核心]]

## 参考资料

`bash(1)` / `grep(1)` / `sed(1)` / `awk(1)` man page、GNU Bash 官方手册、Google Shell Style Guide、ShellCheck 静态检查工具。
