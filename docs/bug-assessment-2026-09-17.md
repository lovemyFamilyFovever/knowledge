# 知库 Bug 评估报告

**日期**：2026-09-17 · **范围**：工作区未提交改动（治理驾驶舱 Story 5/6 + 统计磁盘缓存重构）+ 周边抽查
**方法**：diff 审查 → ruff/ESLint 静态检查 → Flask test client 运行时实测 → smoke 套件回归

---

## 结论速览

| # | 严重度 | 位置 | 问题 | 状态 |
|---|--------|------|------|------|
| 1 | 🔴 P0 | `app/routes_stats.py:174` | `open_db` 未定义名 → 全局统计弹窗双链数**恒为 0**，且被静默吞掉 | 实测复现 |
| 2 | 🔴 P0 | `app/routes_stats.py:66-105` | 新增的 `stats_cjk.json` 磁盘缓存三重断裂：永不生成、命中即丢数、还会清空已有缓存 | 实测复现 |
| 3 | 🟡 P2 | `static/pages/governance.js:init()` | 进页即自动全库扫描，与后端/模板注释声明的「点按钮才跑」直接矛盾 | 代码证实 |
| 4 | 🟡 P2 | `static/pages/governance.js:batchDead()` | 断链处置只匹配字面量 `[[raw]]`，别名/锚点/嵌入变体全部漏网 | 逻辑证实 |
| 5 | 🔵 P3 | 若干 | 工程卫生问题（见文末清单） | — |

Smoke 套件（reader 74 + learn 208 + govern）全绿却带着 P0 —— 回归网本身有洞，见「过程建议」。

---

## P0-1 统计弹窗双链健康度恒为 0（静默 NameError）

本次重构把 `open_db` 从模块顶部导入移除，改成治理函数内部的惰性导入：

```python
# app/routes_stats.py 顶部（改后）
from app.fts import build_index, extract_wikilinks   # open_db 被删掉了
```

但 `api_globalstats` 里原有调用点没改（L174）：

```python
n_links = n_dead = dead_docs = 0
try:
    con = open_db(_indexes())        # ← NameError！
    ...
except Exception:
    pass  # “FTS 索引缺失时缺省为 0” —— 现在这个 except 把笔误也吞了
```

**实测证据**（Flask test client）：

```
FTS 实况：links 总数=4283, 未解析=1
/api/globalstats → links: {"total": 0, "dead": 0, "dead_docs": 0}
```

**影响**：顶栏「统计」弹窗永远显示 0 条双链。不报错、不崩溃、不返回非 200 —— 纯静默错数。断链报警功能（治理页依赖的同一张表）对普通用户失效。

**修复**（二选一）：

```python
# 方案 A：恢复模块级导入
from app.fts import build_index, extract_wikilinks, open_db

# 方案 B：就近惰性导入，与治理函数风格一致
    try:
        from app.fts import open_db
        con = open_db(_indexes())
```

并把 `except Exception` 收窄为 `except (sqlite3.Error, OSError)`，否则下次同类笔误照样隐身。

## P0-2 `_corpus_agg` 持久化字数的缓存是死的，还会自毁

新增“冷启动不全库扫盘”的磁盘缓存（`indexes/stats_cjk.json`），但拼装断了三截：

```python
cjk_cache = stats_cjk_load(_indexes())
new_cache: dict[str, list] = {}          # ③ 之后从未写入，永远是 {}
...
    if ent is not None and ent[0] == st.st_mtime_ns:
        n_cjk = int(ent[1])              # ① 命中值算出来了，从未 cjk += n_cjk（ruff F841）
    else:
        ...
        cjk += len(re.findall(...))      # ② 未写 new_cache[rel] = [...]\n
...
if new_cache != (cjk_cache or {}):
    stats_cjk_save(_indexes(), new_cache)  # ③ 永远拿 {} 去比/去写
```

三行合成一个死循环：`new_cache` 恒空 → 缓存文件永不生成 → 永远不会命中；即便文件存在（手工造/未来修复一半），收尾还会把 `{}` 写回去**清空整个缓存**。

**实测证据**：

```
全量跑完 stats_cjk.json 生成? False                    ← 优化完全未生效
预置 1 条缓存(该篇真实字数 708) 重算: 总字数少 708        ← 命中即丢数
重算后缓存文件剩几条: 0                                   ← 已有缓存被清空
```

目前线上数字“恰好还对”，是因为永远命中不了（②掩盖了①）。**只修其中一处必出事故**：比如只补 `cjk += n_cjk`，马上开始少数。应整体补齐：

```python
                if ent is not None and ent[0] == st.st_mtime_ns:
                    n_cjk = int(ent[1])
                else:
                    try:
                        _, body = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
                    except OSError:
                        continue
                    n_cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
                    new_cache[rel] = [st.st_mtime_ns, n_cjk]
                cjk += n_cjk
```

以及未命中且 cjk_cache 存在的条目也要原样带入 `new_cache`（文档还在树里但本轮没遍历到的边角可接受丢弃，重新扫一次即回填——建议加注释说明这个语义）。另注意：`p.suffix != ".md"` 的 `continue` 会把缓存里已无对应文档的旧键静默丢弃，属可接受的自愈行为，同样值得注释一句。

## P2-3 治理页自动扫描违反自己的设计纪律

- `routes_pages.py::governance` docstring：“全库扫描有成本……**不做成进页面就自动跑**，用户点按钮 → /api/governance/scan 取数”
- `governance.html` 模板注释：“进页面不自动扫描（全库扫描有成本），点按钮才跑”
- `governance.js::init()`：`scan(); // 进页面即扫一次` ← **三者中它是少数派，且是执行者**

每次打开 `/governance` 都会全库开 FTS + 建 `LearnStore._suggest_pool()` 候选池 + 标签普查。实测当前规模（4283 链接）成本尚可，但这是明确的意图违背，语料翻倍后页面打开会先卡一次。要么删掉 `init()` 里的 `scan()`，要么改文档承认现状——不能留着互相矛盾的三处注释。

## P2-4 断链批量处置匹配不到变体写法

FTS 提取正则 `!?\[\[([^\[\]|#]+)(?:#...)?(?:|...)]]` 存入的 `raw` 是**剥掉别名/锚点后的目标名**。而 `batchDead()` 预览与替换都用字面量拼接：

```js
text.indexOf("[[" + raw + "]]")            // 预览匹配
newText.split("[[" + raw + "]]").join(...) // 替换
```

原文若写的是 `[[目标|显示名]]`、`[[目标#节]]` 或 `![[目标]]`，该断链**永远匹配不到** → 预览计 0 → toast「在原文中未找到（可能已被修改）」，用户误以为已修好或数据过期，实际断链原样躺在文里。治理页的招牌处置功能对带别名断链无效。建议改用与提取端同源的正则做替换（注意转义 raw 中的正则元字符），并在替换后重新跑 wikilink_check 确认 resolved。

## P3 杂项清单

1. `routes_stats.py` 本次新增导入的 `SQLITE_BUSY_TIMEOUT_S` 全模块未使用（ruff `F401` 被显式 ignore，故 lint 不报）。
2. `routes_stats.py` 文件尾丢了换行符（diff 里 `\ No newline at end of file`）。
3. pre-commit 钩子只跑 smoke，**不跑 ruff** —— 而 ruff.toml 自述定位就是“回归安全网（F821 未定义名/F841 赋值未使用）”，本次两个 P0 恰好都是它声称要拦的类型。建议钩子加一行 `$PY -m ruff check . || exit 1`。
4. `tests/test_govern.py` 对 `/api/globalstats` 的双链字段与 `_corpus_agg` 字数**零断言**（全库 grep 无 matches）→ P0-1/P0-2 对测试网完全透明。建议补：建库→读 stats→断言 `links.total == links 表 count(*)`。
5. 前端契约核对无误：`KB.util.docUrl/rawUrl`、`KB.overlay.open({initialFocus})`、`i-localhost-shield/i-folder/i-folder-open/i-archive-box` 符号均存在；`tag_census/find_similar_tags/_top_suggestion/LearnStore.close` 后端函数签名与调用一致。
6. `app.js:669` 有 1 个存量 ESLint error（`no-misleading-character-class`），非本次改动引入。
7. `content/小说/` 仍在盘上（大量 txt/epub），但 taxonomy 已无小说域、`index.md` 在工作区被删——若是有意下架，建议把目录一并迁出 `content/`（它会被备份脚本长期携带）；`content/ai-assets/测试.md` 的删除同理未提交。
8. 仓库根目录散落 8 个 `image*.png` 上传残留 + `output/`、`.spark/` 未跟踪目录，建议清理或补 `.gitignore`。
9. ⚠️ 非代码问题但顺带提醒：`_local_env.bat` 内含明文 API key（已被 gitignore，未入库，保持现状即可；建议确认该 key 无其他暴露渠道）。

## 过程建议（防复发）

1. 本次两个 P0 属同一类型：**重构动了导入面/数据面，但消费端没同步 + `except Exception: pass` 把笔误降级成静默错数**。宽捕获只应包 IO，不应包 NameError/TypeError 级别的编程错误。
2. 磁盘缓存这类“修好前后数字必须一致”的重构，加一个等价性断言测试最便宜：同一语料分别走全量路径与预置缓存路径，`total_cjk` 必须相等。
3. 治理页三处注释两个口径（自动扫 vs 手动扫），代码评审时以“哪份文档在撒谎”为检查项。

## 验证命令备忘

```powershell
# 静态
ruff check app                        # F821 routes_stats.py:174 / F841 routes_stats.py:95
# 运行时（Python313 有 flask）
& 'C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe' -X utf8 .cowork-temp\repro.py
# 回归现状（全绿——这正说明测试网有洞）
python tests\test_govern.py
```

---

## 修复记录（同日 13:30，均已验证）

| # | 处置 | 验证结果 |
|---|------|----------|
| P0-1 | 恢复 `open_db` 模块级导入（治理函数内两处惰性导入同步删除）；`except Exception` 收窄为 `except (sqlite3.Error, OSError)` | `/api/globalstats` 实测返回 `links: {total: 4283, dead: 1, dead_docs: 1}`，与 FTS 实况一致 |
| P0-2 | 命中分支补 `cjk += n_cjk`；两分支统一回填 `new_cache[rel]`（全量重建视图，树上消失文档自愈式掉出） | 首轮落盘 `stats_cjk.json`（685 条）；二轮全命中重算总字数分毫不差（1,210,873）、缓存不再被清空；改单文件 mtime 后仅该篇重算且条目刷新 |
| P2-3 | `governance.js init()` 删除自动 `scan()`，与后端 docstring/模板空态口径归一（按钮唯一触发点） | 页面 200，空态正常 |
| P2-4 | 新增 `escapeRe`/`linkRe`：匹配 `[[raw]]`/`[[raw#锚点]]`/`[[raw\|别名]]`/`![[raw\|别名]]`；tplain 转纯文本保留别名、remove 整体删除 | node 实测：四种变体全命中；`[[BX]]`/`[[A前缀]]` 不误匹配；raw 含正则元字符（`C++(x)`）正确转义 |
| P3-1 | 移除未用导入 `SQLITE_BUSY_TIMEOUT_S` | ruff 全仓 `All checks passed` |
| P3-2 | 补文件尾换行 | — |
| P3-3 | pre-commit 钩子新增 `$PY -m ruff check .`（拦截在 smoke 之前） | 本次提交即经新钩子验证 |
| P3-4 | `test_govern.py` 新增 `test_globalstats_links_and_cjk_cache`：临时语料夹具断言双链计数与 links 表一致 + 缓存落盘/命中无损 | 新增用例绿；reader 74 / learn 208 存量全绿；eslint --quiet 0 error（含顺手修的 app.js:669 `^(?:⚠\uFE0F?|❗)` 变体字符类） |
| P3-8 | `.gitignore` 追加 `/image*.png`、`/output/`、`/.spark/`（保留原有条目，仅尾部合并） | 根目录截图不再出现在 git status |
| 未动 | P3-7 `content/小说/` 目录迁移（涉及大批个人文件位置变动）与仓库根 8 张 png 的物理删除，留待用户决定 | — |

修复后所有改动位于工作区未提交状态（与治理功能 WIP 同文件交叠，不适合拆单提交），待浏览器实测 /stats 弹窗与 /governance 页后一并入库。

---

## 追加：设置面板 ESC「幽灵弹窗」（同日 13:40，用户实测报新 bug）

**现象**：点齿轮设置 → 点任意空白 → 按 ESC，凭空多出一个居中弹窗（命令面板）；而齿轮 → 直接 ESC 却正常关闭。

**真相**：「新弹窗」不是新弹窗 —— 设置面板本就复用命令面板（`#kb-palette` 的 `readpref` 模式，代码注释「不另起一套弹层」），居中是命令面板的固有布局。三个缺陷叠加后 ESC 把它「变身」成了命令列表：

1. 遮罩 `data-close="1"` 是孤儿契约 —— 全仓无任何处理器消费（搜索浮层有同款逻辑，面板漏接），点空白关不掉面板，只把焦点甩到 BODY；
2. ESC 双通道重复消费：document 捕获层（keys.handle）与 input 的 keydown 各处理一次。焦点在输入框时：捕获层先「退回命令列表」、input 再「关闭」→ 恰好正常（场景 1 的巧合）；焦点在 BODY 时只剩前半→ 面板原地变身命令列表常驻（场景 2 的幽灵弹窗）；
3. 齿轮入口的 ESC 本就不该有「退回命令列表」语义 —— 用户从未请求过那个视图。

浏览器实测复现链：齿轮→ESC = 关（双处理器巧合）；齿轮→点遮罩（open 仍 true，focus=BODY）→ESC = mode 变 palette 且 show 保持 true。

**修复**（`static/kb-core.js`）：

1. 新增 `palEscape(e)` 统一收口 + 事件级去重（`__kbPalEsc`），捕获层与 input 两处共用，行为不再随焦点漂移；
2. 新增 `palette.viaSettings` 来源标记：齿轮打开 → ESC 直接关；从命令面板执行「阅读偏好」进入 → ESC 退回命令列表（保留原回退语义的唯一合理场景）；
3. 接通遮罩 `data-close` 点击→关闭，点空白处即关面板。

**验证**（浏览器实测，合成事件 + CDP 真实按键双路径）：齿轮→ESC 关；齿轮→点遮罩立即关、再 ESC 无幽灵；命令面板→阅读偏好→ESC 回列表→ESC 关；eslint 0 error、ruff 全仓通过。
