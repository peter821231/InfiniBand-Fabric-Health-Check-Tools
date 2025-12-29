#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import subprocess
import sys
import re
import datetime
import os

# 設定檔名
DB_FILE = 'full_port_mapping.csv'

class Colors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    CYAN = '\033[96m'

def load_mapping_db(filename):
    mapping = {}
    if not os.path.exists(filename):
        print(f"{Colors.FAIL}Error: Database file '{filename}' not found.{Colors.ENDC}")
        sys.exit(1)

    try:
        with open(filename, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sw = row['Switch_Name'].strip()
                v_port = row['vPort'].strip()
                # Key = (SwitchName, vPort)
                mapping[(sw, v_port)] = row
    except Exception as e:
        print(f"{Colors.FAIL}Error reading CSV: {e}{Colors.ENDC}")
        sys.exit(1)
    return mapping

def get_down_links():
    down_links = {}
    try:
        cmd = ["iblinkinfo", "-l"]
        # Python 3.6+ compatible check
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=True)
    except Exception:
        print(f"{Colors.FAIL}Error executing iblinkinfo{Colors.ENDC}")
        sys.exit(1)

    # Regex 解析: 抓取 GUID, Switch Name, Port(括號前), State(括號內)
    regex = re.compile(r'^0x[\da-fA-F]+\s+"(.*?)"\s+\d+\s+(\d+)\[.*?\((.*?)\)')

    for line in result.stdout.splitlines():
        match = regex.search(line)
        if match:
            sw = match.group(1).strip()
            port = match.group(2).strip()
            state = match.group(3).strip()

            # 過濾掉 Active 的連線
            if "Active" not in state:
                down_links[(sw, port)] = state
    return down_links

def main():
    print(f"{Colors.HEADER}====== InfiniBand Fabric Health Check (Paired View) ======{Colors.ENDC}")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("Loading database...", end=" ")
    db = load_mapping_db(DB_FILE)
    print(f"Done ({len(db)} links).")

    print("Scanning fabric...", end=" ")
    down_links_map = get_down_links()
    print("Done.\n")

    # ================= [新增] 預先篩選邏輯 =================
    # 找出「既在 down_links_map 裡面」又「在 db 資料庫裡面」的有效問題
    valid_issues = []
    sorted_keys = sorted(down_links_map.keys())

    for key in sorted_keys:
        if key in db:
            valid_issues.append(key)

    # 如果篩選後發現沒有任何「已定義的」Port 斷線，就視為健康
    if not valid_issues:
        print(f"{Colors.OKGREEN}All mapped ports are Active! System Healthy.{Colors.ENDC}")
        # 這裡直接結束，不會印出表格標題
        return
    # ======================================================

    # 只有當 valid_issues 不為空時，才印出 Header
    print(f"{Colors.CYAN}[Legend] Format: DeviceName(p=Physical port/v=Virtual port){Colors.ENDC}")
    print(f"{'Severity':<10} | {'Source Device':<35} | {'State':<15} | {'Target Device':<35}")
    print("-" * 100)

    processed_links = set()

    # 只迴圈那些「有效的」問題
    for sw_name, v_port in valid_issues:
        state = down_links_map[(sw_name, v_port)]

        # 取得本機資訊
        src_info = db[(sw_name, v_port)] # 這裡一定取得到，因為前面 filter 過了

        target_name = src_info['Target_Name']
        target_vport = src_info['Target_Port']
        dev_type = src_info['Device_Type']
        src_p_port = src_info['pPort']

        # 產生唯一連線 ID (A->B 和 B->A 視為同一條)
        link_id = tuple(sorted([ (sw_name, v_port), (target_name, target_vport) ]))

        if link_id in processed_links:
            continue # 已經印過這條線的另一端了
        processed_links.add(link_id)

        # 檢查對面是否也斷線 (Pairs Check)
        is_peer_down = (target_name, target_vport) in down_links_map

        # 組合顯示字串
        src_str = f"{sw_name}(p{src_p_port}/v{v_port})"

        if dev_type == 'Switch':
            # 查對面 Switch 的 pPort
            tgt_row = db.get((target_name, target_vport))
            if tgt_row:
                tgt_p_port = tgt_row['pPort']
                tgt_str = f"{target_name}(p{tgt_p_port}/v{target_vport})"
            else:
                tgt_str = f"{target_name}(v{target_vport})"

            # 判定邏輯
            if is_peer_down:
                severity = f"{Colors.FAIL}[CRITICAL]{Colors.ENDC}"
                arrow = "<--->"
            else:
                severity = f"{Colors.FAIL}[CRITICAL]{Colors.ENDC}"
                arrow = " --->" # 單邊斷線

        else: # Server
            tgt_str = f"{target_name} (Server)"
            severity = f"{Colors.WARNING}[WARNING]{Colors.ENDC}"
            arrow = " --->"

        print(f"{severity:<19} | {src_str:<35} | {state:<15} | {arrow} {tgt_str}")

    print("-" * 100)
    print(f"\n{Colors.FAIL}Issues detected! Please check the devices listed above.{Colors.ENDC}")

if __name__ == "__main__":
    main()
