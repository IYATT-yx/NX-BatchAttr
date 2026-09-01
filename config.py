"""
file: config.py
description: NX 批量属性设置工具配置文件
author: IYATT-yx
copyright:  Copyright (c) 2026 IYATT-yx.
            Licensed under the MIT License. See LICENSE file in the project root for full license information.
"""
import os
import datetime

# 基础静态属性配置
staticAttributes = {    
    "CompanyName": "IYATT-yx有限公司",
    "DESIGNER": "IYATT-yx",
    "Designer_Date": datetime.datetime.now().strftime("%Y/%#m/%#d") if os.name == 'nt' else datetime.datetime.now().strftime("%Y/%-m/%-d") # 当前日期，如 2026/9/1
}

# 文件名自动解析映射的 NX 属性名称
# 可根据企业标准/自定义需求修改属性 Key（如 "DB_PART_NAME", "DB_PART_NO", "DMaterial" 等）
fileNameAttributes = {
    "name": "DB_PART_NAME",    # 对应 [名字]
    "number": "DB_PART_NO",    # 对应 [图号]
    "material": "DMaterial"    # 对应 [材料]
}

# 开关选项配置
# parseFileName: 是否从文件名自动解析 "名字 [图号] [材料]" (空格分隔，名字必然存在，图号/材料可选)
# overwriteExisting: 是否覆盖已存在的同名属性 (True: 覆盖, False: 仅新增缺失属性)
featureConfig = {
    "parseFileName": True,
    "overwriteExisting": True
}