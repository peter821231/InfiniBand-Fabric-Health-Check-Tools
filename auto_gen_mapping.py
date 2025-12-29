#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import csv
import subprocess
import sys
import datetime

# ================= 設定 =================
# 輸出檔名前綴
OUTPUT_PREFIX = 'full_port_mapping'
# =======================================

def get_current_date_string():
    """回傳 YYYYMMDD 格式的日期字串"""
    return datetime.datetime.now().strftime('%Y%m%d')

def run_ibnetdiscover():
    """執行 ibnetdiscover 並回傳輸出的每一行 (List of strings)"""
    print("正在執行 ibnetdiscover 掃描網路拓樸...")
    try:
        # 使用 subprocess 直接執行指令
        # universal_newlines=True 確保輸出是文字字串而不是 bytes
        cmd = ["ibnetdiscover"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=True)

        # 回傳輸出的每一行
        return result.stdout.splitlines()

    except FileNotFoundError:
        print("錯誤: 找不到 'ibnetdiscover' 指令。請確認您是否在管理節點且已安裝 infiniband-diags。")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"錯誤: 執行 ibnetdiscover 失敗。\n{e}")
        sys.exit(1)

def calculate_p_port(v_port, total_switch_ports):
    """計算物理 Port (pPort)"""
    v_port = int(v_port)
    total_switch_ports = int(total_switch_ports)
    if total_switch_ports > 100: split_factor = 4
    elif total_switch_ports > 50: split_factor = 2
    else: split_factor = 1
    return (v_port + split_factor - 1) // split_factor, split_factor

def parse_topology_data(lines, output_file):
    """
    解析拓樸資料並寫入 CSV
    :param lines: ibnetdiscover 的輸出內容 (List)
    :param output_file: 輸出的 CSV 檔名
    """
    print("正在解析拓樸資料...")
    mappings = []
    current_switch_name = "Unknown"
    current_switch_total_ports = 32

    # Regex 1: Switch 定義
    rx_switch_def = re.compile(r'^Switch\s+(\d+)\s+".*?"\s+#\s*"(.*?)"')

    # Regex 2: 連線定義 (已包含修正，可處理 GUID)
    rx_link = re.compile(r'^\s*\[(\d+)\]\s+"(H-|S-).*?\[(\d+)\].*?#\s*"(.*?)"')

    for line in lines:
        line = line.strip()

        # 1. 識別 Switch
        sw_match = rx_switch_def.search(line)
        if sw_match:
            current_switch_total_ports = int(sw_match.group(1))
            # 取出 Switch 名稱 (去除引號與多餘資訊)
            current_switch_name = sw_match.group(2).split()[0]
            continue

        # 2. 識別連線
        link_match = rx_link.search(line)
        if link_match:
            v_port = link_match.group(1)
            type_prefix = link_match.group(2)
            target_port = link_match.group(3)
            raw_target = link_match.group(4)

            # 計算物理 Port
            p_port, _ = calculate_p_port(v_port, current_switch_total_ports)

            # 判斷類型
            dev_type = "Server" if "H-" in type_prefix else "Switch"
            target_name = raw_target.split()[0]

            mappings.append({
                'Switch_Name': current_switch_name,
                'vPort': int(v_port),
                'pPort': p_port,
                'Target_Name': target_name,
                'Target_Port': target_port,
                'Device_Type': dev_type
            })

    # 3. 寫入 CSV
    if mappings:
        # 排序: 先排 Switch 名字，再排 vPort 數字
        mappings.sort(key=lambda x: (x['Switch_Name'], x['vPort']))

        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Switch_Name', 'vPort', 'pPort', 'Target_Name', 'Target_Port', 'Device_Type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(mappings)

            print(f"成功! 對照表已產生: {output_file}")
            print(f"共處理 {len(mappings)} 條連線。")
        except IOError as e:
            print(f"錯誤: 無法寫入檔案 {output_file}。\n{e}")
    else:
        print("警告: 未找到任何連線資料，請檢查 ibnetdiscover 輸出是否正常。")

def main():
    # 1. 決定檔名
    date_str = get_current_date_string()
    output_csv = f"{OUTPUT_PREFIX}_{date_str}.csv"

    # 2. 取得資料
    topo_lines = run_ibnetdiscover()

    # 3. 解析並存檔
    parse_topology_data(topo_lines, output_csv)

if __name__ == "__main__":
    main()
