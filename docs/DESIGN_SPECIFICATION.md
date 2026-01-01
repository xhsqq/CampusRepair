# 校园报修系统 - 设计说明书 (Design Specification)

## 1. 系统架构设计
本项目采用典型的 **B/S (Browser/Server)** 架构，后端基于 Python Flask 框架实现 MVC 模式的简化版。
- **前端 (View)**: 基于 HTML5, Bootstrap 5 和 Jinja2 模板引擎。
- **逻辑层 (Controller)**: `app.py` 承载所有路由分发与业务逻辑。
- **数据层 (Model)**: 使用 SQLite3 关系型数据库进行持久化。

## 2. 数据库设计
系统数据库包含以下核心表结构：
- **users**: 存储用户信息（id, username, password, role, name, phone）。
- **repairs**: 存储报修单主信息（id, creator_id, location, content, status, urgency_level）。
- **repair_logs**: 存储工单状态流转记录，用于审计和历史追踪。

## 3. 模块划分
系统在逻辑上划分为四个核心功能模块：
- **认证模块 (Auth)**: 负责用户注册、登录、Session 管理。
- **报修管理 (Repairs)**: 负责工单的创建、查询、撤回及状态变更。
- **工作台 (Dashboard)**: 负责首页数据统计与快速导航。
- **个人中心 (Profile)**: 负责用户基本信息的维护。

## 4. 接口设计 (API Design)
系统主要接口遵循 RESTful 风格设计：
- `GET /repairs`: 查看工单列表。
- `POST /repairs/new`: 提交新报修申请。
- `POST /repairs/<id>/action`: 执行工单操作（接单、完成、取消）。
- `GET /auth/login`: 用户登录接口。

## 5. 安全性设计
- **身份校验**: 使用 `@login_required` 装饰器保护敏感路由。
- **权限隔离**: 后端硬编码校验 `session['role']`，防止越权操作。
- **数据安全**: 采用参数化查询防止 SQL 注入。
