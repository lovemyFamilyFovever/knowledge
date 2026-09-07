# -*- coding: utf-8 -*-
"""命令行语义检索 —— 给 Agent / 自动化用的 RAG 检索入口。

用法：
    python scripts/rag_search.py "如何排查 CSRF 403"            # 人类可读输出
    python scripts/rag_search.py "CSRF 403" --json              # JSON 输出（供 agent）
    python scripts/rag_search.py "双链解析" --domain baike       # 限定域
    python scripts/rag_search.py "挂载点" -k 3 --full            # 输出整块正文

说明：脚本独立于 Flask 应用运行，自动完成模型下载与索引同步；
索引为派生缓存（indexes/rag.db），与阅读器共用同一份。
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.rag import OnnxEmbedder, RagStore, query_rag, rag_status, sync_rag  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="知库本地语义检索（RAG）")
    ap.add_argument("query", help="自然语言查询")
    ap.add_argument("-k", type=int, default=8, help="返回条数（默认 8）")
    ap.add_argument("--domain", default=None, help="限定域（如 baike / projects）")
    ap.add_argument("--sub", default=None, help="限定子域")
    ap.add_argument("--json", action="store_true", help="输出 JSON（供 agent 消费）")
    ap.add_argument("--full", action="store_true", help="输出整块正文（默认截断 160 字）")
    args = ap.parse_args()

    t0 = time.time()
    content = ROOT / "content"
    if not content.is_dir():
        print("错误：找不到 content/ 语料目录", file=sys.stderr)
        return 1

    try:
        embedder = OnnxEmbedder(ROOT / "app" / "rag_models")
        store = RagStore(ROOT / "indexes")
    except Exception as e:
        print(f"错误：RAG 组件初始化失败（{e}）。", file=sys.stderr)
        print("依赖安装：pip install numpy onnxruntime sqlite-vec", file=sys.stderr)
        return 2

    stat = sync_rag(content, embedder, store, log=lambda m: print(m, file=sys.stderr))
    hits = query_rag(store, embedder, args.query, k=args.k, domain=args.domain, sub=args.sub)
    dt = time.time() - t0

    if args.json:
        print(json.dumps({
            "query": args.query, "took_ms": round(dt * 1000),
            "index": rag_status(store), "sync": stat,
            "hits": hits,
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"「{args.query}」— {len(hits)} 条结果 · {dt:.1f}s"
          f"（索引 {stat['total_chunks']} 块，本次同步 {stat['changed']} 文件）")
    for i, h in enumerate(hits, 1):
        score = f"{h['score']:.3f}"
        head = f"  [{i}] {score}  {h['title']}"
        if h.get("heading"):
            head += f"  § {h['heading']}"
        print(head)
        print(f"      {h['file']}  (块 {h['chunk_ix'] + 1}/{h['chunk_n']})")
        body = h["contents"] if args.full else h["contents"][:160].replace("\n", " ") + ("…" if len(h["contents"]) > 160 else "")
        print(f"      {body}")
        print()
    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
