"""v3_1_0_optimize_multi_tenant_menu

1. 从 sys_menu 移除 tenant_id（平台资源不应绑定租户）
2. 创建 sys_tenant_package（租户套餐表）
3. 创建 sys_tenant_package_menu（套餐-菜单关联表）
4. sys_tenant 增加 package_id 字段

Revision ID: dd4806d8fc16
Revises: 0306640395d9
Create Date: 2026-06-01 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dd4806d8fc16"
down_revision: str | None = "0306640395d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- 1. 从 sys_menu 移除 tenant_id ---
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sys_menu' "
            "AND COLUMN_NAME = 'tenant_id' AND REFERENCED_TABLE_NAME = 'sys_tenant'"
        )
    )
    fk_row = result.fetchone()
    if fk_row:
        op.drop_constraint(fk_row[0], "sys_menu", type_="foreignkey")

    op.drop_index("ix_sys_menu_tenant_id", table_name="sys_menu")
    op.drop_column("sys_menu", "tenant_id")

    # --- 2. 创建 sys_tenant_package（租户套餐表） ---
    op.create_table(
        "sys_tenant_package",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="套餐名称"),
        sa.Column("code", sa.String(length=100), nullable=False, comment="套餐编码"),
        sa.Column(
            "status",
            sa.String(length=10),
            nullable=False,
            server_default="0",
            comment="状态(0:正常 1:禁用)",
        ),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="0", comment="排序"),
        sa.Column("description", sa.String(length=255), nullable=True, comment="描述"),
        sa.Column("create_time", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("update_time", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_package_name"),
        sa.UniqueConstraint("code", name="uq_package_code"),
        comment="租户套餐表",
    )

    # --- 3. 创建 sys_tenant_package_menu（套餐-菜单关联表） ---
    op.create_table(
        "sys_tenant_package_menu",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
        sa.Column("package_id", sa.Integer(), nullable=False, comment="套餐ID"),
        sa.Column("menu_id", sa.Integer(), nullable=False, comment="菜单ID"),
        sa.ForeignKeyConstraint(
            ["package_id"], ["sys_tenant_package.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["menu_id"], ["sys_menu.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("package_id", "menu_id", name="uq_package_menu"),
        comment="套餐菜单关联表",
    )
    op.create_index(
        op.f("ix_sys_tenant_package_menu_package_id"),
        "sys_tenant_package_menu",
        ["package_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sys_tenant_package_menu_menu_id"),
        "sys_tenant_package_menu",
        ["menu_id"],
        unique=False,
    )

    # --- 4. sys_tenant 增加 package_id 字段 ---
    op.add_column(
        "sys_tenant",
        sa.Column("package_id", sa.Integer(), nullable=True, default=None, comment="关联套餐ID"),
    )
    op.create_foreign_key(
        "fk_sys_tenant_package_id",
        "sys_tenant",
        "sys_tenant_package",
        ["package_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_sys_tenant_package_id"), "sys_tenant", ["package_id"], unique=False)


def downgrade() -> None:
    # --- 反向：移除 package_id ---
    op.drop_index(op.f("ix_sys_tenant_package_id"), table_name="sys_tenant")
    op.drop_constraint("fk_sys_tenant_package_id", "sys_tenant", type_="foreignkey")
    op.drop_column("sys_tenant", "package_id")

    # --- 反向：删除套餐-菜单关联表 ---
    op.drop_table("sys_tenant_package_menu")

    # --- 反向：删除租户套餐表 ---
    op.drop_table("sys_tenant_package")

    # --- 反向：恢复 sys_menu.tenant_id ---
    op.add_column(
        "sys_menu",
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1", comment="租户ID"),
    )
    op.create_foreign_key(
        "fk_sys_menu_tenant_id",
        "sys_menu",
        "sys_tenant",
        ["tenant_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="RESTRICT",
    )
    op.create_index(op.f("ix_sys_menu_tenant_id"), "sys_menu", ["tenant_id"], unique=False)
