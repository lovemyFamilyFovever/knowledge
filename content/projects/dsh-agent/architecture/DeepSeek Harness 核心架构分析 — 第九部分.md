---
title: "DeepSeek Harness 核心架构分析 — 第九部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

# DeepSeek Harness 核心架构分析 — 第九部分

## 设置、凭据与存储系统

---

## 37. 设置系统（Settings）

### 37.1 架构

```typescript
class Settings extends Service {
  register<T>(ns: SettingsNamespace, schema: z<T>, options?: SettingsRegisterOptions<T>): SettingsScope<T>
}
```

设置系统是 **namespace-based** 的：每个插件注册一个命名空间 schema，读取解析后的值。

### 37.2 值解析层次

```
schema defaults（schema 默认值）
  ↓
composition base（组合层值，来自 cordis.yml）
  ↓
user document section（用户文档部分）
```

### 37.3 SettingsScope

```typescript
interface SettingsScope<T> {
  get(): T                    // 当前解析值
  watch(callback): () => void // 观察变更
  update(patch): void         // 合并补丁
  replace(value): void        // 完全替换
  mutate(fn): void            // 函数式变更
}
```

### 37.4 设置描述符

```typescript
interface SettingsDescriptor {
  ns: SettingsNamespace
  schema: unknown
  value: unknown
  revision: number
  base?: unknown
  user?: unknown
  applies: 'live' | 'restart'
  secrets?: RedactedSecret[]
}
```

### 37.5 密钥脱敏

`redactSecrets()` 从设置描述符中剥离 `role('secret')` 字段，枚举它们在 `secrets` 中。每个 wire 表面必须传递此选项。

### 37.6 变更验证

```typescript
validate?: (value: T) => void
```

可选的验证函数用于跨字段约束。throw 拒绝写入，存储部分失败保持最后一个好值并警告。

---

## 38. 凭据系统（Credentials）

### 38.1 架构

```typescript
class Credentials extends Service {
  resolve(ref: CredentialRef): Promise<ResolvedCredential | undefined>
}
```

设置和组合文件携带对密钥的 **引用**（环境变量名），而提供者拥有实际值和存储。消费者每次操作解析一次引用。

### 38.2 凭据引用

```typescript
type CredentialRef = Branded<'CredentialRef'>  // POSIX shell 标识符如 DEEPSEEK_API_KEY
```

### 38.3 凭据键

```typescript
type CredentialKey = Branded<'CredentialKey'>  // '<scope>/<id>' 如 'llm-deepseek/deepseek'
```

- `scope`：拥有插件的注册名
- `id`：插件自己的寻址单元

### 38.4 解析的凭据

```typescript
interface ResolvedCredential {
  value: string   // 非空密钥值
  source: string  // 提供者定义的源层 id
}
```

### 38.5 设计原则

- **引用而非值**：配置携带引用，不携带密钥
- **每次操作解析**：更改的凭据到达下一次操作，无需重启
- **配置表面看不到值**：描述引用而不看到其值
- **提供者拥有存储**：本地提供者使用 `env`、`file`、`project-env`、`user-env`

---

## 39. 存储系统（Storage）

### 39.1 架构

```typescript
class Storage extends Service {
  readonly backend: BackendRegistry
  mount<K>(form: K, facility: StorageForms[K]): () => void
  form<K>(form: K): StorageForms[K]
  get domain(): StorageForms['domain']
}
```

存储中心是一个 **命名后端注册表** + **可挂载数据形式** 的服务。中心本身不执行 IO——后端拥有媒体，数据形式拥有语义。

### 39.2 后端注册表

```typescript
class BackendRegistry {
  register(name: string, backend: StorageBackend): () => void
  resolve(name: string): StorageBackend
}
```

多个后端并排挂载。

### 39.3 数据形式

数据形式通过声明合并扩展 `StorageForms` 接口：

```typescript
interface StorageForms {
  domain: DomainFacility
  // ... 其他形式
}
```

### 39.4 后端实现

| 后端 | 说明 |
|---|---|
| `storage-json` | JSON 文件后端：原子写入、格式化 |
| `storage-sqlite` | SQLite 后端：schema、单元 |

### 39.5 领域层

`storage-domain` 包提供领域数据形式：
- `DomainFacility`：领域设施
- 事件、规范、错误处理

---

## 40. 三个系统的协作

```
Settings（设置）
  ├── 携带 CredentialRef（凭据引用）
  ├── 携带 provider/model 路由配置
  └── 通过 SettingsScope.watch() 响应变更

Credentials（凭据）
  ├── 解析 CredentialRef → 实际值
  ├── 提供者拥有存储（env/file/project-env/user-env）
  └── 每次操作解析，支持热更新

Storage（存储）
  ├── BackendRegistry 管理多个后端
  ├── 数据形式挂载到中心
  └── 领域层提供语义
```

### 40.1 配置到 LLM 适配器的传递

```
Settings (deepseek namespace)
  ↓ 解析
Credentials (DEEPSEEK_API_KEY)
  ↓ 解析
DeepSeekConnectionOptions
  ↓ 传递
DeepSeekAdapter.stream()
```
