# 10. 秀吗数据每日导入 SOP（手动操作指引）

> 最后更新：2026-08-17
> 适用：AI金 配单数据源的每日维护
> 核心原则：**数据全部从秀吗 ERP 后台手动导出 → AI金「秀吗数据导入」上传**，不调任何接口、不连数据库、不碰服务器文件
>
> 作者：刘相辰
>
> **导入频率简化（2026-08-17 与秀吗侧核实后确认）**：
> | 数据 | 频率 | 触发条件 |
> | --- | --- | --- |
> | 货品文件 | **每天必导** | 日常唯一必导数据 |
> | PRODUCT_ID 映射 | 按需 | 货品文件出现新货品编码（XH 开头）时补一次 |
> | 供应商联系方式 | 基本不用 | 仅供应商电话变更时 |
> | 会员联系方式 | 基本不用 | 仅想补齐缺电话货品时（现有 91 条） |

---

## 一、为什么需要每日导入

AI金 配单展示的货品数据存在本地快照表 `xiuma_product_snapshot`（约 3000 条上架现货）。秀吗平台每天会有货品上下架、价格变动、新增挂单，需要**每天同步一次**，让 AI金 展示的数据跟上秀吗实际状态。

- 展示过期可接受：成交回秀吗下单，秀吗自己校验库存，AI金 数据最多"滞后一天"
- 失败可重试：当天没导成功，第二天再导一次即可

---

## 二、每日操作流程（约 5 分钟）

### 第 1 步：秀吗 ERP 导出货品数据

1. 浏览器登录秀吗 ERP：`https://xiuma.com/erp/`
2. 左侧菜单依次展开：**ERP → 基础信息 → 产品信息 → 卷板—信息**
3. 页面打开后，**直接点"下载结果"**按钮（不需要手动筛选，默认导出全部上架现货）
4. 浏览器下载得到文件，重命名为 `product_info_YYYYMMDD.xlsx`（例：`product_info_20260816.xlsx`）

> 如果记不清菜单位置，页面 URL 是：
> `https://xiuma.com/erp/modules/erp/product_information/product_info.aspx`

### 第 2 步：登录 AI金 ERP

1. 打开 AI金 平台 ERP 地址（你的主站 + `/erp`）
2. 登录后左侧菜单找到：**系统管理 → 秀吗数据导入**

### 第 3 步：上传货品文件

1. 在「秀吗数据导入」页面的 **"货品文件"** 卡片处，选择刚下载的 `product_info_*.xlsx`
2. 点击上传，页面顶部出现提示：`货品导入完成: 成功 N 条`
3. 查看页面顶部的统计卡片：
   - **快照总数** = 当前库中货品总数
   - **有效货品** = 上架中的货品数
   - **最近同步** = 本次导入时间

### 第 4 步：核对结果（可选但建议）

确认「最近同步」显示的是刚才的时间，且「快照总数」数量级正确（约 3000 左右，无异常暴增/骤降）。

> ⚠️ **新增货品检查（2026-08-17 新增）**：导入后在列表里抽查是否有**新货品编码**（此前没见过的 XH 开头编码）。
> 日常货品文件不含 PRODUCT_ID，新货品入库后 product_id 为空，会导致**无法跳转秀吗详情、无法联系绑定成交**。
> 发现新货品 → 跑一次第五节的 ERP 导出脚本，上传「PRODUCT_ID 映射」补全；没有新货品则无需任何额外操作。

> 上传是**增量合并**：秀吗已下架的货品在 AI金 里不会自动消失（除非数量归零被后续处理），短期影响可忽略。如需精确下架同步，后续可再补充对账功能。

---

## 三、首次/大版本导入（重导全量）

如果快照表数据异常、或长时间未同步需要重建：

1. 秀吗 ERP 导出全量货品（同上第 1 步）
2. AI金「秀吗数据导入」上传货品文件即可（**全量覆盖式合并**，不会重复）
3. 如需恢复 PRODUCT_ID / 联系方式 / 城市等增强字段，见第四节

---

## 四、增强字段补充（非每日，按触发条件）

首次全量导入时增强字段已补齐，日常**仅在以下触发条件出现时**才需操作（2026-08-17 简化）：

| 字段 | 触发条件 | 操作 |
| --- | --- | --- |
| PRODUCT_ID | ① 清库重建；② **货品文件出现新货品编码** | F12 控制台跑第五节脚本 → 上传「PRODUCT_ID 映射」 |
| 联系方式/会员等级 | 清库重建 / 供应商电话变更 | 导出 CSV（见 09 文档）→「供应商联系方式」上传 |
| 城市/省份 | 清库重建 | 秀吗数据库只读 SQL（见 09 文档），联系开发协助回填 |
| 会员联系方式（用户表） | 想补齐缺电话货品（现有约 91 条） | member_contact.aspx 导出 →「会员联系方式」上传（自动回填，主联系人优先） |

> ⚠️ 城市/省份目前**不走 ERP 上传界面**（上传界面只有货品/映射/联系方式/会员联系方式四类，城市是开发导入）。若重建，联系开发协助。

### 会员联系方式（用户表）说明

- 来源：秀吗 ERP **CRM → 会员联系方式**（`member_contact.aspx`），下载结果含：公司全称/联系人编号/名称/职位/固定电话/移动电话/主联系人/决策人/信息状态/备注/创建时间
- 导入后存 `xiuma_member_contact` 表（一个公司多个联系人 = 多行）
- **自动回填**：货品导入后，按供应商名自动从用户表补齐缺失电话，**主联系人优先**（固定电话 > 移动电话）
- ⚠️ **注意事项**：
  1. 秀吗**新增客户/新增电话**不会自动出现在 AI金——需要重新导出 member_contact 文件上传一次
  2. 一条货源可能对应多个联系人，回填只取**主联系人**的电话；若该供应商无主联系人，取第一条有电话的联系人
  3. 已有电话的货品**不会被覆盖**（回填只补缺失）

---

## 五、ERP 导出脚本（含 PRODUCT_ID）

日常"下载结果"导出的文件**不含 PRODUCT_ID**（PRODUCT_ID 是页面隐藏列）。当需要补 PRODUCT_ID 映射时（如清库重建、新货品），用以下脚本从 ERP 后台导出。

> 脚本保存于项目 `scripts/xiuma-erp-export-with-id.js`，与本文档内容一致。

### 使用步骤

1. 浏览器登录秀吗 ERP，打开**「ERP → 基础信息 → 产品信息 → 卷板—信息」**
2. 按需筛选后点"查询"，确保表格有数据
3. 按 `F12` 打开开发者工具 → 切到 **Console（控制台）**
4. 粘贴下面的脚本 → 回车
5. 脚本会：
   - 自动定位正确的 iframe 窗口（ERP 是 iframe 结构）
   - **先查总数并校验**（上架现货约 3000 条；若返回 86 万说明筛选未生效会中止，不会误导出几十万条）
   - 自动下载 `product_info_with_id_YYYYMMDD.csv`（含 PRODUCT_ID 列）
6. 把该 CSV 整理为两列（`product_code` / `product_id`）或在 AI金「秀吗数据导入」→「PRODUCT_ID 映射」直接上传

> 脚本只从页面自己的查询接口读数据（与页面"查询"按钮完全一致，走当前登录态），**不修改任何代码、不连数据库**。

### 脚本代码

```javascript
(function () {
  var PAGE_STEP = 10000;
  var MAX_PAGES = 10;

  function pad(n) { return n < 10 ? '0' + n : String(n); }
  function nowStr() {
    var d = new Date();
    return d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate());
  }
  function esc(v) {
    if (v == null) return '';
    var s = String(v);
    if (/[",\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
    return s;
  }

  function findTargetWindow() {
    var visited = new Set();
    var candidates = [];

    function collect(win) {
      if (!win || visited.has(win)) return;
      visited.add(win);
      try {
        var path = win.location && win.location.pathname ? win.location.pathname : '';
        var isProductPage = /product_info\.aspx/i.test(path);
        var hasQueryObj = typeof win._query_obj !== 'undefined';
        var hasZERP = !!(win.ZERP && win.ZERP.AJAX && win.ZERP.AJAX.Call);
        if (isProductPage || hasQueryObj || hasZERP) {
          candidates.push({ win: win, path: path, isProductPage: isProductPage, hasQueryObj: hasQueryObj, hasZERP: hasZERP });
        }
      } catch (e) { }

      try {
        var frames = win.frames;
        for (var i = 0; i < frames.length; i++) collect(frames[i]);
      } catch (e) { }
    }

    var topWin = null;
    try { topWin = window.top; } catch (e) { topWin = window; }
    collect(topWin);
    if (!candidates.length) collect(window);
    if (!candidates.length) return null;

    candidates.sort(function (a, b) {
      var sa = (a.isProductPage ? 4 : 0) + (a.hasQueryObj ? 2 : 0) + (a.hasZERP ? 1 : 0);
      var sb = (b.isProductPage ? 4 : 0) + (b.hasQueryObj ? 2 : 0) + (b.hasZERP ? 1 : 0);
      return sb - sa;
    });

    console.log('[export] 找到候选窗口 ' + candidates.length + ' 个:');
    candidates.slice(0, 8).forEach(function (c, i) {
      console.log('  [' + i + '] ' + (c.isProductPage ? '★product页' : '') + (c.hasQueryObj ? ' _query_obj' : '') + (c.hasZERP ? ' ZERP' : '') + ' ' + c.path);
    });

    return candidates[0].win;
  }

  function callDoQuery(targetWin, pageNum) {
    var queryFilter = null;
    try {
      if (targetWin && targetWin._query_obj && targetWin._query_obj.GetQueryFilter) {
        queryFilter = targetWin._query_obj.GetQueryFilter();
        if (queryFilter && typeof queryFilter === 'object') queryFilter = JSON.parse(JSON.stringify(queryFilter));
      }
    } catch (e) { queryFilter = null; }

    if (!queryFilter || typeof queryFilter !== 'object') queryFilter = {};

    var NO_SELECT = '_no_select';
    var hasStatus = Object.prototype.hasOwnProperty.call(queryFilter, 'status') &&
      queryFilter.status !== null && queryFilter.status !== '' && queryFilter.status !== undefined &&
      String(queryFilter.status).trim() !== NO_SELECT;
    if (!hasStatus) {
      queryFilter['status'] = 0;
      console.log('[export] 页面未筛货品状态(或为请选择)，已自动补 status=0(上架)');
    } else {
      console.log('[export] 保留页面货品状态筛选: status=' + String(queryFilter.status));
    }
    console.log('[export] 使用筛选条件:', JSON.stringify(queryFilter));

    var param = {
      query_filter: queryFilter,
      query_option: {
        page_num: pageNum,
        page_step: PAGE_STEP,
        sort_on_column: 'CREATE_TIME',
        sort_direction: 1
      }
    };

    if (targetWin && targetWin.ZERP && targetWin.ZERP.AJAX && targetWin.ZERP.AJAX.Call) {
      return new Promise(function (resolve, reject) {
        targetWin.ZERP.AJAX.Call('do_query', function (code, msg, data) {
          if (code !== 0) { reject(new Error('do_query: ' + (msg || code))); return; }
          resolve(data);
        }, param, targetWin.location.pathname, true);
      });
    }

    return new Promise(function (resolve, reject) {
      var base = targetWin ? targetWin.location.pathname : window.location.pathname;
      var url = base + '?z_access_mode=web_service&ws_func=do_query';

      var sid = null;
      try {
        if (targetWin && typeof targetWin._PAGE_SESSION_ID !== 'undefined') sid = targetWin._PAGE_SESSION_ID;
        else if (typeof _PAGE_SESSION_ID !== 'undefined') sid = _PAGE_SESSION_ID;
      } catch (e) { }
      if (sid) url += '&session_page_id=' + sid;

      url += '&has_req_data=true&retry_num=0';

      var body = 'z_data=' + encodeURIComponent(JSON.stringify(param));
      var xhr = new XMLHttpRequest();
      xhr.open('POST', url, true);
      xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
      xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) return;
        if (xhr.status !== 200) { reject(new Error('HTTP ' + xhr.status)); return; }
        try {
          var r_dt = (window.myJSONparse || targetWin.myJSONparse)
            ? (window.myJSONparse || targetWin.myJSONparse)(xhr.responseText)
            : JSON.parse(xhr.responseText);
          if (r_dt.WS_RET_CODE !== 0) {
            reject(new Error('do_query: ' + (r_dt.WS_RET_MSG || 'code=' + r_dt.WS_RET_CODE)));
            return;
          }
          resolve(r_dt.WS_RET_DATA);
        } catch (e) { reject(e); }
      };
      xhr.send(body);
    });
  }

  function extractTable(wrap) {
    var dt = wrap && wrap.DataTable ? wrap.DataTable : null;
    if (dt && dt.Columns && dt.Columns.Count !== undefined) return dt;
    if (dt && Array.isArray(dt.Columns)) return dt;
    return null;
  }

  function downloadCSV(rows, columns) {
    var lines = [columns.map(esc).join(',')];
    for (var i = 0; i < rows.length; i++) {
      var line = [];
      for (var c = 0; c < columns.length; c++) line.push(esc(rows[i][columns[c]]));
      lines.push(line.join(','));
    }
    var csv = '\ufeff' + lines.join('\r\n');
    var fname = 'product_info_with_id_' + nowStr() + '.csv';
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = fname;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
    return { count: rows.length, fname: fname };
  }

  async function run() {
    var targetWin = findTargetWindow();
    console.log('[export] 目标窗口:', targetWin ? (targetWin.location.pathname) : '当前窗口');
    console.log('[export] 当前窗口:', window.location.pathname);
    if (!targetWin) {
      throw new Error('未找到 ERP 页面窗口。请确认：\n1) 你正停留在「卷板—信息」页面（不是左侧菜单树）\n2) F12 控制台切换到包含表格的 iframe 上下文\n3) 或把 location.href 发给我');
    }

    var SAFE_MAX = 50000;

    var firstWrap = await callDoQuery(targetWin, 0);
    var firstDt = extractTable(firstWrap);
    if (!firstDt) {
      console.log('[export] 响应结构:', Object.keys(firstWrap || {}));
      throw new Error('未从返回中找到 DataTable，请把上方输出发我排查');
    }
    console.log('[export] PageInfo 字段:', firstWrap.PageInfo ? Object.keys(firstWrap.PageInfo) : '(无)');
    console.log('[export] PageInfo 内容:', JSON.stringify(firstWrap.PageInfo).substring(0, 300));

    var total = firstWrap.PageInfo
      ? (firstWrap.PageInfo.total_records || firstWrap.PageInfo.total || firstWrap.PageInfo.TOTAL_NUM || firstWrap.PageInfo.TotalRecords || 0)
      : 0;
    var firstCount = firstDt.Rows ? firstDt.Rows.length : 0;
    console.log('[export] 首查: 返回 ' + firstCount + ' 行, 总数=' + total);

    if (total > SAFE_MAX) {
      throw new Error('查询总数为 ' + total + ' 条，超出安全上限 ' + SAFE_MAX + '。\n说明"货品状态=上架"筛选未生效（可能导出了全部历史现货）。\n请检查控制台上方"使用筛选条件"输出，确认 status=0 已带上。');
    }
    if (total > 0 && firstCount === 0) {
      throw new Error('查询总数为 ' + total + ' 但首页无数据，分页逻辑异常，请排查');
    }
    console.log('[export] 总数 ' + total + ' 在安全范围，开始导出...');

    var allRows = [];
    var columns = null;

    if (firstCount > 0) {
      if (!columns) {
        columns = [];
        for (var i = 0; i < firstDt.Columns.length; i++) columns.push(firstDt.Columns[i].ColumnName);
        if (columns.length === 0 && firstDt.Columns.Count) {
          for (var j = 0; j < firstDt.Columns.Count; j++) columns.push(firstDt.Columns[j].ColumnName);
        }
      }
      for (var k = 0; k < firstCount; k++) allRows.push(firstDt.Rows[k]);
    }

    var needMore = firstCount >= PAGE_STEP;
    var page = 1;
    while (needMore && page < MAX_PAGES) {
      var wrap = await callDoQuery(targetWin, page);
      var dt = extractTable(wrap);

      if (!dt) {
        console.log('[export] 响应结构:', Object.keys(wrap || {}));
        throw new Error('第' + (page + 1) + '页未找到 DataTable，请把上方输出发我排查');
      }

      if (!columns) {
        columns = [];
        for (var i = 0; i < dt.Columns.length; i++) columns.push(dt.Columns[i].ColumnName);
        if (columns.length === 0 && dt.Columns.Count) {
          for (var j = 0; j < dt.Columns.Count; j++) columns.push(dt.Columns[j].ColumnName);
        }
      }

      var pageRows = dt.Rows || [];
      for (var k = 0; k < pageRows.length; k++) allRows.push(pageRows[k]);
      console.log('[export] 第' + (page + 1) + '页: 返回 ' + pageRows.length + ' 行, 累计 ' + allRows.length);

      needMore = pageRows.length >= PAGE_STEP;
      page++;
    }

    if (!columns) throw new Error('未能获取列名');
    if (columns.indexOf('PRODUCT_ID') < 0) {
      console.log('[export] 列清单:', columns);
      throw new Error('返回数据不含 PRODUCT_ID 列');
    }

    var r = downloadCSV(allRows, columns);
    alert('已导出 ' + r.count + ' 行（含 PRODUCT_ID）→ ' + r.fname);
  }

  run().catch(function (e) {
    console.error('[export] 失败:', e);
    alert('导出失败: ' + e.message + '\n（请把 F12 控制台的完整输出发给我排查）');
  });
})();
```

---

## 六、异常处理

| 现象 | 处理 |
| --- | --- |
| 上传提示"文件解析失败" | 确认导出的是**最新版** product_info.aspx 的下载结果，列结构完整 |
| 统计总数异常（远超 3000） | 可能导出了历史/全部记录，检查导出时页面是否被筛选了别的条件 |
| 统计总数骤降为 0 | 文件为空或表头缺失，重新导出 |
| 上传后页面没反应 | 刷新页面重新上传；仍不行联系开发查日志 |
| 会员联系方式上传后"联系人数"统计为 0 | 确认导出页面是 CRM→会员联系方式（member_contact.aspx），且文件含"公司全称"列 |
| 货品电话始终缺失 | 该供应商在会员联系方式文件里没有记录，或没有主联系人且无电话；重新导出最新文件上传 |

---

## 七、要点速查

- ✅ 每天：只导**货品文件**（秀吗导出 → AI金上传，约 5 分钟）
- ✅ 发现新货品编码：补一次 PRODUCT_ID 映射（第五节脚本）
- ✅ 其余三类数据：基本不用管，按第四节触发条件操作
- ❌ 禁止：调接口、连数据库、改服务器文件
- ❌ 不要：删除快照表数据、清空统计

---

## 八、关联文档

- `08-数据源改造与同步方案.md`：整体方案与代码位置
- `09-秀吗数据库取数SQL.md`：数据库取数 SQL 与增强字段来源
