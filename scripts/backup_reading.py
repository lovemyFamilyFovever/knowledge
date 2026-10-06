# -*- coding: utf-8 -*-
"""reading.db 在线滚动备份。

indexes/ 整体被 gitignore（派生缓存），但 reading.db 里的复习排期与掌握度
是唯一不可再生的用户数据——删了卡片库能重建，进度归零。本脚本用 sqlite3
的在线 backup API 拷贝（直接 Copy 正在写入的库文件可能得到截断损坏的副本），
保留最近 KEEP 份滚动。由 daily_backup.ps1 每日调用，也可手动执行。
"""
import sqlite3
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "indexes" / "reading.db"
dst_dir = root / "backups" / "reading"
KEEP = 7

if not src.exists():
    print("backup_reading: no reading.db, skip")
    sys.exit(0)

dst_dir.mkdir(parents=True, exist_ok=True)
dst = dst_dir / ("reading-" + time.strftime("%Y%m%d") + ".db")

con = sqlite3.connect(str(src))
try:
    bak = sqlite3.connect(str(dst))
    try:
        con.backup(bak)
    finally:
        bak.close()
finally:
    con.close()

files = sorted(dst_dir.glob("reading-*.db"))
for old in files[:-KEEP]:
    old.unlink(missing_ok=True)
print(f"backup_reading: {dst.name} ({dst.stat().st_size // 1024} KB), kept {min(len(files), KEEP)}")
