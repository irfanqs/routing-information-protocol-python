# COSC 364 RIP Assignment - Testing Report

## 1. Student Information

- **Name:** [Your Name]
- **Student ID:** [Your Student ID]
- **Course:** COSC 364 - Internet Protocols
- **Date:** [Submission Date]

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

Paste one full configuration example below (as requested by assignment instructions).

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

- Router 4 table after convergence: [Insert screenshot]


---

### Test Case 4 - Split Horizon with Poisoned Reverse

**Purpose:** Verify updates sent to each neighbor apply poisoned reverse correctly.

**Execution Steps:**
1. Observe route learned through neighbor X.
2. Verify update sent back to X advertises that route with metric 16.

**Expected Result:**
- Per-neighbor updates differ when required.
- Routes learned from neighbor X are advertised to X as unreachable (metric 16).

**Actual Result:**
[Fill in]

**Status:** [PASS / FAIL]

**Evidence (Screenshots):**
- Screenshot 1: [Insert screenshot]

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

**Actual Result:**
[Fill in]

**Status:** [PASS / FAIL]

**Evidence (Screenshots):**
- Before failure: [Insert screenshot]
- During transition/flurry of updates: [Insert screenshot]
- After reconvergence: [Insert screenshot]

---

### Test Case 6 - Router Recovery Handling

**Purpose:** Verify network returns to optimal routes after failed router restarts.

**Execution Steps:**
1. Restart previously failed router.
2. Observe periodic updates and route refresh.
3. Compare final tables with initial convergence state.

**Expected Result:**
- Recovered router rejoins normally.
- Network reconverges back to initial minimum-cost state.

**Actual Result:**
[Fill in]

**Status:** [PASS / FAIL]

**Evidence (Screenshots):**
- Router restart output: [Insert screenshot]
- Final converged tables: [Insert screenshot]

---

### Test Case 7 - Timer Behavior (Periodic, Timeout, Garbage)

**Purpose:** Verify timer-driven behavior in route lifecycle.

**Execution Steps:**
1. Observe periodic table updates and timer countdowns.
2. Trigger route timeout condition.
3. Observe garbage collection removal after invalidation period.

**Expected Result:**
- Timer values decrease and refresh correctly.
- Expired routes are invalidated then eventually removed.

**Actual Result:**
[Fill in]

**Status:** [PASS / FAIL]

**Evidence (Screenshots):**
- Timer display during normal operation: [Insert screenshot]
- Timeout/garbage phase: [Insert screenshot]

## 8. Unit Test Summary

| Test Module | Description | Result |
|---|---|---|
| `tests/test_config.py` | Config parsing and validation | [PASS/FAIL] |
| `tests/test_packet.py` | RIP packet encode/decode checks | [PASS/FAIL] |
| `tests/test_router_logic.py` | Split horizon poisoned reverse logic | [PASS/FAIL] |

Additional notes:
[Fill in]

## 9. Overall Result

- **Functional correctness:** [PASS / PARTIAL / FAIL]
- **Convergence behavior:** [PASS / PARTIAL / FAIL]
- **Failure and recovery behavior:** [PASS / PARTIAL / FAIL]
- **Packet/config validation:** [PASS / PARTIAL / FAIL]

Final assessment:
[Fill in]

## 10. Known Limitations / Issues Observed

[List any limitations, edge cases, or observed issues during testing]

## 11. Conclusion

Summarize whether the implementation meets the assignment requirements and what evidence supports this conclusion.

[Fill in]
