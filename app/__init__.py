# -*- coding: utf-8 -*-
"""知库应用包标记 —— 此文件必须存在且被 git 跟踪，勿删。

背景（2026-09-09 启动报错修复）：`python app/app.py` 脚本直启时，sys.path 同时
含项目根（app.py 引导代码补入）与 app/ 目录本身。若 app/ 无 __init__.py，
导入名 `app` 的扫描中，项目根下的 app/ 目录只是 PEP 420 命名空间包候选，
扫描继续后会命中 app/ 目录里的 app.py 文件本体（普通模块优先于命名空间包），
app.py 被二次导入形成循环：ImportError: cannot import name 'store' from 'app'。

有本文件后 `app` 解析为正规包，路径扫描即时命中并终止，脚本直启
（start.bat / python app/app.py）与 tests 包导入两条路径统一。
回归入口：python app/app.py --import-check（tests/test_reader.py 断言覆盖）。
"""
