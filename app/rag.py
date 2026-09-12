# -*- coding: utf-8 -*-
"""本地向量检索（RAG）— 纯离线，语料不出网。

管线：content/**/*.md → 智能切块（标题路径继承 + 重叠窗口）→
bge-small-zh-v1.5（CLS pooling，L2 归一化后点积即余弦相似度）→
sqlite-vec 虚拟表 vec_docs（indexes/rag.db，纯派生缓存，可随时删除重建）。

依赖（缺失时 app.py 自动降级为纯 FTS，不影响阅读器其余功能）：
    numpy, onnxruntime, sqlite-vec
模型：首次运行自动从 hf-mirror.com 下载至 app/rag_models/（约 24MB），
之后完全离线。bge-small-zh-v1.5 为 Apache-2.0 许可的中文嵌入模型。

tokenizer 说明：不引入 transformers/tokenizers，这里按 Rust tokenizers 的
WordPiece 管线实现最小解析（BertNormalizer → BertPreTokenizer → WordPiece
贪心最长匹配 → [CLS]/[SEP]），行为与 HF BertTokenizerFast 对齐；切块长度
按 token 数控制，确保送入 ONNX 模型不超 512 上限、不触发静默截断。
"""
import json
import os
import re
import sqlite3
import threading
import time
import unicodedata
import urllib.request
from pathlib import Path

import numpy as np

# ---------------- 常量 ----------------
MODEL_ID = "Xenova/bge-small-zh-v1.5"   # 含 ONNX 的社区转换版
MODEL_REVISION = "main"
HF_ENDPOINT = "https://hf-mirror.com"   # 大陆可达镜像；模型只需下载一次
MODEL_FILES = {"onnx/model.onnx": "model.onnx", "tokenizer.json": "tokenizer.json"}

DIM = 512          # bge-small-zh-v1.5 隐藏维度
MAX_TOKENS = 512   # 模型硬上限（含 [CLS]/[SEP]）

# 切块参数（bge 中文按字分词，1 汉字 ≈ 1 token；按字符控长即近似 token 数）
CHUNK_MAX_CHARS = 420   # 单块正文字符上限
CHUNK_MIN_CHARS = 60    # 过短段落并入前块，避免碎片向量
OVERLAP_CHARS = 60      # 相邻块重叠，防止答案恰好被切断

QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："  # bge 官方查询前缀
EMBED_BATCH = 16
RAG_CODE_VERSION = "3"  # 嵌入/批量/分词逻辑变更时递增；不匹配则触发全量重建

SYNC_LOCK = threading.Lock()  # 后台 watcher 与查询线程并发同步的互斥锁

FM_RE = re.compile(r"\A---\n(.*?)\n---\n\n?", re.S)
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
SKIP_DIRS = {"_inbox", "_assets", "_unfiled", "_trash"}


# ---------------- tokenizer ----------------
_PUNCT_CHARS = set(
    "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    "\u2010\u2011\u2012\u2013\u2014\u2015\u2018\u2019\u201c\u201d\u2020\u2026"
    "\uff01\uff08\uff09\uff0c\uff1a\uff1b\uff1f\u3001\u3002\u300a\u300b\u300c\u300d\uff5e\uff5c"
)


class HFTokenizer:
    """tokenizer.json（WordPiece）最小实现。与 Rust tokenizers 的 BERT 管线逐
    token 对齐（已用 tokenizers 库交叉验证）：BertNormalizer（clean_text +
    handle_chinese_chars 逐字拆分 + 按 json 的小写化策略）→ BertPreTokenizer
    （Unicode 标点两侧切断）→ WordPiece 贪心最长匹配 → [CLS]/[SEP]。
    仅支持 WordPiece，其他模型类型（BPE/UNigram）直接抛错。"""

    # Rust tokenizers BertNormalizer.is_chinese_char 的 CJK 区段
    _CJK_RANGES = ((0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x20000, 0x2A6DF),
                   (0x2A700, 0x2B73F), (0x2B740, 0x2B81F), (0x2B920, 0x2CEAF),
                   (0xF900, 0xFAFF), (0x2F800, 0x2FA1F))

    def __init__(self, tok_path: Path):
        data = json.loads(tok_path.read_text(encoding="utf-8"))
        model = data.get("model", {})
        if model.get("type") != "WordPiece":
            raise ValueError(f"unsupported tokenizer model type: {model.get('type')}")
        self.vocab: dict[str, int] = model["vocab"]
        self.unk = model.get("unk_token", "[UNK]")
        self.unk_id = self.vocab[self.unk]
        self.max_input_chars_per_word = int(model.get("max_input_chars_per_word", 100))
        self.cont = model.get("continuing_subword_prefix", "##")
        nrm = data.get("normalizer", {})
        # 忠实读取 json：Xenova 版 lowercase=false（实测 The→[UNK]，与参考一致）。
        # ⚠️ 不能强制小写：该模型就是以未小写输入训练/转换的。
        self.lowercase = bool(nrm.get("lowercase", False)) if nrm.get("type") == "BertNormalizer" else False
        self.clean_text = bool(nrm.get("clean_text", True))
        self.handle_chinese_chars = bool(nrm.get("handle_chinese_chars", True))
        self.cls_id = self.vocab.get("[CLS]")
        self.sep_id = self.vocab.get("[SEP]")
        if self.cls_id is None or self.sep_id is None:
            raise ValueError("vocab missing [CLS]/[SEP]")

    @classmethod
    def _is_cjk(cls, ch: str) -> bool:
        cp = ord(ch)
        return any(lo <= cp <= hi for lo, hi in cls._CJK_RANGES)

    def _norm(self, s: str) -> str:
        out: list[str] = []
        for ch in s:
            if self.clean_text and (unicodedata.category(ch) == "Cc" or ch == "\ufffd"):
                continue  # Rust clean_text：丢弃控制字符与替换符
            if self.handle_chinese_chars and self._is_cjk(ch):
                out.extend((" ", ch, " "))  # 每个汉字两侧插空格 → 逐字成词
                continue
            out.append(ch)
        s = "".join(out)
        if self.lowercase:
            s = unicodedata.normalize("NFD", s)
            s = "".join(c for c in s if unicodedata.category(c) != "Mn")
            s = s.lower()
        return s

    def _pre(self, s: str) -> list[str]:
        # BertPreTokenizer：Unicode 标点（P* 类）两侧切断，空白再切
        out: list[str] = []
        buf: list[str] = []
        for ch in s:
            if unicodedata.category(ch).startswith("P"):
                if buf:
                    out.extend(t for t in "".join(buf).split() if t)
                    buf = []
                out.append(ch)
            else:
                buf.append(ch)
        if buf:
            out.extend(t for t in "".join(buf).split() if t)
        return out

    def _wordpiece(self, word: str) -> list[int]:
        # 贪心最长匹配；超长词与无法切分的词整体 → [UNK]
        if len(word) > self.max_input_chars_per_word:
            return [self.unk_id]
        ids: list[int] = []
        start = 0
        while start < len(word):
            end = len(word)
            cur = None
            while end > start:
                sub = word[start:end]
                if start > 0:
                    sub = self.cont + sub
                hit = self.vocab.get(sub)
                if hit is not None:
                    cur = hit
                    break
                end -= 1
            if cur is None:
                return [self.unk_id]
            ids.append(cur)
            start = end
        return ids

    def encode(self, text: str, add_special: bool = True) -> list[int]:
        ids: list[int] = []
        for w in self._pre(self._norm(text)):
            ids.extend(self._wordpiece(w))
        if add_special:
            ids = [self.cls_id] + ids + [self.sep_id]
        return ids

    def token_count(self, text: str) -> int:
        return len(self.encode(text, add_special=False))


# ---------------- 模型下载 ----------------
MODEL_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")  # 镜像站拦默认 UA


def download_model(model_dir: Path) -> None:
    """首次运行下载 model.onnx + tokenizer.json；已存在则跳过（离线可用）。"""
    model_dir.mkdir(parents=True, exist_ok=True)
    for remote, local in MODEL_FILES.items():
        dest = model_dir / local
        if dest.is_file() and dest.stat().st_size > 0:
            continue
        url = f"{HF_ENDPOINT}/{MODEL_ID}/resolve/{MODEL_REVISION}/{remote}"
        tmp = dest.with_suffix(dest.suffix + ".part")
        req = urllib.request.Request(url, headers={"User-Agent": MODEL_UA})
        with urllib.request.urlopen(req, timeout=120) as resp, tmp.open("wb") as f:
            while True:
                block = resp.read(1 << 16)
                if not block:
                    break
                f.write(block)
        tmp.replace(dest)


# ---------------- 切块 ----------------
def _flush(buf: list[str], heading: str, out: list[dict]) -> None:
    text = "\n".join(buf).strip()
    if text:
        out.append({"heading": heading, "text": text})


def _merge_short(chunks: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for c in chunks:
        if len(c["text"]) < CHUNK_MIN_CHARS and merged:
            prev = merged[-1]
            prev["text"] += "\n\n" + c["text"]
            if not prev["heading"] and c["heading"]:
                prev["heading"] = c["heading"]
        else:
            merged.append(dict(c))
    return merged


def markdown_split(md_text: str) -> list[dict]:
    """按 1-3 级标题切块；标题路径继承进块内；超长段落滚动窗口切分。"""
    fm = FM_RE.match(md_text)
    body = md_text[fm.end():] if fm else md_text
    out: list[dict] = []
    stack: list[str] = []
    levels: list[int] = []
    buf: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            buf.append(line)
            continue
        m = HEADING_RE.match(line) if not in_fence else None
        if m:
            _flush(buf, " > ".join(t for t in stack if t), out)
            buf = []
            level = len(m.group(1))
            title = m.group(2).strip()
            while levels and levels[-1] >= level:
                levels.pop()
                stack.pop()
            levels.append(level)
            stack.append(title)
        else:
            buf.append(line)
            if len("\n".join(buf)) >= CHUNK_MAX_CHARS:
                text = "\n".join(buf).strip()
                cut = text[:CHUNK_MAX_CHARS]
                nl = cut.rfind("\n")
                if nl > CHUNK_MAX_CHARS // 2:
                    cut = cut[:nl]
                _flush([cut], " > ".join(t for t in stack if t), out)
                rest = text[len(cut):].lstrip()
                buf = [rest[-OVERLAP_CHARS:]] if rest else []
    _flush(buf, " > ".join(t for t in stack if t), out)
    return _merge_short(out)


# ---------------- ONNX 嵌入 ----------------
def os_cpu() -> int:
    try:
        return len(__import__("os").sched_getaffinity(0))
    except AttributeError:
        import os
        return os.cpu_count() or 4


class OnnxEmbedder:
    """bge-small-zh-v1.5 的 ONNX 推理封装：CLS pooling + L2 归一化。"""

    def __init__(self, model_dir: Path):
        import onnxruntime as ort

        download_model(model_dir)
        so = ort.SessionOptions()
        so.intra_op_num_threads = max(2, os_cpu() // 2)
        self.sess = ort.InferenceSession(
            str(model_dir / "model.onnx"),
            sess_options=so,
            providers=["CPUExecutionProvider"],
        )
        self.in_names = [i.name for i in self.sess.get_inputs()]
        self.tok = HFTokenizer(model_dir / "tokenizer.json")

    def _pool(self, hidden: np.ndarray) -> np.ndarray:
        # CLS pooling（bge-small-zh 官方 1_Pooling 配置 cls_token=true）。
        # hidden: last_hidden_state 单样本切片，形状 (seq, 512)，取 [0, :] 即 [CLS] 位置。
        v = hidden[0].astype(np.float32)
        n = float(np.linalg.norm(v))
        return v / (n if n > 0 else 1.0)

    def _run(self, texts: list[str]) -> list[list[float]]:
        enc = [self.tok.encode(t)[:MAX_TOKENS] for t in texts]
        max_len = max(len(e) for e in enc)
        ids = np.zeros((len(enc), max_len), dtype=np.int64)
        att = np.zeros((len(enc), max_len), dtype=np.int64)
        for i, e in enumerate(enc):
            ids[i, : len(e)] = e
            att[i, : len(e)] = 1
        feed = {}
        for name in self.in_names:
            if "input_ids" in name:
                feed[name] = ids
            elif "attention" in name:
                feed[name] = att
            elif "token_type" in name:
                feed[name] = np.zeros_like(ids)
        out = self.sess.run(None, feed)
        # ONNX 输出: out[0] = last_hidden_state, 形状 (batch, seq, 512)。
        # 逐样本取 [CLS] 隐状态池化 —— 每个 batch 元素产出一个向量。
        hidden = out[0]
        return [self._pool(hidden[i]) for i in range(hidden.shape[0])]

    def embed_query(self, q: str) -> list[float]:
        return self._run([QUERY_PREFIX + q.strip()])[0]

    def embed_chunks(self, chunks: list[dict]) -> list[list[float]]:
        texts = []
        for c in chunks:
            head = f"{c['heading']}\n" if c.get("heading") else ""
            texts.append(head + c["text"])
        vecs: list[list[float]] = []
        for i in range(0, len(texts), EMBED_BATCH):
            vecs.extend(self._run(texts[i: i + EMBED_BATCH]))
        return vecs


# ---------------- 向量库（sqlite-vec） ----------------
COLS = ("contents", "file", "title", "heading", "source", "collected", "tags",
        "chunk_ix", "chunk_n", "score")


class RagStore:
    """indexes/rag.db：vec0 虚拟表 + files 元数据表。纯派生缓存。"""

    def __init__(self, indexes: Path, dim: int = DIM):
        import sqlite_vec

        indexes.mkdir(parents=True, exist_ok=True)
        self.db_path = indexes / "rag.db"
        # rag.db 也是 indexes/ 下的派生库，同样会和 _index_watcher 抢锁。
        # 这里用字面量而不是 app.store.SQLITE_BUSY_TIMEOUT_S：本模块被 numpy 缺失的
        # 环境整体跳过，且可能被脚本单独导入，不额外引入 app 包依赖。
        self.con = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        self.con.enable_load_extension(True)
        sqlite_vec.load(self.con)
        self.con.enable_load_extension(False)
        self.dim = dim
        self.con.execute(
            f"""CREATE VIRTUAL TABLE IF NOT EXISTS vec_docs USING vec0(
                chunk_id TEXT PRIMARY KEY,
                contents TEXT, file TEXT, title TEXT, heading TEXT,
                source TEXT, collected TEXT, tags TEXT,
                chunk_ix INTEGER, chunk_n INTEGER,
                embedding float[{dim}])"""
        )
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, mtime REAL, chunk_n INTEGER)")
        self.con.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
        self.con.commit()

    def upsert_file(self, rel: str, mtime: float, chunks: list[dict],
                    vecs: list[list[float]]) -> None:
        cur = self.con
        cur.execute("BEGIN")
        try:
            cur.execute("DELETE FROM vec_docs WHERE file=?", (rel,))
            n = len(chunks)
            for ix, (c, v) in enumerate(zip(chunks, vecs)):
                cur.execute(
                    """INSERT INTO vec_docs(chunk_id,contents,file,title,heading,source,
                       collected,tags,chunk_ix,chunk_n,embedding)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (f"{rel}::{ix}", c["text"], rel, c["title"], c["heading"],
                     c["source"], c["collected"], c["tags"], ix, n,
                     np.asarray(v, dtype=np.float32).tobytes()),
                )
            cur.execute(
                "INSERT INTO files(path,mtime,chunk_n) VALUES(?,?,?) "
                "ON CONFLICT(path) DO UPDATE SET mtime=excluded.mtime, chunk_n=excluded.chunk_n",
                (rel, mtime, n),
            )
            cur.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('built_at',?)",
                        (str(time.time()),))
            cur.commit()
        except Exception:
            cur.rollback()
            raise

    def delete_file(self, rel: str) -> None:
        self.con.execute("DELETE FROM vec_docs WHERE file=?", (rel,))
        self.con.execute("DELETE FROM files WHERE path=?", (rel,))
        self.con.commit()

    def known_files(self) -> dict[str, float]:
        return {r[0]: r[1] for r in self.con.execute("SELECT path, mtime FROM files")}

    def count_chunks(self) -> int:
        for r in self.con.execute("SELECT count(*) FROM vec_docs"):
            return int(r[0])
        return 0

    def search(self, qvec: list[float], k: int, files: set[str] | None = None) -> list[dict]:
        # sqlite-vec KNN 语法：embedding MATCH 时只能用 k = ? 或 LIMIT 之一，不能并存
        q = np.asarray(qvec, dtype=np.float32).tobytes()
        if files:
            # KNN 索引扫描不支持任意 IN 过滤：取 4k 邻居再按文件集过滤，
            # 不足时回退全量暴力扫描（语义搜索 k 小，代价可忽略）
            ph = ",".join("?" for _ in files)
            rows = self.con.execute(
                f"""SELECT contents,file,title,heading,source,collected,tags,chunk_ix,chunk_n,distance
                    FROM vec_docs WHERE embedding MATCH ? AND k = ? AND file IN ({ph})
                    ORDER BY distance""",
                (q, 4 * k, *files),
            ).fetchall()
            if len(rows) < min(k, 8):
                return self._bruteforce(qvec, k, files)
            # 统一 score 极性：distance 为欧氏距离（已实测确认，非平方/余弦距离），
            # 归一化向量下余弦相似度 = 1 - d²/2（越大越相关）
            return [dict(zip(COLS, (*r[:9], 1.0 - float(r[9]) ** 2 / 2.0))) for r in rows[:k]]
        rows = self.con.execute(
            """SELECT contents,file,title,heading,source,collected,tags,chunk_ix,chunk_n,distance
               FROM vec_docs WHERE embedding MATCH ? AND k = ?
               ORDER BY distance""",
            (q, k),
        ).fetchall()
        # distance 为欧氏距离（已实测）：余弦相似度 = 1 - d²/2；与 _bruteforce 同极性
        return [dict(zip(COLS, (*r[:9], 1.0 - float(r[9]) ** 2 / 2.0))) for r in rows]

    def _bruteforce(self, qvec: list[float], k: int, files: set[str]) -> list[dict]:
        qv = np.asarray(qvec, dtype=np.float32)
        scored = []
        for r in self.con.execute(
            "SELECT contents,file,title,heading,source,collected,tags,chunk_ix,chunk_n,embedding "
            "FROM vec_docs WHERE embedding IS NOT NULL"
        ):
            if files is not None and r[1] not in files:
                continue
            v = np.frombuffer(r[9], dtype=np.float32)
            scored.append((float(np.dot(qv, v)), r))
        scored.sort(key=lambda x: -x[0])
        return [dict(zip(COLS, (*s[1][:9], s[0]))) for s in scored[:k]]

    def close(self) -> None:
        try:
            self.con.close()
        except Exception:
            pass


# ---------------- 语料同步 ----------------
def md_corpus_files(content: Path) -> dict[str, float]:
    """收编语料的 {相对路径: mtime}；跳过派生目录与备注文件。

    B21a：用 os.walk 而非 Path.walk（后者 Python >=3.12 才有）——
    AGENTS 不变量 8 承诺 start.bat 任意 Python 可启动，不能绑定新标准库 API。"""
    out: dict[str, float] = {}
    for dirpath, dirnames, filenames in os.walk(content):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith("_")]
        for fn in filenames:
            if not fn.endswith(".md") or fn.endswith(".notes.md"):
                continue
            p = Path(dirpath) / fn
            out[p.relative_to(content).as_posix()] = p.stat().st_mtime
    return out


def parse_fm(md_text: str) -> dict:
    fm: dict = {}
    m = FM_RE.match(md_text)
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [x.strip().strip("\"'") for x in inner.split(",") if x.strip()]
        elif val.lower() in ("true", "false"):
            fm[key] = val.lower() == "true"
        else:
            fm[key] = val.strip("\"'")
    return fm


def sync_rag(content: Path, embedder: "OnnxEmbedder", store: RagStore, log=None) -> dict:
    """增量同步：mtime 变化的文件重新切块嵌入，删除的文件清出索引。

    完整性自检：vec_docs 行数与 files 表 chunk_n 总和不符、或代码版本
    变更（pooling/批量逻辑修复过）时，全量重建 —— 保证索引与嵌入逻辑
    始终一致，无需手工删库。"""
    with SYNC_LOCK:
        known = store.known_files()
        current = md_corpus_files(content)
        changed = [rel for rel, mt in current.items() if rel not in known or known[rel] < mt]
        deleted = [rel for rel in known if rel not in current]
        # 完整性自检：行数与元数据不符 / 嵌入代码版本变更 → 全量重建
        sum_chunks = store.con.execute(
            "SELECT COALESCE(sum(chunk_n),0) FROM files").fetchone()[0]
        n_vec = store.con.execute("SELECT count(*) FROM vec_docs").fetchone()[0]
        ver = store.con.execute("SELECT v FROM meta WHERE k='code_version'").fetchone()
        if (not ver or ver[0] != RAG_CODE_VERSION) or n_vec != sum_chunks:
            changed = list(current.keys())  # 嵌入逻辑或索引完整性异常：全部重算
        for rel in deleted:
            store.delete_file(rel)
        total = len(changed)
        n_chunks = 0
        for i, rel in enumerate(changed):
            p = content / rel
            try:
                raw = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue  # 竞争删除：下轮同步自然一致
            fm = parse_fm(raw)
            chunks = markdown_split(raw)
            for c in chunks:
                c["title"] = str(fm.get("title") or p.stem)
                c["source"] = str(fm.get("source", ""))
                c["collected"] = str(fm.get("collected", ""))
                tags = fm.get("tags")
                c["tags"] = " ".join(tags) if isinstance(tags, list) else str(tags or "")
            if not chunks:
                store.delete_file(rel)
                continue
            vecs = embedder.embed_chunks(chunks)
            store.upsert_file(rel, current[rel], chunks, vecs)
            n_chunks += len(chunks)
            if log and (i + 1) % 10 == 0:
                log(f"[rag] 嵌入中 {i + 1}/{total}")
        n_all = store.count_chunks()
        store.con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('n_chunks',?)", (str(n_all),))
        store.con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('model_id',?)", (MODEL_ID,))
        store.con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('code_version',?)",
                          (RAG_CODE_VERSION,))
        store.con.commit()
        return {"changed": total, "deleted": len(deleted),
                "new_chunks": n_chunks, "total_chunks": n_all}


def rag_status(store: "RagStore | None") -> dict:
    if store is None:
        return {"enabled": False, "chunks": 0, "model": ""}
    row = store.con.execute("SELECT v FROM meta WHERE k='n_chunks'").fetchone()
    mid = store.con.execute("SELECT v FROM meta WHERE k='model_id'").fetchone()
    return {"enabled": True, "chunks": int(row[0]) if row else 0,
            "model": mid[0] if mid else MODEL_ID}


# ---------------- 查询 ----------------
def query_rag(store: RagStore, embedder: OnnxEmbedder, q: str, k: int = 8,
              domain: str | None = None, sub: str | None = None) -> list[dict]:
    qvec = embedder.embed_query(q)
    files: set[str] | None = None
    if domain:
        prefix = f"{domain}/{sub}/" if sub and sub != "_root" else f"{domain}/"
        files = {rel for rel in store.known_files() if rel.startswith(prefix)}
        if not files:
            return []
    hits = store.search(qvec, k, files)
    from urllib.parse import quote as _urlquote
    for h in hits:
        # 逐段编码：含空格/中文的路径裸拼会在复制链接、代理等场景断链
        segs = h["file"][:-3].split("/")
        if len(segs) == 2:  # 两段 rel = 域根文档，与 docUrl()/doc_url() 一致补 _root 段
            segs.insert(1, "_root")
        h["url"] = "/doc/" + "/".join(_urlquote(x) for x in segs)
    return hits
