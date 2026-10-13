# RETAILPULSE DASHBOARD
# This file loads project results and shows them as charts, tables, and reports.
# Import the tools used by the dashboard.
from pathlib import Path
import re
import json
import pandas as pd
import plotly.express as px
import streamlit as st
# Find the project folder and where the saved results live.
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"
# Set the dashboard title, icon, layout, and sidebar settings.
st.set_page_config(
    page_title="RetailPulse | Retail Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Consistent light theme and readable components across every dashboard page.
st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --rp-navy: #14243a; --rp-teal: #0f9d91; --rp-ink: #182433;
        --rp-muted: #64748b; --rp-border: #dbe4ee; --rp-panel: #ffffff;
        --rp-canvas: #f4f7fb;
    }
    .stApp { background: var(--rp-canvas); color: var(--rp-ink); }
    .block-container { max-width: 1500px; padding: 1.8rem 2.2rem 2.5rem; }
    h1 { color: var(--rp-navy); letter-spacing: -0.035em; font-weight: 800; }
    h2, h3, h4 { color: var(--rp-navy); letter-spacing: -0.02em; }
    p, li, label, [data-testid="stMarkdownContainer"] { line-height: 1.55; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #14243a 0%, #1d344e 100%); }
    [data-testid="stSidebar"] * { color: #f7fafc !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .4rem .25rem; border-radius: 8px; }
    div[data-testid="stMetric"] { background: var(--rp-panel); border: 1px solid var(--rp-border);
        border-top: 3px solid var(--rp-teal); padding: 1rem 1.1rem; border-radius: 14px;
        box-shadow: 0 4px 14px rgba(20,36,58,.05); min-height: 112px; }
    div[data-testid="stMetricLabel"] { color: var(--rp-muted); font-weight: 600; }
    div[data-testid="stMetricValue"] { color: var(--rp-navy); font-weight: 750; }
    [data-testid="stDataFrame"], [data-testid="stTable"] { border: 1px solid var(--rp-border);
        border-radius: 10px; overflow: hidden; background: #fff; }
    [data-testid="stExpander"] { background: #fff; border: 1px solid var(--rp-border);
        border-radius: 12px; margin-bottom: .65rem; }
    div[data-testid="stPlotlyChart"] { background: #fff; border: 1px solid var(--rp-border);
        border-radius: 12px; padding: .4rem; box-shadow: 0 3px 12px rgba(20,36,58,.04); }
    div.stButton > button, div.stDownloadButton > button { border-radius: 9px;
        border: 1px solid #b9d8d5; font-weight: 650; }
    hr { border-color: var(--rp-border); }
    [data-testid="stCaptionContainer"] { color: var(--rp-muted); }
    .rp-report-intro { color: var(--rp-muted); font-size: .92rem; }
    </style>
    """,
    unsafe_allow_html=True,
)
# Load a CSV result. If it is missing or unreadable, return an empty table.
@st.cache_data
def load_csv(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False)
    except (OSError, ValueError, pd.errors.ParserError):
        return pd.DataFrame()
# Read a saved text report. If it is missing, return an empty string.
@st.cache_data
def read_report(filename):
    path = REPORT_DIR / filename
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
# Find a column using a list of possible names.
def find_column(df, candidates):
    lookup = {str(col).lower().replace(" ", "_"): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower().replace(" ", "_") in lookup:
            return lookup[candidate.lower().replace(" ", "_")]
    return None
# Show a table, or a message if there is no data.
def show_table(df, height=350):
    if df.empty:
        st.info("This dataset is not available yet. Run the relevant project script first.")
        return

    display_df = df.copy()
    # Format numeric values for display only; original data and downloads are unchanged.
    for col in display_df.select_dtypes(include=["float"]).columns:
        display_df[col] = display_df[col].round(3)
    st.caption(f"{len(display_df):,} rows · {len(display_df.columns):,} columns")
    st.dataframe(display_df, width="stretch", height=height, hide_index=True)


def _report_heading(line):
    stripped = line.strip().strip("#* ")
    if not stripped or len(stripped) > 90:
        return False
    if re.fullmatch(r"[-=_*]{3,}", stripped):
        return True
    if re.match(r"^(?:\d+\.\s+)?(?:summary|limitations|class distribution|model comparison|classification report|confusion matrix|monthly revenue|top \d+|inventory recommendations|evaluation notes|customer segmentation|demand forecasting|inventory planning|feature window|observation window)", stripped, re.I):
        return True
    return (stripped.upper() == stripped and any(c.isalpha() for c in stripped)
            and not re.search(r"\d{4}-\d{2}", stripped))

def _render_report_json(value, title=None):
    """Render JSON-like report data as compact tables rather than scattered raw lines."""
    if isinstance(value, dict):
        rows = []
        for key, item in value.items():
            if isinstance(item, dict):
                for subkey, subvalue in item.items():
                    if isinstance(subvalue, (dict, list)):
                        rows.append((f"{key} · {subkey}", json.dumps(subvalue, ensure_ascii=False)))
                    else:
                        rows.append((f"{key} · {subkey}", subvalue))
            elif isinstance(item, list):
                rows.append((key, json.dumps(item, ensure_ascii=False)))
            else:
                rows.append((key, item))
        if rows:
            if title:
                st.markdown(f"**{title}**")
            st.dataframe(pd.DataFrame(rows, columns=["Metric", "Value"]), width="stretch", hide_index=True)
    elif isinstance(value, list):
        try:
            frame = pd.DataFrame(value)
        except (ValueError, TypeError):
            frame = pd.DataFrame({"Value": [str(v) for v in value]})
        if title:
            st.markdown(f"**{title}**")
        st.dataframe(frame, width="stretch", hide_index=True)

def show_report(filename):
    """Display saved reports as readable sections and tables across all pages."""
    content = read_report(filename)
    if not content:
        st.info(f"Report not found: reports/{filename}")
        return

    lines = content.splitlines()
    section_title = "Report summary"
    section_lines = []

    def render_section(title, items):
        if not items:
            return
        st.markdown(f"#### {title}")
        i = 0
        while i < len(items):
            line = items[i].strip()
            if not line or re.fullmatch(r"[-=_*]{3,}", line):
                i += 1
                continue

            # Parse a multi-line JSON object/array into a readable metric table.
            if line.startswith(("{", "[")):
                chunk = [line]
                balance = line.count("{") - line.count("}") + line.count("[") - line.count("]")
                j = i + 1
                while balance > 0 and j < len(items):
                    chunk.append(items[j])
                    balance += items[j].count("{") - items[j].count("}") + items[j].count("[") - items[j].count("]")
                    j += 1
                raw = "\n".join(chunk)
                try:
                    parsed = json.loads(raw.rstrip(","))
                    _render_report_json(parsed)
                    i = j
                    continue
                except (json.JSONDecodeError, TypeError):
                    pass

            # Collect label/value lines into a table, including colon-separated metrics.
            match = re.match(r'^\s*["\']?(.+?)["\']?\s*:\s*["\']?(-?[$£€]?\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?%?)["\']?\s*,?\s*$', line, re.I)
            if not match:
                match = re.match(r"^(.+?)\s{2,}(-?[$£€]?\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?%?)$", line, re.I)
            if match:
                rows = []
                while i < len(items):
                    candidate = items[i].strip()
                    m = re.match(r'^\s*["\']?(.+?)["\']?\s*:\s*["\']?(-?[$£€]?\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?%?)["\']?\s*,?\s*$', candidate, re.I)
                    if not m:
                        m = re.match(r"^(.+?)\s{2,}(-?[$£€]?\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?%?)$", candidate, re.I)
                    if not m:
                        break
                    rows.append((m.group(1).strip().strip("\"'"), m.group(2).strip()))
                    i += 1
                st.dataframe(pd.DataFrame(rows, columns=["Metric / Item", "Value"]), width="stretch", hide_index=True)
                continue

            # Recognize whitespace-separated tabular headings/rows (classification reports).
            if re.search(r"\bprecision\b.*\brecall\b.*\bf1-score\b", line, re.I):
                headers = re.split(r"\s{2,}|\t+", line)
                table_rows = []
                j = i + 1
                while j < len(items):
                    parts = re.split(r"\s{2,}|\t+", items[j].strip())
                    if len(parts) >= 2 and any(re.search(r"\d", part) for part in parts[1:]):
                        table_rows.append(parts[:len(headers)])
                        j += 1
                    else:
                        break
                if table_rows:
                    st.dataframe(pd.DataFrame(table_rows, columns=headers[:len(table_rows[0])]), width="stretch", hide_index=True)
                    i = j
                    continue

            # Render ordinary prose and list items with proper spacing.
            clean = line.strip()
            if clean.startswith(("- ", "* ")):
                st.markdown(clean)
            elif clean.startswith("#"):
                st.markdown(clean.lstrip("# "))
            else:
                st.markdown(clean)
            i += 1

    for raw_line in lines:
        line = raw_line.strip()
        if not line or re.fullmatch(r"[-=_*]{3,}", line):
            continue
        if _report_heading(line) and section_lines:
            render_section(section_title, section_lines)
            section_title = line.strip("#* ").title()
            section_lines = []
        elif _report_heading(line) and not section_lines:
            section_title = line.strip("#* ").title()
        else:
            section_lines.append(line)
    render_section(section_title, section_lines)

# LOAD PROJECT RESULTS
# These saved files are used by the different dashboard pages.
customer_features = load_csv("customer_features.csv")
segments = load_csv("customer_rfm_segments.csv")
cluster_summary = load_csv("customer_cluster_summary.csv")
churn_predictions = load_csv("churn_test_predictions.csv")
forecast_evaluation = load_csv("forecast_evaluation.csv")
forecasts = load_csv("demand_forecasts.csv")
inventory = load_csv("inventory_recommendations.csv")
# DASHBOARD TITLE AND INTRODUCTION
st.title("RetailPulse")
st.subheader("AI-Powered Customer Analytics & Demand Forecasting")
st.caption("Retail intelligence for customer engagement, sales planning, and inventory decisions.")
# SIDEBAR MENU: let the user choose a dashboard page.
with st.sidebar:
    st.title("📊 RetailPulse")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        [
            "Executive Overview",
            "Customer Segmentation",
            "Churn Analysis",
            "Demand Forecasting",
            "Inventory Planning",
            "Model Evaluation",
            "About & Data Notes",
        ],
    )
    st.markdown("---")
    st.caption("Analytics based on the project's processed retail transaction dataset.")
# PAGE 1: Main business numbers and summary charts.
if page == "Executive Overview":
    st.header("Executive Overview")
    st.write("Explore the key outputs generated by the RetailPulse analytics pipeline.")
    # Read the EDA report to get the main business numbers.
    eda_report = read_report("eda_summary.txt")
    revenue = None
    customer_count = None
    product_count = None
    invoice_count = None
    # Use the recorded EDA summary where possible.
    if eda_report:
        patterns = {
            "revenue": r"(?:Revenue|Total standard sales revenue):\s*([0-9,]+(?:\.[0-9]+)?)",
            "customers": r"(?:Customers|Unique customers in sales subset):\s*([0-9,]+)",
            "products": r"(?:Products|Unique products in sales subset):\s*([0-9,]+)",
            "invoices": r"(?:Invoices|Invoice count in sales subset):\s*([0-9,]+)",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, eda_report, re.IGNORECASE)
            if match:
                value = match.group(1).replace(",", "")
                if key == "revenue":
                    revenue = float(value)
                elif key == "customers":
                    customer_count = int(float(value))
                elif key == "products":
                    product_count = int(float(value))
                elif key == "invoices":
                    invoice_count = int(float(value))
    if customer_count is None and not customer_features.empty:
        customer_count = len(customer_features)
    if product_count is None:
        daily_sales = load_csv("daily_product_sales.csv")
        product_col = find_column(daily_sales, ["stock_code", "product_id", "product"])
        if product_col:
            product_count = daily_sales[product_col].nunique()
    if revenue is None:
        st.warning(
            "Revenue KPI could not be extracted from the EDA report. "
            "Check reports/eda_summary.txt before using revenue figures in a presentation."
        )
    # Show the four main numbers in separate KPI cards.
    metrics = st.columns(4)
    metrics[0].metric(
        "Customers analyzed",
        f"{customer_count:,}" if customer_count is not None else "N/A",
    )
    metrics[1].metric(
        "Products analyzed",
        f"{product_count:,}" if product_count is not None else "N/A",
    )
    metrics[2].metric(
        "Invoices",
        f"{invoice_count:,}" if invoice_count is not None else "N/A",
    )
    metrics[3].metric(
        "Recorded sales revenue",
        f"{revenue:,.2f}" if revenue is not None else "N/A",
    )
    st.markdown("---")
    # Split the page into two columns for the charts.
    left, right = st.columns(2)
    with left:
        st.subheader("Customer segments")
        if not segments.empty:
            cluster_col = find_column(segments, ["cluster", "cluster_id", "segment"])
            if cluster_col:
                counts = segments[cluster_col].astype(str).value_counts().rename_axis(
                    "Cluster"
                ).reset_index(name="Customers")
                fig = px.bar(
                    counts,
                    x="Cluster",
                    y="Customers",
                    title="Customers by cluster",
                    color="Cluster",
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Could not identify the cluster column in the segmentation file.")
        else:
            st.info("Customer segmentation output is not available.")
    with right:
        st.subheader("Forecast evaluation")
        if not forecast_evaluation.empty:
            metric_col = find_column(forecast_evaluation, ["mae"])
            model_col = find_column(forecast_evaluation, ["baseline", "model"])
            if metric_col and model_col:
                chart_data = (
                    forecast_evaluation.groupby(model_col, as_index=False)[metric_col]
                    .mean()
                    .sort_values(metric_col)
                )
                fig = px.bar(
                    chart_data,
                    x=model_col,
                    y=metric_col,
                    title="Mean MAE by baseline (lower is better)",
                    color=model_col,
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Forecast evaluation file has an unexpected schema.")
        else:
            st.info("Forecast evaluation results are not available.")
    # Show the saved EDA report at the bottom of this page.
    st.subheader("Latest exploratory analysis")
    show_report("eda_summary.txt")
# PAGE 2: Customer groups and their details.
elif page == "Customer Segmentation":
    st.header("Customer Segmentation")
    st.write(
        "Customers are grouped using RFM-style behavior: recency, purchase frequency, "
        "and monetary value. Cluster numbers are model labels, not a ranking."
    )
    if not cluster_summary.empty:
        st.subheader("Cluster profiles")
        show_table(cluster_summary)
    else:
        st.info("Cluster summary is not available.")
    if not segments.empty:
        st.subheader("Customer-level segments")
        cluster_col = find_column(segments, ["cluster", "cluster_id", "segment"])
        if cluster_col:
            options = ["All"] + sorted(segments[cluster_col].dropna().astype(str).unique())
            selected = st.selectbox("Filter by cluster", options)
            view = segments.copy()
            if selected != "All":
                view = view[view[cluster_col].astype(str) == selected]
            st.caption(f"{len(view):,} customer records")
            show_table(view)
            st.download_button(
                "Download displayed customer segments",
                view.to_csv(index=False).encode("utf-8"),
                file_name="retailpulse_customer_segments.csv",
                mime="text/csv",
            )
        else:
            show_table(segments)
    else:
        st.info("Customer-level segment data is not available.")
# PAGE 3: Churn model results and customer predictions.
elif page == "Churn Analysis":
    st.header("Customer Churn Analysis")
    st.write(
        "The current churn experiment defines churn as no qualifying purchase "
        "during July–September 2011, using historical behavior from December 2010 "
        "through June 2011."
    )
    report = read_report("churn_model_report.txt")
    if report:
        show_report("churn_model_report.txt")
    else:
        st.info("Churn model report is not available.")
    if not churn_predictions.empty:
        st.subheader("Test-set predictions")
        show_table(churn_predictions)
        st.download_button(
            "Download churn predictions",
            churn_predictions.to_csv(index=False).encode("utf-8"),
            file_name="retailpulse_churn_predictions.csv",
            mime="text/csv",
        )
    else:
        st.info("Churn test predictions are not available.")
    st.warning(
        "These results come from a historical experiment, not a guarantee of future "
        "customer behavior. Validate on a later, untouched time period before production use."
    )
# PAGE 4: Forecast results, charts, and product demand.
elif page == "Demand Forecasting":
    st.header("Demand Forecasting")
    st.write(
        "Forecasts use baseline time-series methods. Forecast quantities are estimates, "
        "not guaranteed future demand."
    )
    if not forecast_evaluation.empty:
        st.subheader("Historical evaluation")
        show_table(forecast_evaluation)
        mae_col = find_column(forecast_evaluation, ["mae"])
        model_col = find_column(forecast_evaluation, ["baseline", "model"])
        if mae_col and model_col:
            chart_data = forecast_evaluation.groupby(model_col, as_index=False)[mae_col].mean()
            fig = px.bar(
                chart_data,
                x=model_col,
                y=mae_col,
                title="Average MAE across evaluated products",
                color=model_col,
            )
            st.plotly_chart(fig, width="stretch")
    else:
        st.info("Forecast evaluation output is not available.")
    if not forecasts.empty:
        st.subheader("Product demand forecasts")
        product_col = find_column(forecasts, ["stock_code", "product_id", "product"])
        if product_col:
            products = sorted(forecasts[product_col].dropna().astype(str).unique())
            selected_product = st.selectbox("Select product", products)
            view = forecasts[forecasts[product_col].astype(str) == selected_product]
        else:
            view = forecasts
        date_col = find_column(view, ["forecast_date", "date", "ds"])
        value_col = find_column(
            view, ["forecast_quantity", "forecast", "predicted_quantity", "prediction"]
        )
        if date_col and value_col:
            chart_data = view.copy()
            chart_data[date_col] = pd.to_datetime(chart_data[date_col], errors="coerce")
            chart_data[value_col] = pd.to_numeric(chart_data[value_col], errors="coerce")
            chart_data = chart_data.dropna(subset=[date_col, value_col]).sort_values(date_col)
            if not chart_data.empty:
                fig = px.line(
                    chart_data,
                    x=date_col,
                    y=value_col,
                    markers=True,
                    title="Forecasted demand by date",
                )
                st.plotly_chart(fig, width="stretch")
        show_table(view)
        st.download_button(
            "Download demand forecasts",
            view.to_csv(index=False).encode("utf-8"),
            file_name="retailpulse_demand_forecasts.csv",
            mime="text/csv",
        )
    else:
        st.info("Demand forecast output is not available.")
    st.caption("Evaluation results were used during baseline comparison; treat the comparison as preliminary.")
# PAGE 5: Reorder suggestions and inventory estimates.
elif page == "Inventory Planning":
    st.header("Inventory Planning")
    st.write(
        "Review suggested replenishment quantities derived from demand forecasts "
        "and explicit planning assumptions."
    )
    if not inventory.empty:
        status_col = find_column(inventory, ["planning_status", "status"])
        if status_col:
            st.subheader("Planning status")
            status_counts = inventory[status_col].astype(str).value_counts().rename_axis(
                "Status"
            ).reset_index(name="Products")
            fig = px.bar(status_counts, x="Status", y="Products", color="Status")
            st.plotly_chart(fig, width="stretch")
        st.subheader("Replenishment recommendations")
        show_table(inventory)
        st.download_button(
            "Download inventory recommendations",
            inventory.to_csv(index=False).encode("utf-8"),
            file_name="retailpulse_inventory_recommendations.csv",
            mime="text/csv",
        )
    else:
        st.info("Inventory recommendations are not available.")
    st.warning(
        "Lead time, safety stock, and stock-on-hand values are assumptions in this project, "
        "not actual warehouse inventory records. Validate unusually large forecasts before acting."
    )
    show_report("inventory_planning_summary.txt")
# PAGE 6: Combined model evaluation report.
elif page == "Model Evaluation":
    st.header("Consolidated Model Evaluation")
    st.write(
        "This report consolidates the current churn, forecasting, segmentation, "
        "and inventory outputs, including their limitations."
    )
    show_report("model_evaluation_summary.txt")
# PAGE 7: Project details, dataset, and limitations.
elif page == "About & Data Notes":
    st.header("About RetailPulse")
# Add basic CSS to control page spacing and KPI card style.
    st.markdown(
        """
        **RetailPulse** is a retail analytics portfolio project covering:
        - Exploratory sales analysis
        - RFM customer features and K-Means segmentation
        - Historical customer churn classification
        - Baseline product demand forecasting
        - Assumption-based inventory planning
        **Dataset:** UCI Online Retail II.
        **Important limitations**
        - Historical transactions do not represent live retail activity.
        - Customer cluster IDs are arbitrary.
        - Churn performance is based on a defined historical evaluation window.
        - Forecast accuracy varies by product and demand scale.
        - Inventory suggestions rely on assumed stock and lead-time values.
        - No displayed estimate should be treated as a guaranteed business outcome.
        """
    )
    st.subheader("Generated reports")
    for filename in [
        "dataset_profile.txt",
        "cleaning_summary.txt",
        "eda_summary.txt",
        "feature_engineering_summary.txt",
        "customer_segmentation_summary.txt",
        "churn_model_report.txt",
        "demand_forecasting_summary.txt",
        "inventory_planning_summary.txt",
        "model_evaluation_summary.txt",
    ]:
        path = REPORT_DIR / filename
        st.write(f"{'✅' if path.exists() else '○'} {filename}")
    st.caption("Data source: UCI Machine Learning Repository — Online Retail II.")
    st.markdown("https://archive.ics.uci.edu/dataset/502/online+retail+ii")
st.markdown("---")
st.caption("RetailPulse | Data Science & Analytics | Team Project")
