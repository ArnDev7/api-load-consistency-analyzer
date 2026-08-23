# Experimental Limitations & Environmental Constraints

This document details the engineering limitations and environmental assumptions of the experimental setup to ensure analytical honesty and prevent unjustified generalizations.

---

## 1. Single-Host Co-Location & Core Contention
- In the local testing environment, the load generator (Locust), the ASGI application server (FastAPI/Uvicorn), and the database engine (PostgreSQL container) all execute on the **same physical CPU and OS kernel**.
- **Impact**: CPU cycles are shared between client load generation and server-side request execution. Under high concurrency, CPU starvation in the load generator can manifest as artificial client-perceived latency.

---

## 2. Lack of Network Realism & Regional WAN Latency
- Requests transit via local loopback (`127.0.0.1` / IPC).
- **Impact**: Network round-trip times (RTT) are sub-millisecond (< 0.5 ms). Real-world production deployments incur TCP handshakes, TLS termination overhead, packet loss, and multi-region routing delays (10–100 ms) that are not modeled here.

---

## 3. Synthetic Benchmark Durations
- Individual benchmark runs execute for 10–30 seconds per scenario.
- **Impact**: Short durations are sufficient to measure steady-state concurrency mechanics and verify invariant consistency, but do not capture long-term phenomena such as PostgreSQL table bloat, autovacuum background overhead, memory leaks, or prolonged connection pool leak degradation over hours of sustained load.

---

## 4. PostgreSQL Specific Storage Engine Semantics
- Results and lock contention profiles reflect PostgreSQL’s Multi-Version Concurrency Control (MVCC) and row-locking model (`heap_update`, `tuple_lock`, `Read Committed` isolation).
- **Impact**: Findings may differ under alternative storage engines such as MySQL InnoDB (which employs gap locking and next-key locks) or distributed databases (CockroachDB, Spanner) that use Two-Phase Commit (2PC) and Raft consensus.

---

## 5. Non-Generalizability to Production Capacity
- The throughput (RPS) and latency figures measured in this repository reflect a developer workstation environment.
- **Explicit Disclosure**: These figures must **never** be cited as absolute production capacity claims for a commercial enterprise system or high-frequency exchange.
