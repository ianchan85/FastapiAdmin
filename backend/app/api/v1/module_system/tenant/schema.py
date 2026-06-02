from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema
from app.core.validator import DateTimeStr, email_validator, mobile_validator


class TenantCreateSchema(BaseModel):
    """新增租户"""

    name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    code: str = Field(..., min_length=2, max_length=100, description="租户编码")
    status: str = Field(default="0", max_length=1, description="状态(0:正常 1:禁用)")
    description: str | None = Field(default=None, max_length=255, description="描述")
    start_time: DateTimeStr | None = Field(default=None, description="开始时间")
    end_time: DateTimeStr | None = Field(default=None, description="结束时间")
    contact_name: str | None = Field(default=None, max_length=64, description="联系人姓名")
    contact_phone: str | None = Field(default=None, max_length=20, description="联系人电话")
    contact_email: str | None = Field(default=None, max_length=128, description="联系人邮箱")
    address: str | None = Field(default=None, max_length=255, description="地址")
    domain: str | None = Field(default=None, max_length=255, description="域名")
    logo_url: str | None = Field(default=None, max_length=500, description="Logo URL")
    sort: int = Field(default=0, ge=0, description="排序")
    package_id: int | None = Field(default=None, gt=0, description="关联套餐ID")

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("租户名称不能为空")
        return v

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("租户编码不能为空")
        if not v.isalnum():
            raise ValueError("租户编码仅允许字母和数字")
        return v

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        if v not in {"0", "1"}:
            raise ValueError("状态仅支持 0(正常) 或 1(禁用)")
        return v

    @field_validator("contact_phone")
    @classmethod
    def _validate_contact_phone(cls, v: str | None) -> str | None:
        return mobile_validator(v)

    @field_validator("contact_email")
    @classmethod
    def _validate_contact_email(cls, v: str | None) -> str | None:
        if not v:
            return v
        return email_validator(v)

    @model_validator(mode="after")
    def _validate_time_range(self):
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("结束时间不能早于开始时间")
        return self


class TenantUpdateSchema(BaseModel):
    """更新租户"""

    name: str | None = Field(default=None, max_length=100, description="租户名称")
    code: str | None = Field(default=None, max_length=100, description="租户编码")
    status: str | None = Field(default=None, max_length=1, description="状态(0:正常 1:禁用)")
    description: str | None = Field(default=None, max_length=255, description="描述")
    start_time: DateTimeStr | None = Field(default=None, description="开始时间")
    end_time: DateTimeStr | None = Field(default=None, description="结束时间")
    contact_name: str | None = Field(default=None, max_length=64, description="联系人姓名")
    contact_phone: str | None = Field(default=None, max_length=20, description="联系人电话")
    contact_email: str | None = Field(default=None, max_length=128, description="联系人邮箱")
    address: str | None = Field(default=None, max_length=255, description="地址")
    domain: str | None = Field(default=None, max_length=255, description="域名")
    logo_url: str | None = Field(default=None, max_length=500, description="Logo URL")
    sort: int | None = Field(default=None, ge=0, description="排序")
    package_id: int | None = Field(default=None, gt=0, description="关联套餐ID")

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v.isalnum():
            raise ValueError("租户编码仅允许字母和数字")
        return v

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in {"0", "1"}:
            raise ValueError("状态仅支持 0(正常) 或 1(禁用)")
        return v

    @field_validator("contact_phone")
    @classmethod
    def _validate_contact_phone(cls, v: str | None) -> str | None:
        return mobile_validator(v)

    @field_validator("contact_email")
    @classmethod
    def _validate_contact_email(cls, v: str | None) -> str | None:
        if not v:
            return v
        return email_validator(v)

    @model_validator(mode="after")
    def _validate_time_range(self):
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("结束时间不能早于开始时间")
        return self


class TenantOutSchema(TenantCreateSchema, BaseSchema):
    """租户响应"""

    model_config = ConfigDict(from_attributes=True)


class TenantQueryParam:
    """租户查询参数"""

    def __init__(
        self,
        name: str | None = Query(None, description="租户名称"),
        code: str | None = Query(None, description="租户编码"),
        status: str | None = Query(None, description="状态"),
        created_time: list[DateTimeStr] | None = Query(
            None,
            description="创建时间范围",
            examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"],
        ),
    ) -> None:
        if name:
            self.name = (QueueEnum.like.value, name)
        if code:
            self.code = (QueueEnum.like.value, code)
        if status:
            self.status = (QueueEnum.eq.value, status)
        if created_time and len(created_time) == 2:
            self.created_time = (QueueEnum.between.value, (created_time[0], created_time[1]))


class TenantUserAddSchema(BaseModel):
    """向租户添加用户"""

    user_id: int = Field(..., gt=0, description="用户ID")
    role: str = Field(default="member", max_length=20, description="租户内角色(owner/admin/member)")
    is_default: int = Field(default=0, ge=0, le=1, description="是否默认租户(0:否 1:是)")

    @field_validator("role")
    @classmethod
    def _validate_role(cls, v: str) -> str:
        if v not in {"owner", "admin", "member"}:
            raise ValueError("租户角色仅支持 owner(拥有者)、admin(管理员)、member(成员)")
        return v

    @field_validator("is_default")
    @classmethod
    def _validate_is_default(cls, v: int) -> int:
        if v not in {0, 1}:
            raise ValueError("是否默认仅支持 0(否) 或 1(是)")
        return v


class TenantUserOutSchema(BaseModel):
    """租户用户响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="关联ID")
    user_id: int = Field(..., description="用户ID")
    tenant_id: int = Field(..., description="租户ID")
    role: str = Field(..., description="租户内角色")
    is_default: int = Field(..., description="是否默认租户")
    create_time: DateTimeStr | None = Field(default=None, description="创建时间")
    username: str = Field(default="", description="用户名")
    name: str = Field(default="", description="用户姓名")


# ============ P1: 配额管理 ============


class TenantQuotaOutSchema(BaseModel):
    """租户配额响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    max_users: int
    max_roles: int
    max_storage_mb: int
    max_depts: int


class TenantQuotaUpdateSchema(BaseModel):
    """租户配额更新"""

    max_users: int | None = Field(default=None, ge=0, description="最大用户数")
    max_roles: int | None = Field(default=None, ge=0, description="最大角色数")
    max_storage_mb: int | None = Field(default=None, ge=0, description="最大存储(MB)")
    max_depts: int | None = Field(default=None, ge=0, description="最大部门数")


# ============ P1: 租户配置 ============


class TenantConfigItem(BaseModel):
    """单个配置项"""

    config_key: str = Field(..., min_length=1, max_length=100, description="配置键")
    config_value: str = Field(..., max_length=65535, description="配置值")
    config_type: str = Field(default="string", max_length=20, description="配置类型(string/json/int/bool)")

    @field_validator("config_type")
    @classmethod
    def _validate_config_type(cls, v: str) -> str:
        if v not in {"string", "json", "int", "bool"}:
            raise ValueError("配置类型仅支持 string、json、int、bool")
        return v


class TenantConfigOutSchema(TenantConfigItem):
    """租户配置响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int


# ============ P1: 租户菜单 ============


class TenantMenuSetSchema(BaseModel):
    """批量设置租户菜单权限"""

    menu_ids: list[int] = Field(..., description="菜单ID列表")
