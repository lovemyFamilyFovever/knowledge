---
title: "Shell脚本编程"
tags: []
source: "baike"
source_path: "开发术语 / 操作系统与Linux"
collected: "2026-09-05"
status: "imported"
---

# Shell脚本编程

## 基础语法

```bash
#!/bin/bash

# 变量
name="world"
echo "Hello, $name"

# 条件
if [ -f "$file" ]; then
    echo "文件存在"
elif [ -d "$file" ]; then
    echo "是目录"
else
    echo "不存在"
fi

# 循环
for i in {1..10}; do
    echo $i
done

while read line; do
    echo "$line"
done < file.txt
```

## 常用工具

```bash
# 文本处理
grep -r "pattern" .           # 搜索
sed 's/old/new/g' file        # 替换
awk '{print $1, $3}' file     # 列提取
cut -d',' -f1,3 file          # 分割提取

# 管道组合
cat access.log | grep "404" | awk '{print $1}' | sort | uniq -c | sort -rn | head 10
```

## 实用脚本

```bash
# 批量重命名
for f in *.jpg; do
    mv "$f" "${f%.jpg}.png"
done

# 监控磁盘
df -h | awk '$5 > 80 {print "警告: " $6 " 使用率 " $5}'
```
