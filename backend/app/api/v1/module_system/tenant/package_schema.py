from fastapi import Query
from pydantic import BaseModel, Field, field_validator

from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema
from app.core.validator import DateTimeStr


class TenantPackageCreateSchema(BaseModel):
    """新增租户套餐"""

    name: str = Field(..., max_length=100, description="套餐名称")
    code: str = Field(..., max_length=100, description="套餐编码")
    status: str = Field(default="0", description="状态(0:正常 1:禁用)")
    sort: int = Field(default=0, description="排序")
    description: str | None = Field(default=None, max_length=255, description="描述")

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("名称不能为空")
        return v

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("编码不能为空")
        if not v.isalnum():
            raise ValueError("编码只能包含字母和数字")
        return v


class TenantPackageUpdateSchema(BaseModel):
    """更新租户套餐"""

    name: str | None = Field(default=None, max_length=100, description="套餐名称")
    code: str | None = Field(default=None, max_length=100, description="套餐编码")
    status: str | None = Field(default=None, description="状态(0:正常 1:禁用)")
    sort: int | None = Field(default=None, description="排序")
    description: str | None = Field(default=None, max_length=255, description="描述")

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v.isalnum():
            raise ValueError("编码只能包含字母和数字")
        return v


class TenantPackageOutSchema(BaseSchema):
    """套餐响应"""

    id: int
    name: str
    code: str
    status: str
    sort: int
    description: str | None
    create_time: DateTimeStr | None
    update_time: DateTimeStr | None


class TenantPackageQueryParam:
    """套餐查询参数"""

    def __init__(
        self,
        name: str | None = Query(None, description="套餐名称"),
        code: str | None = Query(None, description="套餐编码"),
        status: str | None = Query(None, description="状态"),
    ) -> None:
        if name:
            self.name = (QueueEnum.like.value, name)
        if code:
            self.code = (QueueEnum.like.value, code)
        if status:
            self.status = (QueueEnum.eq.value, status)


class TenantPackageMenuSetSchema(BaseModel):
    """批量设置套餐菜单权限"""

    menu_ids: list[int] = Field(..., description="菜单ID列表")
