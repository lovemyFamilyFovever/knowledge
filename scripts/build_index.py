# -*- coding: utf-8 -*-
"""手动重建 FTS 索引。应用启动时会按 mtime 自动增量重建，一般无需手动跑。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.app import build_index, DEFAULT_ROOT  # noqa: E402

n = build_index(DEFAULT_ROOT / "content", DEFAULT_ROOT / "indexes")
print(f"FTS index rebuilt: {n} documents")
