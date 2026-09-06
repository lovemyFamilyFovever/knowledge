---
title: "SaaS产品技术架构"
tags: []
source: "baike"
source_path: "技术文章 / 架构与设计"
collected: "2026-09-05"
status: "imported"
---

# SaaS产品技术架构

# SaaS产品技术架构指南

## 1. SaaS架构模式

### 1.1 单租户架构（Single-Tenancy）

**定义**：每个租户拥有独立的基础设施实例，包括独立的数据库、应用服务器等。

**优势**：
- 完全隔离：数据完全分离，安全性最高
- 定制灵活：每个租户可独立升级和定制
- 合规友好：满足严格的监管要求

**劣势**：
- 成本高昂：资源利用率低
- 运维复杂：需要管理大量独立实例
- 扩展困难：水平扩展成本呈线性增长

**适用场景**：
- 金融、医疗等高安全要求行业
- 租户数量少但数据量大
- 需要深度定制的大型企业客户

```typescript
// 单租户架构配置示例
interface TenantConfig {
  tenantId: string;
  database: {
    host: string;
    port: number;
    username: string;
    password: string;
    databaseName: string;
  };
  application: {
    serverUrl: string;
    redisUrl: string;
    storagePath: string;
  };
}

class SingleTenantManager {
  private tenants: Map<string, TenantConfig> = new Map();

  async provisionTenant(tenantConfig: TenantConfig): Promise<void> {
    // 创建独立数据库
    await this.createDatabase(tenantConfig.database);
    
    // 部署独立应用实例
    await this.deployApplication(tenantConfig);
    
    // 存储租户配置
    this.tenants.set(tenantConfig.tenantId, tenantConfig);
  }

  private async createDatabase(dbConfig: any): Promise<void> {
    // 创建数据库、用户、权限等
    const client = new Pool({
      host: 'postgres-master',
      port: 5432,
      user: 'admin',
      password: process.env.DB_ADMIN_PASSWORD
    });
    
    await client.query(`CREATE DATABASE ${dbConfig.databaseName}`);
    await client.query(`
      CREATE USER ${dbConfig.username} 
      WITH PASSWORD '${dbConfig.password}'
    `);
    await client.query(`
      GRANT ALL PRIVILEGES ON DATABASE ${dbConfig.databaseName} 
      TO ${dbConfig.username}
    `);
  }
}
```

### 1.2 多租户架构（Multi-Tenancy）

**定义**：所有租户共享相同的基础设施和应用实例，通过逻辑隔离实现数据分离。

**优势**：
- 成本高效：资源共享，降低运营成本
- 运维简便：单一实例管理
- 快速扩展：易于水平扩展

**劣势**：
- 隔离性相对较弱
- 定制灵活性有限
- 性能可能相互影响

**适用场景**：
- 中小企业市场
- SaaS产品标准化程度高
- 租户数量多、数据量相对较小

```typescript
// 多租户架构核心实现
class MultiTenantApp {
  private tenantMiddleware: TenantMiddleware;
  
  constructor() {
    this.tenantMiddleware = new TenantMiddleware();
  }

  async handleRequest(req: Request, res: Response): Promise<void> {
    // 从请求中解析租户标识
    const tenantId = this.extractTenantId(req);
    
    // 设置租户上下文
    await this.tenantMiddleware.setTenantContext(tenantId);
    
    // 业务逻辑处理
    const result = await this.processBusinessLogic(req);
    
    // 清理租户上下文
    this.tenantMiddleware.clearTenantContext();
    
    res.json(result);
  }

  private extractTenantId(req: Request): string {
    // 支持多种租户识别方式
    const strategies = [
      this.extractFromHeader,
      this.extractFromSubdomain,
      this.extractFromPath,
      this.extractFromJwt
    ];
    
    for (const strategy of strategies) {
      const tenantId = strategy(req);
      if (tenantId) return tenantId;
    }
    
    throw new Error('Tenant identification failed');
  }
}
```

### 1.3 混合架构（Hybrid Tenancy）

**定义**：结合单租户和多租户优势，为不同租户提供不同级别的隔离。

**实现方式**：
- **分层租户**：大客户独立实例，小客户共享实例
- **功能隔离**：敏感模块单租户，通用模块多租户
- **数据隔离**：关键数据单租户存储，非关键数据多租户共享

```typescript
// 混合架构实现
class HybridTenantManager {
  private routingRules: TenantRoutingRule[] = [];
  
  constructor() {
    this.initializeRoutingRules();
  }

  private initializeRoutingRules(): void {
    this.routingRules = [
      {
        condition: (tenant: Tenant) => tenant.plan === 'enterprise',
        handler: new SingleTenantHandler(),
        priority: 1
      },
      {
        condition: (tenant: Tenant) => tenant.dataSize > 1000000,
        handler: new ShardedMultiTenantHandler(),
        priority: 2
      },
      {
        condition: () => true, // 默认处理
        handler: new StandardMultiTenantHandler(),
        priority: 3
      }
    ];
  }

  async routeRequest(tenant: Tenant, request: any): Promise<any> {
    // 根据路由规则选择处理器
    const rule = this.routingRules.find(r => r.condition(tenant));
    
    if (!rule) {
      throw new Error('No routing rule found');
    }
    
    return rule.handler.handle(request, tenant);
  }
}
```

## 2. 租户隔离策略

### 2.1 数据库级隔离（Database-per-Tenant）

**实现方式**：每个租户拥有独立的数据库实例。

**技术实现**：
```sql
-- 创建租户数据库脚本
CREATE DATABASE tenant_${tenant_id};

-- 创建租户专用用户
CREATE USER tenant_${tenant_id}_user 
WITH PASSWORD '${generated_password}';

-- 授予数据库权限
GRANT ALL PRIVILEGES ON DATABASE tenant_${tenant_id} 
TO tenant_${tenant_id}_user;
```

**连接管理**：
```typescript
class DatabasePerTenantManager {
  private connectionPools: Map<string, Pool> = new Map();
  
  async getPoolForTenant(tenantId: string): Promise<Pool> {
    if (!this.connectionPools.has(tenantId)) {
      const config = await this.getTenantDbConfig(tenantId);
      const pool = new Pool(config);
      this.connectionPools.set(tenantId, pool);
    }
    
    return this.connectionPools.get(tenantId)!;
  }

  async executeQuery(tenantId: string, query: string, params?: any[]): Promise<any> {
    const pool = await this.getPoolForTenant(tenantId);
    const client = await pool.connect();
    
    try {
      return await client.query(query, params);
    } finally {
      client.release();
    }
  }
}
```

### 2.2 Schema级隔离（Schema-per-Tenant）

**实现方式**：所有租户共享数据库，但每个租户拥有独立的Schema。

**优势**：
- 成本低于数据库级隔离
- 支持租户间数据共享（跨Schema查询）
- 备份和恢复可按租户进行

```sql
-- 创建租户Schema
CREATE SCHEMA tenant_${tenant_id};

-- 设置搜索路径
SET search_path TO tenant_${tenant_id}, public;

-- 在租户Schema中创建表
CREATE TABLE tenant_${tenant_id}.users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建公共函数（所有租户可用）
CREATE OR REPLACE FUNCTION current_tenant_id() 
RETURNS TEXT AS $$
  SELECT current_setting('app.current_tenant', true);
$$ LANGUAGE SQL;
```

**应用层管理**：
```typescript
class SchemaPerTenantManager {
  private defaultPool: Pool;
  
  constructor() {
    this.defaultPool = new Pool({
      connectionString: process.env.DATABASE_URL
    });
  }

  async setTenantContext(tenantId: string): Promise<void> {
    await this.defaultPool.query(
      `SET search_path TO tenant_${tenantId}, public`
    );
    
    // 设置会话变量
    await this.defaultPool.query(
      `SET app.current_tenant = '${tenantId}'`
    );
  }

  async executeInTenantContext<T>(
    tenantId: string, 
    callback: () => Promise<T>
  ): Promise<T> {
    const client = await this.defaultPool.connect();
    
    try {
      await client.query(`BEGIN`);
      await client.query(
        `SET LOCAL search_path TO tenant_${tenantId}, public`
      );
      await client.query(
        `SET LOCAL app.current_tenant = '${tenantId}'`
      );
      
      const result = await callback();
      
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }
}
```

### 2.3 行级隔离（Row-Level Security）

**实现方式**：所有租户共享表结构，通过行级安全策略实现数据隔离。

```sql
-- 启用行级安全
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- 创建租户ID列
ALTER TABLE documents ADD COLUMN tenant_id VARCHAR(50);

-- 创建行级安全策略
CREATE POLICY tenant_isolation_policy ON documents
  USING (tenant_id = current_setting('app.current_tenant'));

-- 创建RLS函数
CREATE OR REPLACE FUNCTION create_tenant_policy(
  table_name TEXT,
  tenant_column TEXT DEFAULT 'tenant_id'
) RETURNS void AS $$
DECLARE
  policy_name TEXT;
BEGIN
  policy_name := 'rls_' || table_name || '_policy';
  
  EXECUTE format('
    ALTER TABLE %I ENABLE ROW LEVEL SECURITY;
    CREATE POLICY %I ON %I
      USING (%I = current_setting(''app.current_tenant''));
  ', table_name, policy_name, table_name, tenant_column);
END;
$$ LANGUAGE plpgsql;
```

**应用层实现**：
```typescript
class RowLevelSecurityManager {
  private pool: Pool;
  
  constructor() {
    this.pool = new Pool({
      connectionString: process.env.DATABASE_URL
    });
  }

  async withTenantContext<T>(
    tenantId: string,
    operation: (client: PoolClient) => Promise<T>
  ): Promise<T> {
    const client = await this.pool.connect();
    
    try {
      // 设置租户上下文
      await client.query(
        `SET app.current_tenant = '${tenantId}'`
      );
      
      // 启用行级安全
      await client.query(`SET row_security = on`);
      
      return await operation(client);
    } finally {
      client.release();
    }
  }

  // 自动添加租户过滤条件
  async findWithTenant(
    tenantId: string,
    table: string,
    conditions: Record<string, any> = {}
  ): Promise<any[]> {
    return this.withTenantContext(tenantId, async (client) => {
      const whereClauses = Object.keys(conditions)
        .map((key, i) => `${key} = $${i + 1}`)
        .join(' AND ');
      
      const query = `
        SELECT * FROM ${table} 
        ${whereClauses ? `WHERE ${whereClauses}` : ''}
        ORDER BY created_at DESC
      `;
      
      const result = await client.query(query, Object.values(conditions));
      return result.rows;
    });
  }
}
```

## 3. 计费系统设计

### 3.1 订阅计费模式

**实现模型**：
- 基于时间的订阅（月付/年付）
- 基于功能的订阅（基础版/专业版/企业版）
- 席位计费（按用户数计费）

```typescript
// 订阅模型定义
interface Subscription {
  id: string;
  tenantId: string;
  planId: string;
  status: 'active' | 'canceled' | 'expired' | 'trial';
  startDate: Date;
  endDate: Date;
  billingCycle: 'monthly' | 'yearly';
  quantity: number; // 席位数或资源单位
  metadata: Record<string, any>;
}

// 计费计划
interface PricingPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  interval: 'month' | 'year';
  features: string[];
  limits: {
    users: number;
    storage: number; // GB
    apiCalls: number;
    [key: string]: number;
  };
}

class SubscriptionService {
  private stripe: Stripe;
  
  constructor() {
    this.stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
      apiVersion: '2023-10-16'
    });
  }

  async createSubscription(
    tenantId: string,
    planId: string,
    quantity: number
  ): Promise<Subscription> {
    // 1. 获取或创建Stripe客户
    const customer = await this.getOrCreateStripeCustomer(tenantId);
    
    // 2. 创建订阅
    const stripeSubscription = await this.stripe.subscriptions.create({
      customer: customer.id,
      items: [{
        price: planId,
        quantity: quantity
      }],
      metadata: {
        tenantId: tenantId
      },
      payment_behavior: 'default_incomplete',
      expand: ['latest_invoice.payment_intent']
    });
    
    // 3. 保存到本地数据库
    const subscription = await this.saveSubscription({
      tenantId,
      planId,
      stripeSubscriptionId: stripeSubscription.id,
      status: stripeSubscription.status,
      startDate: new Date(stripeSubscription.current_period_start * 1000),
      endDate: new Date(stripeSubscription.current_period_end * 1000),
      quantity,
      billingCycle: stripeSubscription.plan.interval
    });
    
    return subscription;
  }

  async handleSubscriptionUpdated(event: Stripe.Event): Promise<void> {
    const subscription = event.data.object as Stripe.Subscription;
    const tenantId = subscription.metadata.tenantId;
    
    // 更新本地订阅状态
    await this.updateSubscriptionStatus(
      subscription.id,
      subscription.status,
      {
        startDate: new Date(subscription.current_period_start * 1000),
        endDate: new Date(subscription.current_period_end * 1000)
      }
    );
    
    // 触发相应的业务逻辑
    await this.triggerPlanChangeActions(tenantId, subscription.status);
  }
}
```

### 3.2 用量计费模式

**适用场景**：
- API调用次数
- 存储使用量
- 计算资源消耗
- 数据传输量

```typescript
// 用量记录模型
interface UsageRecord {
  id: string;
  tenantId: string;
  metric: string; // 'api_calls', 'storage_gb', 'compute_hours'
  quantity: number;
  timestamp: Date;
  metadata: Record<string, any>;
  reported: boolean;
}

class UsageBasedBillingService {
  private stripe: Stripe;
  private usageRecords: Map<string, UsageRecord[]> = new Map();
  
  async recordUsage(
    tenantId: string,
    metric: string,
    quantity: number,
    metadata: Record<string, any> = {}
  ): Promise<void> {
    const record: UsageRecord = {
      id: uuid(),
      tenantId,
      metric,
      quantity,
      timestamp: new Date(),
      metadata,
      reported: false
    };
    
    // 缓存使用记录
    if (!this.usageRecords.has(tenantId)) {
      this.usageRecords.set(tenantId, []);
    }
    this.usageRecords.get(tenantId)!.push(record);
    
    // 批量报告（每小时或达到阈值）
    await this.maybeReportUsage(tenantId, metric);
  }

  private async maybeReportUsage(
    tenantId: string,
    metric: string
  ): Promise<void> {
    const records = this.usageRecords.get(tenantId) || [];
    const unreproted = records.filter(r => !r.reported && r.metric === metric);
    
    // 每小时或积累100条记录时报告
    if (unreproted.length >= 100 || 
        (unreproted.length > 0 && this.isHourlyReportDue(unreproted[0].timestamp))) {
      await this.reportUsageToStripe(tenantId, metric, unreproted);
      
      // 标记为已报告
      unreproted.forEach(record => {
        record.reported = true;
      });
    }
  }

  private async reportUsageToStripe(
    tenantId: string,
    metric: string,
    records: UsageRecord[]
  ): Promise<void> {
    const totalQuantity = records.reduce((sum, r) => sum + r.quantity, 0);
    const timestamp = Math.floor(records[0].timestamp.getTime() / 1000);
    
    // 获取订阅项目ID
    const subscriptionItemId = await this.getSubscriptionItemId(tenantId, metric);
    
    // 报告给Stripe
    await this.stripe.subscriptionItems.createUsageRecord(
      subscriptionItemId,
      {
        quantity: totalQuantity,
        timestamp: timestamp,
        action: 'increment'
      }
    );
    
    console.log(`Reported ${totalQuantity} ${metric} for tenant ${tenantId}`);
  }
}
```

### 3.3 Stripe集成最佳实践

**Webhook处理**：
```typescript
// Stripe Webhook处理器
class StripeWebhookHandler {
  private stripe: Stripe;
  private webhookSecret: string;
  
  constructor() {
    this.stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
    this.webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;
  }

  async handleWebhook(req: Request, res: Response): Promise<void> {
    const sig = req.headers['stripe-signature'] as string;
    let event: Stripe.Event;
    
    try {
      event = this.stripe.webhooks.constructEvent(
        req.body,
        sig,
        this.webhookSecret
      );
    } catch (err) {
      console.error('Webhook signature verification failed:', err);
      res.status(400).send(`Webhook Error: ${err.message}`);
      return;
    }
    
    // 处理不同类型的事件
    switch (event.type) {
      case 'customer.subscription.created':
        await this.handleSubscriptionCreated(event);
        break;
      case 'customer.subscription.updated':
        await this.handleSubscriptionUpdated(event);
        break;
      case 'customer.subscription.deleted':
        await this.handleSubscriptionDeleted(event);
        break;
      case 'invoice.payment_succeeded':
        await this.handleInvoicePaid(event);
        break;
      case 'invoice.payment_failed':
        await this.handleInvoiceFailed(event);
        break;
      default:
        console.log(`Unhandled event type: ${event.type}`);
    }
    
    res.json({ received: true });
  }

  private async handleInvoicePaid(event: Stripe.Event): Promise<void> {
    const invoice = event.data.object as Stripe.Invoice;
    const tenantId = invoice.metadata.tenantId;
    
    if (tenantId) {
      // 更新租户计费状态
      await this.updateBillingStatus(tenantId, 'paid');
      
      // 发送收据邮件
      await this.sendReceiptEmail(tenantId, invoice);
      
      // 记录付款历史
      await this.recordPaymentHistory(tenantId, invoice);
    }
  }
}
```

## 4. 权限和角色系统

### 4.1 RBAC（基于角色的访问控制）

```typescript
// RBAC核心模型
interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string; // 'projects', 'users', 'reports'
  action: string; // 'create', 'read', 'update', 'delete'
  conditions?: Record<string, any>; // 动态条件
}

interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[]; // 权限ID列表
  isDefault: boolean;
  tenantId: string; // 租户特定角色
}

interface UserRole {
  userId: string;
  roleId: string;
  tenantId: string;
  assignedAt: Date;
  assignedBy: string;
}

class RBACService {
  private permissionCache: Map<string, Permission[]> = new Map();
  
  async checkPermission(
    userId: string,
    tenantId: string,
    resource: string,
    action: string,
    context: Record<string, any> = {}
  ): Promise<boolean> {
    // 获取用户角色
    const roles = await this.getUserRoles(userId, tenantId);
    
    // 获取角色权限
    const permissions = await this.getRolesPermissions(roles);
    
    // 检查是否有匹配的权限
    return permissions.some(permission => {
      // 检查资源和动作匹配
      if (permission.resource !== resource || permission.action !== action) {
        return false;
      }
      
      // 检查条件（如果有）
      if (permission.conditions) {
        return this.evaluateConditions(permission.conditions, context);
      }
      
      return true;
    });
  }

  async assignRole(
    userId: string,
    roleId: string,
    tenantId: string,
    assignedBy: string
  ): Promise<UserRole> {
    // 检查是否已有该角色
    const existing = await this.findUserRole(userId, roleId, tenantId);
    if (existing) {
      throw new Error('User already has this role');
    }
    
    // 保存角色分配
    const userRole = await this.saveUserRole({
      userId,
      roleId,
      tenantId,
      assignedAt: new Date(),
      assignedBy
    });
    
    // 缓存失效
    this.invalidatePermissionCache(userId, tenantId);
    
    return userRole;
  }

  private evaluateConditions(
    conditions: Record<string, any>,
    context: Record<string, any>
  ): boolean {
    // 实现条件评估逻辑
    // 例如：{"project.owner": "$currentUser"}
    for (const [conditionKey, conditionValue] of Object.entries(conditions)) {
      const contextValue = this.resolveContextValue(conditionKey, context);
      
      if (typeof conditionValue === 'string' && conditionValue.startsWith('$')) {
        // 变量引用
        const varName = conditionValue.slice(1);
        if (context[varName] !== contextValue) {
          return false;
        }
      } else if (conditionValue !== contextValue) {
        return false;
      }
    }
    
    return true;
  }
}
```

### 4.2 ABAC（基于属性的访问控制）

```typescript
// ABAC策略定义
interface ABACPolicy {
  id: string;
  name: string;
  description: string;
  effect: 'allow' | 'deny';
  target: {
    resource: string;
    actions: string[];
  };
  condition: {
    subject: Record<string, any>;
    environment: Record<string, any>;
    resource: Record<string, any>;
  };
  priority: number; // 策略优先级
}

class ABACService {
  private policies: ABACPolicy[] = [];
  
  async evaluatePolicy(
    subject: Record<string, any>, // 用户属性
    resource: Record<string, any>, // 资源属性
    action: string,
    environment: Record<string, any> // 环境属性
  ): Promise<boolean> {
    // 筛选相关策略
    const relevantPolicies = this.policies.filter(policy => {
      return policy.target.resource === resource.type &&
             policy.target.actions.includes(action);
    });
    
    // 按优先级排序
    relevantPolicies.sort((a, b) => b.priority - a.priority);
    
    // 评估策略
    for (const policy of relevantPolicies) {
      const matches = this.evaluatePolicyCondition(
        policy.condition,
        subject,
        resource,
        environment
      );
      
      if (matches) {
        return policy.effect === 'allow';
      }
    }
    
    // 默认拒绝
    return false;
  }

  private evaluatePolicyCondition(
    condition: ABACPolicy['condition'],
    subject: Record<string, any>,
    resource: Record<string, any>,
    environment: Record<string, any>
  ): boolean {
    // 评估主体条件
    if (!this.evaluateAttributes(condition.subject, subject)) {
      return false;
    }
    
    // 评估资源条件
    if (!this.evaluateAttributes(condition.resource, resource)) {
      return false;
    }
    
    // 评估环境条件
    if (!this.evaluateAttributes(condition.environment, environment)) {
      return false;
    }
    
    return true;
  }

  private evaluateAttributes(
    expected: Record<string, any>,
    actual: Record<string, any>
  ): boolean {
    for (const [key, expectedValue] of Object.entries(expected)) {
      const actualValue = actual[key];
      
      if (expectedValue instanceof RegExp) {
        if (!expectedValue.test(actualValue)) {
          return false;
        }
      } else if (Array.isArray(expectedValue)) {
        if (!expectedValue.includes(actualValue)) {
          return false;
        }
      } else if (expectedValue !== actualValue) {
        return false;
      }
    }
    
    return true;
  }
}
```

### 4.3 混合权限系统

```typescript
// 混合权限系统实现
class HybridPermissionService {
  private rbacService: RBACService;
  private abacService: ABACService;
  
  constructor() {
    this.rbacService = new RBACService();
    this.abacService = new ABACService();
  }

  async checkAccess(
    request: AccessRequest
  ): Promise<AccessDecision> {
    // 首先检查RBAC（快速路径）
    const rbacAllowed = await this.rbacService.checkPermission(
      request.userId,
      request.tenantId,
      request.resource,
      request.action,
      request.context
    );
    
    // 如果RBAC明确允许，直接返回
    if (rbacAllowed) {
      return {
        allowed: true,
        reason: 'rbac_allow',
        policyId: 'rbac'
      };
    }
    
    // RBAC拒绝，尝试ABAC
    const abacAllowed = await this.abacService.evaluatePolicy(
      await this.getSubjectAttributes(request.userId),
      await this.getResourceAttributes(request.resource, request.resourceId),
      request.action,
      request.environment
    );
    
    if (abacAllowed) {
      return {
        allowed: true,
        reason: 'abac_allow',
        policyId: 'abac'
      };
    }
    
    // 都拒绝
    return {
      allowed: false,
      reason: 'no_matching_policy',
      policyId: null
    };
  }

  // 权限中间件
  createPermissionMiddleware(
    resource: string,
    action: string
  ) {
    return async (req: Request, res: Response, next: NextFunction) => {
      const decision = await this.checkAccess({
        userId: req.user?.id,
        tenantId: req.tenant?.id,
        resource,
        action,
        resourceId: req.params.id,
        context: req.body,
        environment: {
          ip: req.ip,
          userAgent: req.headers['user-agent'],
          timestamp: new Date()
        }
      });
      
      if (!decision.allowed) {
        return res.status(403).json({
          error: 'Access denied',
          reason: decision.reason
        });
      }
      
      next();
    };
  }
}
```

## 5. 多租户数据隔离

### 5.1 数据库连接池管理

```typescript
// 多租户连接池管理器
class MultiTenantConnectionPool {
  private pools: Map<string, Pool> = new Map();
  private defaultPool: Pool;
  private tenantConfigs: Map<string, TenantDatabaseConfig> = new Map();
  
  constructor() {
    // 默认连接池（用于管理操作）
    this.defaultPool = new Pool({
      connectionString: process.env.ADMIN_DATABASE_URL,
      max: 10,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000
    });
  }

  async getPoolForTenant(tenantId: string): Promise<Pool> {
    if (!this.pools.has(tenantId)) {
      // 获取租户数据库配置
      const config = await this.getTenantDatabaseConfig(tenantId);
      
      // 创建新连接池
      const pool = new Pool({
        host: config.host,
        port: config.port,
        database: config.database,
        user: config.user,
        password: config.password,
        max: config.maxConnections || 5,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
        statement_timeout: 30000, // 30秒查询超时
        query_timeout: 30000
      });
      
      // 连接池事件处理
      pool.on('error', (err) => {
        console.error(`Pool error for tenant ${tenantId}:`, err);
      });
      
      pool.on('connect', () => {
        console.log(`New connection created for tenant ${tenantId}`);
      });
      
      this.pools.set(tenantId, pool);
    }
    
    return this.pools.get(tenantId)!;
  }

  async executeInTenantContext<T>(
    tenantId: string,
    operation: (client: PoolClient) => Promise<T>
  ): Promise<T> {
    const pool = await this.getPoolForTenant(tenantId);
    const client = await pool.connect();
    
    try {
      // 设置连接上下文
      await client.query(`SET search_path TO tenant_${tenantId}`);
      await client.query(`SET app.tenant_id = '${tenantId}'`);
      
      return await operation(client);
    } finally {
      client.release();
    }
  }

  // 健康检查
  async healthCheck(): Promise<Record<string, boolean>> {
    const results: Record<string, boolean> = {};
    
    for (const [tenantId, pool] of this.pools) {
      try {
        const client = await pool.connect();
        await client.query('SELECT 1');
        client.release();
        results[tenantId] = true;
      } catch (error) {
        results[tenantId] = false;
        console.error(`Health check failed for tenant ${tenantId}:`, error);
      }
    }
    
    return results;
  }
}
```

### 5.2 查询中间件

```typescript
// 查询中间件，自动添加租户过滤
class TenantQueryMiddleware {
  private connectionPool: MultiTenantConnectionPool;
  
  constructor(connectionPool: MultiTenantConnectionPool) {
    this.connectionPool = connectionPool;
  }

  // 自动添加WHERE条件
  async executeQuery(
    tenantId: string,
    query: string,
    params: any[] = []
  ): Promise<any> {
    return this.connectionPool.executeInTenantContext(
      tenantId,
      async (client) => {
        // 检查是否需要添加租户过滤
        const modifiedQuery = this.addTenantFilterIfMissing(query, tenantId);
        
        // 执行查询
        return client.query(modifiedQuery, params);
      }
    );
  }

  private addTenantFilterIfMissing(query: string, tenantId: string): string {
    const lowerQuery = query.toLowerCase();
    
    // 如果是SELECT查询且没有WHERE子句，添加租户过滤
    if (lowerQuery.startsWith('select') && 
        !lowerQuery.includes('where') && 
        !lowerQuery.includes('tenant_id')) {
      
      // 解析表名
      const fromMatch = lowerQuery.match(/from\s+(\w+)/);
      if (fromMatch) {
        const tableName = fromMatch[1];
        
        // 检查表是否有tenant_id列
        if (this.tableHasTenantColumn(tableName)) {
          query += ` WHERE tenant_id = '${tenantId}'`;
        }
      }
    }
    
    return query;
  }

  // ORM钩子集成
  createKnexPlugin(): any {
    return {
      'query': (builder: any) => {
        const tenantId = this.getCurrentTenantId();
        if (tenantId && builder._single?.table) {
          builder.where('tenant_id', tenantId);
        }
      }
    };
  }
}
```

### 5.3 数据迁移和备份

```typescript
// 多租户数据迁移管理器
class TenantMigrationManager {
  private migrations: Migration[] = [];
  
  async migrateTenant(
    tenantId: string,
    targetVersion: string
  ): Promise<void> {
    const currentVersion = await this.getCurrentVersion(tenantId);
    const migrationsToRun = this.getMigrationsToRun(currentVersion, targetVersion);
    
    console.log(`Migrating tenant ${tenantId} from ${currentVersion} to ${targetVersion}`);
    
    for (const migration of migrationsToRun) {
      await this.runMigration(tenantId, migration);
      await this.updateVersion(tenantId, migration.version);
    }
  }

  async backupTenant(tenantId: string): Promise<string> {
    const backupId = `backup_${tenantId}_${Date.now()}`;
    const backupPath = `/backups/${backupId}.sql`;
    
    // 获取租户数据库配置
    const config = await this.getTenantDatabaseConfig(tenantId);
    
    // 执行pg_dump
    const command = `pg_dump -h ${config.host} -p ${config.port} -U ${config.user} -d ${config.database} -f ${backupPath}`;
    
    await execPromise(command);
    
    // 上传到S3
    await this.uploadToS3(backupPath, `backups/${tenantId}/${backupId}.sql`);
    
    console.log(`Backup created for tenant ${tenantId}: ${backupId}`);
    return backupId;
  }

  async restoreTenant(tenantId: string, backupId: string): Promise<void> {
    // 从S3下载备份
    const backupPath = await this.downloadFromS3(
      `backups/${tenantId}/${backupId}.sql`
    );
    
    // 获取租户数据库配置
    const config = await this.getTenantDatabaseConfig(tenantId);
    
    // 创建临时数据库
    const tempDb = `${config.database}_restore_${Date.now()}`;
    await this.createDatabase(tempDb, config);
    
    // 恢复备份
    const command = `psql -h ${config.host} -p ${config.port} -U ${config.user} -d ${tempDb} -f ${backupPath}`;
    await execPromise(command);
    
    // 重命名数据库
    await this.renameDatabase(tempDb, config.database, config);
    
    console.log(`Tenant ${tenantId} restored from backup ${backupId}`);
  }
}
```

## 6. 白标和自定义域名

### 6.1 动态品牌定制

```typescript
// 品牌定制管理器
class BrandingManager {
  private tenantBranding: Map<string, TenantBranding> = new Map();
  
  async getBrandingForTenant(tenantId: string): Promise<TenantBranding> {
    if (!this.tenantBranding.has(tenantId)) {
      const branding = await this.loadBrandingFromDatabase(tenantId);
      this.tenantBranding.set(tenantId, branding);
    }
    
    return this.tenantBranding.get(tenantId)!;