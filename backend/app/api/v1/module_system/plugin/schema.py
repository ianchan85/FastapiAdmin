from pydantic import BaseModel, ConfigDict, Field, field_validator


class PluginCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="插件名称")
    code: str = Field(..., min_length=1, max_length=50, description="插件编码（如 module_xxx）")
    description: str | None = Field(default=None, max_length=255, description="插件描述")
    version: str = Field(default="1.0.0", max_length=20, description="版本号")
    author: str | None = Field(default=None, max_length=100, description="作者")
    icon: str | None = Field(default=None, max_length=500, description="图标URL")
    category: str = Field(
        default="tool", max_length=20, description="分类(tool/ai/monitor/business)"
    )
    price: int = Field(default=0, ge=0, description="价格(分，0=免费)")
    menu_path: str | None = Field(default=None, max_length=200, description="菜单路径")
    permission_prefix: str | None = Field(default=None, max_length=100, description="权限前缀")
    dependencies: str | None = Field(default=None, description="依赖插件编码(JSON数组)")
    sort: int = Field(default=0, ge=0, description="排序")

    @field_validator("category")
    @classmethod
    def _validate_category(cls, v: str) -> str:
        allowed = {"tool", "ai", "monitor", "business"}
        if v not in allowed:
            raise ValueError(f"插件分类仅支持 tool、ai、monitor、business，当前值: {v}")
        return v

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: str) -> str:
        import re
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("版本号格式需为 x.y.z（如 1.0.0）")
        return v

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("插件编码不能为空")
        return v


class PluginUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=100, description="插件名称")
    description: str | None = Field(default=None, max_length=255, description="插件描述")
    version: str | None = Field(default=None, max_length=20, description="版本号")
    author: str | None = Field(default=None, max_length=100, description="作者")
    icon: str | None = Field(default=None, max_length=500, description="图标URL")
    category: str | None = Field(default=None, max_length=20, description="分类")
    price: int | None = Field(default=None, ge=0, description="价格(分，0=免费)")
    menu_path: str | None = Field(default=None, max_length=200, description="菜单路径")
    permission_prefix: str | None = Field(default=None, max_length=100, description="权限前缀")
    dependencies: str | None = Field(default=None, description="依赖插件编码(JSON数组)")
    sort: int | None = Field(default=None, ge=0, description="排序")
    status: str | None = Field(default=None, max_length=1, description="状态(0:正常 1:禁用)")

    @field_validator("category")
    @classmethod
    def _validate_category(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"tool", "ai", "monitor", "business"}
        if v not in allowed:
            raise ValueError(f"插件分类仅支持 tool、ai、monitor、business，当前值: {v}")
        return v

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in {"0", "1"}:
            raise ValueError("状态仅支持 0(正常) 或 1(禁用)")
        return v


class PluginOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    description: str | None = None
    version: str
    author: str | None = None
    icon: str | None = None
    category: str
    price: int
    menu_path: str | None = None
    permission_prefix: str | None = None
    dependencies: str | None = None
    sort: int
    status: str
    installed: bool = False  # 当前租户是否已安装


class PluginQueryParam:
    def __init__(
        self, name: str | None = None, category: str | None = None, status: str | None = None
    ):
        if name:
            self.name = ("like", name)
        if category:
            self.category = ("eq", category)
        if status:
            self.status = ("eq", status)


class PluginInstallSchema(BaseModel):
    plugin_id: int = Field(..., description="插件ID")
