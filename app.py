from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from core.analytical_engine import (
    build_analysis_rows,
    build_benchmark_rows,
    build_recommendation_rows,
)
from core.data_cleaning import clean_input_df
from core.models import (
    BUILDING_GRADES,
    BUILDING_TYPES,
    DOOR_TYPES,
    ZONING_OPTIONS,
    LiftBankInput,
)
from core.simulation_engine import run_advanced_simulation
from reporting.excel_generator import create_excel
from reporting.pdf_generator import create_pdf


st.set_page_config(page_title="VT Engineering Review Platform Advanced", page_icon="🛗", layout="wide")


DEFAULT_BANKS = pd.DataFrame(json.loads(Path("data/default_banks.json").read_text(encoding="utf-8")))


def init_state():
    defaults = {
        "page": 1,
        "project_name": "Radiant Tower",
        "project_address": "",
        "prepared_by": "ATGC Engineering",
        "logo_bytes": None,
        "logo_name": None,
        "project_photo_bytes": None,
        "project_photo_name": None,
        "input_df": DEFAULT_BANKS.copy(),
        "simulation_summary_df": pd.DataFrame(),
        "simulation_trials_df": pd.DataFrame(),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to(page: int):
    st.session_state.page = page
    st.rerun()


def page_header(step: int):
    captions = {
        1: "Step 1 of 4 — Project Information",
        2: "Step 2 of 4 — Tower & Lift Engineering Inputs",
        3: "Step 3 of 4 — Advanced Simulation Engine",
        4: "Step 4 of 4 — Benchmarks, Results, Recommendations & Reports",
    }
    st.caption(captions[step])


def build_banks_from_state():
    input_df = clean_input_df(st.session_state.input_df)
    banks = [LiftBankInput(**row) for row in input_df.to_dict(orient="records")]
    return input_df, banks


init_state()

st.title("🛗 VT Engineering Review Platform — Advanced")
st.caption("Professional VT benchmark review + recommendation engine + advanced simulation + Excel/PDF reporting.")

if st.session_state.page == 1:
    page_header(1)
    st.header("🏗️ Project Information")

    project_name = st.text_input("Project Name", value=st.session_state.project_name)
    project_address = st.text_area("Project Address", value=st.session_state.project_address)
    prepared_by = st.text_input("Prepared By", value=st.session_state.prepared_by)

    c1, c2 = st.columns(2)

    with c1:
        logo_file = st.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"])
        if logo_file:
            st.image(logo_file, caption="Company Logo Preview", width=180)

    with c2:
        project_photo = st.file_uploader("Upload Project Photo", type=["png", "jpg", "jpeg"])
        if project_photo:
            st.image(project_photo, caption="Project Photo Preview", width=260)

    if st.button("Next →", type="primary"):
        st.session_state.project_name = project_name
        st.session_state.project_address = project_address
        st.session_state.prepared_by = prepared_by

        if logo_file:
            st.session_state.logo_bytes = logo_file.getvalue()
            st.session_state.logo_name = logo_file.name

        if project_photo:
            st.session_state.project_photo_bytes = project_photo.getvalue()
            st.session_state.project_photo_name = project_photo.name

        go_to(2)

elif st.session_state.page == 2:
    page_header(2)
    st.header("🛗 Tower & Lift Engineering Inputs")
    st.write("Include architectural, population, hardware, door, control/zoning, and pit/overhead data.")

    column_config = {
        "building_type": st.column_config.SelectboxColumn("building_type", options=BUILDING_TYPES, required=True),
        "building_grade": st.column_config.SelectboxColumn("building_grade", options=BUILDING_GRADES, required=True),
        "door_type": st.column_config.SelectboxColumn("door_type", options=DOOR_TYPES, required=True),
        "zoning_strategy": st.column_config.SelectboxColumn("zoning_strategy", options=ZONING_OPTIONS, required=True),
    }

    edited_df = st.data_editor(
        st.session_state.input_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("← Back"):
            st.session_state.input_df = edited_df
            go_to(1)

    with c2:
        if st.button("Advanced Simulation →", type="secondary"):
            st.session_state.input_df = clean_input_df(edited_df)
            go_to(3)

    with c3:
        if st.button("Generate Results →", type="primary"):
            st.session_state.input_df = clean_input_df(edited_df)
            go_to(4)

elif st.session_state.page == 3:
    page_header(3)
    st.header("⚙️ Advanced Simulation Engine")

    input_df, banks = build_banks_from_state()

    if not banks:
        st.warning("No lift bank found. Please go back and add at least one lift bank.")
    else:
        bank_names = [b.bank_name for b in banks]
        selected_bank_name = st.selectbox("Select Lift Bank", bank_names)
        bank = next(b for b in banks if b.bank_name == selected_bank_name)

        c1, c2, c3 = st.columns(3)

        with c1:
            trials = st.number_input("Trials", min_value=1, max_value=1000, value=100, step=10)
            duration = st.number_input("Simulation Duration (sec)", min_value=300, value=4800, step=300)

        with c2:
            arrival_min = st.number_input("Arrival Min Separation (sec)", min_value=0.1, value=1.0, step=0.5)
            arrival_max = st.number_input("Arrival Max Separation (sec)", min_value=0.2, value=30.0, step=0.5)

        with c3:
            dispatch_wait = st.number_input("Dispatch Wait Time (sec)", min_value=1.0, value=10.0, step=1.0)
            control = st.selectbox("Control Method", ["Conventional", "Hybrid", "DCS"], index=1)
            seed = st.number_input("Random Seed", min_value=1, value=42, step=1)

        if st.button("Run Advanced Simulation", type="primary"):
            if arrival_max < arrival_min:
                st.error("Arrival Max must be greater than Arrival Min.")
            else:
                with st.spinner("Running advanced simulation..."):
                    summary, trials_df = run_advanced_simulation(
                        bank=bank,
                        trials=int(trials),
                        simulation_duration_sec=int(duration),
                        arrival_min_sec=float(arrival_min),
                        arrival_max_sec=float(arrival_max),
                        dispatch_wait_sec=float(dispatch_wait),
                        control_method=control,
                        seed=int(seed),
                    )

                summary_df = pd.DataFrame([summary])
                st.session_state.simulation_summary_df = summary_df
                st.session_state.simulation_trials_df = trials_df

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Mean Wait", f"{summary['Mean Waiting Time (s)']} s")
                m2.metric("Max Wait", f"{summary['Max Waiting Time (s)']} s")
                m3.metric("Simulation HC", f"{summary['Simulation HC (%)']}%")
                m4.metric("Max Queue", summary["Max Queue Size"])

                st.subheader("Simulation Summary")
                st.dataframe(summary_df, use_container_width=True, hide_index=True)

                st.subheader("Trial Details")
                st.dataframe(trials_df, use_container_width=True, hide_index=True)

                st.line_chart(
                    trials_df.set_index("Trial")[
                        ["Mean Waiting Time (s)", "Max Waiting Time (s)", "Max Queue Size"]
                    ]
                )

                st.download_button(
                    "Download Simulation Trials CSV",
                    data=trials_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="advanced_simulation_trials.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

    c1, c2 = st.columns(2)

    with c1:
        if st.button("← Back to Inputs"):
            go_to(2)

    with c2:
        if st.button("Go to Results & Reports →", type="primary"):
            go_to(4)

elif st.session_state.page == 4:
    page_header(4)
    st.header("📊 Benchmarks, Results & Recommendations")

    input_df, banks = build_banks_from_state()

    analysis_df = build_analysis_rows(banks)
    rec_df = build_recommendation_rows(banks)
    bm_df = build_benchmark_rows(banks)

    st.subheader("Project")
    st.write(f"**Project Name:** {st.session_state.project_name}")
    st.write(f"**Address:** {st.session_state.project_address or '-'}")
    st.write(f"**Prepared By:** {st.session_state.prepared_by}")

    if st.session_state.logo_bytes:
        st.image(st.session_state.logo_bytes, caption="Company Logo", width=150)

    if st.session_state.project_photo_bytes:
        st.image(st.session_state.project_photo_bytes, caption="Project Photo", width=300)

    st.subheader("Benchmark Targets")
    st.dataframe(bm_df, use_container_width=True, hide_index=True)

    st.subheader("Result Recommendations")
    st.dataframe(rec_df, use_container_width=True, hide_index=True)

    st.subheader("Detailed Benchmark Analysis")
    st.dataframe(analysis_df, use_container_width=True, hide_index=True)

    if not st.session_state.simulation_summary_df.empty:
        st.subheader("Advanced Simulation Summary")
        st.dataframe(st.session_state.simulation_summary_df, use_container_width=True, hide_index=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Checks", len(analysis_df))
    m2.metric("PASS", int((analysis_df["Result"] == "PASS").sum()) if not analysis_df.empty else 0)
    m3.metric("FAIL", int((analysis_df["Result"] == "FAIL").sum()) if not analysis_df.empty else 0)

    project_info_df = pd.DataFrame(
        [
            {
                "Project Name": st.session_state.project_name,
                "Address": st.session_state.project_address,
                "Prepared By": st.session_state.prepared_by,
            }
        ]
    )

    excel_bytes = create_excel(
        project_info_df=project_info_df,
        input_df=input_df,
        benchmark_df=bm_df,
        recommendation_df=rec_df,
        analysis_df=analysis_df,
        simulation_summary_df=st.session_state.simulation_summary_df,
        simulation_trials_df=st.session_state.simulation_trials_df,
    )

    pdf_bytes = create_pdf(
        st.session_state.project_name,
        st.session_state.project_address,
        st.session_state.prepared_by,
        st.session_state.logo_bytes,
        st.session_state.logo_name,
        st.session_state.project_photo_bytes,
        st.session_state.project_photo_name,
        input_df,
        analysis_df,
        rec_df,
        bm_df,
        st.session_state.simulation_summary_df,
    )

    st.subheader("Downloads")
    d1, d2, d3, d4 = st.columns(4)

    with d1:
        st.download_button(
            "Download Excel",
            data=excel_bytes,
            file_name="vt_engineering_review_advanced.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with d2:
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="vt_engineering_review_advanced.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with d3:
        st.download_button(
            "Download Detailed CSV",
            data=analysis_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="vt_detailed_analysis.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with d4:
        if not st.session_state.simulation_trials_df.empty:
            st.download_button(
                "Download Simulation CSV",
                data=st.session_state.simulation_trials_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="advanced_simulation_trials.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button("No Simulation CSV", disabled=True, use_container_width=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("← Back to Inputs"):
            go_to(2)

    with c2:
        if st.button("Advanced Simulation"):
            go_to(3)

    with c3:
        if st.button("Start New Project"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.warning(
        "Preliminary benchmark comparison only. Final VT traffic analysis, fire/life-safety compliance "
        "and shaft dimensions must be confirmed by the elevator specialist/manufacturer."
    )