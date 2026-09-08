---
tags: [AI资产, 提示词]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "artificialIntelligence/program-prompt.md"
---

# 开发项目提示词

想让AI一次性改完所有需求不出错，需要从**任务组织方式、验证机制、防错策略**三个维度设计提示词。以下是完整方案。

## 一、任务拆解与编排

AI容易出错的核心原因是任务太多、上下文太长。需要用**分阶段、自验证、原子化**的方式组织提示词。

### 最佳的"一次性"提示词结构

```
【项目快照】→ 【执行清单】→ 【逐项实施】→ 【自检清单】→ 【修复循环】
```

## 二、直接可用的超级提示词模板

### 模板：全流程自验证优化


```txt

使用提问的方式帮助我确认需求
不要猜测我的意图
不明确的地方必须向我提问

```


```
===== 项目优化全流程 =====

【阶段0：项目快照生成】
在执行任何修改前，先生成项目快照：

1. 列出当前src/目录的完整文件树
2. 记录package.json的所有依赖及版本
3. 记录vite.config.ts的当前配置
4. 记录tsconfig.json的compilerOptions

这些信息将作为回滚依据，在任意步骤失败时使用。

---

【阶段1：执行清单确认】
我将要执行以下优化任务，请生成序号化的执行清单：

[ ] 任务1：优化 LazyImage.vue（8项子任务）
[ ] 任务2：创建 performanceMonitor.ts
[ ] 任务3：创建 PerformanceDashboard.vue
[ ] 任务4：创建 benchmark.ts
[ ] 任务5：更新 vite.config.ts（分包+压缩）
[ ] 任务6：更新 tsconfig.json（如需要）
[ ] 任务7：创建测试文件
[ ] 任务8：更新 package.json（新增依赖）

每个任务完成后立即自检，通过才进入下一个。

---

【阶段2：逐项实施】
对每个任务，按以下格式执行：

━━━ 任务X：[任务名] ━━━
📝 修改文件：[文件路径]
📋 修改类型：[新增/修改/删除]
⚠️ 影响范围：[列出会被影响的其他文件]
✅ 自检方式：[具体检查命令或方法]

[此处输出完整代码]

🔍 自检结果：
- TypeScript编译：通过/失败
- ESLint检查：通过/失败
- 类型安全：通过/失败
- 文件引用：所有import路径存在
- 功能完整：所有子任务已完成

---

【阶段3：全局自检】
所有任务完成后，执行全局自检：

□ 文件引用检查：逐行扫描所有import语句，确认目标文件存在
□ 类型导出检查：所有被导入的类型/函数都已export
□ 组件注册检查：所有使用的组件已注册或导入
□ 生命周期完整性：所有onMounted配对onUnmounted清理
□ 事件监听清理：所有addEventListener配对了removeEventListener
□ 定时器清理：所有setInterval/setTimeout在onUnmounted中清除
□ Observer清理：所有IntersectionObserver/MutationObserver已disconnect
□ URL清理：所有createObjectURL配对了revokeObjectURL
□ 依赖冲突检查：新依赖与现有依赖无版本冲突
□ 浏览器兼容性：所用API的最低浏览器版本标注

---

【阶段4：编译与修复】
执行以下验证命令，遇到错误自动修复：

1. npx vue-tsc --noEmit
   → 如有类型错误，逐行分析并修复
   → 重新执行直到通过

2. npm run build
   → 如有构建错误，分析错误信息并修复
   → 重新执行直到通过

3. npx eslint src/ --ext .vue,.ts
   → 如有lint错误，逐条修复
   → 重新执行直到通过

4. npm run test（如配置了vitest）
   → 如有测试失败，分析失败原因并修复
   → 重新执行直到通过

5. npx depcheck
   → 检查是否有多余或缺失的依赖
   → 自动补全或清理

6. 最终确认：
   - dist/目录已生成
   - 构建产物大小与预期一致
   - 无控制台警告
```

## 三、让AI深度自检的额外命令

除了 `npm run build/dev`，以下命令能让AI更全面地验证代码：

### 1. TypeScript深度检查

```
# 严格模式类型检查（比build更严）
npx vue-tsc --noEmit --strict

# 检查未使用的变量和导入
npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters

# 跳过node_modules的类型检查（更快）
npx vue-tsc --noEmit --skipLibCheck
```

在提示词中加入：
```
完成后执行：npx vue-tsc --noEmit --strict
要求：零错误。如果报错，逐文件分析并修复，不得使用@ts-ignore或as any规避。
```

### 2. ESLint全面扫描

```
# 扫描所有文件，尝试自动修复
npx eslint src/ --ext .vue,.ts,.js --fix

# 输出格式化的错误报告
npx eslint src/ --ext .vue,.ts --format json > lint-report.json

# 检查是否有禁用注释（eslint-disable）
npx eslint src/ --ext .vue,.ts --report-unused-disable-directives
```

在提示词中加入：
```
完成后执行：npx eslint src/ --ext .vue,.ts --report-unused-disable-directives
要求：零错误零警告。禁用注释和any类型必须逐一说明原因。
```

### 3. 依赖分析

```
# 检查缺失/多余的依赖
npx depcheck

# 检查依赖是否有已知漏洞
npm audit

# 分析包体积
npx vite-bundle-visualizer

# 检查循环依赖
npx madge --circular --extensions ts,vue src/
```

在提示词中加入：
```
完成后执行：
1. npx depcheck → 如有缺失依赖，自动安装；多余依赖，确认后删除
2. npm audit → 如有高危漏洞，自动npm audit fix
3. npx madge --circular src/ → 如有循环引用，重构解除
```

### 4. 运行时验证

```
# 构建预览（模拟生产环境）
npm run build && npm run preview
# 然后检查preview的控制台是否有错误

# 性能分析
npx lighthouse http://localhost:4173 --output html --output-path ./lighthouse-report.html

# 检查是否有未捕获的Promise
# 在入口文件加入：
window.addEventListener('unhandledrejection', event => {
  console.error('未捕获的Promise拒绝:', event.reason);
});
```

在提示词中加入：
```
完成后执行：npm run build && npx serve dist -p 4173
在浏览器控制台运行以下检查：
- 检查是否有红色报错
- 检查是否有黄色警告（特别是deprecation warning）
- 执行：document.querySelectorAll('img').forEach(img => console.log(img.complete, img.naturalWidth))
  确认所有图片加载状态正常
- 刷新页面10次，确认无偶发性白屏或报错
```

### 5. 组件级单元测试

```
# 运行组件测试
npx vitest run

# 带覆盖率的测试
npx vitest run --coverage

# 只跑改动的文件相关测试
npx vitest run --changed
```

## 四、防错保底的提示词技巧

### 技巧1：预检清单

```
在生成代码前，先回答以下问题：
1. 我是否完全理解了需求？（用一句话复述）
2. 需要修改哪些文件？（列出完整路径）
3. 每个文件的修改会影响哪些其他文件？
4. 新增的依赖是否与现有依赖兼容？
5. 是否有更简单的实现方式？

确认后再开始生成代码。
```

### 技巧2：沙箱化修改

```
对每个文件的修改遵循以下规则：
1. 使用 --- 分隔线明确标注修改区域
2. 用 // [OPTIMIZATION] 注释标记新增代码
3. 用 // [KEPT] 注释标记未改动的原有代码
4. 不允许删除任何现有代码，除非明确标注 // [REMOVED] 并说明原因
```

### 技巧3：回滚机制

```
在每次修改文件前，生成对应的 .backup 版本：
1. 记录修改前的完整内容
2. 如果后续验证失败，提供回滚到 .backup 版本的方法
3. 所有优化完成后，提供清理 .backup 文件的命令
```

### 技巧4：断言式验证

```
生成代码后，为每个功能点生成一条验证断言：

- "LazyImage组件在挂载时必须创建IntersectionObserver" → 代码中包含 new IntersectionObserver
- "组件卸载时必须disconnect" → onUnmounted中包含 observer.disconnect()
- "并发控制不超过4" → 代码中loadingCount <= 4的判断存在

逐条检查所有断言是否成立，不成立的立即修复。
```

## 五、终极版"一键搞定"提示词

```
你是Vue3全栈工程师。执行以下优化任务，要求零错误完成。

【项目信息】
- 框架：Vue3 + Vite + TypeScript
- 包管理：npm
- 测试框架：vitest（如有）

【任务清单】
1. 优化图片懒加载（8项子任务：IntersectionObserver、预设宽高、并发控制、GPU加速、节流、createImageBitmap、ObjectURL管理、性能监控）
2. 建立性能监控系统（monitor + dashboard + benchmark）
3. 配置生产构建优化（分包 + 压缩）
4. 编写自动化测试（7项断言）

【执行规则】
- 逐项执行，每完成一项输出 "[任务名] ✅ 已完成"
- 遇到任何编译错误立即修复，不得跳过
- 所有修改必须保留原有功能
- 不使用 any 类型，不使用 @ts-ignore

【验证流水线】（全部通过才算完成）
Step 1: npx vue-tsc --noEmit --strict
Step 2: npx eslint src/ --ext .vue,.ts
Step 3: npm run build
Step 4: npx depcheck
Step 5: npm audit
Step 6: npm run test（如有）
Step 7: 检查dist大小是否符合预期

【最终交付】
1. 所有修改文件的完整代码
2. 验证结果截图（每条命令的输出摘要）
3. 性能对比表格
4. 新增依赖清单及用途说明
```

这个提示词让AI像执行CI/CD流水线一样工作，每步都验证，出错即修，最终保证一次性通过。你只需要把具体项目信息填进去即可。