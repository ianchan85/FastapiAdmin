# SaaS 多租户平台需求文档

> 版本：v3.2.0
> 最后更新：2026-06-02

---

# Part 1：平台架构与基础设施

---

## 1. 概述

### 1.1 背景

FastapiAdmin 是一个基于 FastAPI + SQLAlchemy 的管理后台框架，需要支持 SaaS 多租户模式。平台提供完善的多租户隔离和授权体系，包含平台管理端、套餐体系、租户独立授权、插件系统、工单系统等能力。

### 1.2 核心目标

1. **数据隔离**：不同租户间的业务数据严格隔离，通过 `tenant_id` 行级过滤实现
2. **权限分层**：平台层（菜单/套餐/插件）→ 租户层（可见菜单/配额/配置）→ 用户层（角色/数据权限）
3. **灵活授权**：通过套餐体系预设权限 + 自定义授权相结合，简化租户开通流程
4. **资源管控**：租户配额管理（用户数/角色数/存储空间等）防止资源滥用

### 1.3 角色定义

| 角色 | 说明 | 租户范围 |
|------|------|---------|
| **超级管理员 (Super Admin)** | 平台拥有者，管理所有租户和套餐，不受租户过滤 | 平台 |
| **租户管理员 (Tenant Admin)** | 被指定为租户的 owner/admin，管理租户内部资源 | 单个租户 |
| **租户用户 (Tenant User)** | 普通业务用户，使用租户内的功能 | 单个租户 |

### 1.4 模块总览

| 模块 | 类型 | 租户隔离 | 核心用途 |
|------|------|---------|---------|
| Auth | 系统 | 无 | 登录认证、OAuth、JWT |
| User | 系统 | ✅ TenantMixin | 用户管理、角色/岗位分配 |
| Role | 系统 | ✅ TenantMixin | 角色定义、菜单/部门权限分配 |
| Dept | 系统 | ✅ TenantMixin | 树形部门管理 |
| Position | 系统 | ✅ TenantMixin | 岗位管理 |
| Menu | 系统 | **无** | 平台菜单树（纯平台资源） |
| Dict | 系统 | ✅ TenantMixin（平台共享） | 字典类型+数据 |
| Notice | 系统 | ✅ TenantMixin | 通知公告 |
| Params | 系统 | ✅ TenantMixin | 系统参数配置 |
| Log | 系统 | ✅ TenantMixin | 操作/登录日志 |
| Tenant | 系统 | **无**（自身为租户定义） | 租户管理 |
| Package | 系统 | **无** | 套餐管理 |
| Ticket | 系统 | ✅ TenantMixin | 工单反馈 |
| Plugin | 系统 | **无**（平台资源） | 插件注册表 |
| Cronjob | 插件 | ✅ TenantMixin | 定时任务 |
| Workflow | 插件 | ✅ TenantMixin | 工作流引擎 |
| AI Chat | 插件 | ✅ TenantMixin | AI 对话 |
| CodeGen | 插件 | ✅ TenantMixin | 代码生成器 |

---

## 2. 平台架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────┐
│                  Controller 层                    │
│    路由定义 / 参数校验 / 响应封装 / 操作日志      │
├─────────────────────────────────────────────────┤
│                  Service 层                       │
│    业务逻辑编排 / 数据校验 / 权限检查             │
├─────────────────────────────────────────────────┤
│                   CRUD 层                         │
│    CRUDBase 通用增删改查 / 租户过滤 / 权限过滤     │
├─────────────────────────────────────────────────┤
│                   Model 层                        │
│    SQLAlchemy ORM / Mixin 体系 / 关系定义         │
├─────────────────────────────────────────────────┤
│   DB (MySQL/PgSQL/SQLite)    │    Redis 缓存      │
└─────────────────────────────────────────────────┘
```

### 2.2 请求链路

```
请求 → Middleware链 → 租户中间件(解析token,设置ContextVar) →
路由匹配 → 依赖注入(DI) → Controller → Service → CRUD →
ORM(自动注入tenant_id) → DB → 反向响应 → ContextVar清理
```

### 2.3 模块目录结构

每个业务模块遵循统一结构：

```
module_xxx/
├── __init__.py
├── controller.py    # API 路由定义
├── service.py       # 业务逻辑
├── crud.py          # 数据操作（继承 CRUDBase）
├── model.py         # SQLAlchemy 模型
└── schema.py        # Pydantic 请求/响应模型
```

---

## 3. 数据隔离模型

### 3.1 核心设计原则

```
平台资源（无 tenant_id）
  ├── sys_menu              ← 菜单定义，纯平台资源
  ├── sys_tenant_package    ← 套餐定义
  ├── sys_plugin            ← 插件注册表
  └── sys_tenant            ← 租户定义

租户资源（含 tenant_id，ORM 自动过滤）
  ├── sys_user              ← 用户
  ├── sys_role              ← 角色
  ├── sys_dept              ← 部门
  ├── sys_position          ← 岗位
  ├── sys_notice            ← 通知公告
  ├── sys_param             ← 系统参数
  ├── sys_log               ← 日志
  ├── sys_ticket            ← 工单
  └── 插件业务表

平台共享资源（tenant_id=1 的平台数据对所有租户可读）
  ├── sys_dict_type         ← 字典类型
  └── sys_dict_data         ← 字典数据
```

### 3.2 三层隔离机制

| 层级 | 实现文件 | 机制说明 |
|------|---------|---------|
| **ORM 事件层** | `tenant_filter.py` | SQLAlchemy `do_orm_execute` 事件自动注入 `WHERE tenant_id = ?` |
| **CRUD 层** | `base_crud.py` | `__build_conditions` / `__tenant_condition` 二次确认 |
| **权限策略层** | `permission.py` | 基于角色 `data_scope` 字段精细化控制 |

#### ORM 事件层行为

| 操作 | 超管 | 普通用户 |
|------|------|---------|
| SELECT | 不过滤 | 自动追加 `WHERE tenant_id = ?`（`__platform_data_shared__` 模型跳过此层过滤，由 CRUD 层处理） |
| INSERT | 不自动设置 | 自动设置 `tenant_id = 当前租户` |
| UPDATE/DELETE | 不过滤 | 自动追加 `WHERE tenant_id = ?` |
| 系统表(sys_tenant) | 不过滤 | 不过滤 |

> **⚠️ 特别注意**：标记了 `__platform_data_shared__ = True` 的模型（DictType/DictData），ORM 事件层**跳过**自动 tenant_id 过滤，由 CRUD 层的 `__tenant_condition(read_mode=True)` 统一处理 `WHERE tenant_id = current OR tenant_id = 1` 逻辑。防止 ORM 事件层覆盖了"平台共享"读取策略。

#### 权限策略层

| 策略 | 枚举值 | 说明 | 适用模型 |
|------|--------|------|---------|
| `ROLE_BASED` | 1 | 仅显示用户角色授权的数据 | Menu |
| `DEPT_BASED` | 2 | 基于部门范围过滤 | Dept |
| `USER_ROLE` | 3 | 仅显示用户绑定的角色 | Role |
| `SELF_ONLY` | 4 | 仅本人数据 | 预留 |
| `DATA_SCOPE` | 5 | 基于 data_scope 字段 | Tenant（通用） |

#### data_scope 数据范围

| 值 | 说明 |
|----|------|
| 1 | 仅本人数据 |
| 2 | 本部门数据 |
| 3 | 本部门及以下数据 |
| 4 | 全部数据 |
| 5 | 自定义数据（通过 sys_role_depts 指定可见部门） |

### 3.3 Mixin 体系

```
MappedBase (声明式基类)
  ├── ModelMixin (id, uuid, status, description, 时间戳, 软删除)
  ├── TenantMixin (tenant_id FK → sys_tenant.id, NOT NULL, default=1, ON DELETE RESTRICT)
  ├── TenantAwareMixin (tenant_id 无FK, nullable)
  └── UserMixin (created_id, updated_id, deleted_id FK → sys_user)
```

#### ModelMixin 通用字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK AI | 主键 |
| `uuid` | String(64) UNIQUE | UUID 全局唯一标识 |
| `status` | String(10) default="0" | 状态（0:正常 1:禁用） |
| `description` | Text nullable | 备注/描述 |
| `created_time` | DateTime | 创建时间 |
| `updated_time` | DateTime | 更新时间（onupdate） |
| `is_deleted` | Boolean default=False | 软删除标记 |
| `deleted_time` | DateTime nullable | 删除时间 |

#### __platform_data_shared__ 机制

标记了 `__platform_data_shared__ = True` 的模型（DictType/DictData），在 CRUD 层查询时：
- 超管：不过滤，可查看/修改所有租户的数据
- 普通用户：`WHERE tenant_id = current_tenant_id OR tenant_id = 1`

---

# Part 2：核心业务模块需求

---

## 4. Auth 认证模块

### 4.1 业务描述

提供用户认证、授权、会话管理功能，支持多种登录方式（密码登录、OAuth2 第三方登录），支持验证码安全校验。

### 4.2 业务流程

```
登录请求 → 验证码校验(启用时) → 用户认证(用户名+密码) →
检查用户状态 → 更新最后登录时间 → 查询用户关联租户列表 →
生成 JWT(access_token + refresh_token) → 记录在线会话 →
返回 token + 租户列表
```

### 4.3 核心规则

| 规则 | 说明 |
|------|------|
| **验证码** | 配置控制是否启用，API 文档请求（docs/redoc）跳过验证码 |
| **密码校验** | Bcrypt 哈希比对 |
| **状态检查** | 用户 status="1"（禁用）时拒绝登录 |
| **JWT 载荷** | 包含 session_id, user_id, tenant_id, is_super_admin, 登录信息 |
| **Token 刷新** | refresh_token 专用，不可用 access_token 刷新 |
| **多租户登录** | 登录后返回用户关联的租户列表，前端选择后再生成含 tenant_id 的 token |
| **在线记录** | 登录成功后 Redis 记录在线会话，含 IP/OS/浏览器/登录位置 |
| **日志记录** | 操作日志路由类自动记录登录日志 |

### 4.4 数据模型

无独立数据表，使用 Redis 存储会话和验证码。

### 4.5 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录（返回可选租户列表） |
| POST | `/auth/token/refresh` | 刷新 token |
| POST | `/auth/logout` | 退出登录（清除 Redis 会话） |
| GET | `/auth/captcha` | 获取验证码（Base64 图片） |
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/select/tenant` | 选择/切换租户 |
| POST | `/auth/forget/password` | 忘记密码 |
| GET | `/auth/auto/login/{token}` | 免登录（用于邮件/消息免登链接） |
| GET | `/auth/oauth/{provider}/authorize` | OAuth2 授权跳转 |
| GET | `/auth/oauth/{provider}/callback` | OAuth2 回调处理 |

---

## 5. User 用户模块

### 5.1 业务描述

管理平台和租户下的用户账号，支持角色分配、岗位分配、部门归属、密码管理、Excel 导入导出。用户数据按租户严格隔离。

### 5.2 数据模型

**表名**：`sys_user`（TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `username` | String(64) | NOT NULL, UNIQUE(tenant_id) | 用户名/登录账号 |
| `password` | String(255) | NOT NULL | Bcrypt 密码哈希 |
| `name` | String(32) | NOT NULL | 昵称/姓名 |
| `mobile` | String(11) | nullable | 手机号 |
| `email` | String(64) | nullable | 邮箱 |
| `gender` | String(1) | default="2" | 性别（0:男 1:女 2:未知） |
| `avatar` | String(255) | nullable | 头像 URL |
| `is_superuser` | Boolean | default=False | 是否超级管理员 |
| `last_login` | DateTime | nullable | 最后登录时间 |
| `dept_id` | FK→sys_dept.id | nullable, ON DELETE SET NULL | 所属部门 |
| `gitee_login` | String(32) | nullable | Gitee 第三方登录 |
| `github_login` | String(32) | nullable | Github 第三方登录 |
| `wx_login` | String(32) | nullable | 微信第三方登录 |
| `qq_login` | String(32) | nullable | QQ 第三方登录 |

**关联关系**：

| 关联表 | 关系类型 | 说明 |
|--------|---------|------|
| `sys_user_roles` | 多对多 | 用户 ↔ 角色 |
| `sys_user_positions` | 多对多 | 用户 ↔ 岗位 |
| `sys_user_tenant` | 多对多 | 用户 ↔ 租户（跨租户支持） |

### 5.3 业务规则

| 类别 | 规则 |
|------|------|
| **创建** | username 字母开头、3~32位；不允许创建超管；username/mobile/email 唯一 |
| **修改** | 不可修改超管；username/mobile/email 唯一性检查；部门必须存在且可用 |
| **删除** | 仅已禁用(status=1)用户可删除；不可删除超管；不可删除当前登录用户 |
| **密码** | Bcrypt 加密存储；修改需验证原密码；重置不可操作超管 |
| **导入导出** | 支持 Excel 导入导出；导入时校验字段合法性 |
| **状态** | 批量启用/禁用；不可操作超管 |

### 5.4 当前用户菜单权限

```
get_current_user_info_service:
  ├── 超管 → 返回全部 PC 端菜单（type=1/2/4, client=pc）
  └── 普通用户：
        ├── 收集角色菜单 ID（角色→菜单，去重）
        ├── 与租户可用菜单取交集
        └── 构建菜单树返回
```

### 5.5 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/user/detail/{id}` | 用户详情 |
| GET | `/user/list` | 用户列表 |
| POST | `/user/create` | 创建用户 |
| PUT | `/user/update/{id}` | 更新用户 |
| DELETE | `/user/delete` | 删除用户（批量） |
| PATCH | `/user/available/setting` | 批量设置用户状态 |
| GET | `/user/current/info` | 获取当前用户信息（含菜单树） |
| PUT | `/user/current/update` | 更新当前用户信息 |
| PUT | `/user/current/password/change` | 修改密码（本人操作，需验证原密码） |
| PUT | `/user/password/reset` | 重置密码（管理员操作，跳过原密码） |
| POST | `/user/import` | 导入用户（Excel） |
| POST | `/user/export` | 导出用户（Excel） |

---

## 6. Role 角色模块

### 6.1 业务描述

角色是权限分配的核心载体，每个角色可绑定多个菜单（功能权限）和多个部门（数据权限）。角色数据按租户严格隔离。

### 6.2 数据模型

**表名**：`sys_role`（TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 角色名称 |
| `code` | String(64) | NOT NULL, UNIQUE(tenant_id) | 角色编码 |
| `order` | Integer | default=999 | 显示排序 |
| `data_scope` | Integer | default=1 | 数据权限范围（1~5） |

**关联关系**：

| 关联表 | 关系类型 | 说明 |
|--------|---------|------|
| `sys_role_menus` | 多对多 | 角色 ↔ 菜单 |
| `sys_role_depts` | 多对多 | 角色 ↔ 部门（仅 data_scope=5 时使用） |
| `sys_user_roles` | 多对多 | 用户 ↔ 角色 |

### 6.3 业务规则

| 规则 | 说明 |
|------|------|
| **编码规则** | 字母开头，仅含字母/数字/下划线 |
| **租户唯一** | (tenant_id, code) 唯一约束 |
| **权限策略** | `USER_ROLE` — 非超管用户只能看到自己绑定的角色 |
| **菜单约束** | 非超管只能为角色分配租户可用菜单内的菜单，越权时抛出异常含菜单名称 |
| **数据范围** | 1=仅本人 2=本部门 3=本部门及以下 4=全部 5=自定义（绑定部门） |

### 6.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/role/detail/{id}` | 角色详情 |
| GET | `/role/list` | 角色列表 |
| POST | `/role/create` | 创建角色 |
| PUT | `/role/update/{id}` | 更新角色 |
| DELETE | `/role/delete` | 删除角色（批量） |
| PATCH | `/role/available/setting` | 批量设置角色状态 |
| PUT | `/role/menus` | 设置角色菜单 |
| PUT | `/role/permission` | 设置角色权限（含数据范围+部门） |

---

## 7. Dept 部门模块

### 7.1 业务描述

部门是组织架构的核心，采用树形结构支持无限层级。部门数据按租户严格隔离。

### 7.2 数据模型

**表名**：`sys_dept`（TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 部门名称 |
| `code` | String(64) | NOT NULL, UNIQUE(tenant_id, code) | 部门编码 |
| `parent_id` | Integer FK | nullable | 父级部门 |
| `order` | Integer | default=999 | 显示排序 |
| `leader` | String(32) | nullable | 负责人 |
| `phone` | String(20) | nullable | 联系电话 |
| `email` | String(128) | nullable | 邮箱 |

### 7.3 业务规则

| 规则 | 说明 |
|------|------|
| **树形结构** | parent_id 自引用，支持无限层级。创建/更新 parent_id 时需检测循环引用 |
| **编码规则** | 字母开头，仅含字母/数字/下划线 |
| **租户唯一** | (tenant_id, code) 唯一约束 |
| **权限策略** | `DEPT_BASED` — 基于部门范围过滤 |
| **删除约束** | 有子部门的父部门不可删除 |
| **状态级联** | 父部门禁用时子部门同步禁用（业务层实现） |

### 7.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dept/detail/{id}` | 部门详情 |
| GET | `/dept/list` | 部门列表（树形） |
| POST | `/dept/create` | 创建部门 |
| PUT | `/dept/update/{id}` | 更新部门 |
| DELETE | `/dept/delete` | 删除部门（批量） |
| PATCH | `/dept/available/setting` | 批量设置部门状态 |

---

## 8. Position 岗位模块

### 8.1 业务描述

岗位用于定义用户在组织内的职务角色，一个用户可绑定多个岗位。

### 8.2 数据模型

**表名**：`sys_position`（TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 岗位名称 |
| `order` | Integer | default=1 | 显示排序 |

### 8.3 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/position/detail/{id}` | 岗位详情 |
| GET | `/position/list` | 岗位列表 |
| POST | `/position/create` | 创建岗位 |
| PUT | `/position/update/{id}` | 更新岗位 |
| DELETE | `/position/delete` | 删除岗位（批量） |
| PATCH | `/position/available/setting` | 批量设置岗位状态 |

---

## 9. Menu 菜单模块

### 9.1 业务描述

菜单是系统功能权限的基础定义单元，属于**平台级资源**（无 tenant_id），由超级管理员统一管理。菜单以树形结构组织，支撑前端动态路由和后端权限控制。

### 9.2 数据模型

**表名**：`sys_menu`（ModelMixin，**无 TenantMixin**）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(50) | NOT NULL | 菜单名称 |
| `type` | Integer | NOT NULL, default=2 | 类型（1:目录 2:菜单 3:按钮 4:外链） |
| `order` | Integer | NOT NULL, default=999 | 显示排序 |
| `permission` | String(100) | nullable | 权限标识（如 `system:user:query`） |
| `icon` | String(50) | nullable | 菜单图标 |
| `route_name` | String(100) | nullable | 路由名称 |
| `route_path` | String(200) | nullable | 路由路径（以 `/` 开头） |
| `component_path` | String(200) | nullable | 组件路径（不能以 `/` 开头） |
| `redirect` | String(200) | nullable | 重定向地址 |
| `hidden` | Boolean | default=False | 是否隐藏 |
| `keep_alive` | Boolean | default=True | 是否缓存 |
| `always_show` | Boolean | default=False | 是否始终显示 |
| `title` | String(50) | nullable | 菜单标题 |
| `params` | JSON | nullable | 路由参数 |
| `affix` | Boolean | default=False | 是否固定标签页 |
| `client` | String(20) | NOT NULL, default="pc" | 终端（pc/app） |
| `parent_id` | FK→sys_menu.id | nullable, ON DELETE SET NULL | 父菜单 |

### 9.3 菜单类型

| 类型 | 说明 | 路由 | 前端行为 |
|------|------|------|---------|
| 1 | 目录 | 无 | 展开项，不可点击 |
| 2 | 菜单 | 有 | 可点击进入页面 |
| 3 | 按钮/权限 | 无 | 页面内操作权限标识 |
| 4 | 外部链接 | 有 | 跳转外部 URL |

### 9.4 业务规则

| 规则 | 说明 |
|------|------|
| **平台资源** | 无 tenant_id，所有租户共享菜单池 |
| **路由规则** | `route_path` 以 `/` 开头，`component_path` 不能以 `/` 开头 |
| **类型校验** | ge=1, le=4 |
| **client 过滤** | 前端菜单渲染仅取 `client="pc"` 的菜单 |
| **权限策略** | `ROLE_BASED` — 非超管用户按角色菜单过滤 |
| **树形结构** | parent_id 自引用，children 按 order 排序。创建/更新 parent_id 时需检测循环引用（如 A→B→C→A），禁止导致循环的操作 |

### 9.5 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/menu/detail/{id}` | 菜单详情 |
| GET | `/menu/list` | 菜单列表（树形） |
| POST | `/menu/create` | 创建菜单 |
| PUT | `/menu/update/{id}` | 更新菜单 |
| DELETE | `/menu/delete` | 删除菜单（批量） |

---

## 10. Dict 字典模块

### 10.1 业务描述

字典模块提供统一的类型-数据管理，用于维护系统中固定的下拉选项和枚举值。字典数据支持**平台共享**（tenant_id=1 的平台字典对所有租户可读）。

### 10.2 数据模型

#### DictType（sys_dict_type）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `dict_name` | String(64) | NOT NULL | 字典名称 |
| `dict_type` | String(255) | NOT NULL, UNIQUE(tenant_id) | 字典类型编码 |

**平台共享**：`__platform_data_shared__ = True`

#### DictData（sys_dict_data）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `dict_sort` | Integer | default=0 | 排序 |
| `dict_label` | String(255) | NOT NULL | 字典标签 |
| `dict_value` | String(255) | NOT NULL | 字典键值 |
| `css_class` | String(255) | nullable | 样式属性 |
| `list_class` | String(255) | nullable | 表格回显样式 |
| `is_default` | Boolean | default=False | 是否默认 |
| `dict_type` | String(255) | NOT NULL | 字典类型（冗余字段） |
| `dict_type_id` | FK→sys_dict_type.id | NOT NULL, ON DELETE CASCADE | 字典类型 ID |

### 10.3 业务规则

| 规则 | 说明 |
|------|------|
| **平台共享** | tenant_id=1 的字典对所有租户可读。**写保护**：修改/删除 tenant_id=1 的平台字典数据时，仅允许超管操作，普通租户管理员不可修改平台字典 |
| **编码规则** | dict_type 以小写字母开头，仅含小写字母/数字/下划线 |
| **级联删除** | 删除 DictType 时，关联的 DictData 自动级联删除 |
| **双关联** | DictData 同时保留 dict_type（字符串冗余）和 dict_type_id（FK）双重关联。`dict_type` 为冗余字段，用于避免频繁 JOIN DictType 表获取类型编码。两者应保持一致，业务层插入时自动填充 dict_type 并与 dict_type_id 对应 |
| **唯一约束** | DictData 表：`UNIQUE(tenant_id, dict_type_id, dict_value)`，同一字典类型下不可有重复的 dict_value |

### 10.4 API 端点

#### 字典类型

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dict/type/detail/{id}` | 字典类型详情 |
| GET | `/dict/type/list` | 字典类型列表 |
| POST | `/dict/type/create` | 创建字典类型 |
| PUT | `/dict/type/update/{id}` | 更新字典类型 |
| DELETE | `/dict/type/delete` | 删除字典类型（批量） |

#### 字典数据

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dict/data/detail/{id}` | 字典数据详情 |
| GET | `/dict/data/list` | 字典数据列表 |
| POST | `/dict/data/create` | 创建字典数据 |
| PUT | `/dict/data/update/{id}` | 更新字典数据 |
| DELETE | `/dict/data/delete` | 删除字典数据（批量） |

---

## 11. Notice 通知公告模块

### 11.1 业务描述

管理租户内部的通知和公告发布。通知数据按租户严格隔离。

### 11.2 数据模型

**表名**：`sys_notice`（TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `notice_title` | String(64) | NOT NULL | 公告标题 |
| `notice_type` | String(1) | NOT NULL | 类型（1:通知 2:公告） |
| `notice_content` | Text | nullable | 公告内容（富文本，XSS 过滤） |

### 11.3 业务规则

| 规则 | 说明 |
|------|------|
| **类型校验** | 仅支持 "1"(通知) 和 "2"(公告) |
| **XSS 防护** | notice_content 经过 `sanitize_html` 清洗 |

### 11.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/notice/detail/{id}` | 公告详情 |
| GET | `/notice/list` | 公告列表 |
| POST | `/notice/create` | 创建公告 |
| PUT | `/notice/update/{id}` | 更新公告 |
| DELETE | `/notice/delete` | 删除公告（批量） |
| PATCH | `/notice/available/setting` | 批量设置公告状态 |

---

## 12. Params 系统参数模块

### 12.1 业务描述

管理系统级别的配置参数，支持区分系统内置参数（不可删除）和自定义参数。参数数据按租户隔离。

### 12.2 数据模型

**表名**：`sys_param`（TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `config_name` | String(64) | NOT NULL | 参数名称 |
| `config_key` | String(500) | NOT NULL | 参数键名 |
| `config_value` | String(500) | nullable | 参数键值 |
| `config_type` | Boolean | default=False | 是否系统内置 |

### 12.3 业务规则

| 规则 | 说明 |
|------|------|
| **键名规则** | 小写字母开头，仅含小写字母/数字/_.- |
| **系统内置** | config_type=True 的参数不允许删除（业务层实现） |

### 12.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/params/detail/{id}` | 参数详情 |
| GET | `/params/list` | 参数列表 |
| POST | `/params/create` | 创建参数 |
| PUT | `/params/update/{id}` | 更新参数 |
| DELETE | `/params/delete` | 删除参数（批量） |

---

## 13. Log 日志模块

### 13.1 业务描述

记录系统的操作日志和登录日志，用于审计和问题追踪。通过 `OperationLogRoute` 路由类自动记录操作日志。日志数据按租户隔离。

### 13.2 数据模型

**表名**：`sys_log`（TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `type` | Integer | NOT NULL | 日志类型（1:登录日志 2:操作日志） |
| `request_path` | String(255) | NOT NULL | 请求路径 |
| `request_method` | String(10) | NOT NULL | 请求方法 |
| `request_payload` | LONGTEXT/TEXT | nullable | 请求体 |
| `request_ip` | String(50) | nullable | 请求 IP |
| `login_location` | String(255) | nullable | 登录位置 |
| `request_os` | String(64) | nullable | 操作系统 |
| `request_browser` | String(64) | nullable | 浏览器 |
| `response_code` | Integer | NOT NULL | 响应状态码 |
| `response_json` | LONGTEXT/TEXT | nullable | 响应体 |
| `process_time` | String(20) | nullable | 处理耗时 |

### 13.3 存储适配

| 数据库 | 大字段类型 |
|--------|-----------|
| MySQL | LONGTEXT |
| PostgreSQL | TEXT |
| SQLite | Text |

### 13.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/log/detail/{id}` | 日志详情 |
| GET | `/log/list` | 日志列表 |
| DELETE | `/log/delete` | 删除日志（批量） |

---

## 14. Tenant 租户管理模块

### 14.1 业务描述

租户是 SaaS 平台的核心概念，代表一个独立的组织。租户管理包含：租户定义、配额管理、配置管理、用户关联、自定义菜单授权。

### 14.2 数据模型

#### 核心表：sys_tenant（ModelMixin，无 TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(100) | NOT NULL, UNIQUE | 租户名称 |
| `code` | String(100) | NOT NULL, UNIQUE | 租户编码（字母数字） |
| `contact_name` | String(64) | nullable | 联系人 |
| `contact_phone` | String(20) | nullable | 联系电话 |
| `contact_email` | String(128) | nullable | 联系邮箱 |
| `address` | String(255) | nullable | 地址 |
| `domain` | String(255) | nullable | 自定义域名 |
| `logo_url` | String(500) | nullable | Logo URL |
| `sort` | Integer | default=0 | 排序 |
| `package_id` | FK→sys_tenant_package.id | nullable, ON DELETE SET NULL | 关联套餐 |
| `start_time` | DateTime | nullable | 开始时间 |
| `end_time` | DateTime | nullable | 结束时间 |

#### 子表

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `sys_user_tenant` | 用户-租户关联 | user_id, tenant_id, role(owner/admin/member), is_default |
| `sys_tenant_quota` | 租户配额 | max_users(50), max_roles(20), max_storage_mb(500), max_depts(50) |
| `sys_tenant_config` | 租户配置 | config_key, config_value, config_type(string/json/int/bool)，仅限 4 种类型，Schema 层校验 |
| `sys_tenant_menu` | 租户自定义菜单 | tenant_id, menu_id, UNIQUE(tenant_id, menu_id) |

### 14.3 核心业务流程

#### 创建租户

```
POST /tenant/create
  ├── 创建租户记录（sys_tenant）
  ├── 生成初始管理员：{code}_admin + 随机12位密码（含特殊字符）
  ├── 初始化租户配额（sys_tenant_quota，默认值）
  └── 返回租户信息 + 初始管理员凭据（日志输出）
```

#### 删除租户

```
DELETE /tenant/delete
  ├── 系统租户(id=1)不可删除
  ├── 检查关联数据：用户/部门/角色/岗位
  ├── 有关联数据时拒绝删除，提示需先清理
  └── 通过则删除
```

#### 套餐变更

```
PUT /tenant/update/{id} (package_id 变更)
  ├── 仅超管可操作
  ├── 更新 tenant.package_id
  ├── 获取新可用菜单 ID（套餐菜单 ∪ 自定义菜单）
  ├── 清理角色中不再可用的菜单关联
  └── 完成
```

### 14.4 业务规则

| 类别 | 规则 |
|------|------|
| **系统租户** | id=1 不可删除、禁用、修改编码 |
| **编码** | 仅含字母和数字，用于生成初始管理员用户名 |
| **初始管理员** | 自动创建，用户名 `{code}_admin`，密码 12 位随机（含特殊字符）。注：初始管理员无角色关联，登录后看不到菜单，需超管先为该租户分配角色后再绑定给初始管理员 |
| **配额** | 创建租户时自动初始化默认值 |
| **owner 保护** | 每个租户至少保留一个 owner。从租户移除用户时，检查该用户是否为该租户的唯一 owner，是则拒绝移除。修改用户租户角色时，禁止将最后一个 owner 降级为 member |
| **配额执行** | 租户配额在创建资源时执行检查。UserCRUD.create 检查 max_users，RoleCRUD.create 检查 max_roles，DeptCRUD.create 检查 max_depts。达到上限时拒绝创建并提示 |
| **默认租户** | 用户首次加入的租户自动设为默认，设置新默认时清除旧默认 |
| **多租户** | 一个用户可关联多个租户 |

### 14.5 配置缓存策略

| 机制 | 说明 |
|------|------|
| **缓存 key** | `tenant_config:{tenant_id}:{config_key}` |
| **读取策略** | 优先读 Redis，未命中回源 DB 并写回缓存 |
| **更新策略** | 更新后自动同步刷新 Redis |
| **预热** | 应用启动时 `init_tenant_config_cache` 预加载所有配置 |

### 14.6 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tenant/detail/{id}` | 租户详情 |
| GET | `/tenant/list` | 租户列表 |
| POST | `/tenant/create` | 创建租户（自动配管理员） |
| PUT | `/tenant/update/{id}` | 修改租户 |
| DELETE | `/tenant/delete` | 删除租户（批量） |
| PATCH | `/tenant/available/setting` | 批量修改状态 |
| PUT | `/tenant/status/{id}` | 启/禁用单个租户 |
| GET | `/tenant/{id}/users` | 获取租户用户列表 |
| POST | `/tenant/{id}/users` | 向租户添加用户 |
| DELETE | `/tenant/{id}/users/{uid}` | 从租户移除用户 |
| GET | `/tenant/{id}/quota` | 获取租户配额 |
| PUT | `/tenant/{id}/quota` | 修改租户配额 |
| GET | `/tenant/{id}/config` | 获取租户配置 |
| GET | `/tenant/{id}/config/info` | 获取租户配置（公开，缓存） |
| PUT | `/tenant/{id}/config` | 批量更新配置 |
| GET | `/tenant/{id}/menus` | 获取租户自定义菜单 |
| PUT | `/tenant/{id}/menus` | 设置租户自定义菜单 |

---

## 15. Package 套餐模块

### 15.1 业务描述

套餐是预定义的功能菜单集合，用于标准化租户授权流程。通过套餐体系可以减少逐个分配菜单的工作量，实现基础版/专业版/企业版等分级授权。

### 15.2 数据模型

#### sys_tenant_package

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(100) | NOT NULL, UNIQUE | 套餐名称 |
| `code` | String(100) | NOT NULL, UNIQUE | 套餐编码 |
| `status` | String | default="0" | 状态（0:正常 1:禁用） |
| `sort` | Integer | default=0 | 排序 |

#### sys_tenant_package_menu

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `package_id` | FK→sys_tenant_package.id | PK, ON DELETE CASCADE | 套餐 ID |
| `menu_id` | FK→sys_menu.id | PK, ON DELETE CASCADE | 菜单 ID |

唯一约束：`(package_id, menu_id)`

### 15.3 核心流程

#### 租户可用菜单合并逻辑

```
get_tenant_available_menu_ids(tenant_id):
  可用菜单 = set()
  
  # 1. 如果租户关联了套餐，取出套餐的所有菜单
  if tenant.package_id:
      可用菜单.add(套餐菜单...)
  
  # 2. 取出租户自定义授权菜单（sys_tenant_menu）
  可用菜单.add(自定义菜单...)
  
  return list(可用菜单)  # 并集
```

#### 套餐变更后清理

```
套餐变更 → 取新可用菜单 ID →
查询该租户所有角色 → 删除角色中不在可用菜单内的 RoleMenus 记录 → 完成
```

### 15.4 业务规则

| 规则 | 说明 |
|------|------|
| **套餐变更** | 仅超管可操作 |
| **删除约束** | 删除前检查是否有租户使用，有则拒绝 |
| **级联策略** | 套餐删除时，租户 package_id SET NULL |
| **菜单设置** | 套餐菜单全量替换（先删后插） |
| **套餐禁用** | 套餐 status=1 时，已关联该套餐的租户在 `get_tenant_available_menu_ids` 中**不再计入**套餐菜单，仅保留租户自定义菜单（sys_tenant_menu）。恢复 status=0 后套餐菜单自动恢复 |
| **套餐已删** | 套餐被删除（package_id SET NULL）后，租户降级为仅有自定义菜单，需及时为受影响租户迁移或补配权限 |

### 15.5 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tenant/package/detail/{id}` | 套餐详情 |
| GET | `/tenant/package/list` | 套餐列表 |
| POST | `/tenant/package/create` | 创建套餐 |
| PUT | `/tenant/package/update/{id}` | 修改套餐 |
| DELETE | `/tenant/package/delete` | 删除套餐 |
| GET | `/tenant/package/{id}/menus` | 获取套餐菜单 |
| PUT | `/tenant/package/{id}/menus` | 设置套餐菜单（全量替换） |

---

## 16. Ticket 工单模块

### 16.1 业务描述

工单系统用于用户提交反馈、建议和缺陷报告，支持指派处理人进行跟踪处理。工单数据按租户隔离。

### 16.2 数据模型

**表名**：`sys_ticket`（TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `title` | String(200) | NOT NULL | 工单标题 |
| `ticket_content` | Text | nullable | 工单内容（富文本） |
| `summary` | Text | nullable | 工单内容（纯文本摘要） |
| `ticket_type` | String(20) | NOT NULL, default="suggestion" | 类型（suggestion/bug/optimize/other） |
| `status` | String(10) | NOT NULL, default="0" | 状态（0:待处理 1:处理中 2:已完成 3:已关闭） |
| `images` | Text | nullable | 图片 URL 列表（JSON 数组） |
| `reply` | Text | nullable | 回复内容 |
| `assigned_id` | FK→sys_user.id | nullable, ON DELETE SET NULL | 处理人 |

### 16.3 状态流转

```
待处理(0) → 处理中(1) → 已完成(2)
   ↑            │
   └──── 已关闭(3)
```

#### 状态转换规则

| 源状态 | 目标状态 | 允许角色 | 说明 |
|-------|---------|---------|------|
| 待处理(0) | 处理中(1) | 创建人/处理人/超管 | 确认受理 |
| 待处理(0) | 已关闭(3) | 创建人/超管 | 取消提交 |
| 处理中(1) | 已完成(2) | 处理人/超管 | 处理完成 |
| 处理中(1) | 已关闭(3) | 创建人/处理人/超管 | 强行关闭（需填写原因） |
| 已完成(2) | 已关闭(3) | 创建人/超管 | 确认关闭 |
| 已关闭(3) | 待处理(0) | 超管 | 仅超管可重新打开 |

> 非法转换（如已完成→处理中）应在 Service 层校验并拒绝 |

### 16.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/ticket/detail/{id}` | 工单详情 |
| GET | `/ticket/list` | 工单列表 |
| POST | `/ticket/create` | 创建工单 |
| PUT | `/ticket/update/{id}` | 更新工单 |
| DELETE | `/ticket/delete` | 删除工单（批量） |
| PUT | `/ticket/batch/status` | 批量更新工单状态 |

---

## 17. Plugin 插件模块

### 17.1 业务描述

插件系统是平台的扩展机制。`sys_plugin` 作为插件注册表（平台级资源），记录所有可用插件的元数据。租户通过 `sys_tenant_plugin` 关联表安装插件。

### 17.2 数据模型

#### sys_plugin（平台资源，无 TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(100) | NOT NULL, UNIQUE | 插件名称 |
| `code` | String(50) | NOT NULL, UNIQUE | 插件编码（module_xxx） |
| `description` | Text | nullable | 插件描述 |
| `version` | String(20) | NOT NULL, default="1.0.0" | 版本号 |
| `author` | String(100) | nullable | 作者 |
| `icon` | String(500) | nullable | 图标 URL |
| `category` | String(20) | NOT NULL, default="tool" | 分类（tool/ai/monitor/business） |
| `price` | Integer | NOT NULL, default=0 | 价格（分，0=免费） |
| `menu_path` | String(200) | nullable | 菜单路径（安装后显示） |
| `permission_prefix` | String(100) | nullable | 权限前缀 |
| `dependencies` | Text | nullable | 依赖插件编码（JSON 数组） |
| `sort` | Integer | NOT NULL, default=0 | 排序 |

#### sys_tenant_plugin

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `tenant_id` | FK→sys_tenant.id | NOT NULL, ON DELETE CASCADE | 租户 ID |
| `plugin_id` | FK→sys_plugin.id | NOT NULL, ON DELETE CASCADE | 插件 ID |
| `enabled` | String(1) | NOT NULL, default="1" | 启用（1:启用 0:禁用） |
| `installed_time` | DateTime | NOT NULL | 安装时间 |

唯一约束：`(tenant_id, plugin_id)`

### 17.3 插件目录结构

```
plugin/module_xxx/
├── __init__.py
├── plugin.toml          # 插件元数据（名称、版本、路由前缀等）
├── controller.py
├── service.py
├── crud.py
├── model.py
└── schema.py
```

已内置插件：
- `module_ai/chat` — AI 对话
- `module_example/demo` — 示例
- `module_generator/gencode` — 代码生成器
- `module_task/cronjob` — 定时任务
- `module_task/workflow` — 工作流引擎

### 17.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/plugin/detail/{id}` | 插件详情 |
| GET | `/plugin/list` | 插件列表（含当前租户安装状态） |
| POST | `/plugin/create` | 创建插件 |
| PUT | `/plugin/update/{id}` | 更新插件 |
| DELETE | `/plugin/delete` | 删除插件（批量） |
| POST | `/plugin/install` | 租户安装插件 |
| POST | `/plugin/uninstall` | 租户卸载插件 |

---

## 18. 到期处理

### 18.1 自动禁用逻辑

定时任务 `check_tenant_expiry` 定期扫描所有正常状态的租户：

1. 遍历 `status=0` 且 `end_time` 不为空的租户
2. 如 `end_time <= now`：自动设为禁用（`status=1`）
3. 如 `end_time` 在 30天/7天/1天 内：触发到期提醒

### 18.2 到期后行为

| 场景 | 行为 |
|------|------|
| **登录拦截** | 租户被禁用后，AuthService.login 检查 tenant.status，对 status!=0 的租户拒绝登录 |
| **数据状态** | 租户数据保留（不变更），仅禁止新的写入操作 |
| **恢复机制** | 超管手动恢复 status=0 后功能正常，无需额外操作 |
| **定时频率** | 每小时检查一次 |

### 18.3 提醒方式

当前为日志输出，预留邮件/短信通知扩展点。

---

# Part 3：附录

---

## 19. API 接口汇总

### 19.1 认证模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录 |
| POST | `/auth/token/refresh` | 刷新 token |
| POST | `/auth/logout` | 退出登录 |
| GET | `/auth/captcha` | 验证码 |
| POST | `/auth/register` | 注册 |
| POST | `/auth/select/tenant` | 选择租户 |
| POST | `/auth/forget/password` | 忘记密码 |

### 19.2 用户模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/user/detail/{id}` | user:query | 详情 |
| GET | `/user/list` | user:query | 列表 |
| POST | `/user/create` | user:create | 创建 |
| PUT | `/user/update/{id}` | user:update | 更新 |
| DELETE | `/user/delete` | user:delete | 删除 |
| PATCH | `/user/available/setting` | user:patch | 批量设状态 |
| GET | `/user/current/info` | - | 当前用户信息 |
| PUT | `/user/current/update` | - | 更新当前用户 |
| PUT | `/user/current/password/change` | - | 改密码（本人操作） |
| PUT | `/user/password/reset` | user:update | 重置密码（管理员操作） |
| POST | `/user/import` | user:create | 导入 |
| POST | `/user/export` | user:query | 导出 |

### 19.3 角色模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/role/detail/{id}` | role:query | 详情 |
| GET | `/role/list` | role:query | 列表 |
| POST | `/role/create` | role:create | 创建 |
| PUT | `/role/update/{id}` | role:update | 更新 |
| DELETE | `/role/delete` | role:delete | 删除 |
| PATCH | `/role/available/setting` | role:patch | 批量设状态 |
| PUT | `/role/menus` | role:update | 设置菜单 |
| PUT | `/role/permission` | role:update | 设置权限 |

### 19.4 部门模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/dept/detail/{id}` | dept:query | 详情 |
| GET | `/dept/list` | dept:query | 列表 |
| POST | `/dept/create` | dept:create | 创建 |
| PUT | `/dept/update/{id}` | dept:update | 更新 |
| DELETE | `/dept/delete` | dept:delete | 删除 |
| PATCH | `/dept/available/setting` | dept:patch | 批量设状态 |

### 19.5 岗位模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/position/detail/{id}` | position:query | 详情 |
| GET | `/position/list` | position:query | 列表 |
| POST | `/position/create` | position:create | 创建 |
| PUT | `/position/update/{id}` | position:update | 更新 |
| DELETE | `/position/delete` | position:delete | 删除 |
| PATCH | `/position/available/setting` | position:patch | 批量设状态 |

### 19.6 菜单模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/menu/detail/{id}` | menu:query | 详情 |
| GET | `/menu/list` | menu:query | 列表 |
| POST | `/menu/create` | menu:create | 创建 |
| PUT | `/menu/update/{id}` | menu:update | 更新 |
| DELETE | `/menu/delete` | menu:delete | 删除 |
| PATCH | `/menu/available/setting` | menu:patch | 批量设状态 |

### 19.7 字典模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/dict/type/detail/{id}` | dict:query | 字典类型详情 |
| GET | `/dict/type/list` | dict:query | 字典类型列表 |
| POST | `/dict/type/create` | dict:create | 创建字典类型 |
| PUT | `/dict/type/update/{id}` | dict:update | 更新字典类型 |
| DELETE | `/dict/type/delete` | dict:delete | 删除字典类型 |
| PATCH | `/dict/type/available/setting` | dict:patch | 批量设状态 |
| GET | `/dict/data/detail/{id}` | dict:query | 字典数据详情 |
| GET | `/dict/data/list` | dict:query | 字典数据列表 |
| POST | `/dict/data/create` | dict:create | 创建字典数据 |
| PUT | `/dict/data/update/{id}` | dict:update | 更新字典数据 |
| DELETE | `/dict/data/delete` | dict:delete | 删除字典数据 |

### 19.8 通知公告

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/notice/detail/{id}` | notice:query | 详情 |
| GET | `/notice/list` | notice:query | 列表 |
| POST | `/notice/create` | notice:create | 创建 |
| PUT | `/notice/update/{id}` | notice:update | 更新 |
| DELETE | `/notice/delete` | notice:delete | 删除 |
| PATCH | `/notice/available/setting` | notice:patch | 批量设状态 |

### 19.9 系统参数

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/params/detail/{id}` | params:query | 详情 |
| GET | `/params/list` | params:query | 列表 |
| POST | `/params/create` | params:create | 创建 |
| PUT | `/params/update/{id}` | params:update | 更新 |
| DELETE | `/params/delete` | params:delete | 删除 |
| PATCH | `/params/available/setting` | params:patch | 批量设状态 |

### 19.10 日志模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/log/detail/{id}` | log:query | 详情 |
| GET | `/log/list` | log:query | 列表 |
| DELETE | `/log/delete` | log:delete | 删除 |

### 19.11 工单模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/ticket/detail/{id}` | ticket:query | 详情 |
| GET | `/ticket/list` | ticket:query | 列表 |
| POST | `/ticket/create` | ticket:create | 创建 |
| PUT | `/ticket/update/{id}` | ticket:update | 更新 |
| DELETE | `/ticket/delete` | ticket:delete | 删除 |
| PATCH | `/ticket/available/setting` | ticket:patch | 批量设状态 |
| PUT | `/ticket/batch/status` | ticket:update | 批量更新状态 |

### 19.12 插件模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/plugin/detail/{id}` | plugin:query | 详情 |
| GET | `/plugin/list` | plugin:query | 列表 |
| POST | `/plugin/create` | plugin:create | 创建 |
| PUT | `/plugin/update/{id}` | plugin:update | 更新 |
| DELETE | `/plugin/delete` | plugin:delete | 删除 |
| PATCH | `/plugin/available/setting` | plugin:patch | 批量设状态 |
| POST | `/plugin/install` | - | 安装插件 |
| POST | `/plugin/uninstall` | - | 卸载插件 |

### 19.13 租户模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/tenant/detail/{id}` | tenant:query | 详情 |
| GET | `/tenant/list` | tenant:query | 列表 |
| POST | `/tenant/create` | tenant:create | 创建 |
| PUT | `/tenant/update/{id}` | tenant:update | 更新 |
| DELETE | `/tenant/delete` | tenant:delete | 删除 |
| PATCH | `/tenant/available/setting` | tenant:patch | 批量设状态 |
| PUT | `/tenant/status/{id}` | tenant:update | 启/禁用 |
| GET | `/tenant/{id}/users` | tenant:query | 用户列表 |
| POST | `/tenant/{id}/users` | tenant:update | 添加用户 |
| DELETE | `/tenant/{id}/users/{uid}` | tenant:update | 移除用户 |
| GET | `/tenant/{id}/quota` | tenant:query | 获取配额 |
| PUT | `/tenant/{id}/quota` | tenant:update | 修改配额 |
| GET | `/tenant/{id}/config` | tenant:query | 获取配置 |
| PUT | `/tenant/{id}/config` | tenant:update | 更新配置 |

### 19.14 套餐模块

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/tenant/package/detail/{id}` | package:query | 详情 |
| GET | `/tenant/package/list` | package:query | 列表 |
| POST | `/tenant/package/create` | package:create | 创建 |
| PUT | `/tenant/package/update/{id}` | package:update | 更新 |
| DELETE | `/tenant/package/delete` | package:delete | 删除 |
| GET | `/tenant/package/{id}/menus` | package:query | 获取菜单 |
| PUT | `/tenant/package/{id}/menus` | package:update | 设置菜单 |

### 19.15 监控模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/monitor/health` | 健康检查 |
| GET | `/monitor/metrics` | 性能指标 |
| GET | `/monitor/cache` | 缓存监控 |
| GET | `/monitor/online` | 在线用户 |
| GET | `/monitor/resource` | 资源监控 |
| GET | `/monitor/server` | 服务器信息 |

---

## 20. 数据库表结构

### 20.1 平台资源表（无 tenant_id）

| 表名 | 说明 | 关键索引 |
|------|------|---------|
| `sys_tenant` | 租户 | UNIQUE(name), UNIQUE(code) |
| `sys_tenant_package` | 套餐 | UNIQUE(name), UNIQUE(code) |
| `sys_tenant_package_menu` | 套餐-菜单关联 | UNIQUE(package_id, menu_id) |
| `sys_menu` | 菜单 | - |
| `sys_plugin` | 插件注册表 | UNIQUE(name), UNIQUE(code) |

### 20.2 租户关联表（无 tenant_id，FK→tenant）

| 表名 | 说明 | 关键索引 |
|------|------|---------|
| `sys_tenant_quota` | 租户配额 | UNIQUE(tenant_id) |
| `sys_tenant_config` | 租户配置 | UNIQUE(tenant_id, config_key) |
| `sys_tenant_menu` | 租户自定义菜单 | UNIQUE(tenant_id, menu_id) |
| `sys_tenant_plugin` | 租户安装插件 | UNIQUE(tenant_id, plugin_id) |
| `sys_user_tenant` | 用户-租户关联 | UNIQUE(user_id, tenant_id) |

### 20.3 租户隔离业务表（含 tenant_id）

| 表名 | 说明 | 关键索引 |
|------|------|---------|
| `sys_user` | 用户 | UNIQUE(tenant_id, username) |
| `sys_role` | 角色 | UNIQUE(tenant_id, code) |
| `sys_dept` | 部门 | UNIQUE(tenant_id, code) |
| `sys_position` | 岗位 | - |
| `sys_notice` | 通知公告 | - |
| `sys_param` | 系统参数 | - |
| `sys_log` | 系统日志 | - |
| `sys_ticket` | 工单 | - |

### 20.4 平台共享业务表（含 tenant_id，__platform_data_shared__）

| 表名 | 说明 | 关键索引 |
|------|------|---------|
| `sys_dict_type` | 字典类型 | UNIQUE(tenant_id, dict_type) |
| `sys_dict_data` | 字典数据 | UNIQUE(tenant_id, dict_type_id, dict_value) |

### 20.5 关联表

| 表名 | 说明 | 约束 |
|------|------|------|
| `sys_user_roles` | 用户-角色关联 | PK(user_id, role_id)，ON DELETE CASCADE |
| `sys_user_positions` | 用户-岗位关联 | PK(user_id, position_id)，ON DELETE CASCADE |
| `sys_role_menus` | 角色-菜单关联 | PK(role_id, menu_id)，ON DELETE CASCADE |
| `sys_role_depts` | 角色-部门关联 | PK(role_id, dept_id)，ON DELETE CASCADE |

---

## 21. 安全性要求

1. **JWT 租户上下文**：从 Token 中提取 `tenant_id` 和 `is_super_admin`，通过 ContextVar 在整个请求周期传递
2. **白名单路径**：登录、验证码、健康检查等公开接口不设置租户上下文
3. **系统租户保护**：
   - id=1 不可删除
   - id=1 不可禁用
   - id=1 的编码不可修改
4. **数据删除保护**：删除租户前检查关联数据，防止孤立记录
5. **租户 owner 保护**：每个租户至少保留一个 owner
6. **菜单越权防护**：非超管用户只能在租户可用菜单范围内分配角色菜单
7. **ContextVar 清理**：请求结束后清理 ContextVar，防止跨请求泄漏
8. **密码安全**：Bcrypt 哈希存储，不存储明文
9. **XSS 防护**：通知公告内容经过 `sanitize_html` 清洗
10. **级联策略**：所有 FK 均有 ON DELETE/ON UPDATE 级联策略，保证数据完整性

---

## 22. 未来扩展建议

1. **配额硬限制**：当前配额仅为预设值，需在业务层实现实际限制（如创建用户时检查 max_users）
2. **租户自定义域名**：支持通过 `domain` 字段实现租户专属域名
3. **租户主题/品牌**：通过 `sys_tenant_config` 扩展 Logo、颜色、页面标题等自定义
4. **套餐升降级**：基础版/专业版/企业版分级套餐，切换时的菜单过渡和数据处理
5. **跨租户协作增强**：用户多租户切换时的数据可见性和操作约束
6. **租户审计日志**：记录租户管理操作，便于合规审查
7. **计费集成**：对接支付系统，实现套餐自动续费/过期处理
8. **到期通知扩展**：当前仅日志输出，扩展为邮件/短信/站内信通知

---

## 23. 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v3.1.0 | 2026-06-01 | 初始版本，完整的模块化需求文档 |
| v3.2.0 | 2026-06-02 | 新增 Plugin 子模块需求：AI Chat/Cronjob/Workflow/CodeGen/Demo |


---

# Part 4：Plugin 子模块需求

---

## 24. AI Chat 聊天模块（module_ai/chat）

### 24.1 业务描述

AI 对话模块，提供用户与大模型进行对话的能力。支持多会话管理、WebSocket 流式对话、非流式对话。ChatSession 数据按租户隔离。

### 24.2 数据模型

聊天会话数据存储在外部（具体存储取决于 ChatService 实现，可能为内存/Redis/数据库）。Schema 层定义如下：

#### ChatSessionCreateSchema

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `title` | str | NOT NULL, min_length=1, max_length=200 | 会话标题 |

#### ChatSessionUpdateSchema

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `title` | str | NOT NULL, min_length=1, max_length=200 | 会话标题 |

#### AiChatRequestSchema

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `message` | str | NOT NULL, min_length=1 | 用户消息内容 |
| `session_id` | str | nullable | 会话ID，不传则创建新会话 |

#### AiChatResponseSchema

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `response` | str | NOT NULL | AI 回复内容 |
| `session_id` | str | NOT NULL | 会话ID |
| `function_calls` | list[dict] | nullable | 函数调用信息 |
| `action` | dict | nullable | 建议执行的操作 |

### 24.3 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/chat/detail/{session_id}` | module_ai:chat:detail | 会话详情 |
| GET | `/chat/list` | module_ai:chat:query | 会话列表 |
| POST | `/chat/create` | module_ai:chat:create | 创建会话 |
| PUT | `/chat/update/{session_id}` | module_ai:chat:update | 更新会话 |
| DELETE | `/chat/delete` | module_ai:chat:delete | 删除会话 |
| POST | `/chat/ai-chat` | module_ai:chat:query | AI 对话（非流式） |
| WS | `/chat/ws` | — | WebSocket 流式对话 |

---

## 25. Cronjob 定时任务模块（module_task/cronjob）

### 25.1 业务描述

定时任务模块提供动态节点定义（NodeModel）和任务执行日志记录（JobModel）。节点定义执行代码块、触发器和参数，通过 APScheduler 调度执行。

### 25.2 数据模型

#### NodeModel（task_node，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 节点名称 |
| `code` | String(32) | NOT NULL, UNIQUE(tenant_id, code) | 节点编码 |
| `jobstore` | String(64) | nullable, default="default" | 存储器 |
| `executor` | String(64) | nullable, default="default" | 执行器 |
| `trigger` | String(64) | nullable | 触发器 |
| `trigger_args` | Text | nullable | 触发器参数 |
| `func` | Text | nullable | 代码块（须定义 handler 函数） |
| `args` | Text | nullable | 位置参数 |
| `kwargs` | Text | nullable | 关键字参数 |
| `coalesce` | Boolean | nullable, default=False | 是否合并运行 |
| `max_instances` | Integer | nullable, default=1 | 最大并发实例数 |
| `start_date` | String(64) | nullable | 开始时间 |
| `end_date` | String(64) | nullable | 结束时间 |

#### JobModel（task_job，TenantMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `job_id` | String(64) | NOT NULL, index | 任务ID |
| `job_name` | String(128) | nullable | 任务名称 |
| `trigger_type` | String(32) | nullable | 触发方式：cron/interval/date/manual |
| `status` | String(16) | NOT NULL, default="pending" | 执行状态：pending/running/success/failed/timeout/cancelled |
| `next_run_time` | String(64) | nullable | 下次执行时间 |
| `job_state` | Text | nullable | 任务状态信息 |
| `result` | Text | nullable | 执行结果 |
| `error` | Text | nullable | 错误信息 |

### 25.3 业务规则

| 规则 | 说明 |
|------|------|
| **Node 编码** | 字母开头，仅含字母/数字/下划线 |
| **触发器类型** | 仅支持 now/cron/interval/date |
| **非立即执行** | trigger != "now" 时必须提供 trigger_args |
| **时间校验** | end_date 不能早于 start_date |
| **func 必填** | Node 创建时 func 不能为空 |
| **Job 状态** | 仅支持 pending/running/success/failed/timeout/cancelled |
| **trigger_type** | 仅支持 cron/interval/date/manual |

### 25.4 API 端点

#### Node（节点）

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/cronjob/node/detail/{id}` | module_task:cronjob:query | 节点详情 |
| GET | `/cronjob/node/list` | module_task:cronjob:query | 节点列表 |
| POST | `/cronjob/node/create` | module_task:cronjob:create | 创建节点 |
| PUT | `/cronjob/node/update/{id}` | module_task:cronjob:update | 更新节点 |
| DELETE | `/cronjob/node/delete` | module_task:cronjob:delete | 删除节点 |
| PATCH | `/cronjob/node/available/setting` | module_task:cronjob:patch | 批量设状态 |
| POST | `/cronjob/node/execute/{id}` | module_task:cronjob:update | 执行节点 |

#### Job（执行日志）

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/cronjob/job/detail/{id}` | module_task:cronjob:query | 日志详情 |
| GET | `/cronjob/job/list` | module_task:cronjob:query | 日志列表 |
| DELETE | `/cronjob/job/delete` | module_task:cronjob:delete | 删除日志 |

---

## 26. Workflow 工作流模块（module_task/workflow）

### 26.1 业务描述

工作流模块提供可视化流程编排和执行能力。基于 Vue Flow 画布定义流程节点和连线，通过 Prefect 引擎执行。数据按租户隔离。

### 26.2 数据模型

#### WorkflowModel（task_workflow，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(128) | NOT NULL | 流程名称 |
| `code` | String(64) | NOT NULL, UNIQUE(tenant_id, code) | 流程编码 |
| `workflow_status` | String(32) | NOT NULL, default="draft" | 状态：draft/published/archived |
| `nodes` | JSON | nullable | Vue Flow nodes JSON |
| `edges` | JSON | nullable | Vue Flow edges JSON |

#### WorkflowNodeTypeModel（task_workflow_node_type，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(128) | NOT NULL | 显示名称 |
| `code` | String(64) | NOT NULL, UNIQUE(tenant_id, code) | 节点编码，对应画布 node.type |
| `category` | String(32) | NOT NULL, default="action" | 分类：trigger/action/condition/control |
| `func` | Text | NOT NULL | Python 代码块（须定义 handler） |
| `args` | Text | nullable | 默认位置参数，逗号分隔 |
| `kwargs` | Text | nullable | 默认关键字参数 JSON |
| `sort_order` | Integer | NOT NULL, default=0 | 排序 |
| `is_active` | Boolean | NOT NULL, default=True | 是否启用 |

### 26.3 业务规则

| 规则 | 说明 |
|------|------|
| **Workflow 编码** | 字母开头，仅含字母/数字/下划线 |
| **Workflow 状态** | 仅支持 draft（草稿）、published（已发布）、archived（已归档） |
| **NodeType 分类** | 仅支持 trigger（触发器）、action（动作）、condition（条件）、control（控制） |
| **发布流程** | 发布时可选备注（remark），由 draft → published |
| **执行流程** | 需传入 workflow_id 和可选的 variables/business_key/job_id |
| **执行结果** | 返回 completed/failed 状态及各节点执行结果 |

### 26.4 API 端点

#### Workflow（流程定义）

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/workflow/definition/detail/{id}` | module_task:workflow:query | 流程详情 |
| GET | `/workflow/definition/list` | module_task:workflow:query | 流程列表 |
| POST | `/workflow/definition/create` | module_task:workflow:create | 创建流程 |
| PUT | `/workflow/definition/update/{id}` | module_task:workflow:update | 更新流程 |
| DELETE | `/workflow/definition/delete` | module_task:workflow:delete | 删除流程 |
| POST | `/workflow/definition/publish/{id}` | module_task:workflow:update | 发布流程 |
| POST | `/workflow/definition/execute/{id}` | module_task:workflow:update | 执行流程 |

#### NodeType（节点类型）

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/workflow/node-type/detail/{id}` | module_task:workflow:query | 节点详情 |
| GET | `/workflow/node-type/list` | module_task:workflow:query | 节点列表 |
| POST | `/workflow/node-type/create` | module_task:workflow:create | 创建节点 |
| PUT | `/workflow/node-type/update/{id}` | module_task:workflow:update | 更新节点 |
| DELETE | `/workflow/node-type/delete` | module_task:workflow:delete | 删除节点 |

---

## 27. CodeGen 代码生成器模块（module_generator/gencode）

### 27.1 业务描述

代码生成器模块，通过读取数据库表结构自动生成 CRUD 代码（Python 后端 + Vue 前端 + TypeScript API 层）。支持主子表结构。数据按租户隔离。

### 27.2 数据模型

#### GenTableModel（gen_table，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `table_name` | String(200) | NOT NULL | 数据库表名 |
| `table_comment` | String(500) | nullable | 表描述 |
| `class_name` | String(100) | NOT NULL | 实体类名称 |
| `package_name` | String(100) | nullable | 生成包路径（module_xxx） |
| `module_name` | String(30) | nullable | 生成模块名 |
| `business_name` | String(30) | nullable | 功能子目录/路由段 |
| `function_name` | String(100) | nullable | 生成功能名 |
| `sub_table_name` | String(64) | nullable | 关联子表的表名 |
| `sub_table_fk_name` | String(64) | nullable | 子表关联的外键名 |
| `parent_menu_id` | Integer | nullable | 父菜单ID |

#### GenTableColumnModel（gen_table_column，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `table_id` | FK→gen_table.id | NOT NULL, ON DELETE CASCADE | 归属表ID |
| `column_name` | String(200) | NOT NULL | 列名称 |
| `column_comment` | String(500) | nullable | 列描述 |
| `column_type` | String(100) | NOT NULL | 列类型 |
| `column_length` | String(50) | nullable | 列长度 |
| `column_default` | String(200) | nullable | 列默认值 |
| `is_pk` | Boolean | NOT NULL, default=False | 是否主键 |
| `is_increment` | Boolean | NOT NULL, default=False | 是否自增 |
| `is_nullable` | Boolean | NOT NULL, default=True | 是否允许为空 |
| `is_unique` | Boolean | NOT NULL, default=False | 是否唯一 |
| `python_type` | String(100) | nullable | Python 类型 |
| `python_field` | String(200) | nullable | Python 字段名 |
| `is_insert` | Boolean | NOT NULL, default=True | 是否为新增字段 |
| `is_edit` | Boolean | NOT NULL, default=True | 是否编辑字段 |
| `is_list` | Boolean | NOT NULL, default=True | 是否列表字段 |
| `is_query` | Boolean | NOT NULL, default=False | 是否查询字段 |
| `query_type` | String(50) | nullable | 查询方式 |
| `html_type` | String(100) | nullable, default="input" | 显示类型 |
| `dict_type` | String(200) | nullable, default="" | 字典类型 |
| `sort` | Integer | NOT NULL, default=0 | 排序 |

### 27.3 业务规则

| 规则 | 说明 |
|------|------|
| **表名校验** | table_name/class_name 非空去空白 |
| **包名规范** | package_name 必须以 module_ 开头 |
| **业务名规范** | business_name 支持斜杠多段（如 demo/demo01） |
| **同步预览** | 支持 DB→Gen 差异预览（新增/删除/变更字段） |
| **建表SQL** | 支持从 CREATE TABLE SQL 导入表结构 |
| **模板生成** | 支持 Python/TS/Vue 三端代码模板（Jinja2） |
| **主子表** | 通过 sub_table_name/sub_table_fk_name 配置主子表关联 |

### 27.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/gencode/detail/{id}` | module_generator:gencode:query | 业务表详情 |
| GET | `/gencode/list` | module_generator:gencode:query | 业务表列表 |
| POST | `/gencode/create` | module_generator:gencode:create | 创建业务表 |
| PUT | `/gencode/update/{id}` | module_generator:gencode:update | 更新业务表 |
| DELETE | `/gencode/delete` | module_generator:gencode:delete | 删除业务表 |
| PATCH | `/gencode/available/setting` | module_generator:gencode:patch | 批量设状态 |
| GET | `/gencode/db/list` | module_generator:gencode:query | 数据库表列表 |
| POST | `/gencode/import` | module_generator:gencode:create | 导入表结构 |
| POST | `/gencode/sync/preview/{id}` | module_generator:gencode:query | 同步预览 |
| POST | `/gencode/sync/{id}` | module_generator:gencode:update | 同步表结构 |
| POST | `/gencode/create/table` | module_generator:gencode:create | 从SQL建表 |
| POST | `/gencode/preview/{id}` | module_generator:gencode:query | 预览代码 |
| POST | `/gencode/zip/{id}` | module_generator:gencode:query | 下载代码ZIP |
| POST | `/gencode/gen/{id}` | module_generator:gencode:update | 生成代码到本地 |
| POST | `/gencode/current/select` | module_generator:gencode:query | 切换当前业务表 |

---

## 28. Demo 示例模块（module_example/demo）

### 28.1 业务描述

示例模块，演示 CRUD 标准开发模式和多种数据类型的用法。数据按租户隔离。

### 28.2 数据模型

#### DemoModel（gen_demo，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 名称 |
| `a` | Integer | nullable | 整数 |
| `b` | BIGINT | nullable | 大整数 |
| `c` | Float | nullable | 浮点数 |
| `d` | Boolean | NOT NULL, default=True | 布尔型 |
| `e` | Date | nullable | 日期 |
| `f` | Time | nullable | 时间 |
| `g` | DateTime | nullable | 日期时间 |
| `h` | Text | nullable | 长文本 |
| `i` | JSON | nullable | 元数据 JSON |

#### Demo01Model（gen_demo01，TenantMixin, UserMixin）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | String(64) | NOT NULL | 名称 |

### 28.3 业务规则

| 规则 | 说明 |
|------|------|
| **名称校验** | 2-50 位，仅含字母/数字/下划线/中划线 |
| **状态校验** | 仅支持 0(正常)、1(禁用) |

### 28.4 API 端点

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/example/demo/detail/{id}` | module_example:demo:query | 详情 |
| GET | `/example/demo/list` | module_example:demo:query | 列表 |
| POST | `/example/demo/create` | module_example:demo:create | 创建 |
| PUT | `/example/demo/update/{id}` | module_example:demo:update | 更新 |
| DELETE | `/example/demo/delete` | module_example:demo:delete | 删除 |
| PATCH | `/example/demo/available/setting` | module_example:demo:patch | 批量设状态 |

#### Demo01

| 方法 | 路径 | 权限标识 | 说明 |
|------|------|---------|------|
| GET | `/example/demo01/detail/{id}` | module_example:demo01:query | 详情 |
| GET | `/example/demo01/list` | module_example:demo01:query | 列表 |
| POST | `/example/demo01/create` | module_example:demo01:create | 创建 |
| PUT | `/example/demo01/update/{id}` | module_example:demo01:update | 更新 |
| DELETE | `/example/demo01/delete` | module_example:demo01:delete | 删除 |
| PATCH | `/example/demo01/available/setting` | module_example:demo01:patch | 批量设状态 |

---