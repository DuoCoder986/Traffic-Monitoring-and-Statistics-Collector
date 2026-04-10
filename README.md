# SDN Project: POX Controller and Mininet Custom Topology

## Problem Statement
The objective of this project is to implement a complete Software Defined Networking (SDN) solution to demonstrate custom network topology creation, OpenFlow controller interactions, and dynamic flow rule installations using the **POX Controller**.

The primary goals are to:
1. Orchestrate a data plane simulation using Mininet with Open vSwitch.
2. Develop a custom POX-based control plane to act as a Learning Switch.
3. Integrate a Firewall module inside the controller to inspect IP layer traffic and block specific communications (`h1` and `h4`), effectively deploying dynamic DROP flow entries using OpenFlow 1.0.
4. Provide active network monitoring and statistics logging of current OpenFlow rules pushed into the virtual switch.

## Prerequisites & Setup Instructions

These scripts are built to run on **Linux (Ubuntu)**, which natively supports Open vSwitch and Mininet network namespaces.

1. **Install Mininet & Git:**
   ```bash
   sudo apt-get update
   sudo apt-get install mininet git python3
   ```

2. **POX Installation:**
   POX is lightweight and runs directly from its source code. The included `run.sh` script automatically clones it into your directory:
   ```bash
   git clone https://github.com/noxrepo/pox.git
   ```

3. **Install xterm (Optional, but recommended for logging split):**
   ```bash
   sudo apt-get install xterm
   ```

## Execution Steps

You can launch the entire project instantly using the provided shell script:

```bash
chmod +x run.sh
./run.sh
```

**What the script does under the hood:**
1. Runs `sudo mn -c` to clear existing artifacts.
2. Clones the POX repository if it isn't downloaded yet.
3. Copies your `controller.py` code directly into the `pox/ext/` folder as `custom_controller.py` so POX can find it.
4. Starts POX in the background (or in a new `xterm` window if installed): `python3 ./pox/pox.py log.level --DEBUG ext.custom_controller`.
5. Starts the Mininet custom topology, connecting it to the POX Controller using POX's default port `6633`.

---

## Testing Scenarios

Once the Mininet CLI (`mininet>`) is open, run the following academic test cases.

### Scenario 1: Failing Case (Firewall Active)
The controller is hardcoded to drop IPv4 traffic attempting to traverse between host 1 (`h1`) and host 4 (`h4`).

**Mininet Command:**
```bash
mininet> pingall
```
**Expected Output:**
```text
*** Ping: testing ping reachability
h1 -> h2 h3 X
h2 -> h1 h3 h4
h3 -> h1 h2 h4
h4 -> X h2 h3
*** Results: 16% dropped (10/12 received)
```
*Notice that `h1` cannot reach `h4` and vice-versa, marking an `X`!*

### Scenario 2: Normal Forwarding (Allowed Traffic)
To prove that our switch is learning MAC addresses properly using the POX dictionary and actively forwarding unaffected traffic, we will benchmark throughput using `iperf`.

**Mininet Command:**
```bash
mininet> iperf h2 h3
```
**Expected Output:**
```text
*** Iperf: testing TCP bandwidth between h2 and h3
*** Results: ['33.1 Gbits/sec', '33.2 Gbits/sec']
```

---

## Monitoring and Observations

### 1. Controller Output Logging
Watch the logs printed by the POX Controller.
When `h1` tries to configure communication with `h4` (or vice-versa), the controller detects this matching event via `packet_in` and drops the packet. It logs the action explicitly:

```text
WARNING:ext.custom_controller:[FIREWALL] Dropping packet from 10.0.0.1 to 10.0.0.4
```

Additionally, **every 10 seconds**, the controller outputs a formatted periodic flow table monitoring report using the `FlowStatsReceived` event loop:
```text
============================================================
          TRAFFIC MONITORING STATS (Flow Table)          
============================================================
PRIORITY   | PACKETS    | BYTES        | MATCH REQ
------------------------------------------------------------
100        | 3          | 294          | OFPMatch(dl_type=0x800,nw_src=10.0.0.1,nw_dst=10.0.0.4)
10         | 15         | 1470         | OFPMatch(in_port=1,dl_src=00:00:00:00:00:01,dl_dst=00:00:00:00:00:02)
============================================================
```


### 2. Validating the Actual Core Switch Table
To view the raw flow entries directly installed inside the underlying Open vSwitch data plane by POX, run standard `ovs-ofctl`:

**Mininet Command:**
```bash
mininet> sh ovs-ofctl dump-flows s1
```
**Expected Output:**
```text
 cookie=0x0, duration=6.551s, table=0, n_packets=5, n_bytes=490, idle_timeout=60, priority=100,ip,nw_src=10.0.0.1,nw_dst=10.0.0.4 actions=drop
 cookie=0x0, duration=8.349s, table=0, n_packets=20, n_bytes=1960, idle_timeout=15, hard_timeout=30, priority=10,in_port="s1-eth1",dl_src=00:00:00:00:00:01,dl_dst=00:00:00:00:00:02 actions=output:"s1-eth2"
```

## Proof of Output (Screenshots)
*(Please replace these placeholders with actual screenshots from your Ubuntu execution during submission)*

![Topology Setup Demo Image Placeholder]()
*Caption: Mininet initialization with 4 hosts and POX remote controller.*

![Controller Output Demo Image Placeholder]()
*Caption: POX controller reporting MAC learning, Firewall DROP actions, and Flow table updates.*
