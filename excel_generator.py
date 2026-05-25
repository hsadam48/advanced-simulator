from __future__ import annotations

import io
import pandas as pd


def create_excel(
    project_info_df: pd.DataFrame,
    input_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    recommendation_df: pd.DataFrame,
    analysis_df: pd.DataFrame,
    simulation_summary_df: pd.DataFrame | None = None,
    simulation_trials_df: pd.DataFrame | None = None,
) -> bytes:
    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        project_info_df.to_excel(writer, sheet_name="Project Info", index=False)
        input_df.to_excel(writer, sheet_name="Inputs", index=False)
        benchmark_df.to_excel(writer, sheet_name="Benchmark Targets", index=False)
        recommendation_df.to_excel(writer, sheet_name="Recommendations", index=False)
        analysis_df.to_excel(writer, sheet_name="Detailed Analysis", index=False)

        if simulation_summary_df is not None and not simulation_summary_df.empty:
            simulation_summary_df.to_excel(writer, sheet_name="Simulation Summary", index=False)

        if simulation_trials_df is not None and not simulation_trials_df.empty:
            simulation_trials_df.to_excel(writer, sheet_name="Simulation Trials", index=False)

    excel_buffer.seek(0)
    return excel_buffer.getvalue()