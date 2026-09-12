---
title: "版本控制与Git深入"
tags: []
source: "baike"
source_path: "开发术语 / 开发工具与环境"
collected: "2026-09-05"
status: "imported"
---

# 版本控制与Git深入


> 📌 **导航**：本文是 **版本控制与Git深入** 词条，属于 tools 术语集。相关枢纽：[[包管理器与构建工具]]、[[容器化与Docker]]、[[版本控制与Git深入]]、[[调试与性能分析]]。

## Git核心概念

**一句话定义：** Git是分布式版本控制系统，记录文件的每一次变更，支持多人协作。

**通俗类比：** Git就像一个"时光机+平行宇宙"——你可以随时回到过去（历史版本），也可以创建平行世界（分支）来实验。

### 三个区域

```
工作区(Working Directory)
    ↓ git add
暂存区(Staging Area / Index)
    ↓ git commit
Git仓库(.git目录)
```

### 分支策略

**Git Flow：**
```
main ← 生产环境
 └── develop ← 开发主线
      ├── feature/login ← 功能分支
      ├── feature/payment ← 功能分支
      └── hotfix/bug ← 紧急修复
```

**GitHub Flow（更简洁）：**
```
main ← 始终可部署
 └── feature-xxx ← PR合并回main
```

### 常用命令深入

```bash
# 变基：把提交"搬"到另一个分支上
git rebase main

# 交互式变基：整理提交历史
git rebase -i HEAD~3

# 暂存当前工作
git stash
git stash pop

# 查看提交图
git log --oneline --graph --all

# 回退到某个版本（保留修改）
git reset --soft HEAD~1

# 回退到某个版本（丢弃修改）
git reset --hard HEAD~1

# Cherry-pick：只取某个提交
git cherry-pick abc123
```

### .gitignore最佳实践

```
# 依赖
node_modules/
vendor/

# 编译产物
*.pyc
dist/
build/

# IDE
.idea/
.vscode/
*.swp

# 系统文件
.DS_Store
Thumbs.db

# 环境变量
.env
.env.local
```

### 解决冲突

```
<<<<<<< HEAD
你的修改
=======
别人的修改
>>>>>>> feature-branch
```

策略：沟通协商 → 手动合并 → 测试验证 → 提交

## 相关术语

[[包管理器与构建工具]]、[[容器化与Docker]]、[[调试与性能分析]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
