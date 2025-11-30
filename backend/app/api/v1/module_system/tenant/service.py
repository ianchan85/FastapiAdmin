# -*- coding: utf-8 -*-

import io
import random
import string
import time
from typing import Any, List, Dict, Optional
from fastapi import UploadFile
import pandas as pd

from app.core.base_schema import BatchSetAvailable
from app.core.exceptions import CustomException
from app.utils.excel_util import ExcelUtil
from app.core.logger import log
from app.utils.hash_bcrpy_util import PwdUtil

from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.user.crud import UserCRUD
from .schema import TenantCreateSchema, TenantUpdateSchema, TenantOutSchema, TenantQueryParam
from .crud import TenantCRUD


class TenantService:
    """
    租户管理模块服务层
    """
    
    @classmethod
    async def detail_service(cls, auth: AuthSchema, id: int) -> Dict:
        """
        详情
        
        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 租户ID
        
        返回:
        - Dict: 租户模型实例字典
        """
        obj = await TenantCRUD(auth).get_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg="该数据不存在")
        
        # 获取租户详情基础数据
        result = TenantOutSchema.model_validate(obj).model_dump()
        
        return result
    
    @classmethod
    async def list_service(cls, auth: AuthSchema, search: Optional[TenantQueryParam] = None, order_by: Optional[List[Dict[str, str]]] = None) -> List[Dict]:
        """
        列表查询
        
        参数:
        - auth (AuthSchema): 认证信息模型
        - search (Optional[TenantQueryParam]): 查询参数
        - order_by (Optional[List[Dict[str, str]]]): 排序参数
        
        返回:
        - List[Dict]: 租户模型实例字典列表
        """
        search_dict = search.__dict__ if search else None
        obj_list = await TenantCRUD(auth).list_crud(search=search_dict, order_by=order_by)
        return [TenantOutSchema.model_validate(obj).model_dump() for obj in obj_list]
    
    @classmethod
    async def page_service(cls, auth: AuthSchema, page_no: int, page_size: int, search: Optional[TenantQueryParam] = None, order_by: Optional[List[Dict[str, str]]] = None) -> Dict:
        """
        分页查询
        
        参数:
        - auth (AuthSchema): 认证信息模型
        - page_no (int): 页码
        - page_size (int): 每页数量
        - search (Optional[TenantQueryParam]): 查询参数
        - order_by (Optional[List[Dict[str, str]]]): 排序参数
        
        返回:
        - Dict: 分页数据
        """
        search_dict = search.__dict__ if search else {}
        order_by_list = order_by or [{'id': 'asc'}]
        offset = (page_no - 1) * page_size
        
        result = await TenantCRUD(auth).page_crud(
            offset=offset,
            limit=page_size,
            order_by=order_by_list,
            search=search_dict
        )
        return result
    
    @classmethod
    async def create_service(cls, auth: AuthSchema, data: TenantCreateSchema) -> Dict:
        """
        创建
        
        参数:
        - auth (AuthSchema): 认证信息模型
        - data (TenantCreateSchema): 租户创建模型
        
        返回:
        - Dict: 租户模型实例字典
        """
        obj = await TenantCRUD(auth).get(name=data.name)
        if obj:
            raise CustomException(msg='创建失败，名称已存在')
        obj = await TenantCRUD(auth).get(code=data.code)
        if obj:
            raise CustomException(msg='创建失败，编码已存在')

        # 创建租户
        tenant_obj = await TenantCRUD(auth).create_crud(data=data)
        
        # 自动创建租户初始管理员用户
        await cls._create_tenant_admin_user(auth, tenant_obj)
        
        return TenantOutSchema.model_validate(tenant_obj).model_dump()
    
    @classmethod
    async def _create_tenant_admin_user(cls, auth: AuthSchema, tenant_obj) -> None:
        """
        为新创建的租户自动创建初始管理员用户
        
        参数:
        - auth (AuthSchema): 认证信息模型
        - tenant_obj: 租户对象
        
        返回:
        - None
        """
        try:
            # 生成初始管理员用户名（使用租户编码）
            username = f"{tenant_obj.code}_admin"
            
            # 生成随机密码
            password_length = 12
            characters = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(random.choice(characters) for _ in range(password_length))
            
            # 创建管理员用户数据
            admin_user_data = {
                "username": username,
                "password": PwdUtil.set_password_hash(password=password),
                "name": f"{tenant_obj.name}管理员",
                "tenant_id": tenant_obj.id,
                "user_type": "1",  # 租户管理员类型
                "status": True,
                "created_id": auth.user.id if auth.user else None
            }
            
            # 创建用户
            new_user = await UserCRUD(auth).create(data=admin_user_data)
            
            # 记录日志，包含临时密码信息（仅开发环境记录，生产环境应避免）
            log.info(f"为租户[{tenant_obj.name}]创建初始管理员用户成功，用户名: {username}，临时密码: {password}")
            
        except Exception as e:
            log.error(f"为租户[{tenant_obj.name}]创建初始管理员用户失败: {str(e)}")
            # 不中断租户创建流程，仅记录错误
            pass
    
    @classmethod
    async def update_service(cls, auth: AuthSchema, id: int, data: TenantUpdateSchema) -> Dict:
        """
        更新
        
        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 租户ID
        - data (TenantUpdateSchema): 租户更新模型
        
        返回:
        - Dict: 租户模型实例字典
        """
        # 系统租户特殊处理
        if id == 1:
            obj = await TenantCRUD(auth).update_crud(id=id, data=data)
            log.info(f"系统租户配额设置已更新")
            
            return TenantOutSchema.model_validate(obj).model_dump()
            
        # 检查数据是否存在
        obj = await TenantCRUD(auth).get_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg='更新失败，该数据不存在')
        
        # 检查名称是否重复
        exist_obj = await TenantCRUD(auth).get(name=data.name)
        if exist_obj and exist_obj.id != id:
            raise CustomException(msg='更新失败，名称重复')
            
        obj = await TenantCRUD(auth).update_crud(id=id, data=data)
        return TenantOutSchema.model_validate(obj).model_dump()
    
    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: List[int]) -> None:
        """
        删除
        
        参数:
        - auth (AuthSchema): 认证信息模型
        - ids (List[int]): 租户ID列表
        
        返回:
        - None
        """
        if len(ids) < 1:
            raise CustomException(msg='删除失败，删除对象不能为空')
        
        # 系统租户保护：不允许删除系统租户(id=1)
        if 1 in ids:
            raise CustomException(msg='系统租户不允许删除')
        
        # 检查所有要删除的数据是否存在
        for id in ids:
            obj = await TenantCRUD(auth).get_by_id_crud(id=id)
            if not obj:
                raise CustomException(msg=f'删除失败，ID为{id}的数据不存在')
                
        await TenantCRUD(auth).delete_crud(ids=ids)
    
    @classmethod
    async def set_available_service(cls, auth: AuthSchema, data: BatchSetAvailable) -> None:
        """
        批量设置状态
        
        参数:
        - auth (AuthSchema): 认证信息模型
        - data (BatchSetAvailable): 批量设置状态模型
        
        返回:
        - None
        """
        # 系统租户保护：不允许禁用系统租户(id=1)
        if data.status is False and 1 in data.ids:
            raise CustomException(msg='系统租户不允许禁用')
        
        await TenantCRUD(auth).set_available_crud(ids=data.ids, status=data.status)
    
    @classmethod
    async def batch_export_service(cls, obj_list: List[Dict[str, Any]]) -> bytes:
        """
        批量导出
        
        参数:
        - obj_list (List[Dict[str, Any]]): 租户模型实例字典列表
        
        返回:
        - bytes: Excel文件字节流
        """
        mapping_dict = {
            'id': '编号',
            'name': '名称', 
            'code': '编码',
            'status': '状态',
            'description': '备注',
            'start_time': '开始时间',
            'end_time': '结束时间',
            'created_time': '创建时间',
            'updated_time': '更新时间',
            'created_id': '创建者',
        }

        # 复制数据并转换状态
        data = obj_list.copy()
        for item in data:
            # 系统租户特殊标记
            if item.get('id') == 1:
                item['name'] = f"{item.get('name')} [系统租户]"
            
            # 处理状态
            item['status'] = '启用' if item.get('status') == '0' else '停用'
            
            # 处理创建者
            creator_info = item.get('created_id')
            if isinstance(creator_info, dict):
                item['created_id'] = creator_info.get('name', '未知')
            else:
                item['created_id'] = '未知'
        
        # 限制导出数量，防止大数据量导出
        max_export_count = 1000
        if len(data) > max_export_count:
            data = data[:max_export_count]
            log.warning(f'导出数据超过{max_export_count}条限制，仅导出前{max_export_count}条')

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)

    @classmethod
    async def batch_import_service(cls, auth: AuthSchema, file: UploadFile, update_support: bool = False) -> str:
        """
        批量导入
        
        参数:
        - auth (AuthSchema): 认证信息模型
        - file (UploadFile): 上传的Excel文件
        - update_support (bool): 是否支持更新存在数据
        
        返回:
        - str: 导入结果信息
        """
        
        header_dict = {
            '名称': 'name',
            '编码': 'code',
            '状态': 'status',
            '描述': 'description',
            '开始时间': 'start_time',
            '结束时间': 'end_time'
        }

        try:
            # 读取Excel文件
            contents = await file.read()
            df = pd.read_excel(io.BytesIO(contents))
            await file.close()
            
            # 验证导入数量限制
            max_import_count = 100
            if len(df) > max_import_count:
                raise CustomException(msg=f"单次导入不能超过{max_import_count}条数据")
            
            if df.empty:
                raise CustomException(msg="导入文件为空")
            
            # 检查表头是否完整
            missing_headers = [header for header in header_dict.keys() if header not in df.columns]
            if missing_headers:
                raise CustomException(msg=f"导入文件缺少必要的列: {', '.join(missing_headers)}")
            
            # 重命名列名
            df.rename(columns=header_dict, inplace=True)
            
            # 验证必填字段
            required_fields = ['name', 'code', 'status']
            for field in required_fields:
                missing_rows = df[df[field].isnull()].index.tolist()
                if missing_rows:
                    field_name = [k for k,v in header_dict.items() if v == field][0]
                    error_rows = [i+1 for i in missing_rows]
                    raise CustomException(msg=f"{field_name}不能为空，第{error_rows}行")
            
            error_msgs = []
            success_count = 0
            count = 0
            processed_names = set()  # 用于检测重复名称
            processed_codes = set()  # 用于检测重复编码
            
            # 处理每一行数据
            for index, row in df.iterrows():
                count += 1
                try:
                    # 数据转换前的类型检查
                    try:
                        status = True if str(row['status']).strip() == '正常' else False
                    except ValueError:
                        error_msgs.append(f"第{count}行: 状态必须是'正常'或'停用'")
                        continue
                    
                    # 字段格式验证
                    name = str(row['name']).strip()
                    if len(name) < 2 or len(name) > 64:
                        error_msgs.append(f"第{count}行: 租户名称长度必须在2-64个字符之间")
                        continue
                    
                    # 检查名称是否只包含允许的字符
                    if not all(c.isalnum() or c in '-_' for c in name.replace(' ', '')):
                        error_msgs.append(f"第{count}行: 租户名称只能包含字母、数字、下划线、中划线和空格")
                        continue
                    
                    # 检查导入文件内的重复名称
                    if name in processed_names:
                        error_msgs.append(f"第{count}行: 租户名称 '{name}' 在文件中重复")
                        continue
                    processed_names.add(name)
                    
                    # 处理编码
                    code = str(row['code']).strip()
                    if code in processed_codes:
                        error_msgs.append(f"第{count}行: 租户编码 '{code}' 在文件中重复")
                        continue
                    processed_codes.add(code)
                    
                    # 构建租户数据
                    data = {
                        "name": name,
                        "code": code,
                        "status": status,
                        "description": str(row['description']).strip(),
                    }
                    
                    
                    # 检查时间有效性
                    if 'start_time' in data and 'end_time' in data and data['start_time'] > data['end_time']:
                        error_msgs.append(f"第{count}行: 开始时间不能晚于结束时间")
                        continue
                    
                    # 处理租户导入
                    exists_obj = await TenantCRUD(auth).get(name=data["name"])
                    if exists_obj:
                        # 系统租户保护
                        if exists_obj.id == 1:
                            error_msgs.append(f"第{count}行: 系统租户不允许修改")
                            continue
                            
                        if update_support:
                            await TenantCRUD(auth).update(id=exists_obj.id, data=data)
                            success_count += 1
                        else:
                            error_msgs.append(f"第{count}行: 租户 {data['name']} 已存在")
                    else:
                        # 检查编码是否已存在
                        exists_code = await TenantCRUD(auth).get(code=data["code"])
                        if exists_code:
                            error_msgs.append(f"第{count}行: 租户编码 '{data['code']}' 已存在")
                            continue
                            
                        # 创建租户
                        new_tenant = await TenantCRUD(auth).create(data=data)
                        success_count += 1
                        
                        # 自动创建租户管理员（如果导入数量不是特别大）
                        if success_count < 10:  # 限制自动创建管理员的数量
                            await cls._create_tenant_admin_user(auth, new_tenant)
                        else:
                            log.info(f"批量导入超过10个租户，跳过自动创建管理员用户")
                        
                except Exception as e:
                    error_msgs.append(f"第{count}行: {str(e)}")
                    continue

            # 返回详细的导入结果
            result = f"成功导入 {success_count} 条数据"
            if error_msgs:
                result += "\n错误信息:\n" + "\n".join(error_msgs)
                # 记录错误详情到日志
                log.error(f"租户批量导入错误详情: {error_msgs}")
            
            log.info(f"租户批量导入完成: 成功{success_count}条, 失败{len(error_msgs)}条")
            return result
            
        except CustomException:
            raise
        except Exception as e:
            log.error(f"批量导入租户失败: {str(e)}")
            raise CustomException(msg=f"导入失败: {str(e)}")

    @classmethod
    async def import_template_download_service(cls) -> bytes:
        """
        下载导入模板
        
        返回:
        - bytes: Excel文件字节流
        """
        header_list = ['名称', '编码', '状态', '描述', '开始时间', '结束时间']
        selector_header_list = ['状态'] 
        option_list = [{'状态': ['正常', '停用']}]
        
        # 添加示例数据和说明
        sample_data = [
            ['测试租户1', 'TEST001', '正常', '这是一个测试租户', '', ''],
            ['测试租户2', 'TEST002', '正常', '这是另一个测试租户', '', '']
        ]
        
        # 添加说明文本
        description = """导入说明：
1. 名称和编码为必填项，名称长度2-64个字符
2. 编码如果不填写，系统会自动生成
3. 状态只能选择'正常'或'停用'
4. 时间格式：YYYY-MM-DD HH:MM:SS或YYYY-MM-DD
5. 单次导入最多支持100条数据
"""
        
        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=selector_header_list,
            option_list=option_list
        )