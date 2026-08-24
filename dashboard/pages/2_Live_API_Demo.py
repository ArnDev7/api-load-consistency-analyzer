from dashboard.utils.bootstrap import configure_project_path
configure_project_path()

import json
import streamlit as st
from dashboard.components.disclosures import render_project_disclosure
from dashboard.components.status_panels import render_sidebar_status
from dashboard.utils.api_client import api_client

st.set_page_config(page_title="Live API Demo | API Load Analyzer", page_icon="🧪", layout="wide")

render_sidebar_status()
render_project_disclosure()

st.title("🧪 Live Interactive API Demonstration")
st.markdown("Interact directly with the running FastAPI backend to test CRUD operations, atomic reservations, idempotency replays, and invariant audits.")

health = api_client.check_health()
if not health["online"]:
    st.error("⚠️ **FastAPI Service is Offline**. Please start the API server to use this demo:")
    st.code("uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload")
    st.stop()

tab_reserve, tab_items, tab_audit, tab_admin = st.tabs([
    "1. Reserve & Idempotency Replay",
    "2. View & Create Items",
    "3. Live Invariant Auditor",
    "4. Test Data & Database Admin",
])

# ----------------------------------------------------
# TAB 1: Reserve & Idempotency Replay
# ----------------------------------------------------
with tab_reserve:
    st.subheader("📦 Inventory Allocation & Reservation")
    
    col_r1, col_r2 = st.columns([1, 1])
    
    with col_r1:
        item_id_input = st.number_input("Target Item ID", min_value=1, value=1, step=1)
        qty_input = st.number_input("Reservation Quantity", min_value=1, value=5, step=1)
        key_input = st.text_input("Idempotency Key", value="demo-client-key-001")
        strategy_input = st.selectbox("Concurrency Strategy", ["atomic_update", "pessimistic_lock"])
        
        btn_reserve = st.button("🚀 Submit Reservation Request", type="primary")
        
    with col_r2:
        if btn_reserve:
            with st.spinner("Executing reservation..."):
                res = api_client.reserve_item(
                    item_id=item_id_input,
                    quantity=qty_input,
                    idempotency_key=key_input,
                    strategy=strategy_input,
                )
            
            st.markdown(f"**HTTP Status**: `{res['status_code']}` ({'Success' if res['success'] else 'Rejected'})")
            st.caption(f"Execution Latency: {res['duration_ms']:.2f} ms")
            
            if res["success"]:
                st.success("✅ Reservation created / replayed successfully.")
            else:
                st.warning(f"⚠️ Operation Rejected: {res.get('body', {}).get('detail', {}).get('message', res.get('error'))}")
                
            st.json(res.get("body", {}))
            
    st.markdown("---")
    st.subheader("🔄 Reservation Release")
    col_rel1, col_rel2 = st.columns([1, 1])
    with col_rel1:
        res_id_input = st.number_input("Reservation ID to Release", min_value=1, value=1, step=1)
        btn_release = st.button("🔓 Release Reservation")
    with col_rel2:
        if btn_release:
            with st.spinner("Releasing reservation..."):
                res_rel = api_client.release_reservation(reservation_id=res_id_input)
            st.markdown(f"**HTTP Status**: `{res_rel['status_code']}`")
            st.caption(f"Latency: {res_rel['duration_ms']:.2f} ms")
            if res_rel["success"]:
                st.success("✅ Reservation released and stock restored to item.")
            else:
                st.warning(f"⚠️ Release Rejected: {res_rel.get('body', {}).get('detail', {}).get('message', res_rel.get('error'))}")
            st.json(res_rel.get("body", {}))

# ----------------------------------------------------
# TAB 2: View & Create Items
# ----------------------------------------------------
with tab_items:
    st.subheader("📋 Inventory Catalog")
    
    col_i1, col_i2 = st.columns([2, 1])
    
    with col_i1:
        items_resp = api_client.list_items(limit=50)
        if items_resp["success"]:
            items_data = items_resp["data"]
            if items_data:
                st.dataframe(items_data, use_container_width=True)
            else:
                st.info("No items found. Use the form on the right or the Admin tab to seed items.")
        else:
            st.error(f"Failed to fetch items: {items_resp.get('error')}")
            
    with col_i2:
        st.markdown("#### Create New Item")
        new_sku = st.text_input("SKU", value="PROD-DEMO-01")
        new_name = st.text_input("Item Name", value="Demo High-Demand Widget")
        new_qty = st.number_input("Initial Inventory", min_value=1, value=100, step=10)
        
        if st.button("➕ Create Item"):
            res_create = api_client.create_item(sku=new_sku, name=new_name, initial_quantity=new_qty)
            if res_create["success"]:
                st.success("Item created!")
                st.rerun()
            else:
                st.error(f"Failed: {res_create.get('body', {}).get('detail', {}).get('message', res_create.get('error'))}")

# ----------------------------------------------------
# TAB 3: Live Invariant Auditor
# ----------------------------------------------------
with tab_audit:
    st.subheader("🛡️ Single-Snapshot Consistency Verification")
    st.markdown("Executes a real-time multi-table SQL snapshot join to verify that all inventory conservation equations hold.")
    
    if st.button("🔍 Execute Real-Time Consistency Audit"):
        with st.spinner("Auditing database invariants..."):
            audit_res = api_client.check_consistency()
            
        if audit_res["success"]:
            body = audit_res.get("body", {})
            consistent = body.get("consistent", False)
            violations = body.get("violations_count", 0)
            
            if consistent and violations == 0:
                st.success("✅ **Consistency Status: 100% Valid (0 Invariant Violations)**")
            else:
                st.error(f"🔴 **Consistency Status: FAILED ({violations} Invariant Violations)**")
                
            col_a1, col_a2, col_a3 = st.columns(3)
            col_a1.metric("Total Items Audited", body.get("total_items", 0))
            col_a2.metric("Negative Inventory Count", body.get("negative_inventory_count", 0))
            col_a3.metric("Reconciliation Discrepancies", body.get("reconciliation_discrepancies", 0))
            
            items_breakdown = body.get("items", [])
            if items_breakdown:
                st.markdown("#### Per-Item Conservation Detail")
                st.dataframe(items_breakdown, use_container_width=True)
        else:
            st.error(f"Audit endpoint query failed: {audit_res.get('error')}")

# ----------------------------------------------------
# TAB 4: Test Data & Admin
# ----------------------------------------------------
with tab_admin:
    st.subheader("⚙️ Test Environment Seeding & Reset")
    
    col_adm1, col_adm2 = st.columns(2)
    
    with col_adm1:
        st.markdown("#### Deterministic Test Seed")
        seed_count = st.number_input("Item Count", min_value=1, max_value=100, value=10)
        seed_qty = st.number_input("Initial Inventory Per Item", min_value=10, max_value=1000, value=100)
        
        if st.button("🌱 Seed Database"):
            with st.spinner("Seeding database..."):
                seed_res = api_client.seed_data(item_count=seed_count, initial_inventory=seed_qty)
            if seed_res["success"]:
                st.success(f"Database seeded with {seed_count} items ({seed_qty} stock each)!")
            else:
                st.error(f"Seed failed: {seed_res.get('error')}")
                
    with col_adm2:
        st.markdown("#### Database Reset (Destructive)")
        confirm_reset = st.checkbox("I understand this will truncate all items and reservations.")
        if st.button("🗑️ Reset Database", disabled=not confirm_reset, type="primary"):
            with st.spinner("Resetting database..."):
                reset_res = api_client.reset_database()
            if reset_res["success"]:
                st.success("Database reset successfully.")
            else:
                st.error(f"Reset failed: {reset_res.get('error')}")
