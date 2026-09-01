"""
file: NX-BatchAttr.py
description: NX 批量属性设置工具
author: IYATT-yx
copyright:   Copyright (c) 2026 IYATT-yx.
            Licensed under the MIT License. See LICENSE file in the project root for full license information.
"""
import os
import ctypes
from ctypes import wintypes
import NXOpen
import config

def openWithDialog(filePath):
    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("fMask", wintypes.ULONG),
            ("hwnd", wintypes.HWND),
            ("lpVerb", wintypes.LPCWSTR),
            ("lpFile", wintypes.LPCWSTR),
            ("lpParameters", wintypes.LPCWSTR),
            ("lpDirectory", wintypes.LPCWSTR),
            ("nShow", ctypes.c_int),
            ("hInstApp", wintypes.HINSTANCE),
            ("lpIDList", wintypes.LPVOID),
            ("lpClass", wintypes.LPCWSTR),
            ("hkeyClass", wintypes.HKEY),
            ("dwHotKey", wintypes.DWORD),
            ("hIconOrMonitor", wintypes.HANDLE),
            ("hProcess", wintypes.HANDLE)
        ]

    SEE_MASK_INVOKEIDLIST = 0x0000000C
    SW_SHOWNORMAL = 1

    sei = SHELLEXECUTEINFO()
    sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
    sei.fMask = SEE_MASK_INVOKEIDLIST
    sei.hwnd = None
    sei.lpVerb = "openas"
    sei.lpFile = os.path.abspath(filePath)
    sei.nShow = SW_SHOWNORMAL

    ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))

def main():
    session = NXOpen.Session.GetSession()
    ui = NXOpen.UI.GetUI()
    workPart = session.Parts.Work
    lw = session.ListingWindow

    promptMessage = "请选择运行模式：\n\n【是】选择打开方式修改属性配置文件 (config.py)\n【否】直接应用属性配置文件"

    dialogResult = ui.NXMessageBox.Show(
        "NX-BatchAttr 属性批处理",
        NXOpen.NXMessageBox.DialogType.Question,
        promptMessage
    )

    if dialogResult == 1:
        configPath = config.__file__
        openWithDialog(configPath)
        return
    elif dialogResult != 2:
        return

    lw.Open()
    if not workPart:
        ui.NXMessageBox.Show("错误", NXOpen.NXMessageBox.DialogType.Error, "未检测到活动零件！")
        return

    # 统计计数器
    stats = {
        "parts_success": 0,
        "parts_failed": 0,
        "attrs_added": 0,
        "attrs_modified": 0,
        "attrs_skipped": 0,
        "attrs_unchanged": 0
    }

    processedParts = set()
    rootComponent = workPart.ComponentAssembly.RootComponent

    lw.WriteLine("==========================================================")
    lw.WriteLine("            NX-BatchAttr 属性批处理任务开始")
    lw.WriteLine("==========================================================")

    if rootComponent is None:
        updatePartAttributes(workPart, lw, processedParts, stats)
    else:
        processComponentRecursive(rootComponent, lw, processedParts, stats)

    # 打印全局汇总信息
    lw.WriteLine("\n==========================================================")
    lw.WriteLine("                  任务处理统计结果")
    lw.WriteLine("==========================================================")
    lw.WriteLine(f"  [>] 处理零件总数 : {len(processedParts)} 件")
    lw.WriteLine(f"  [V] 成功处理零件 : {stats['parts_success']} 件")
    lw.WriteLine(f"  [X] 处理失败零件 : {stats['parts_failed']} 件")
    lw.WriteLine("  --------------------------------------------------------")
    lw.WriteLine(f"  [+] 新增属性 : {stats['attrs_added']} 个")
    lw.WriteLine(f"  [*] 修改属性 : {stats['attrs_modified']} 个")
    lw.WriteLine(f"  [-] 跳过属性 : {stats['attrs_skipped']} 个")
    lw.WriteLine(f"  [=] 保持不变 : {stats['attrs_unchanged']} 个")
    lw.WriteLine("==========================================================")

def processComponentRecursive(component, lw, processedParts, stats):
    """递归遍历组件及其子组件"""
    try:
        prototype = component.Prototype
        
        if prototype is None or not isinstance(prototype, NXOpen.Part):
            try:
                component.EnsureAttributeAndSurrogateObjectsLoaded()
                prototype = component.Prototype
            except Exception:
                pass

        if isinstance(prototype, NXOpen.Part):
            updatePartAttributes(prototype, lw, processedParts, stats)
        else:
            lw.WriteLine(f"\n[!] 跳过件 (未加载/轻量化): {component.DisplayName}")
    except Exception as e:
        lw.WriteLine(f"\n[X] 组件异常: {component.DisplayName} -> {e}")
        stats["parts_failed"] += 1

    for child in component.GetChildren():
        processComponentRecursive(child, lw, processedParts, stats)

def updatePartAttributes(part, lw, processedParts, stats):
    """更新指定零件对象的属性"""
    partTag = part.Tag
    if partTag in processedParts:
        return
    processedParts.add(partTag)

    try:
        fullPath = getattr(part, 'FullPath', '')
        if fullPath:
            filename = os.path.basename(fullPath)
        else:
            filename = getattr(part, 'Leaf', part.Name if hasattr(part, 'Name') else "未知零件")

        nameWithoutExt, _ = os.path.splitext(filename)
        targetAttributes = dict(config.staticAttributes)

        # 解析文件名 “图号 [名称] [材料]”
        if config.featureConfig.get("parseFileName", False):
            tokens = nameWithoutExt.strip().split()
            
            # 读取 config 中的属性 key 映射（带有默认备用值）
            attrMap = getattr(config, 'fileNameAttributes', {})
            attrNumberKey = attrMap.get("number", "DB_PART_NO")
            attrNameKey = attrMap.get("name", "DB_PART_NAME")
            attrMaterialKey = attrMap.get("material", "DMaterial")

            # 1. 只有一个字段：设置为【名称】
            if len(tokens) == 1:
                targetAttributes[attrNameKey] = tokens[0]

            # 2. 两个字段：分别设置为【图号】和【名称】
            elif len(tokens) == 2:
                targetAttributes[attrNumberKey] = tokens[0]
                targetAttributes[attrNameKey] = tokens[1]

            # 3. 三个及以上字段：分别设置为【图号】、【名称】和【材料】
            elif len(tokens) >= 3:
                targetAttributes[attrNumberKey] = tokens[0]
                targetAttributes[attrNameKey] = tokens[1]
                targetAttributes[attrMaterialKey] = tokens[2]

            else:
                lw.WriteLine(f"\n[!] 文件名为空或无法解析: {filename}")

        lw.WriteLine(f"\n[PART] 正在处理: {filename}")
        lw.WriteLine("  │")

        # 遍历比对与更新属性
        for attrName, newValue in targetAttributes.items():
            oldValue = getNxAttribute(part, attrName)

            if oldValue is None:
                setNxAttribute(part, attrName, str(newValue))
                lw.WriteLine(f"  ├─ [+] 新增 -> {attrName} = '{newValue}'")
                stats["attrs_added"] += 1
            elif oldValue != newValue:
                if config.featureConfig.get("overwriteExisting", True):
                    setNxAttribute(part, attrName, str(newValue))
                    lw.WriteLine(f"  ├─ [*] 修改 -> {attrName} : '{oldValue}' => '{newValue}'")
                    stats["attrs_modified"] += 1
                else:
                    lw.WriteLine(f"  ├─ [-] 跳过 -> {attrName} (保留原值: '{oldValue}')")
                    stats["attrs_skipped"] += 1
            else:
                lw.WriteLine(f"  ├─ [=] 保持 -> {attrName} = '{newValue}'")
                stats["attrs_unchanged"] += 1

        stats["parts_success"] += 1

    except Exception as e:
        partNameStr = getattr(part, 'FullPath', part.Name if hasattr(part, 'Name') else str(part))
        lw.WriteLine(f"  └─ [X] 失败 -> {partNameStr} ({e})")
        stats["parts_failed"] += 1

def getNxAttribute(part, attrName):
    """读取零件属性值"""
    try:
        if part.HasUserAttribute(attrName, NXOpen.NXObject.AttributeType.String, -1):
            return part.GetStringUserAttribute(attrName, -1)
    except Exception:
        pass
    return None

def setNxAttribute(part, attrName, value):
    """设置或更新 NX 用户字符串属性"""
    part.SetUserAttribute(attrName, -1, str(value), NXOpen.Update.Option.Now)

if __name__ == "__main__":
    main()