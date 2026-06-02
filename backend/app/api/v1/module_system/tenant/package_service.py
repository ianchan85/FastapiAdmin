from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.exceptions import CustomException
from app.core.logger import log

from .model import TenantPackageMenuModel
from .package_crud import TenantPackageCRUD
from .package_schema import (
    TenantPackageCreateSchema,
    TenantPackageMenuSetSchema,
    TenantPackageOutSchema,
    TenantPackageQueryParam,
    TenantPackageUpdateSchema,
)


class TenantPackageService:
    """租户套餐模块服务层"""

    @classmethod
    async def detail_service(cls, auth: AuthSchema, id: int) -> dict:
        obj = await TenantPackageCRUD(auth).get_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg="套餐不存在")
        return TenantPackageOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: TenantPackageQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        return await TenantPackageCRUD(auth).page_crud(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"sort": "asc"}, {"id": "asc"}],
            search=search.__dict__ if search else {},
            out_schema=TenantPackageOutSchema,
        )

    @classmethod
    async def create_service(cls, auth: AuthSchema, data: TenantPackageCreateSchema) -> dict:
        if await TenantPackageCRUD(auth).get(name=data.name):
            raise CustomException(msg="创建失败，套餐名称已存在")
        if await TenantPackageCRUD(auth).get(code=data.code):
            raise CustomException(msg="创建失败，套餐编码已存在")

        obj = await TenantPackageCRUD(auth).create_crud(data=data)
        if not obj:
            raise CustomException(msg="创建套餐失败")
        result = TenantPackageOutSchema.model_validate(obj).model_dump()
        log.info(f"创建套餐成功: {result.get('name')}")
        return result

    @classmethod
    async def update_service(
        cls, auth: AuthSchema, id: int, data: TenantPackageUpdateSchema
    ) -> dict:
        obj = await TenantPackageCRUD(auth).get_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg="套餐不存在")

        if data.name is not None:
            exist = await TenantPackageCRUD(auth).get(name=data.name)
            if exist and exist.id != id:
                raise CustomException(msg="更新失败，名称重复")
        if data.code is not None:
            exist = await TenantPackageCRUD(auth).get(code=data.code)
            if exist and exist.id != id:
                raise CustomException(msg="更新失败，编码重复")

        updated = await TenantPackageCRUD(auth).update_crud(id=id, data=data)
        if not updated:
            raise CustomException(msg="更新失败")
        return TenantPackageOutSchema.model_validate(updated).model_dump()

    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")

        from sqlalchemy import func, select

        from .model import TenantModel

        for pid in ids:
            stmt = (
                select(func.count()).select_from(TenantModel).where(TenantModel.package_id == pid)
            )
            result = await auth.db.execute(stmt)
            count = result.scalar()
            if count and count > 0:
                raise CustomException(msg=f"套餐 ID={pid} 已被 {count} 个租户使用，无法删除")

        await TenantPackageCRUD(auth).delete_crud(ids=ids)

    @classmethod
    async def get_menus_service(cls, auth: AuthSchema, package_id: int) -> list[int]:
        """获取套餐菜单权限（返回 menu_id 列表）"""
        from sqlalchemy import select

        stmt = select(TenantPackageMenuModel.menu_id).where(
            TenantPackageMenuModel.package_id == package_id
        )
        result = await auth.db.execute(stmt)
        return [row[0] for row in result.all()]

    @classmethod
    async def set_menus_service(
        cls, auth: AuthSchema, package_id: int, data: TenantPackageMenuSetSchema
    ) -> None:
        """批量设置套餐菜单权限（先清空再写入）"""
        from sqlalchemy import delete

        await auth.db.execute(
            delete(TenantPackageMenuModel).where(TenantPackageMenuModel.package_id == package_id)
        )
        for menu_id in data.menu_ids:
            auth.db.add(TenantPackageMenuModel(package_id=package_id, menu_id=menu_id))
        await auth.db.flush()
        log.info(f"套餐[{package_id}]菜单权限已设置, count={len(data.menu_ids)}")

    @staticmethod
    async def get_package_menu_ids(auth: AuthSchema, package_id: int) -> list[int]:
        """获取套餐包含的菜单ID列表（供租户权限约束使用）"""
        from sqlalchemy import select

        stmt = select(TenantPackageMenuModel.menu_id).where(
            TenantPackageMenuModel.package_id == package_id,
        )
        result = await auth.db.execute(stmt)
        ids = [row[0] for row in result.all()]
        return ids

    @staticmethod
    async def get_tenant_available_menu_ids(auth: AuthSchema, tenant_id: int) -> list[int]:
        """获取租户的完整可用菜单ID列表（套餐菜单 + 自定义授权菜单）

        合并逻辑：
        1. 如果租户关联了套餐且套餐状态正常(status=0)，取套餐包含的所有菜单
        2. 如果套餐被禁用(status=1)，跳过套餐菜单
        3. 再取 sys_tenant_menu 中显式授权的菜单
        4. 返回两者的并集
        """
        from sqlalchemy import select

        from .model import TenantMenuModel, TenantPackageModel, TenantModel

        # 查询租户信息
        stmt = select(TenantModel).where(TenantModel.id == tenant_id).limit(1)
        result = await auth.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            return []

        all_menu_ids: set[int] = set()

        # 1. 如果有关联套餐且套餐状态正常，获取套餐包含的菜单
        if tenant.package_id:
            pkg_stmt = select(TenantPackageModel.status).where(
                TenantPackageModel.id == tenant.package_id
            ).limit(1)
            pkg_result = await auth.db.execute(pkg_stmt)
            pkg_status = pkg_result.scalar_one_or_none()
            if pkg_status == "0":  # 仅正常套餐计入
                stmt = select(TenantPackageMenuModel.menu_id).where(
                    TenantPackageMenuModel.package_id == tenant.package_id
                )
                result = await auth.db.execute(stmt)
                for row in result.all():
                    all_menu_ids.add(row[0])

        # 2. 获取自定义授权的菜单（sys_tenant_menu）
        stmt = select(TenantMenuModel.menu_id).where(
            TenantMenuModel.tenant_id == tenant_id,
        )
        result = await auth.db.execute(stmt)
        for row in result.all():
            all_menu_ids.add(row[0])

        return list(all_menu_ids)
