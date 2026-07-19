"""
code_executor.py — Local Python code execution sandbox.

Executes user-approved code against the CareerViet dataset.
Captures stdout, stderr, matplotlib/plotly figures, and DataFrame results.
All execution is LOCAL — nothing runs on remote servers.
"""

import io
import sys
import base64
import signal
import traceback
import contextlib
import threading
import os

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for Streamlit
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import json


# Path to dataset files (relative to project root)
DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset")
JOBS_CSV = os.path.join(DATASET_DIR, "careerviet_all_jobs_renamed.csv")
INDUSTRIES_CSV = os.path.join(DATASET_DIR, "careerviet_industries.csv")
EXPLODED_DIA_DIEM_CSV = os.path.join(DATASET_DIR, "exploded_địa điểm.csv")
EXPLODED_NGANH_CSV = os.path.join(DATASET_DIR, "exploded_ngành.csv")
EXPLODED_PHUC_LOI_CSV = os.path.join(DATASET_DIR, "exploded_phúc lợi.csv")
EXPLODED_ALL_COMBINED_CSV = os.path.join(DATASET_DIR, "exploded_all_combined.csv")

# Execution timeout in seconds
EXEC_TIMEOUT = 30


def _load_datasets():
    """Load all CareerViet datasets into DataFrames."""
    df = pd.read_csv(JOBS_CSV, low_memory=False, encoding="utf-8-sig")
    df_industries = pd.read_csv(INDUSTRIES_CSV, encoding="utf-8-sig")
    df_dia_diem = pd.read_csv(EXPLODED_DIA_DIEM_CSV, low_memory=False, encoding="utf-8-sig")
    df_nganh = pd.read_csv(EXPLODED_NGANH_CSV, low_memory=False, encoding="utf-8-sig")
    df_phuc_loi = pd.read_csv(EXPLODED_PHUC_LOI_CSV, low_memory=False, encoding="utf-8-sig")
    df_dia_diem_nganh = pd.read_csv(EXPLODED_ALL_COMBINED_CSV, low_memory=False, encoding="utf-8-sig")
    return df, df_industries, df_dia_diem, df_nganh, df_phuc_loi, df_dia_diem_nganh


def _capture_matplotlib_figures():
    """Capture all open matplotlib figures as base64 PNG images."""
    figures = []
    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        figures.append(img_base64)
        buf.close()
    plt.close("all")
    return figures


def execute_code(code: str) -> dict:
    """
    Execute Python code in a controlled local environment.
    
    The code has access to:
    - df: Main jobs DataFrame (careerviet_all_jobs_renamed.csv)
    - df_industries: Industries reference DataFrame
    - df_dia_diem: Jobs exploded by location
    - df_nganh: Jobs exploded by industry (Vietnamese names)
    - df_phuc_loi: Jobs exploded by benefit
    - pandas (pd), numpy (np), matplotlib (plt), seaborn (sns)
    - df_dia_diem_nganh: Jobs exploded by both location and industry
    - plotly.express (px), plotly.graph_objects (go)
    - json module
    
    Returns:
        dict with keys:
        - success (bool): Whether execution completed without errors
        - stdout (str): Captured print output
        - stderr (str): Captured error output  
        - figures (list[str]): Base64-encoded matplotlib PNG images
        - plotly_figures (list): Plotly figure objects (serializable)
        - tables (list[dict]): DataFrames named 'result' or 'result_df'
        - error_traceback (str|None): Full traceback if execution failed
    """
    # Load datasets fresh each time to avoid mutation across runs
    try:
        df, df_industries, df_dia_diem, df_nganh, df_phuc_loi, df_dia_diem_nganh = _load_datasets()
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "figures": [],
            "plotly_figures": [],
            "tables": [],
            "error_traceback": f"Lỗi khi đọc dữ liệu: {str(e)}",
        }

    # Close any lingering matplotlib figures
    plt.close("all")

    # Prepare the execution namespace
    exec_namespace = {
        "df": df,
        "df_industries": df_industries,
        "df_dia_diem": df_dia_diem,
        "df_nganh": df_nganh,
        "df_phuc_loi": df_phuc_loi,
        "df_dia_diem_nganh": df_dia_diem_nganh,
        "pd": pd,
        "np": np,
        "plt": plt,
        "sns": sns,
        "px": px,
        "go": go,
        "json": json,
        "__builtins__": __builtins__,
    }

    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    result = {
        "success": False,
        "stdout": "",
        "stderr": "",
        "figures": [],
        "plotly_figures": [],
        "tables": [],
        "error_traceback": None,
    }

    # Execute with timeout using threading
    exec_exception = [None]

    def _run_code():
        try:
            with contextlib.redirect_stdout(stdout_capture), \
                 contextlib.redirect_stderr(stderr_capture):
                exec(code, exec_namespace)
        except Exception as e:
            exec_exception[0] = traceback.format_exc()

    thread = threading.Thread(target=_run_code)
    thread.start()
    thread.join(timeout=EXEC_TIMEOUT)

    if thread.is_alive():
        result["error_traceback"] = (
            f"Code đã chạy quá {EXEC_TIMEOUT} giây và bị dừng lại. "
            f"Hãy tối ưu code hoặc giảm lượng dữ liệu xử lý."
        )
        return result

    # Capture outputs
    result["stdout"] = stdout_capture.getvalue()
    result["stderr"] = stderr_capture.getvalue()

    if exec_exception[0]:
        result["error_traceback"] = exec_exception[0]
        return result

    # Success — capture results
    result["success"] = True

    # Capture matplotlib figures
    result["figures"] = _capture_matplotlib_figures()

    # Capture plotly figures from namespace
    plotly_figs = []
    for var_name, var_value in exec_namespace.items():
        if isinstance(var_value, (go.Figure,)):
            plotly_figs.append(var_value)
    result["plotly_figures"] = plotly_figs

    # Capture DataFrames named 'result' or 'result_df'
    tables = []
    for name in ["result", "result_df"]:
        if name in exec_namespace and isinstance(exec_namespace[name], pd.DataFrame):
            df_result = exec_namespace[name]
            # Limit to 500 rows for display
            if len(df_result) > 500:
                tables.append({
                    "name": name,
                    "data": df_result.head(500),
                    "total_rows": len(df_result),
                    "truncated": True,
                })
            else:
                tables.append({
                    "name": name,
                    "data": df_result,
                    "total_rows": len(df_result),
                    "truncated": False,
                })
    result["tables"] = tables

    return result
