# -*- coding: utf-8 -*-
"""tests 共用的「临时实例」harness（不是测试文件，pytest 不会收集）。

为什么单独一个文件：`test_js_props.py`（P3-B）与 `test_ui_regress.py`（P5）都要
"在 tempfile 里现造一个 KB_ROOT、起一个一次性 Flask 实例、跑完杀掉"。
这段逻辑里有若干**安全约束**（端口不能撞用户的 5001、绝不写真实 content/），
重复实现两遍就是两个可能走样的口径——本仓库刚在 P6 期间为同样的理由删过两处双实现（台账 §10.11）。

约束（改这个文件前必读）：
  · 端口由 `free_port()` 让 OS 现挑，并显式排除 5001/5000 等用户常驻端口；
  · 实例只用 `KB_ROOT` 环境变量指向临时目录，进程级隔离，收工 `kill_instance()`；
  · 本模块不写任何真实语料，也不碰仓库 `indexes/`。
"""
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# 用户机器上可能常驻的端口，一次性都不许占用（5001 是用户的阅读器）。
FORBIDDEN_PORTS = {5000, 5001, 5031, 8080, 8888}


def free_port(exclude=FORBIDDEN_PORTS) -> int:
    """让 OS 挑一个空闲端口；拒绝返回到常驻端口上。"""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    assert port not in exclude, f"OS 发来的端口 {port} 在禁用表里，检查 exclude 口径"
    return port


def port_open(port, timeout=0.4) -> bool:
    with socket.socket() as s:
        s.settimeout(timeout)
        return s.connect_ex(("127.0.0.1", port)) == 0


def start_instance(root: Path, port: int, log_path=None, wait_rounds=60):
    """起一次性实例（KB_ROOT=root）。返回 Popen；调用方负责 kill。"""
    log = open(log_path, "wb") if log_path else subprocess.DEVNULL
    proc = subprocess.Popen(
        [sys.executable, "-c",
         "import sys;sys.path.insert(0,r'%s');"
         "from app.app import create_app;a=create_app();"
         "a.run(host='127.0.0.1',port=%d,debug=False)" % (str(ROOT), port)],
        cwd=str(ROOT), env=dict(os.environ, KB_ROOT=str(root), PYTHONIOENCODING="utf-8"),
        stdout=log, stderr=log)
    for _ in range(wait_rounds):
        if port_open(port):
            return proc
        time.sleep(0.5)
    kill_instance(proc)
    raise RuntimeError(f"临时实例没起来（port={port}），看 {log_path or '（未落日志）'}")


def kill_instance(proc, grace=10):
    if not proc:
        return
    proc.kill()
    try:
        proc.wait(timeout=grace)
    except Exception:                                # noqa: BLE001
        pass


def node_available() -> bool:
    return bool(shutil.which("node"))


def chrome_path():
    """返回本机 Chrome 可执行文件路径，没有则 None（与 shot.mjs 的候选清单同口径）。"""
    cands = [Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
             Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
             Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe"]
    for c in cands:
        try:
            if c.is_file():
                return c
        except OSError:                              # 环境变量为空时 c 可能非法
            continue
    return None


def magick_available() -> bool:
    return shutil.which("magick") is not None or Path(
        "C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/magick.exe").is_file()
