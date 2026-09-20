# Prompt Engineering最佳实践（完整版）

> ⚠️ 本文档内容基于 v2.3 架构编写，部分示例和模板引用"后端生成SQL"模式，与当前 v2.5.5（查询提示→百炼自主生成SQL）不一致。设计原则仍有参考价值，但具体示例请以 `bailian-app-system-prompt-v5.md` 为权威来源。

> 最后更新：2026-06-24
> v3.0架构：百炼Agent 2.0直通模式。v2.3的5步Pipeline相关章节仅作历史参考。

---



## 二、Prompt设计原则

### 2.1 核心原则

| 原则 | 说明 | 示例 |
|------|------|------|
| 明确角色 | 清晰定义AI的角色和能力边界 | "你是不锈钢行业智能伙伴" |
| 结构化输出 | 要求JSON格式输出 | "输出严格JSON格式" |
| 提供示例 | 给出Few-shot示例 | "Example 1: ..." |
| 约束行为 | 明确禁止和要求 | "不要编造数据" |
| 自我校验 | 要求输出前检查 | "输出前检查JSON格式" |
| 动态约束 | 根据意图选择约束模板 | QU01使用"SQL执行机器"约束 |

### 2.2 常见错误

| 错误 | 问题 | 改进 |
|------|------|------|
| 角色模糊 | AI不知道自己能做什么 | 明确角色和能力边界 |
| 输出格式混乱 | 返回自然语言而不是结构化数据 | 要求JSON格式 |
| 缺少示例 | AI不理解预期输出 | 添加Few-shot示例 |
| 约束不足 | AI编造数据或过度分析 | 添加明确约束 |
| 无自校验 | 输出格式错误 | 添加自校验规则 |
| 约束模板错误 | 使用错误的约束模板 | 根据intent_primary动态选择 |

---

---

## 四、工具调用Prompt设计

## 四、工具调用Prompt设计

### 4.1 工具选择Prompt

```
# 角色
你是不锈钢行业智能伙伴"AI金"。
你可以使用以下工具查询数据：

# 工具列表
1. get_price - 查询不锈钢价格
2. query_database - 查询市场数据（库存、产量等）
3. search_news - 搜索行业新闻
4. query_supplier - 查询供应商
5. knowledge_base - 检索知识库
6. predict - 预测价格走势
7. system_info - 系统信息查询
8. clarify - 澄清追问

# 工具选择规则
- 查询价格 → get_price
- 查询库存/产量 → query_database
- 查询新闻/资讯 → search_news
- 查询供应商 → query_supplier
- 查询知识 → knowledge_base
- 预测走势 → predict
- 平台功能 → system_info
- 信息不足 → clarify
```

### 4.2 工具调用Prompt

```
# 工具调用格式
{
  "name": "工具名称",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}

# 调用规则
1. 根据用户问题选择合适的工具
2. 从问题中提取参数
3. 缺失的参数使用默认值或追问
4. 多个工具可以并行调用
```

### 4.3 结果整合Prompt

```
# 结果整合规则
1. 基于工具返回的数据回答
2. 不要编造数据
3. 标注数据来源
4. 回答简洁，不超过200字
5. 语气专业、肯定
```

---

## 五、问答生成Prompt设计

### 5.1 角色定义

```
# 角色
你是不锈钢行业智能伙伴"AI金"。
你基于工具返回的数据，为用户提供专业、准确的回答。
```

### 5.2 回答规则

```
# 回答规则
1. 基于工具返回的数据回答，不要编造数据
2. 标注数据来源（如"根据51行情库数据"）
3. 回答简洁，不超过200字
4. 语气专业、肯定
5. 如果没有数据，明确说明"未找到相关数据"
6. 如果数据不足，说明"数据有限，仅供参考"
```

### 5.3 来源标注规则

```
# 来源标注规则
- 价格数据：标注"根据51行情库数据"
- 库存数据：标注"根据库存数据"
- 资讯数据：标注"根据行业资讯"
- 知识数据：标注"根据知识库"
- 供应商数据：标注"根据企业库"
```

---

## 六、Schema与业务字典注入

### 6.1 业务字典注入（v3.0简化）

```typescript
const businessDictionaryInjection = `
# 业务字典
## 钢种别名
- 304: 304, SUS304, 0Cr18Ni9
- 316L: 316L, SUS316L, 0Cr17Ni12Mo2
- 430: 430, SUS430, 1Cr17

## 区域别名
- 无锡: 无锡, 锡, 南方
- 佛山: 佛山, 佛冈, 南庄

## 市场别名
- 酒钢: 酒钢, JISCO
- 太钢: 太钢, TISCO
`;
```

---

## 七、多轮对话处理

### 7.1 步骤1-4：后端临时状态

v2.3架构中，步骤1-4使用后端临时状态管理多轮对话：

```typescript
interface ConversationState {
  sessionId: string;
  currentStep: number;
  aliasMap: AliasMap;
  quResult: QUResult | null;
  toolResults: ToolResult[];
  tempContext: {
    inheritedEntities: Entities;
    previousIntents: string[];
    clarificationHistory: ClarificationRecord[];
  };
}
```

### 7.2 步骤5：LLM原生上下文

步骤5使用LLM的原生上下文窗口处理多轮对话：

```typescript
// 将历史对话注入到Prompt中
const multiTurnPrompt = `
# 对话历史
${conversationHistory.map(turn => `
用户: ${turn.userQuery}
助手: ${turn.assistantResponse}
`).join('\n')}

# 当前问题
${currentQuery}

请基于对话历史和当前问题，生成回答。
`;
```

---

## 八、温度和参数设置

### 8.1 温度设置

| 场景 | 温度 | 原因 |
|------|------|------|
| 意图分类 | 0.1 | 需要确定性输出 |
| 实体抽取 | 0.1 | 需要确定性输出 |
| 工具选择 | 0.1 | 需要确定性输出 |
| 问答生成 | 0.7 | 需要一定创造性 |
| 创意写作 | 0.9 | 需要创造性 |

### 8.2 其他参数

```json
{
  "temperature": 0.1,
  "top_p": 0.8,
  "max_tokens": 2000,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

---

## 九、Prompt模板

### 9.1 工具调用Prompt模板

```
# 角色
你是{系统名称}，一个{领域}智能伙伴。

# 工具列表
{工具列表}

# 工具选择规则
{工具选择规则}

# 调用格式
{
  "name": "工具名称",
  "arguments": {...}
}

# 调用规则
1. {规则1}
2. {规则2}
3. {规则3}
```

### 9.3 问答生成Prompt模板

```
# 角色
你是{系统名称}，一个{领域}智能伙伴。

# 回答规则
1. 基于工具返回的数据回答，不要编造数据
2. 标注数据来源
3. 回答简洁，不超过200字
4. 语气专业、肯定

# 工具返回数据
{tool_context}

# 用户问题
{user_query}

请基于工具返回的数据，生成专业、简洁的回答。
```

---

## 十、QU01-对比分析特殊处理

### 10.1 两步执行流程

QU01-对比分析（如"酒钢和太钢304价格差多少"）采用两步执行：

```
第一步：价格对比查询
- 调用get_price查询酒钢304价格
- 调用get_price查询太钢304价格
- 计算价差

第二步：新闻搜索（可选）
- 如果用户问"为什么差这么多"
- 调用search_news搜索相关原因
```

### 10.2 实现逻辑

```typescript
async function handleQU01Comparison(quResult: QUResult) {
  // 第一步：价格对比
  const priceResults = await Promise.all([
    executeTool('get_price', quResult.routing_params.price1),
    executeTool('get_price', quResult.routing_params.price2)
  ]);
  
  const priceDiff = calculatePriceDifference(priceResults);
  
  // 第二步：新闻搜索（如果需要）
  if (quResult.sub_intent === '价差原因分析') {
    const newsResults = await executeTool('search_news', {
      keyword: `${quResult.entities.grade} 价格差异`
    });
    return formatComparisonResult(priceDiff, newsResults);
  }
  
  return formatComparisonResult(priceDiff);
}
```

---

## 十一、调试技巧

### 11.1 问题定位

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 输出格式错误 | Prompt约束不足 | 添加格式约束和自校验 |
| 意图分类错误 | 示例不足 | 增加Few-shot示例 |
| 实体抽取错误 | 词典不全 | 扩充实体词典 |
| 回答不准确 | 工具数据不足 | 优化工具查询 |
| 幻觉问题 | 约束不足 | 添加约束，要求基于数据回答 |
| 约束模板错误 | intent_primary判断错误 | 检查意图分类逻辑，确认动态模板选择 |

### 11.2 优化迭代

1. **收集Bad Case**：记录AI回答错误的问题
2. **分析原因**：分析是Prompt问题还是工具问题
3. **优化Prompt**：根据分析结果优化Prompt
4. **验证效果**：用测试集验证优化效果
5. **重复迭代**：持续优化直到达到目标

### 11.3 调试命令

```bash
# 测试意图分类
curl "http://localhost:3000/api/ai/chat?question=304价格多少&mode=fast"

# 测试工具调用
curl "http://localhost:3000/api/ai/chat?question=304库存多少&mode=expert"

# 测试多轮对话
curl "http://localhost:3000/api/ai/chat?question=那304呢&mode=fast"

# 测试对比分析（v2.3两步执行）
curl "http://localhost:3000/api/ai/chat?question=酒钢和太钢304价格差多少&mode=expert"
```

---

## 十二、最佳实践总结

### 12.1 Prompt设计清单

- [ ] 角色定义清晰
- [ ] 输出格式明确（JSON）
- [ ] 有Few-shot示例（作为独立KB挂载）
- [ ] 有约束规则（禁止/要求）
- [ ] 有动态约束模板（根据intent_primary选择）
- [ ] 有自校验规则
- [ ] 温度设置合理（0.1-0.7）
- [ ] 有边界处理规则
- [ ] Schema和业务字典已注入
- [ ] 置信度处理逻辑正确

### 12.2 常见优化点

| 优化点 | 方法 |
|--------|------|
| 提高准确率 | 增加Few-shot示例 |
| 减少幻觉 | 添加约束，要求基于数据回答 |
| 提高一致性 | 降低温度 |
| 处理边界 | 添加边界处理规则 |
| 减少冗长 | 限制回答字数 |
| 优化动态约束 | 根据intent_primary选择正确模板 |

### 12.3 注意事项

1. **不要过度设计**：Prompt应该简洁明了
2. **不要遗漏边界**：考虑异常情况
3. **不要忽略测试**：用测试集验证效果
4. **不要忘记迭代**：持续优化直到达到目标
5. **不要忽略alias_map**：Step 2生成的别名映射必须传递给QU

---

## 十三、下一步操作

了解Prompt Engineering后，请继续阅读：
- [10-常见问题与避坑指南](./10-常见问题与避坑指南.md)
