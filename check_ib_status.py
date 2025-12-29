#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import subprocess
import sys
import re
import datetime
import os

# Set mapping csv file
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

    # Regex : grep GUID, Switch Name, Port, State
    regex = re.compile(r'^0x[\da-fA-F]+\s+"(.*?)"\s+\d+\s+(\d+)\[.*?\((.*?)\)')

    for line in result.stdout.splitlines():
        match = regex.search(line)
        if match:
            sw = match.group(1).strip()
            port = match.group(2).strip()
            state = match.group(3).strip()

            # Filter Active state
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

    valid_issues = []
    sorted_keys = sorted(down_links_map.keys())

    for key in sorted_keys:
        if key in db:
            valid_issues.append(key)

    if not valid_issues:
        print(f"{Colors.OKGREEN}All mapped ports are Active! System Healthy.{Colors.ENDC}")
        return
    # ======================================================

    # Only valid_issues is not empty, then print Header
    print(f"{Colors.CYAN}[Legend] Format: DeviceName(p=Physical port/v=Virtual port){Colors.ENDC}")
    print(f"{'Severity':<10} | {'Source Device':<35} | {'State':<15} | {'Target Device':<35}")
    print("-" * 100)

    processed_links = set()

    for sw_name, v_port in valid_issues:
        state = down_links_map[(sw_name, v_port)]

        # get host info
        src_info = db[(sw_name, v_port)]

        target_name = src_info['Target_Name']
        target_vport = src_info['Target_Port']
        dev_type = src_info['Device_Type']
        src_p_port = src_info['pPort']

        # get link (A->B and B->A are the same)
        link_id = tuple(sorted([ (sw_name, v_port), (target_name, target_vport) ]))

        if link_id in processed_links:
            continue
        processed_links.add(link_id)

        # Pairs Check
        is_peer_down = (target_name, target_vport) in down_links_map

        # Collab the info
        src_str = f"{sw_name}(p{src_p_port}/v{v_port})"

        if dev_type == 'Switch':
            # Peer Switch pPort
            tgt_row = db.get((target_name, target_vport))
            if tgt_row:
                tgt_p_port = tgt_row['pPort']
                tgt_str = f"{target_name}(p{tgt_p_port}/v{target_vport})"
            else:
                tgt_str = f"{target_name}(v{target_vport})"

            # Check Status
            if is_peer_down:
                severity = f"{Colors.FAIL}[CRITICAL]{Colors.ENDC}"
                arrow = "<--->"
            else:
                severity = f"{Colors.FAIL}[CRITICAL]{Colors.ENDC}"
                arrow = " --->" 

        else: # Server
            tgt_str = f"{target_name} (Server)"
            severity = f"{Colors.WARNING}[WARNING]{Colors.ENDC}"
            arrow = " --->"

        print(f"{severity:<19} | {src_str:<35} | {state:<15} | {arrow} {tgt_str}")

    print("-" * 100)
    print(f"\n{Colors.FAIL}Issues detected! Please check the devices listed above.{Colors.ENDC}")

if __name__ == "__main__":
    main()
