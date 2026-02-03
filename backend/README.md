# FastApiAdmin - Backend

一个基于 FastAPI 框架构建企业级后端架构解决方案，为前端 Vue3 管理系统提供完整的 API 服务支持。

## 🚀 项目特性

- **现代技术栈**: FastAPI + SQLAlchemy 2.0 + Pydantic 2.x
- **多数据库支持**: MySQL、PostgreSQL、SQLite
- **异步架构**: 支持高并发异步数据库操作
- **权限管理**: 完整的 RBAC 权限控制体系
- **任务调度**: 基于 APScheduler 的定时任务系统
- **日志监控**: 完整的操作日志和系统监控
- **代码生成**: 智能化代码生成工具
- **AI 集成**: 支持 OpenAI 大模型调用
- **云存储**: 支持阿里云 OSS 对象存储

## 🏗️ 系统架构

### 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| FastAPI | 0.115.2 | 现代 Web 框架 |
| SQLAlchemy | 2.0.36 | ORM 框架 |
| Alembic | 1.15.1 | 数据库迁移工具 |
| Pydantic | 2.x | 数据验证与序列化 |
| APScheduler | 3.11.0 | 定时任务调度 |
| Redis | 5.2.1 | 缓存与会话存储 |
| Uvicorn | 0.30.6 | ASGI 服务器 |
| Python | 3.10+ | 运行环境 |

### 架构设计

```txt
📦 分层架构 (MVC)
├── 🎯 Controller   # 控制器层 - 处理HTTP请求
├── 🏢 Service      # 业务层 - 核心业务逻辑
├── 💾 CRUD         # 数据访问层 - 数据库操作
└── 📊 Model        # 模型层 - 数据模型定义
```

## 📁 项目结构

```txt
FastapiAdmin/backend/
├── 📁 app/                     # 项目核心代码
│   ├── 💾 alembic/             # 数据库迁移管理
│   ├── 🌐 api/                 # API 接口模块
│   │   └── v1/               # API v1 版本
│   │       ├── module_system/  # 系统管理模块
│   │       ├── module_monitor/ # 系统监控模块
│   │       ├── module_ai/      # AI 功能模块
│   │       └── module_*/       # 其他业务模块
│   ├── 📄 common/              # 公共组件（常量、枚举、响应封装）
│   ├── ⚙️ config/              # 项目配置文件
│   ├── 💖 core/                # 核心模块（数据库、中间件、安全）
│   ├── ⏰ module_task/         # 定时任务模块
│   ├── 🔌 plugin/              # 插件模块
│   ├── 📜 scripts/             # 初始化脚本和数据
│   └── 🛠️ utils/               # 工具类（验证码、文件上传等）
├── 🌍 env/                     # 环境配置文件
├── 📄 logs/                    # 日志输出目录
├── 📊 sql/                     # SQL 初始化脚本
├── 📷 static/                  # 静态资源文件
├── 🚀 main.py                  # 项目启动入口
├── 📄 alembic.ini              # Alembic 迁移配置
├── 📎 requirements.txt         # Python 依赖包
└── 📝 README.md                # 项目说明文档
```

### 模块设计

每个业务模块采用统一的分层结构：

```txt
module_*/
├── controller.py    # 控制器 - HTTP 请求处理
├── service.py       # 服务层 - 业务逻辑处理
├── crud.py          # 数据层 - 数据库操作
├── model.py         # ORM 模型 - 数据库表定义
├── schema.py        # Pydantic 模型 - 数据验证
└── param.py         # 参数模型 - 请求参数
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.10+
- **数据库**: MySQL 8.0+ / PostgreSQL 13+ / SQLite 3.x
- **Redis**: 6.0+ (可选)

#### 1. 数据库初始化

```bash
# 生成迁移文件（仅首次或模型变更时）
python main.py revision  --env=dev(不加默认为dev)

# 应用数据库迁移
python main.py upgrade --env=dev(不加默认为dev)

# 如果是uv管理管理python则是
uv run main.py revision  --env=dev(不加默认为dev)
uv run main.py upgrade --env=dev(不加默认为dev)
```

#### 2. 启动服务

```bash
# 创建虚拟环境
python -m venv .venv
# 激活虚拟环境
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 如果是uv管理管理python则是
uv venv (默认创建.venv)


# 安装依赖
pip install -r requirements.txt
# 如果是uv管理管理python则是
uv add -r requirements.txt
或
uv sync

# 开发环境启动
python main.py run --env=dev (不加默认为dev)

# 生产环境启动
python main.py run --env=prod (不加默认为dev)

# 如果是uv管理管理python则是
uv run main.py run --env=dev (不加默认为dev)
uv run main.py run --env=prod (不加默认为dev)
```

#### 3.代码格式化

```bash
# 检查当前目录所有 Python 文件
ruff check
# 检查并自动修复问题
ruff check --fix
# 监听文件变化并重新检查
ruff check --watch

# 如果是uv管理管理python则是
uv run ruff check
uv run ruff check --fix
uv run ruff check --watch
```

## 📜 相关链接

- **FastAPI 官方文档**: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **SQLAlchemy 文档**: [https://docs.sqlalchemy.org/](https://docs.sqlalchemy.org/)
- **Pydantic 文档**: [https://pydantic-docs.helpmanual.io/](https://pydantic-docs.helpmanual.io/)

## 💬 支持与反馈

如果您在使用过程中遇到问题或有任何建议，请通过以下方式联系我们：

- 🐛 **Bug 报告**: 请在 GitHub Issues 中提交
- 💡 **功能建议**: 请在 GitHub Discussions 中讨论
- 💬 **技术交流**: 欢迎参与项目讨论

---

❤️ **感谢您的关注和支持！** 如果这个项目对您有帮助，请给我们一个 ⭐️ Star！

---

## mysql 全类型测试表

```sql
CREATE TABLE `gen_all_types_demo` (
  `tinyint_field` TINYINT NOT NULL COMMENT 'TINYINT类型',
  `tinyint_unsigned_field` TINYINT UNSIGNED NOT NULL COMMENT 'TINYINT UNSIGNED类型',
  `smallint_field` SMALLINT NOT NULL COMMENT 'SMALLINT类型',
  `smallint_unsigned_field` SMALLINT UNSIGNED NOT NULL COMMENT 'SMALLINT UNSIGNED类型',
  `mediumint_field` MEDIUMINT NOT NULL COMMENT 'MEDIUMINT类型',
  `mediumint_unsigned_field` MEDIUMINT UNSIGNED NOT NULL COMMENT 'MEDIUMINT UNSIGNED类型',
  `int_field` INT NOT NULL COMMENT 'INT类型',
  `int_unsigned_field` INT UNSIGNED NOT NULL COMMENT 'INT UNSIGNED类型',
  `bigint_field` BIGINT NOT NULL COMMENT 'BIGINT类型',
  `bigint_unsigned_field` BIGINT UNSIGNED NOT NULL COMMENT 'BIGINT UNSIGNED类型',
  `float_field` FLOAT NOT NULL COMMENT 'FLOAT类型',
  `double_field` DOUBLE NOT NULL COMMENT 'DOUBLE类型',
  `decimal_field` DECIMAL(10,2) NOT NULL COMMENT 'DECIMAL类型',
  `decimal_unsigned_field` DECIMAL(10,2) UNSIGNED NOT NULL COMMENT 'DECIMAL UNSIGNED类型',
  `numeric_field` NUMERIC(10,2) NOT NULL COMMENT 'NUMERIC类型',
  `bit_field` BIT(8) NOT NULL COMMENT 'BIT类型',
  `char_field` CHAR(32) NOT NULL COMMENT 'CHAR类型',
  `varchar_field` VARCHAR(255) NOT NULL COMMENT 'VARCHAR类型',
  `binary_field` BINARY(32) NOT NULL COMMENT 'BINARY类型',
  `varbinary_field` VARBINARY(255) NOT NULL COMMENT 'VARBINARY类型',
  `tinyblob_field` TINYBLOB COMMENT 'TINYBLOB类型',
  `blob_field` BLOB COMMENT 'BLOB类型',
  `mediumblob_field` MEDIUMBLOB COMMENT 'MEDIUMBLOB类型',
  `longblob_field` LONGBLOB COMMENT 'LONGBLOB类型',
  `tinytext_field` TINYTEXT COMMENT 'TINYTEXT类型',
  `text_field` TEXT COMMENT 'TEXT类型',
  `mediumtext_field` MEDIUMTEXT COMMENT 'MEDIUMTEXT类型',
  `longtext_field` LONGTEXT COMMENT 'LONGTEXT类型',
  `enum_field` ENUM('active','inactive','pending') NOT NULL DEFAULT 'pending' COMMENT 'ENUM类型',
  `set_field` SET('read','write','execute') NOT NULL DEFAULT '' COMMENT 'SET类型',
  `date_field` DATE NOT NULL COMMENT 'DATE类型',
  `time_field` TIME NOT NULL COMMENT 'TIME类型',
  `datetime_field` DATETIME NOT NULL COMMENT 'DATETIME类型',
  `timestamp_field` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'TIMESTAMP类型',
  `year_field` YEAR NOT NULL COMMENT 'YEAR类型',
  `json_field` JSON COMMENT 'JSON类型',
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` VARCHAR(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` VARCHAR(10) NOT NULL DEFAULT '0' COMMENT '是否启用(0:启用 1:禁用)',
  `description` TEXT COMMENT '备注/描述',
  `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_id` BIGINT DEFAULT NULL COMMENT '创建人ID',
  `updated_id` BIGINT DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `ix_gen_all_types_demo_created_id` (`created_id`),
  KEY `ix_gen_all_types_demo_updated_id` (`updated_id`),
  KEY `ix_gen_all_types_demo_status` (`status`),
  KEY `ix_gen_all_types_demo_created_time` (`created_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='全类型测试表';
```

## postgresql 全类型测试表

```sql
-- PostgreSQL 全类型测试表
CREATE TABLE gen_all_types_demo (
  -- 整数类型
  smallint_field SMALLINT NOT NULL,
  integer_field INTEGER NOT NULL,
  bigint_field BIGINT NOT NULL,

  -- 浮点类型
  real_field REAL NOT NULL,
  double_precision_field DOUBLE PRECISION NOT NULL,
  numeric_field NUMERIC(10,2) NOT NULL,
  decimal_field DECIMAL(10,2) NOT NULL,

  -- 字符串类型
  char_field CHAR(32) NOT NULL,
  varchar_field VARCHAR(255) NOT NULL,
  text_field TEXT NOT NULL,

  -- 二进制类型
  bytea_field BYTEA,

  -- 日期时间类型
  date_field DATE NOT NULL,
  time_field TIME NOT NULL,
  time_with_tz_field TIMESTAMP WITH TIME ZONE NOT NULL,
  time_without_tz_field TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  timestamp_field TIMESTAMP NOT NULL,
  timestamp_with_tz_field TIMESTAMP WITH TIME ZONE NOT NULL,
  timestamp_without_tz_field TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  interval_field INTERVAL,

  -- 布尔类型
  boolean_field BOOLEAN NOT NULL,

  -- JSON类型
  json_field JSON,
  jsonb_field JSONB,

  -- 其他类型
  uuid_field UUID,
  inet_field INET,
  cidr_field CIDR,
  macaddr_field MACADDR,

  -- 几何类型
  point_field POINT,
  line_field LINE,
  lseg_field LSEG,
  box_field BOX,
  path_field PATH,
  polygon_field POLYGON,
  circle_field CIRCLE,

  -- 位类型
  bit_field BIT(8) NOT NULL,
  bit_varying_field VARBIT(8) NOT NULL,

  -- 文本搜索类型
  tsvector_field TSVECTOR,
  tsquery_field TSQUERY,

  -- XML类型
  xml_field XML,

  -- 数组类型
  array_field INTEGER[],

  -- 范围类型
  range_field INT4RANGE,

  -- 货币类型
  money_field MONEY,

  -- 对象标识符类型
  oid_field OID,
  regproc_field REGPROC,
  regclass_field REGCLASS,
  regtype_field REGTYPE,
  regrole_field REGROLE,
  regnamespace_field REGNAMESPACE,

  -- 常用字段
  id BIGSERIAL PRIMARY KEY,
  uuid VARCHAR(64) NOT NULL UNIQUE,
  status VARCHAR(10) NOT NULL DEFAULT '0',
  description TEXT,
  created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_id BIGINT,
  updated_id BIGINT
);

```

## mysql类型

INT
VARCHAR
CHAR
DATETIME
TIMESTAMP
DATE
BIT
FLOAT
DOUBLE
DECIMAL
BIGINT
TEXT
JSON
BLOB
BINARY
ENUM
SET
TINYINT
SMALLINT
MEDIUMINT
TIME
YEAR
VARBINARY
TINYBLOB
MEDIUMBLOB
LONGBLOB
TINYTEXT
MEDIUMTEXT
LONGTEXT
GEOMETRY
POINT
LINESTRING
POLYGON
MULTIPOINT
MULTILINESTRING
MULTIPOLYGON
GEOMETRYCOLLECTION

## pg类型

INTEGER
VARCHAR
CHAR
TIMESTAMP
DATE
BOOLEAN
FLOAT
TEXT
JSON
BLOB
SMALLINT
BIGINT
REAL
DOUBLE PRECISION
BYTEA
XML
UUID
ARRAY
NUMERIC
MONEY
INTERVAL
CIDR
INET
MACADDR
