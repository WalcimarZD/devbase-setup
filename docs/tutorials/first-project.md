# 🚀 Your First Project in 5 Minutes

This tutorial will walk you through creating your first project with DevBase.

## Prerequisites

- DevBase installed (`python devbase.py doctor` passes)
- Workspace initialized (`python devbase.py setup`)

## Step 1: Create a New Project

```bash
devbase new my-awesome-app
```

This creates a project from the **Clean Architecture** template at:
```
20-29_CODE/21_monorepo_apps/my-awesome-app/
```

## Step 2: Explore the Structure

Your new project includes:

```
my-awesome-app/
├── src/
│   ├── application/      # Use cases, DTOs
│   ├── domain/           # Entities, value objects
│   └── infrastructure/   # External services
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .cursorrules          # AI assistant rules
└── README.md
```

## Step 3: Verify Your Setup

```bash
cd 20-29_CODE/21_monorepo_apps/my-awesome-app
devbase doctor
```

## Step 4: Make Your First Commit

```bash
git init
git add .
git commit -m "feat: initial project setup"
```

> 💡 Git hooks will validate your commit message format!

## What's Next?

- Read about [Clean Architecture](../explanation/clean-architecture.md)
- Learn to [customize templates](../how-to/customize-templates.md)
- Set up [Git hooks](./setup-git-hooks.md)

---

**Time to complete:** ~5 minutes  
**Difficulty:** Beginner
