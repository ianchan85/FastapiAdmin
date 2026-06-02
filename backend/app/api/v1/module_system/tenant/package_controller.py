from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.logger import log
from app.core.router_class import OperationLogRoute

from .package_schema import (
    TenantPackageCreateSchema,
    TenantPackageMenuSetSchema,
    TenantPackageOutSchema,
    TenantPackageQueryParam,
    TenantPackageUpdateSchema,
)
from .package_service import TenantPackageService

PackageRouter = APIRouter(
    route_class=OperationLogRoute, prefix="/tenant/package", tags=["租户套餐管理"]
)


@PackageRouter.get(
    "/detail/{id}",
    summary="获取套餐详情",
    description="获取套餐详情",
    response_model=ResponseSchema[TenantPackageOutSchema],
)
async def get_package_detail_controller(
    id: Annotated[int, Path(description="套餐ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:tenant:query"]))],
) -> JSONResponse:
    result_dict = await TenantPackageService.detail_service(id=id, auth=auth)
    log.info(f"获取套餐详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取套餐详情成功")


@PackageRouter.get(
    "/list",
    summary="查询套餐列表",
    description="查询套餐列表（分页）",
    response_model=ResponseSchema[dict],
)
async def get_package_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[TenantPackageQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:tenant:query"]))],
) -> JSONResponse:
    order_by = [{"sort": "asc"}, {"id": "asc"}]
    if page.order_by:
        order_by = page.order_by
    result_dict = await TenantPackageService.page_service(
        auth=auth,
        page_no=page.page_no if page.page_no is not None else 1,
        page_size=page.page_size if page.page_size is not None else 10,
        search=search,
        order_by=order_by,
    )
    log.info("查询套餐列表成功")
    return SuccessResponse(data=result_dict, msg="查询套餐列表成功")


@PackageRouter.post(
    "/create",
    summary="创建套餐",
    description="创建套餐",
    response_model=ResponseSchema[TenantPackageOutSchema],
)
async def create_package_controller(
    data: TenantPackageCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:tenant:create"]))],
) -> JSONResponse:
    result_dict = await TenantPackageService.create_service(auth=auth, data=data)
    log.info(f"创建套餐成功: {result_dict.get('name')}")
    return SuccessResponse(data=result_dict, msg="创建套餐成功")


@PackageRouter.put(
    "/update/{id}",
    summary="修改套餐",
    description="修改套餐",
    response_model=ResponseSchema[TenantPackageOutSchema],
)
async def update_package_controller(
    data: TenantPackageUpdateSchema,
    id: Annotated[int, Path(description="套餐ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:tenant:update"]))],
) -> JSONResponse:
    result_dict = await TenantPackageService.update_service(auth=auth, id=id, data=data)
    log.info(f"修改套餐成功: {result_dict.get('name')}")
    return SuccessResponse(data=result_dict, msg="修改套餐成功")


@PackageRouter.delete(
    "/delete",
    summary="删除套餐",
    description="删除套餐",
)
async def delete_package_controller(
    ids: Annotated[list[int], Body(..., description="ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:tenant:delete"]))],
) -> JSONResponse:
    await TenantPackageService.delete_service(auth=auth, ids=ids)
    log.info(f"删除套餐成功: {ids}")
    return SuccessResponse(msg="删除套餐成功")


@PackageRouter.get(
    "/{id}/menus",
    summary="获取套餐菜单权限",
    description="获取指定套餐包含的菜单ID列表",
    response_model=ResponseSchema[list[int]],
)
async def get_package_menus_controller(
    id: Annotated[int, Path(description="套餐ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:tenant:query"]))],
) -> JSONResponse:
    result = await TenantPackageService.get_menus_service(auth=auth, package_id=id)
    return SuccessResponse(data=result, msg="获取套餐菜单成功")


@PackageRouter.put(
    "/{id}/menus",
    summary="设置套餐菜单权限",
    description="批量设置套餐的菜单权限（先清空再写入）",
)
async def set_package_menus_controller(
    id: Annotated[int, Path(description="套餐ID")],
    data: TenantPackageMenuSetSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:tenant:update"]))],
) -> JSONResponse:
    await TenantPackageService.set_menus_service(auth=auth, package_id=id, data=data)
    log.info(f"设置套餐菜单权限成功: package_id={id}, count={len(data.menu_ids)}")
    return SuccessResponse(msg="设置套餐菜单权限成功")
