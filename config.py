import os
import datetime

# 属性配置
staticAttributes = {    
    "CompanyName": "IYATT-yx有限公司",
    "DESIGNER": "IYATT-yx",
    "Designer_Date": datetime.datetime.now().strftime("%Y/%#m/%#d") if os.name == 'nt' else datetime.datetime.now().strftime("%Y/%-m/%-d") # 取当前日期，如 2026/9/1
}

# 开关选项配置
# parseFileName: 是否从文件名自动解析 "图号 名称"
# overwriteExisting: 是否覆盖已存在的同名属性 (True: 覆盖, False: 仅新增缺失属性)
featureConfig = {
    "parseFileName": True,
    "overwriteExisting": True
}