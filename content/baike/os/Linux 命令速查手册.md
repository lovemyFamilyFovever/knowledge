---
title: "Linux 命令速查手册"
tags: [计算机体系结构, 操作系统, Linux, 命令速查]
source: "baike"
source_path: "开发术语 / 操作系统与Linux"
collected: "2026-09-05"
status: "imported"
---

# Linux 命令速查手册


> 📌 **导航**：本文是 **Linux 命令速查手册** 词条，属于 os 术语集。相关枢纽：[[Shell脚本编程]]、[[操作系统基础术语]]、[[操作系统核心]]、[[进程管理详解]]。

## 概述

**一句话定义：** 本文按功能分类汇总最常用的 Linux 命令与典型用法（文件与目录、文本处理、权限、进程、磁盘、网络、压缩），作为日常运维与开发的速查参考。

> 多义说明：进程与服务的深入实操见 [[进程管理详解]]；Shell 脚本编写见 [[Shell脚本编程]] 与 [[Shell脚本编程]]；命令背后的概念见 [[操作系统核心]]。

## ls — 列出目录内容

```bash
ls              # 列出当前目录文件
ls -l           # 长格式（权限、大小、时间等）
ls -a           # 显示隐藏文件（以.开头）
ls -lh          # 人类可读大小（KB/MB/GB）
ls -R           # 递归列出所有子目录
ls -lt          # 按修改时间排序
ls -lS          # 按大小排序
```

---

## cd / pwd — 切换与显示目录

```bash
cd /var/log     # 进入绝对路径
cd ..           # 返回上级目录
cd ~            # 回到家目录
cd -            # 回到上一次所在目录
pwd             # 显示当前工作目录
```

---

## mkdir / rmdir — 创建与删除目录

```bash
mkdir mydir                 # 创建目录
mkdir -p a/b/c              # 递归创建多层目录
rmdir emptydir              # 删除空目录
rmdir -p a/b/c              # 递归删除空目录
rm -rf mydir                # 强制删除目录及内容（危险！）
```

---

## cp / mv / rm — 复制、移动、删除

```bash
cp file1.txt file2.txt          # 复制文件
cp -r dir1/ dir2/               # 递归复制目录
cp -p file.txt /backup/         # 保留权限和时间戳
mv old.txt new.txt              # 重命名
mv file.txt /target/            # 移动文件
rm file.txt                     # 删除文件
rm -i file.txt                  # 删除前确认
rm -rf /path/to/dir             # 强制递归删除（慎用！）
```

---

## cat / less / more / tail / head — 查看文件内容

```bash
cat file.txt                # 一次性输出全部内容
head -20 file.txt           # 查看前20行
tail -20 file.txt           # 查看后20行
tail -f /var/log/syslog     # 实时追踪日志（最常用！）
less file.txt               # 分页浏览（支持搜索：/关键词）
more file.txt               # 分页浏览（类似 less，功能较少）
```

---

## grep — 文本搜索

```bash
grep "error" logfile.txt           # 搜索包含 error 的行
grep -i "error" logfile.txt        # 忽略大小写
grep -n "error" logfile.txt        # 显示行号
grep -c "error" logfile.txt        # 统计匹配行数
grep -r "TODO" ./src/              # 递归搜索目录
grep -v "debug" logfile.txt        # 反向匹配（排除）
grep -l "pattern" *.log            # 只显示文件名

# 正则表达式
grep -E "error|warning" logfile.txt    # 扩展正则（OR）
grep "^[0-9]\{4\}" logfile.txt         # 以4位数字开头的行

# 上下文
grep -B 3 -A 3 "error" logfile.txt    # 显示匹配行前后各3行
```

---

## find — 查找文件

```bash
# 按名称
find / -name "*.log"
find . -iname "readme.txt"    # 忽略大小写

# 按时间
find . -mtime -7              # 最近7天修改过的文件
find . -mtime +30             # 30天前修改的文件
find . -newer file.txt        # 比 file.txt 更新的文件

# 按大小
find . -size +100M            # 大于100MB的文件
find . -size 0                # 空文件

# 按类型
find . -type f                # 只找文件
find . -type d                # 只找目录

# 组合操作
find . -name "*.tmp" -exec rm {} \;      # 找到并删除
find . -name "*.log" -mtime +30 -delete  # 删除30天前的日志
```

---

## sed — 流编辑器

```bash
# 替换
sed 's/old/new/' file.txt              # 每行第一个匹配
sed 's/old/new/g' file.txt             # 全局替换
sed -i 's/old/new/g' file.txt          # 直接修改文件
sed -i.bak 's/old/new/g' file.txt     # 修改前备份

# 删除
sed '/^#/d' file.txt                   # 删除注释行
sed '/^$/d' file.txt                   # 删除空行
sed '1,5d' file.txt                    # 删除1-5行

# 插入/追加
sed '3a\新插入的行' file.txt            # 第3行后追加
sed '1i\文件头信息' file.txt            # 第1行前插入
```

---

## awk — 文本处理

```bash
# 字段处理（默认空格分隔）
awk '{print $1, $3}' file.txt          # 打印第1和第3列
awk -F: '{print $1}' /etc/passwd       # 指定冒号分隔符

# 内置变量
awk '{print NR, NF, $0}' file.txt     # 行号、字段数、整行

# 模式匹配
awk '/error/' file.txt                  # 打印包含 error 的行
awk '$3 > 100 {print $1, $3}' file.txt # 第3列大于100

# BEGIN/END
awk 'BEGIN{sum=0} {sum+=$3} END{print "Total:", sum}' file.txt

# 计算列总和
awk '{sum+=$2} END{print sum}' file.txt
```

---

## 管道与重定向

```bash
# 管道：将前一个命令的输出作为后一个命令的输入
ps aux | grep nginx | grep -v grep
cat access.log | sort | uniq -c | sort -rn | head -10

# 重定向
echo "hello" > file.txt        # 覆盖写入
echo "world" >> file.txt       # 追加写入
command < input.txt             # 从文件读取输入
command > out.txt 2>&1          # 标准输出和错误都重定向
command &> all.txt              # 同上（bash简写）
command 2>/dev/null             # 丢弃错误输出
```

---

## chmod / chown — 权限与所有权

```bash
# 数字模式（r=4, w=2, x=1）
chmod 755 script.sh             # rwxr-xr-x
chmod 644 config.txt            # rw-r--r--
chmod 600 secret.key            # rw-------

# 符号模式
chmod u+x script.sh             # 给所有者加执行权限
chmod g+w file.txt              # 给组加写权限
chmod o-r file.txt              # 去掉其他人的读权限
chmod a+r file.txt              # 所有人加读权限

# 递归修改
chmod -R 755 /var/www/html/

# 修改所有者
chown user:group file.txt
chown -R www-data:www-data /var/www/
```

---

## ps / top / htop — 进程查看

```bash
# ps：进程快照
ps aux                          # BSD风格，显示所有进程
ps -ef                          # System V风格
ps aux | grep nginx             # 查找特定进程
ps -eo pid,ppid,%cpu,%mem,cmd   # 自定义输出列

# top：实时监控（按 q 退出，按 M 按内存排序）
top
top -u www-data                 # 只看某用户的进程

# htop：增强版 top（需要安装）
htop
htop -p 1234                    # 监控指定PID
```

---

## df / du — 磁盘使用

```bash
# df：磁盘空间
df -h                           # 人类可读格式
df -hT                          # 显示文件系统类型

# du：目录大小
du -sh /var/log/                # 显示目录总大小
du -h --max-depth=1 /           # 一级子目录大小
du -sh * | sort -rh | head -10  # 当前目录最大的10个文件/目录
```

---

## netstat / ss — 网络连接

```bash
# netstat
netstat -tlnp                   # 查看监听的TCP端口
netstat -anp | grep :80         # 查看80端口的连接
netstat -s                      # 网络统计

# ss（更快的替代品）
ss -tlnp                        # TCP监听端口
ss -s                           # 连接统计摘要
ss state established            # 已建立的连接
```

---

## tar / gzip / zip / unzip — 压缩解压

```bash
# tar 打包/解包
tar -cvf archive.tar dir/       # 打包
tar -xvf archive.tar            # 解包
tar -cvzf archive.tar.gz dir/   # 打包并gzip压缩
tar -xvzf archive.tar.gz        # 解压gzip
tar -xvf archive.tar -C /tmp/   # 解压到指定目录

# gzip
gzip file.txt                   # 压缩（原文件被替换）
gzip -d file.txt.gz             # 解压
gunzip file.txt.gz              # 解压

# zip/unzip
zip -r archive.zip dir/         # 递归压缩目录
unzip archive.zip               # 解压
unzip archive.zip -d /tmp/      # 解压到指定目录
```

---

## 命令速查表

| 操作 | 命令 |
|------|------|
| 查找大文件 | `find / -type f -size +100M` |
| 查找最近修改的文件 | `find . -mtime -1 -type f` |
| 统计代码行数 | `find . -name "*.py" \| xargs wc -l` |
| 批量重命名 | `for f in *.txt; do mv "$f" "${f%.txt}.md"; done` |
| 查看端口占用 | `ss -tlnp \| grep :80` |
| 查看系统负载 | `uptime` |
| 清空文件 | `> file.txt` |
| 实时监控日志 | `tail -f /var/log/syslog` |
| 杀死所有同名进程 | `killall nginx` |
| 查看环境变量 | `env` 或 `printenv` |

---

## 常见误区

- `rm -rf` 不可逆且无回收站，路径写错（尤其含变量/空格未加引号）后果严重；执行前先 `ls` 核对或用 `rm -i`。
- `grep pattern` 未加引号时，通配符/特殊字符会被 shell 先解释；模式含空格或元字符应加引号。
- `>` 覆盖、`>>` 追加，混用会丢数据；`2>&1` 与 `2>/dev/null` 的顺序与含义需分清。

## 相关术语

[[进程管理详解]]、[[Shell脚本编程]]、[[Shell脚本编程]]、[[操作系统核心]]、[[文件系统]]

## 参考资料

建议人工核验：可参考各命令的 man page（如 `ls(1)`、`grep(1)`、`find(1)`、`sed(1)`、`awk(1)`、`chmod(1)`）、GNU coreutils 手册与 `tldr` 速查。
