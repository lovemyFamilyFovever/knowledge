---
title: "Shell 脚本详解"
tags: [计算机体系结构, 操作系统, Linux, Shell]
source: "baike"
source_path: "开发术语 / 操作系统与Linux"
collected: "2026-09-05"
status: "imported"
---

# Shell 脚本详解


> 📌 **导航**：本文是 **Shell 脚本详解** 词条，属于 os 术语集。相关枢纽：[[Shell 脚本详解]]、[[操作系统基础术语]]、[[操作系统核心]]、[[进程管理详解]]。

## 概述

**一句话定义：** 本文系统梳理 Bash Shell 脚本编程的语法与实战要点——变量、条件、循环、函数、数组、字符串操作、正则、管道与重定向、awk/sed 进阶、调试技巧与可复用脚本模板。

> 多义说明：本文是 Shell 脚本的**完整参考**；快速入门见 [[Shell脚本编程]]，常用命令见 [[Linux 命令速查手册]]。以下以 Bash（bash 4+）为准，部分特性（关联数组、`^^`/`,,` 大小写转换）在 POSIX sh/dash 中不支持。

## 变量（定义/引用/环境变量/局部变量）

**一句话定义：** 变量是 Shell 中存储数据的容器，分为环境变量（全局生效）和局部变量（仅当前 shell 有效）。

```bash
# 定义变量（等号两边不能有空格！）
name="Linux"
age=30

# 引用变量
echo "我的系统是 $name"
echo "今年 ${age} 岁"

# 环境变量（子进程也能访问）
export PATH="/opt/bin:$PATH"
export DB_HOST="localhost"

# 局部变量（只在当前 shell 有效）
local tmp_var="仅函数内可用"

# 常用环境变量
echo $HOME          # 家目录
echo $USER          # 当前用户
echo $PWD           # 当前目录
echo $PATH          # 可执行文件搜索路径
echo $RANDOM        # 随机数
echo $$             # 当前 shell PID

# 变量默认值
echo ${name:-"默认值"}    # name 为空时用默认值
echo ${name:="默认值"}    # name 为空时赋默认值
echo ${name:?"错误提示"}  # name 为空时报错退出
```

---

## 条件判断（if/elif/else/test/[]/[[]]）

```bash
# if 语法
if [ "$name" = "Linux" ]; then
    echo "这是Linux"
elif [ "$name" = "Windows" ]; then
    echo "这是Windows"
else
    echo "未知系统"
fi

# [[ ]] 比 [ ] 更强大（支持正则、模式匹配）
if [[ "$email" =~ ^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-z]+$ ]]; then
    echo "邮箱格式正确"
fi

if [[ "$file" == *.log ]]; then
    echo "是日志文件"
fi

# 常用测试条件
# 文件测试
[ -f file.txt ]       # 文件存在且是普通文件
[ -d dir/ ]           # 目录存在
[ -r file.txt ]       # 文件可读
[ -w file.txt ]       # 文件可写
[ -x script.sh ]      # 文件可执行
[ -s file.txt ]       # 文件存在且非空

# 字符串测试
[ -z "$str" ]         # 字符串为空
[ -n "$str" ]         # 字符串非空
[ "$a" = "$b" ]       # 字符串相等
[ "$a" != "$b" ]      # 字符串不相等

# 数值测试
[ $a -eq $b ]         # 等于
[ $a -ne $b ]         # 不等于
[ $a -gt $b ]         # 大于
[ $a -lt $b ]         # 小于
[ $a -ge $b ]         # 大于等于
[ $a -le $b ]         # 小于等于

# 逻辑组合（[[ ]] 中）
[[ $a -gt 10 && $b -lt 20 ]]   # AND
[[ $a -eq 1 || $b -eq 2 ]]     # OR
[[ ! -f file.txt ]]            # NOT
```

---

## 循环（for/while/until/case）

```bash
# for 循环
for i in 1 2 3 4 5; do
    echo "数字: $i"
done

# C 风格 for
for ((i=0; i<10; i++)); do
    echo "索引: $i"
done

# 遍历文件
for file in *.log; do
    echo "处理: $file"
done

# 遍历命令输出
for user in $(cat /etc/passwd | cut -d: -f1); do
    echo "用户: $user"
done

# while 循环
count=0
while [ $count -lt 5 ]; do
    echo "第 $count 次"
    ((count++))
done

# 读取文件每一行
while IFS= read -r line; do
    echo "行: $line"
done < file.txt

# until 循环（条件为假时执行，直到条件为真）
until [ -f /tmp/ready ]; do
    echo "等待文件创建..."
    sleep 1
done

# case 语句
case "$1" in
    start)
        echo "启动服务"
        ;;
    stop)
        echo "停止服务"
        ;;
    restart)
        echo "重启服务"
        ;;
    *)
        echo "用法: $0 {start|stop|restart}"
        exit 1
        ;;
esac
```

---

## 函数（定义/参数/返回值）

```bash
# 定义函数
greet() {
    echo "你好, $1!"
}

# 调用
greet "Linux"

# 带返回值
add() {
    local result=$(( $1 + $2 ))
    echo $result    # 用 echo 返回
}
sum=$(add 3 5)
echo "3 + 5 = $sum"

# 返回状态码
is_root() {
    if [ "$(id -u)" -eq 0 ]; then
        return 0    # 成功
    else
        return 1    # 失败
    fi
}

if is_root; then
    echo "当前是 root"
else
    echo "当前不是 root"
fi

# 函数参数
show_args() {
    echo "参数个数: $#"
    echo "所有参数: $@"
    echo "第一个参数: $1"
    echo "第二个参数: $2"
}
show_args a b c d

# 局部变量
my_func() {
    local local_var="只在函数内有效"
    global_var="全局可见"
}
```

---

## 数组（索引数组/关联数组）

```bash
# 索引数组
fruits=("苹果" "香蕉" "橙子" "葡萄")

# 访问
echo ${fruits[0]}          # 第一个元素
echo ${fruits[@]}          # 所有元素
echo ${#fruits[@]}         # 数组长度

# 添加元素
fruits+=("西瓜")

# 遍历
for fruit in "${fruits[@]}"; do
    echo "水果: $fruit"
done

# 删除元素
unset fruits[1]

# 关联数组（键值对，bash 4+）
declare -A person
person[name]="张三"
person[age]=30
person[city]="北京"

# 访问
echo ${person[name]}
echo ${!person[@]}           # 所有键
echo ${person[@]}            # 所有值

# 遍历关联数组
for key in "${!person[@]}"; do
    echo "$key = ${person[$key]}"
done
```

---

## 字符串操作

```bash
str="Hello, Linux World!"

# 长度
echo ${#str}                    # 20

# 截取
echo ${str:0:5}                 # Hello（从位置0取5个字符）
echo ${str:6}                   # Linux World!（从位置6到末尾）
echo ${str: -6}                 # World!（倒数6个字符）

# 替换
echo ${str/Linux/Unix}          # Hello, Unix World!
echo ${str//l/L}                # HeLLo, Linux WorLd!（全局替换）

# 删除
filename="archive.tar.gz"
echo ${filename#*.}             # tar.gz（删除最短前缀匹配）
echo ${filename##*.}            # gz（删除最长前缀匹配）
echo ${filename%.*}             # archive.tar（删除最短后缀匹配）
echo ${filename%%.*}            # archive（删除最长后缀匹配）

# 大小写转换（bash 4+）
echo ${str^^}                   # HELLO, LINUX WORLD!（全大写）
echo ${str,,}                   # hello, linux world!（全小写）

# 默认值
echo ${var:-"变量未设置"}        # var 为空时输出默认值
echo ${var:="默认值"}            # var 为空时赋默认值
```

---

## 正则表达式（grep/sed/awk 中的使用）

```bash
# 基本正则
grep "^root" /etc/passwd         # 以 root 开头
grep "bash$" /etc/passwd         # 以 bash 结尾
grep "^$" file.txt               # 空行
grep "." file.txt                # 至少一个字符

# 扩展正则（grep -E 或 egrep）
grep -E "error|warning" log.txt           # 或
grep -E "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" access.log  # IP 地址
grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}" log.txt  # 日期格式

# sed 中的正则
sed -n '/start/,/end/p' file.txt          # 打印 start 到 end 之间的行
sed 's/[0-9]\+/数字/g' file.txt           # 将连续数字替换为"数字"

# awk 中的正则
awk '/error/ {print NR, $0}' log.txt     # 打印匹配行及行号
awk '$3 ~ /^[0-9]+$/ {sum+=$3} END{print sum}' data.txt  # 第3列为数字时求和
```

---

## 管道与重定向组合

```bash
# 经典组合：找出访问量最大的 IP
cat access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10

# 统计每个状态码的数量
cat access.log | awk '{print $9}' | sort | uniq -c | sort -rn

# 实时监控日志中的错误
tail -f app.log | grep --line-buffered "ERROR"

# 多命令重定向
{
    echo "报告开始"
    echo "=========="
    df -h
    echo "=========="
    free -h
} > /tmp/report.txt

# 同时输出到屏幕和文件（tee）
df -h | tee /tmp/disk_report.txt

# 管道 + xargs（将前一个命令的输出作为后一个命令的参数）
find . -name "*.log" | xargs wc -l
find . -name "*.tmp" | xargs -I {} rm -f {}
cat urls.txt | xargs -I {} curl -s {}
```

---

## awk 高级用法

```bash
# BEGIN 和 END
awk 'BEGIN{print "=== 报告开始 ==="} {print NR": "$0} END{print "共处理", NR, "行"}' file.txt

# 多文件处理
awk 'FNR==NR{a[$1]=$2; next} ($1 in a){print $0, a[$1]}' file1.txt file2.txt

# 数组统计
awk '{count[$1]++} END{for(k in count) print k, count[k]}' access.log

# 条件过滤 + 计算
awk 'NR>1 && $3>100 {sum+=$3; count++} END{print "平均值:", sum/count}' data.csv

# 格式化输出
awk '{printf "%-20s %10d %s\n", $1, $2, $3}' report.txt

# 多分隔符
awk -F'[,;:]' '{print $1, $2}' multi_delim.txt

# 去重（保持顺序）
awk '!seen[$0]++' file.txt

# 两个文件关联查询
awk 'NR==FNR{a[$1]=$2; next} {if($1 in a) print $0, a[$1]}' users.txt orders.txt
```

---

## sed 高级用法

```bash
# 多行处理
sed 'N;s/\n/ /' file.txt                  # 合并每两行为一行
sed ':a;N;$!ba;s/\n/ /g' file.txt         # 所有行合并为一行

# 分支和标签
sed '/^$/d; /^#/d' file.txt                # 删除空行和注释行
sed ':a;N;$!ba;s/\n/ /g' file.txt          # 用标签实现循环

# 保持空间（Hold Space）
sed -n '1!G;h;$p' file.txt                 # 反转文件内容（类似 tac）
sed 'H;$!d;g;s/\n/ /g' file.txt           # 将所有行合并，用空格分隔

# 在指定行前后插入
sed '3i\--- 新插入的行 ---' file.txt        # 第3行前插入
sed '3a\--- 新追加的行 ---' file.txt        # 第3行后追加

# 删除指定范围
sed '/BEGIN/,/END/d' file.txt              # 删除 BEGIN 到 END 之间的内容

# 提取指定范围
sed -n '10,20p' file.txt                   # 打印10-20行

# 条件替换
sed '/success/s/old/new/g' file.txt        # 只在包含 success 的行做替换
```

---

## 调试技巧

```bash
# set -x：显示每条命令执行前的展开结果（最常用！）
#!/bin/bash
set -x
var="hello"
echo $var
# 输出：+ var=hello
#       + echo hello

# set -e：遇到错误立即退出
#!/bin/bash
set -e
ls /nonexistent    # 这里会报错
echo "这行不会执行"

# set -u：使用未定义变量时报错
#!/bin/bash
set -u
echo $undefined_var   # 报错：unbound variable

# set -o pipefail：管道中任意命令失败则整体失败
#!/bin/bash
set -o pipefail
cat nonexistent.txt | grep "error"    # 会报错

# 组合使用（推荐）
#!/bin/bash
set -euo pipefail

# PS4：自定义 set -x 的输出前缀
export PS4='+${BASH_SOURCE}:${LINENO}: '
# 输出：+script.sh:5: echo "debug"
```

---

## 实用脚本模板

### 模板1：带参数解析的脚本

```bash
#!/bin/bash
set -euo pipefail

# 默认值
VERBOSE=false
OUTPUT="/tmp/output"
TARGET=""

# 帮助信息
usage() {
    cat << EOF
用法: $0 [选项] <目标>

选项:
    -v, --verbose     详细模式
    -o, --output DIR  输出目录 (默认: /tmp/output)
    -h, --help        显示帮助信息

示例:
    $0 -v -o /data myproject
EOF
    exit 1
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose) VERBOSE=true; shift ;;
        -o|--output) OUTPUT="$2"; shift 2 ;;
        -h|--help) usage ;;
        -*) echo "未知选项: $1"; usage ;;
        *) TARGET="$1"; shift ;;
    esac
done

# 检查必要参数
if [ -z "$TARGET" ]; then
    echo "错误: 请指定目标"
    usage
fi

# 主逻辑
echo "目标: $TARGET"
echo "输出: $OUTPUT"
echo "详细模式: $VERBOSE"
```

### 模板2：日志备份脚本

```bash
#!/bin/bash
set -euo pipefail

LOG_DIR="/var/log/myapp"
BACKUP_DIR="/backup/logs"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "[$(date)] 开始日志备份..."

# 压缩并备份
find "$LOG_DIR" -name "*.log" -mtime -1 | while read -r file; do
    filename=$(basename "$file")
    gzip -c "$file" > "${BACKUP_DIR}/${filename}.${DATE}.gz"
    echo "已备份: $filename"
done

# 清理旧备份
find "$BACKUP_DIR" -name "*.gz" -mtime +$KEEP_DAYS -delete
echo "[$(date)] 备份完成"
```

### 模板3：服务健康检查脚本

```bash
#!/bin/bash
set -euo pipefail

SERVICES=("nginx" "mysql" "redis")
LOG_FILE="/var/log/health_check.log"
ALERT_EMAIL="admin@example.com"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service"; then
        log "OK: $service 正在运行"
    else
        log "ALERT: $service 已停止！尝试重启..."
        systemctl restart "$service"
        if systemctl is-active --quiet "$service"; then
            log "OK: $service 重启成功"
        else
            log "CRITICAL: $service 重启失败，发送告警邮件"
            echo "服务器 $(hostname) 上的 $service 服务异常，请检查！" | \
                mail -s "服务告警: $service" "$ALERT_EMAIL"
        fi
    fi
done
```

### 模板4：文件批量重命名

```bash
#!/bin/bash
set -euo pipefail

PATTERN="${1:?用法: $0 <模式>}"
REPLACEMENT="${2:?用法: $0 <模式> <替换>}"
DRY_RUN=true

echo "模式: $PATTERN -> 替换: $REPLACEMENT"
echo "预览模式（加 -y 确认执行）"

if [[ "${3:-}" == "-y" ]]; then
    DRY_RUN=false
fi

count=0
for file in *"$PATTERN"*; do
    [ -e "$file" ] || continue
    newname="${file//$PATTERN/$REPLACEMENT}"
    if [ "$DRY_RUN" = true ]; then
        echo "[预览] $file -> $newname"
    else
        mv "$file" "$newname"
        echo "[执行] $file -> $newname"
    fi
    ((count++))
done

echo "共处理 $count 个文件"
```

---

## 常见误区

- 变量赋值等号两边不能有空格；引用变量应加双引号（`"$var"`）以防单词分割与通配展开。
- `[ ]` 是 test 命令、`[[ ]]` 是 Bash 关键字：后者支持 `=~` 正则与 `&&`/`||`、且不必给变量加引号，但非 POSIX、dash 不支持。
- `set -e` 在管道、命令替换、条件语境下有诸多「不触发退出」的例外，需配合 `set -o pipefail` 并理解其边界。
- `#!/bin/sh` 与 `#!/bin/bash` 不同：许多发行版 `/bin/sh` 指向 dash，不支持数组、`[[ ]]` 等 Bash 特性。

## 相关术语

[[Shell脚本编程]]、[[Linux 命令速查手册]]、[[进程管理详解]]、[[操作系统核心]]

## 参考资料

建议人工核验：可参考 GNU Bash 官方手册、`bash(1)`/`sed(1)`/`awk(1)` man page、Google Shell Style Guide 与 ShellCheck 工具。
