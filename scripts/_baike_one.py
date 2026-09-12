# -*- coding: utf-8 -*-
"""批量提质并提交单个/多个 baike 子目录：处理 -> 校验 -> 生成消息 -> 显式 pathspec 提交。
每个目录独立提交；校验不过则中止该目录、不提交。
用法：python _baike_one.py <dir1> [dir2 ...]
"""
import sys, subprocess, os
PY = r"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
DIRPY = r"E:/GitHub/knowledge/scripts/_baike_dir.py"
REPO = r"E:/GitHub/knowledge"

def run_dir(DIR):
    r = subprocess.run([PY, "-u", DIRPY, DIR], capture_output=True, text=True, timeout=200)
    log = (r.stdout or "") + (r.stderr or "")
    print(f"===== {DIR} =====")
    print(log[-1500:])
    if "VALIDATE: ALL PASS" not in log:
        print(f"  !! {DIR} 校验未通过，跳过提交")
        return False
    out = subprocess.run(["git","-c","core.quotepath=false","diff","--name-only","--",
                          f"content/baike/{DIR}/"], capture_output=True, text=True, cwd=REPO)
    files = [f for f in out.stdout.splitlines() if f.strip()]
    if not files:
        print(f"  {DIR}: 无改动，跳过")
        return True
    msg = (f"feat(baike): 重写 {DIR} 目录 {len(files)} 篇旧稿（导航 + 相关术语 + 参考资料）\n\n"
           f"背景：接 docs/handoff-2026091201.md 继续推进 baike 外科提质。本批覆盖 {DIR} 目录"
           f"全部 {len(files)} 篇旧导入稿。\n\n"
           f"改动（外科提质，严格保留 front matter 六字段名/顺序与值，H1 与 title 逐字一致）：\n"
           f"- 顶部 H1 后新增 `> 📌 导航` 双链块，指向本目录自动挑选的 5 个中心枢纽。\n"
           f"- 末尾补 `## 相关术语`（[[双链]]，由文件名关键词重叠在本目录内挑选真实条目，已断言目标存在）"
           f"与 `## 参考资料`（建议人工核验，未编造文献编号/标准号/URL）。\n"
           f"- 不改动已填好的 tags、source_path/collected/status 与正文；真实（围栏外）H1 唯一且等于 title；"
           f"代码围栏奇偶正确；正文既有跨目录 [[双链]] 合法全树链接予以保留。\n\n"
           f"约束：仅动 content/baike/{DIR}/ 本批 {len(files)} 篇；显式 pathspec，未混入并发/他人无关改动（按坑#8）。\n\n"
           f"验证：脚本内置校验全绿（单一真 H1==title、围栏偶数、导航/相关术语/参考资料齐备、"
           f"[[双链]] 均为全树真实词条名）；pre-commit 四套 smoke 预期全绿；RAG 缺 numpy 则 SKIP/OK。\n\n"
           f"回滚：git revert <本提交> 或 git checkout <父提交> -- content/baike/{DIR}/<文件名>。")
    mp = os.path.join(REPO, "scripts", "_cm.txt")
    open(mp, "w", encoding="utf-8").write(msg)
    rc = subprocess.run(["git","-c","core.quotepath=false","commit","-F", mp, "--"] + files,
                        capture_output=True, text=True, timeout=280, cwd=REPO)
    os.remove(mp)
    print(f"  COMMIT RC={rc.returncode}: {rc.stdout.strip().splitlines()[-1] if rc.stdout.strip() else rc.stderr[-200:]}")
    return rc.returncode == 0

if __name__ == "__main__":
    for d in sys.argv[1:]:
        run_dir(d)
