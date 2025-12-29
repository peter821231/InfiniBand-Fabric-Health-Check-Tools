# InfiniBand Fabric Health Check Tools
### Introduction
This is a suite of automation tools designed for monitoring and diagnosing InfiniBand (IB) fabric health. By creating a "Golden Record" of the network topology, these tools verify the current status against the record to quickly identify disconnected nodes or backbone links.

### Key Features
1.  **Automated Topology Snapshot**: Automatically scans and creates a CSV database of the current network connectivity.
2.  **Physical Port Mapping**: Automatically calculates the physical port (`pPort`) on the switch panel corresponding to the virtual port (`vPort`), simplifying on-site troubleshooting.
3.  **Smart Filtering**: Ignores unused/unmapped ports and alerts only on pre-defined active links.
4.  **Paired View**: Automatically merges disconnection alerts between switches into a single entry to reduce noise.

### Prerequisites
* **OS**: Linux (RHEL/CentOS/Ubuntu, etc.)
* **Python**: Python 3.6 or higher.
* **Packages**: `infiniband-diags` must be installed (provides `ibnetdiscover` and `iblinkinfo` commands).
* **Permissions**: Root privileges are recommended to ensure full fabric scanning.

### File Descriptions
* `auto_gen_mapping.py`: **Topology Generator**. Runs `ibnetdiscover` and generates a date-stamped CSV mapping file.
* `check_ib_status.py`: **Health Checker**. Reads the default symlink `full_port_mapping.csv` and outputs a health report.
* `ibcheck.sh`: **Execution Script**. A shell wrapper to run the health checker.
* `full_port_mapping.csv`: **Symlink**. Must point to the active date-stamped CSV file.

### User Guide

#### Step 1: Generate Topology Baseline (Golden Record)
Run this command when the network is in a known healthy state. It is recommended to re-run this after any cabling changes or node expansions.

```bash
python3 auto_gen_mapping.py
```
##### Output: Generates a file named full_port_mapping_YYYYMMDD.csv (e.g., full_port_mapping_20251229.csv). You could edit it manually to fit the exact statement.
##### Example:
QM9790 with 32 physical ports and x4 split 128+1(Virtual ports).
Target_Port is always vPort.
```bash
Switch_Name,vPort,pPort,Target_Name,Target_Port,Device_Type
IBLF01,1,1,icpnq102,1,Server
IBLF01,2,1,icpnq104,1,Server
IBLF01,3,1,icpnq106,1,Server
IBLF01,4,1,icpnq108,1,Server
IBLF01,5,2,icpnq110,1,Server
IBLF01,6,2,icpnq112,1,Server
IBLF01,7,2,icpnq114,1,Server
IBLF01,8,2,icpnq116,1,Server
IBLF01,9,3,icpnq118,1,Server
IBLF01,10,3,icpnq120,1,Server
IBLF01,11,3,icpnq122,1,Server
IBLF01,12,3,icpnq124,1,Server
IBLF01,13,4,icpnq126,1,Server
IBLF01,14,4,icpnq128,1,Server
IBLF01,15,4,icpnq130,1,Server
IBLF01,16,4,icpnq132,1,Server
IBLF01,17,5,icpnq134,1,Server
IBLF01,18,5,icpnq136,1,Server
IBLF01,19,5,icpnq138,1,Server
IBLF01,20,5,icpnq140,1,Server
IBLF01,21,6,icpnq142,1,Server
IBLF01,22,6,icpnq144,1,Server
IBLF01,23,6,icpnq146,1,Server
IBLF01,24,6,icpnq148,1,Server
IBLF01,25,7,icpnq150,1,Server
IBLF01,26,7,icpnq152,1,Server
IBLF01,27,7,icpnq154,1,Server
IBLF01,28,7,icpnq156,1,Server
IBLF01,33,9,IBSP01,1,Switch
IBLF01,35,9,IBSP01,3,Switch
IBLF01,37,10,IBSP01,5,Switch
IBLF01,39,10,IBSP01,7,Switch
IBLF01,41,11,IBSP02,1,Switch
IBLF01,43,11,IBSP02,2,Switch
IBLF01,45,12,IBSP02,3,Switch
IBLF01,47,12,IBSP02,4,Switch
IBLF01,49,13,IBSP03,1,Switch
IBLF01,51,13,IBSP03,2,Switch
IBLF01,53,14,IBSP03,3,Switch
IBLF01,55,14,IBSP03,4,Switch
IBLF01,57,15,IBSP04,1,Switch
IBLF01,59,15,IBSP04,2,Switch
IBLF01,61,16,IBSP04,3,Switch
IBLF01,63,16,IBSP04,4,Switch
IBLF01,65,17,IBSP05,1,Switch
IBLF01,67,17,IBSP05,2,Switch
IBLF01,69,18,IBSP05,3,Switch
IBLF01,71,18,IBSP05,4,Switch
IBLF01,73,19,IBSP06,1,Switch
IBLF01,75,19,IBSP06,2,Switch
IBLF01,77,20,IBSP06,3,Switch
IBLF01,79,20,IBSP06,4,Switch
IBLF01,81,21,IBSP07,1,Switch
IBLF01,83,21,IBSP07,2,Switch
IBLF01,85,22,IBSP07,3,Switch
IBLF01,87,22,IBSP07,4,Switch
IBLF01,89,23,IBSP08,1,Switch
IBLF01,91,23,IBSP08,2,Switch
IBLF01,93,24,IBSP08,3,Switch
IBLF01,95,24,IBSP08,4,Switch
IBLF01,97,25,icpnq101,1,Server
IBLF01,98,25,icpnq103,1,Server
IBLF01,99,25,icpnq105,1,Server
IBLF01,100,25,icpnq107,1,Server
IBLF01,101,26,icpnq109,1,Server
IBLF01,102,26,icpnq111,1,Server
IBLF01,103,26,icpnq113,1,Server
IBLF01,104,26,icpnq115,1,Server
IBLF01,105,27,icpnq117,1,Server
IBLF01,106,27,icpnq119,1,Server
IBLF01,107,27,icpnq121,1,Server
IBLF01,108,27,icpnq123,1,Server
IBLF01,109,28,icpnq125,1,Server
IBLF01,110,28,icpnq127,1,Server
IBLF01,111,28,icpnq129,1,Server
IBLF01,112,28,icpnq131,1,Server
IBLF01,113,29,icpnq133,1,Server
IBLF01,114,29,icpnq135,1,Server
IBLF01,115,29,icpnq137,1,Server
IBLF01,116,29,icpnq139,1,Server
IBLF01,117,30,icpnq141,1,Server
IBLF01,118,30,icpnq143,1,Server
IBLF01,119,30,icpnq145,1,Server
IBLF01,120,30,icpnq147,1,Server
IBLF01,121,31,icpnq149,1,Server
IBLF01,122,31,icpnq151,1,Server
IBLF01,123,31,icpnq153,1,Server
IBLF01,124,31,icpnq155,1,Server
IBLF01,129,33,Mellanox,1,Server
```
##### Note

#### Step 2: Update Symlink
The checker script reads full_port_mapping.csv by default. You must create a symbolic link pointing to the newly generated file (or any specific historical file you wish to compare against).

```bash
ln -sf full_port_mapping_20251229.csv full_port_mapping.csv
```

#### Step 3: Run Health Check
You can run the check using the wrapper script or directly via Python

Method A:
```bash
./ibcheck.sh
```
Method B:
```python3
python3 check_ib_status.py
```
##### Output:
If the system is healthy:

```bash
====== InfiniBand Fabric Health Check (Paired View) ======
Time: 2025-12-29 15:58:03
Loading database... Done (1580 links).
Scanning fabric... Done.

All mapped ports are Active! System Healthy.

```

If the system is unhealthy:

##### Exapmle:

```bash
====== InfiniBand Fabric Health Check (Paired View) ======
Time: 2025-12-29 15:56:38
Loading database... Done (1585 links).
Scanning fabric... Done.

[Legend] Format: DeviceName(p=Physical port/v=Virtual port)
Severity   | Source Device                       | State           | Target Device
----------------------------------------------------------------------------------------------------
[CRITICAL] | IBLF03(p14/v53)                     | Down/ Polling   | <---> IBSP03(p6/v11)
[CRITICAL] | IBLF03(p14/v55)                     | Down/ Polling   | <---> IBSP03(p6/v12)
[WARNING]  | IBLF13(p26/v101)                    | Down/ Polling   |  ---> gpn04 (Server)
----------------------------------------------------------------------------------------------------

Issues detected! Please check the devices listed above.

```

| Column | Description |
| :--- | :--- |
| **Severity** | **[CRITICAL]**: Switch-to-Switch link down <br>**[WARNING]**: Switch-to-Server link down |
| **Source Device** | Source Switch Name (includes pPort: Physical Port / vPort: Virtual Port) |
| **State** | Current Link State (e.g., `Down`, `Polling`) |
| **Target Device** | Target Device Name and Port info |
