#!/usr/bin/env python3
"""
Ticket Information Formatter Tool

从program.json读取信息并生成格式化的markdown文件。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


def int_to_roman(num: int) -> str:
    """将整数转换为罗马数字"""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syb = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num


def load_program_json(json_path: Path) -> Dict[str, Any]:
    """加载并解析program.json文件"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"错误: 找不到文件 {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: JSON格式无效 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取文件时出错 - {e}")
        sys.exit(1)


def validate_program_data(data: Dict[str, Any]) -> bool:
    """验证program.json数据的有效性"""
    if not isinstance(data, dict):
        print("错误: JSON根对象必须是字典")
        return False
    
    if 'items' not in data:
        print("错误: 缺少 'items' 字段")
        return False
    
    if not isinstance(data['items'], list):
        print("错误: 'items' 必须是数组")
        return False
    
    if len(data['items']) == 0:
        print("错误: 'items' 数组不能为空")
        return False
    
    for i, item in enumerate(data['items']):
        if not isinstance(item, dict):
            print(f"错误: items[{i}] 必须是对象")
            return False
        
        if 'type' not in item:
            print(f"错误: items[{i}] 缺少 'type' 字段")
            return False
        
        item_type = item['type']
        if item_type not in ['piece', 'intermission']:
            print(f"错误: items[{i}] 的 'type' 必须是 'piece' 或 'intermission'")
            return False
        
        if item_type == 'piece':
            required_fields = ['title', 'composer']
            for field in required_fields:
                if field not in item:
                    print(f"错误: items[{i}] (曲目) 缺少必需字段 '{field}'")
                    return False
                if not isinstance(item[field], str) or not item[field].strip():
                    print(f"错误: items[{i}] 的 '{field}' 字段不能为空")
                    return False
            
            # movements是可选的，但如果存在必须是数组
            if 'movements' in item:
                if not isinstance(item['movements'], list):
                    print(f"错误: items[{i}] 的 'movements' 必须是数组")
                    return False
                # 检查数组中的元素都是字符串
                for j, movement in enumerate(item['movements']):
                    if not isinstance(movement, str):
                        print(f"错误: items[{i}].movements[{j}] 必须是字符串")
                        return False
    
    return True


def format_piece(item: Dict[str, Any]) -> str:
    """格式化单个曲目为markdown"""
    composer = item['composer']
    years = item['years']
    title = item['title']
    
    composer_line = f"#### *{composer.upper()}*"
    if years:
        composer_line += f" ({years})"
    lines = [
        f"### **{title}**",
        composer_line
    ]
    
    # 如果有乐章，直接输出，不做任何转换
    if 'movements' in item and item['movements']:
        for movement in item['movements']:
            lines.append(movement)
    
    return '\n'.join(lines)


def format_intermission() -> str:
    """格式化中场休息为markdown"""
    return "#### *— INTERMISSION —*"


def generate_program_markdown(data: Dict[str, Any]) -> str:
    """生成完整的program markdown"""
    # 添加标题
    sections = ["## Piano Recital Program", "---"]
    
    items = data['items']
    
    for i, item in enumerate(items):
        item_type = item['type']
        
        if item_type == 'piece':
            sections.append(format_piece(item))
        elif item_type == 'intermission':
            sections.append(format_intermission())
        
        # 每个item后添加分隔线（最后一个也要）
        sections.append("---")
    
    return '\n'.join(sections)


def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    
    # 默认使用同目录下的program.json
    program_json = script_dir / 'program.json'
    
    # 如果命令行提供了参数，使用参数作为文件路径
    if len(sys.argv) > 1:
        program_json = Path(sys.argv[1])
    
    # 检查文件是否存在
    if not program_json.exists():
        print(f"错误: 文件不存在 {program_json}")
        print(f"提示: 请确保 {program_json} 文件存在，或参考 example_program.json 创建")
        sys.exit(1)
    
    # 加载JSON数据
    data = load_program_json(program_json)
    
    # 验证数据
    if not validate_program_data(data):
        sys.exit(1)
    
    # 生成markdown
    markdown_content = generate_program_markdown(data)
    
    # 输出文件路径
    output_file = script_dir / 'program.md'
    
    # 写入文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"成功: 已生成 {output_file}")
    except Exception as e:
        print(f"错误: 写入文件时出错 - {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
