# exempt-reference 清单（规范 v1.1 §5）

# 用途：登记「参考手册型」文件——正文 >70% 为代码/表格、价值就在逐条示例本身，
#      强行改写成 1def+2trap 单词条会毁掉内容。这类文件原样保留、不改 frontmatter、
#      不重写、不拆分；cards.py 因缺锚点自然不出卡，故无需机器门介入。
#
# 用法：python scripts/agent/check_rewrite.py <路径>...
#      check_rewrite 启动时读本清单，命中者打印 EXEMPT 并早退，不计 FAIL。
#      也可临时用 --exempt <路径> 单独豁免（可重复传）。
#
# 解析规则（见 check_rewrite.load_exempt）：空行与 # 开头行忽略；表格行取首列；
#      其余行去掉前导 ->* 与反引号后，仅接受以 .md 结尾的 token。
#      因此本文件所有说明都必须写在 # 注释行里，避免散文行尾出现 .md 被误当路径。
#
# 登记时须同步：在 docs/refactor/status/sN.md 把该篇状态改为 exempt-reference，
#      并在备注写明理由（>70% 代码/表格 + 为何不可改写）。
#
# 路径口径：一律写仓库根相对路径 content/baike/<子域>/<文件>.md。

content/baike/os/Linux 命令速查手册.md
