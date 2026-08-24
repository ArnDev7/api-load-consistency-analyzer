from dashboard.utils.bootstrap import configure_project_path
configure_project_path()

import os
import subprocess
import sys
import streamlit as st
from dashboard.components.disclosures import render_project_disclosure, render_hardware_warning
from dashboard.components.status_panels import render_sidebar_status
from dashboard.utils.paths import paths

st.set_page_config(page_title="Experiment Runner | API Load Analyzer", page_icon="⚡", layout="wide")

render_sidebar_status()
render_project_disclosure()

st.title("⚡ Controlled Experiment Runner")
st.markdown(
    "Configure and launch headless **Locust load experiments** and post-workload consistency audits "
    "using the project's standardized benchmark harness."
)

render_hardware_warning()

st.markdown("---")

col_cfg1, col_cfg2 = st.columns(2)

with col_cfg1:
    st.subheader("🛠️ Benchmark Configuration")
    profile = st.selectbox(
        "Workload Profile",
        ["read_heavy", "write_heavy", "mixed", "spike"],
        format_func=lambda x: {
            "read_heavy": "Read-Heavy (80% read, 15% write, 5% check)",
            "write_heavy": "Write-Heavy (70% write, 20% release, 10% read)",
            "mixed": "Mixed (40% read, 40% write, 15% release, 5% check)",
            "spike": "Spike (Bursty ramp-up traffic)",
        }[x],
    )
    strategy = st.selectbox(
        "Concurrency Strategy",
        ["atomic_update", "pessimistic_lock"],
        format_func=lambda x: {
            "atomic_update": "Atomic Conditional Update (Single SQL Statement)",
            "pessimistic_lock": "Pessimistic Row Lock (SELECT ... FOR UPDATE)",
        }[x],
    )
    users = st.slider("Concurrent Virtual Users", min_value=5, max_value=100, value=20, step=5)
    duration = st.slider("Run Duration (seconds)", min_value=5, max_value=60, value=15, step=5)
    repetitions = st.number_input("Repetitions", min_value=1, max_value=3, value=1)
    tag = st.text_input("Experiment Tag / Label", value=f"gui_run_{profile}")

with col_cfg2:
    st.subheader("📋 Execution Summary")
    st.markdown(f"""
    - **Workload**: `{profile}`
    - **Strategy**: `{strategy}`
    - **Concurrency**: `{users}` virtual users
    - **Duration**: `{duration}s` per repetition
    - **Repetitions**: `{repetitions}`
    - **Output Directory**: `results/{strategy}/`
    - **Invariant Auditing**: Enabled (Zero-tolerance check runs immediately after workload)
    """)

    st.markdown("#### Equivalent Terminal Command")
    cmd_example = f"locust -f load_tests/locustfile.py --headless -u {users} -r 10 -t {duration}s --host http://127.0.0.1:8000 --csv results/{strategy}/{tag}"
    st.code(cmd_example, language="bash")

st.markdown("---")

st.subheader("🚀 Launch Benchmark Run")

confirm_launch = st.checkbox("I confirm FastAPI server is running on localhost:8000 and database is ready.")

if st.button("▶️ Execute Benchmark Now", disabled=not confirm_launch, type="primary"):
    from experiments.run_experiments import run_locust_headless
    from experiments.consistency_checks import run_consistency_audit

    out_dir = paths.RESULTS_DIR / strategy
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_prefix = out_dir / tag

    st.info(f"Running benchmark with {users} users, profile={profile}, strategy={strategy} for {duration}s...")
    
    with st.spinner("Executing load workload..."):
        success = run_locust_headless(
            host="http://127.0.0.1:8000",
            users=users,
            spawn_rate=min(users, 10),
            duration_seconds=duration,
            csv_prefix=csv_prefix,
            profile=profile,
            strategy=strategy,
            item_count=20,
        )
        
        if success:
            st.success("✅ Locust workload completed!")
            with st.spinner("Auditing post-workload database consistency..."):
                audit_result = run_consistency_audit(output_dir=out_dir, tag=tag)
            
            if audit_result.get("consistent"):
                st.success("✅ Consistency audit: 100% Passed (0 Invariant Violations)")
            else:
                st.error(f"❌ Consistency audit failed: {audit_result.get('violations_count')} violations")
                
            st.json(audit_result)
            st.markdown("➡️ View your results in **[4. Performance Results](4_Performance_Results)**.")
        else:
            st.error("❌ Locust workload execution failed. Verify that FastAPI is running on port 8000.")

