# COSC 364 RIP Assignment - Testing Report

## 1. Student Information

- **Name:** 
- **Student ID:**

## 2. Objective

The objective of this testing report is to verify that the RIP daemon implementation:

1. Parses configuration files correctly.
2. Exchanges RIP response packets correctly over UDP sockets on localhost.
3. Converges to correct minimum-cost routing tables.
4. Handles router failure and recovery as expected.
5. Applies split horizon with poisoned reverse.
6. Performs route timeout, invalidation (metric 16), and garbage collection.

## 3. Test Environment

- **Operating System:** [e.g., Ubuntu 22.04 / macOS + Linux lab machine]
- **Python Version:** [e.g., Python 3.11.x]
- **Execution Mode:** Command line
- **Host Address:** `127.0.0.1`
- **Protocol:** UDP
- **Project Directory:** `rip-python`

## 4. Implementation Under Test

- **Main executable:** `ripd.py`
- **Configuration parser:** `riplib/config.py`
- **Packet encoder/decoder:** `riplib/packet.py`
- **Routing logic:** `riplib/router.py`
- **Sample configs used in testing:**
  - `sample_configs/r1.conf`
  - `sample_configs/r2.conf`
  - `sample_configs/r3.conf`
  - `sample_configs/r4.conf`

## 5. Configuration Used for Demonstration

```text
# Router 1
router-id 1
input-ports 6101, 6102
outputs 6201-1-2, 6401-5-4
periodic-timer 2
timeout-timer 12
garbage-timer 8
jitter false
```

```text
# Router 2
router-id 2
input-ports 6201, 6202, 6203
outputs 6101-1-1, 6301-1-3, 6402-2-4
periodic-timer 2
timeout-timer 12
garbage-timer 8
jitter false
```

```text
# Router 3
router-id 3
input-ports 6301, 6302
outputs 6202-1-2, 6403-1-4
periodic-timer 2
timeout-timer 12
garbage-timer 8
jitter false
```

```text
# Router 4
router-id 4
input-ports 6401, 6402, 6403
outputs 6102-5-1, 6203-2-2, 6302-1-3
periodic-timer 2
timeout-timer 12
garbage-timer 8
jitter false
```

## 6. Test Method

The tests were performed in two ways:

1. **Automated checks** for parser and packet logic.
2. **Runtime integration testing** by launching multiple RIP router instances and observing routing table behavior during:
   - Initial convergence
   - Router shutdown
   - Router restart

## 7. Test Cases and Results

---

### Test Case 1 - Configuration Parsing Validation

**Purpose:** Verify mandatory fields and syntax/range checks in configuration files.

**Input:**
- Valid configuration file.

**Execution Steps:**
1. Run parser tests.
2. Start daemon with valid config.
3. Start daemon with intentionally invalid config(s).

**Expected Result:**
- Valid config loads successfully.

**Status:** [PASS]

**Evidence (Screenshots):** <br>
<img width="377" height="108" alt="image" src="https://github.com/user-attachments/assets/e304f858-ed0c-4ee7-8a6d-782cef8e696e" />

---

### Test Case 2 - RIP Packet Format and Consistency Checks

**Purpose:** Verify packet encoding/decoding and validation of fixed fields/metric range.

**Input:**
- Valid RIP response packets.

**Execution Steps:**
1. Run unit tests for packet encode/decode.
2. Inject/observe malformed packet handling.

**Expected Result:**
- Valid packets are decoded correctly.

**Status:** [PASS]

**Evidence (Screenshots):** <br>
<img width="764" height="137" alt="image" src="https://github.com/user-attachments/assets/69912d15-2127-456f-9254-1064783fe299" />

---

### Test Case 3 - Initial Network Convergence

**Purpose:** Verify all routers converge to correct minimum-cost routes after startup.

**Execution Steps:**
1. Start all router processes.
2. Wait for periodic updates.
3. Observe printed routing tables for all routers.

**Expected Result:**
- Routing tables converge.
- Each destination has correct minimum metric and next hop.

**Status:** [PASS]

**Evidence (Screenshots):** <br>
- Router 1 table after convergence:
  
<img width="386" height="315" alt="image" src="https://github.com/user-attachments/assets/0da3d4e2-cd9e-4bea-9e5d-c29dc35af8cf" />

- Router 2 table after convergence:

<img width="470" height="311" alt="image" src="https://github.com/user-attachments/assets/863ad815-ebe2-465a-ad44-e7d8add350eb" />

- Router 3 table after convergence:

<img width="457" height="372" alt="image" src="https://github.com/user-attachments/assets/2f217b58-1c22-4071-b8d5-d8618b6099f0" />

- Router 4 table after convergence:

<img width="483" height="387" alt="image" src="https://github.com/user-attachments/assets/26b9e8c2-3a10-461b-b21b-097ad5f751b1" />

---

### Test Case 4 - Split Horizon with Poisoned Reverse

**Purpose:** Verify updates sent to each neighbor apply poisoned reverse correctly.

**Execution Steps:**
1. Observe route learned through neighbor X.
2. Verify update sent back to X advertises that route with metric 16.

**Expected Result:**
- Per-neighbor updates differ when required.
- Routes learned from neighbor X are advertised to X as unreachable (metric 16).

**Status:** [PASS]

**Evidence (Screenshots):**

<img width="379" height="115" alt="image" src="https://github.com/user-attachments/assets/0a0ceeb5-6145-4c97-8361-497c1df2b4f0" />

---

### Test Case 5 - Router Failure Handling

**Purpose:** Verify timeout/invalidation behavior when a router stops.

**Execution Steps:**
1. Start all routers and wait for convergence.
2. Stop one router process (e.g., Router 2).
3. Observe updates and routing table changes in remaining routers.

**Expected Result:**
- Routes via failed router time out.
- Metric changes to 16 where appropriate.
- Triggered update occurs for invalid routes.
- Network reconverges to new valid state.

**Status:** [PASS]

**Evidence (Screenshots):**
- Before failure:

<img width="391" height="107" alt="image" src="https://github.com/user-attachments/assets/491e2dee-d0de-416c-9d6d-9a6817dbe33b" />

- During transition/flurry of updates:

<img width="385" height="105" alt="image" src="https://github.com/user-attachments/assets/64255ca6-039e-4547-be65-5b3babf0a58b" />

- After reconvergence:

<img width="392" height="187" alt="image" src="https://github.com/user-attachments/assets/25c6870c-9297-4113-8383-e74de5004bba" />

---

## 8. Unit Test Summary

| Test Module | Description | Result |
|---|---|---|
| `tests/test_config.py` | Config parsing and validation | [PASS] |
| `tests/test_packet.py` | RIP packet encode/decode checks | [PASS] |
| `tests/test_router_logic.py` | Split horizon poisoned reverse logic | [PASS] |


## 9. Overall Result

- **Functional correctness:** [PASS]
- **Convergence behavior:** [PASS]
- **Failure and recovery behavior:** [PASS]
- **Packet/config validation:** [PASS]

## 11. Conclusion

Based on the completed tests, the RIP daemon implementation satisfies the main requirements of the COSC 364 assignment.
The routers successfully exchanged RIP response messages over UDP on localhost, built routing tables, and converged to valid minimum-cost paths in steady state.
During fault simulation, route invalidation behavior was observed (including unreachable metrics), followed by reconvergence when the failed router was restarted, which confirms correct timeout and recovery behavior.
Configuration parsing and packet consistency checks were also validated through runtime behavior and unit tests, including rejection of invalid inputs and malformed metric cases.

Overall, the implementation demonstrates correct core RIP functionality for this assignment scope, including periodic updates, triggered updates on invalidation, split horizon with poisoned reverse, and stable recovery after topology changes.


