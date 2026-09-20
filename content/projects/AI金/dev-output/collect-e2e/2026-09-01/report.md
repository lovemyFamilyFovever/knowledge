# 采集标注端到端 Bug 排查报告（2026-09-01）

- 通过 27 · 失败 0 · 共 27

## 用例明细
| 域 | 用例 | 结果 | 详情 |
|---|---|---|---|
| article | 2.1 提交返回非重复 | PASS | status=pending id=6d5648b8-76ea-4623-ab9f-fc6fe8f36d88 |
| article | 2.1 相同正文二次提交判为重复 | PASS | status=duplicate |
| article | 2.2 路由为事件且 mvp | PASS | route=event conf=0.95 |
| article | 2.2 抽取产出事件 draft | PASS | ok=true records=1 |
| article | 2.4 缺必填字段被硬拦截 | PASS | 审核硬拦截：必填字段为空（summary）；必填字段为空（category）；必填字段为空（sub_category）；判断类字段未确认（impact_level）；判断类字段未确认（impact_direction） reasons=[{"rule":"必填字段为空","field":"summary","detail":"summary 为必填项"},{"rule":"必填字段为空","field":"category","detail":"category 为必填项 |
| article | 2.5 跳过 -> skipped | PASS | status=skipped |
| article | 2.5 放弃 -> rejected | PASS | status=rejected |
| article | 2.6 工作台队列可读 | PASS | total=50 |
| article | 2.7 库存路由判定 | PASS | 已路由为 data_inventory |
| article | 2.7 改判事件后可抽取 | PASS | status=pending_extract |
| price | 3.1 新建报价 mode=insert | PASS | mode=insert |
| price | 3.1 同维度再报当日覆盖 mode=update | PASS | mode=update |
| price | 3.2 多条件查询命中 TST 行 | PASS | total=1 |
| price | 3.3 老平台表头别名导入成功 | PASS | inserted=1 updated=0 failed=0 |
| price | 3.4 重复导入同维度走覆盖 | PASS | inserted=0 updated=2 failed=0 |
| dict | 4.0 词典表清单可读 | PASS | tables=18 |
| dict | 4.1 新增 TST 词条 | PASS | TST-市场-1788280648678 => {"ok":true,"table":"dict_market","name":"TST-市场-1788280648678"} |
| dict | 4.1 修改词条无异常 | PASS |  |
| dict | 4.2 删除无引用词条成功 | PASS |  |
| dict | 4.3 刷新词典缓存 | PASS | {"grades":["304/NO.1","304","201J1","304/2B","201J3","316L","201J4","316L/2B","2 |
| dict | 4.4 未管理的词典表应拒绝 | PASS | 未管理的词典表：dict_not_exist |
| content | 5.3 skill 读取不报 Failed query | PASS | styles=["brief","daily_review","deep"] |
| content | 5.1 空素材付印应拒绝(E5001) | PASS | E5001 参数缺失：record_ids 素材列表不能为空 |
| source | 6.1 来源列表含系统默认项 | PASS | count=6 |
| source | 6.1 新增自定义来源 | PASS | id=0e60c340-11b5-4010-b5d0-e2a0740c76ef |
| source | 6.1 删除自定义来源成功 | PASS |  |
| source | 6.1 系统默认项不可删（受保护） | PASS |  |

## 候选 Bug
- 无