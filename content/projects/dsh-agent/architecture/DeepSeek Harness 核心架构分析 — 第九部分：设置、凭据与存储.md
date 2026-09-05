---
title: "DeepSeek Harness 核心架构分析 — 第九部分：设置、凭据与存储"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 核心架构分析"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness 核心架构分析 — 第九部分：设置、凭据与存储
DeepSeek Harness 核心架构分析
第九部分：设置、凭据与存储系统
37. 设置系统（Settings）
37.1 值解析层次
schema defaults（schema 默认值）
  ↓
composition base（组合层值，来自 cordis.yml）
  ↓
user document section（用户文档部分）
37.2 SettingsScope
interface SettingsScope<T> {
  get(): T                    // 当前解析值
  watch(callback): () => void // 观察变更
  update(patch): void         // 合并补丁
  replace(value): void        // 完全替换
  mutate(fn): void            // 函数式变更
}
37.3 密钥脱敏
redactSecrets()
从设置描述符中剥离
role('secret')
字段。每个 wire 表面必须传递此选项。
38. 凭据系统（Credentials）
38.1 核心设计
引用而非值
：配置携带引用（环境变量名），不携带密钥
每次操作解析
：更改的凭据到达下一次操作，无需重启
配置表面看不到值
：描述引用而不看到其值
提供者拥有存储
：本地提供者使用
env
、
file
、
project-env
、
user-env
38.2 凭据键
type CredentialKey = Branded<'CredentialKey'>  // '<scope>/<id>' 如 'llm-deepseek/deepseek'
39. 存储系统（Storage）
39.1 架构
class Storage extends Service {
  readonly backend: BackendRegistry
  mount<K>(form: K, facility: StorageForms[K]): () => void
  form<K>(form: K): StorageForms[K]
  get domain(): StorageForms['domain']
}
存储中心是一个命名后端注册表 + 可挂载数据形式的服务。中心本身不执行 IO。
39.2 后端实现
后端
说明
storage-json
JSON 文件后端：原子写入、格式化
storage-sqlite
SQLite 后端：schema、单元
40. 三个系统的协作
Settings（设置）
  ├── 携带 CredentialRef（凭据引用）
  ├── 携带 provider/model 路由配置
  └── 通过 SettingsScope.watch() 响应变更

Credentials（凭据）
  ├── 解析 CredentialRef → 实际值
  └── 每次操作解析，支持热更新

Storage（存储）
  ├── BackendRegistry 管理多个后端
  └── 数据形式挂载到中心
40.1 配置到 LLM 适配器的传递
Settings (deepseek namespace)
  ↓ 解析
Credentials (DEEPSEEK_API_KEY)
  ↓ 解析
DeepSeekConnectionOptions
  ↓ 传递
DeepSeekAdapter.stream()
DeepSeek Harness 核心架构分析 — 第九部分 | 生成日期：2026-08-29