import json
import os
import re
from typing import Dict, Any, Tuple


def validate_ir_ctl_cfg(mcp_cfg: Dict[str, Any]) -> Tuple[bool, str, Any]:
    """
    校验irCtl配置
    return: (ok:bool, msg:str, ir_ctl:dict|None)
    """
    ir_ctl = mcp_cfg.get("irCtl")
    if not ir_ctl:
        return False, "未找到irCtl字段", None

    instructions = ir_ctl.get("instructions", "").strip()
    cmd_node = ir_ctl.get("cmd", {})
    raw_cmd_list = cmd_node.get("rawCmdList", [])

    if not instructions:
        return False, "irCtl.instructions不能为空", None
    if not isinstance(raw_cmd_list, list) or len(raw_cmd_list) == 0:
        return False, "irCtl.cmd.rawCmdList必须为非空数组", None

    return True, "", ir_ctl


# 构建 rawCmdList C++片段
def build_raw_cpp(raw_list):
    items = []
    for item in raw_list:
        cmd_name = item.get("cmdName", "")
        raw_data = item.get("rawData", [])
        num_str = ",  ".join(str(x) for x in raw_data)
        block = f'''{{"{cmd_name:s}",{{{num_str}}}}}'''
        items.append(block)
    joined = ",\n".join(items)
    return f"{{\n{joined}\n}}"

# 构建 seqCmdList C++片段
def build_seq_cpp(seq_list):
    seq_items = []
    for seq in seq_list:
        seq_name = seq.get("cmdName", "")
        steps_arr = seq.get("steps", [])
        step_lines = []
        for st in steps_arr:
            s_cmd = st.get("cmdName", "")
            delay_val = st.get("delayAfter", 0)
            step_lines.append(f'            {{"{s_cmd}", {delay_val}UL}}')
        steps_block = ",\n".join(step_lines)
        one_seq = f'''{{"{seq_name}",{{{steps_block}}}}}'''
        seq_items.append(one_seq)
    joined_seq = ",\n".join(seq_items)
    return f"{{\n{joined_seq}\n}}"



def render_esp32_ino_from_irctl(mcp_cfg: Dict[str, Any], ir_ctl: Dict[str, Any]) -> Tuple[bool, str, str]:
    """
    读取ino模板，替换controllerPath / rawCmdList / seqCmdList，返回完整ino源码字符串
    return (ok, msg, ino_code)
    """
    try:
        template_path = './config/local_ir_dvc_exp.ino'
        with open(template_path, 'r', encoding="utf-8") as f:
            tpl_content = f.read()

        args_arr = mcp_cfg.get("args", [])
        module_name = args_arr[-1]
        controller_path_val = f"/{module_name.replace('.', '/')}"
        # 替换controllerPath
        tpl_content = tpl_content.replace('very_very_very_very_very_very_special_controllerPath', controller_path_val)
        # 替换apName
        tpl_content = tpl_content.replace('very_very_very_very_very_very_special_apName', module_name)

        cmd_node = ir_ctl.get("cmd", {})
        raw_cmd_list = cmd_node.get("rawCmdList", [])
        seq_cmd_list = cmd_node.get("seqCmdList", [])
        if not isinstance(seq_cmd_list, list): seq_cmd_list = []
        # 替换rawCmdList整块
        tpl_content = tpl_content.replace('very_very_very_very_very_very_special_rawCmdList', build_raw_cpp(raw_cmd_list))
        # 替换seqCmdList整块
        tpl_content = tpl_content.replace('very_very_very_very_very_very_special_seqCmdList', build_seq_cpp(seq_cmd_list))

        return True, "", tpl_content
    except Exception as e:
        return False, f"ino模板渲染异常:{str(e)}", ""


def write_mcp_py_file(mcp_cfg: Dict[str, Any], out_full_file: str) -> Tuple[bool, str]:
    """
    完全保留你原有逻辑：读取 local_ir_mcp_exp.py 模板，分割标记，生成py文件写入磁盘
    :param mcp_cfg: mcp配置对象
    :param out_full_file: 输出py完整路径
    :return: (ok,msg)
    """
    try:
        with open('./config/local_ir_mcp_exp.py', 'r', encoding="utf-8") as f:
            exp_content = f.read()

        endpoint_module = mcp_cfg.get("args")[-1]
        exp_content = exp_content.replace("very_very_very_very_very_very_special_module_name", endpoint_module)

        mcp_func_name = endpoint_module.split(".")[-1] if '.' in endpoint_module else endpoint_module
        exp_content = exp_content.replace("very_very_very_very_very_very_special_device_controller", mcp_func_name)

        dir_path = os.path.dirname(out_full_file)
        os.makedirs(dir_path, exist_ok=True)
        with open(out_full_file, "w", encoding="utf-8") as f:
            f.write(exp_content)
        return True, f"py脚本已生成:{out_full_file}"
    except Exception as e:
        return False, f"写入mcp py文件异常:{str(e)}"


