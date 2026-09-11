---
title: "Shell脚本编程"
tags: [计算机体系结构, 操作系统, Linux, Shell]
source: "baike"
source_path: "开发术语 / 操作系统与Linux"
collected: "2026-09-05"
status: "imported"
---

# Shell脚本编程

## 定义

**一句话定义：** Shell 脚本是把一系列 Shell 命令与流程控制（变量、条件、循环、函数）写入文件、由 Shell 解释执行的自动化脚本，常用于运维、批处理与任务编排。

**通俗类比：** 就像把「每天要重复的一串操作」录成一个宏——写一次，之后一句 `./script.sh` 就能自动跑完，免去反复敲命令。

> 多义说明：本文是 Shell 脚本的**快速入门**；系统而完整的语法、文本三剑客（grep/sed/awk）、调试技巧与脚本模板见 [[Shell 脚本详解]]；常用命令见 [[Linux 命令速查手册]]。

## 快速入门

```bash
#!/bin/bash
# 第一行 shebang 指定解释器；用 set -euo pipefail 让脚本更健壮
set -euo pipefail

# 变量（等号两边不能有空格）
name="world"
echo "Hello, $name"

# 条件判断
if [ -f "$file" ]; then
    echo "文件存在"
elif [ -d "$file" ]; then
    echo "是目录"
else
    echo "不存在"
fi

# 循环
for i in {1..10}; do
    echo "$i"
done

# 逐行读取文件（IFS= 与 -r 避免吞空格/反斜杠转义）
while IFS= read -r line; do
    echo "$line"
done < file.txt
```

## 常用文本工具

```bash
grep -r "pattern" .           # 递归搜索
sed 's/old/new/g' file        # 全局替换
awk '{print $1, $3}' file     # 提取列
cut -d',' -f1,3 file          # 按分隔符取字段

# 管道组合：访问量 Top 10 的 IP
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10
```

## 实用片段

```bash
# 批量改扩展名 .jpg -> .png
for f in *.jpg; do
    mv "$f" "${f%.jpg}.png"
done

# 磁盘使用率超 80% 告警
df -h | awk '$5+0 > 80 {print "警告: " $6 " 使用率 " $5}'
```

> 修正：原示例 `... | head 10` 应为 `head -10`（缺 `-` 会把 `10` 当作文件名）；`df` 的 `$5` 含 `%`，用 `$5+0` 强制数值比较更稳妥。

## 优点与局限

- 优点：无需编译、贴近系统命令、写运维/胶水逻辑极快；几乎所有 Unix/Linux 环境自带。
- 局限：不适合大型复杂程序（弱类型、错误处理繁琐、性能有限）；不同 Shell（bash/sh/zsh/dash）语法有差异，跨平台需谨慎（推荐 `#!/usr/bin/env bash`）。

## 常见误区

- 变量赋值 `=` 两边加空格（`name = "x"`）会被当作命令而报错。
- 未加执行权限（`chmod +x`）或漏写 shebang，导致用错解释器。
- 引用变量不加引号（`$file` 而非 `"$file"`），在含空格/通配符时会出错。

## 相关术语

[[Shell 脚本详解]]、[[Linux 命令速查手册]]、[[进程管理详解]]、[[操作系统核心]]

## 参考资料

建议人工核验：可参考 `bash(1)`/`grep(1)`/`sed(1)`/`awk(1)` man page、GNU Bash 官方手册、Google Shell Style Guide，以及 ShellCheck 静态检查工具。
