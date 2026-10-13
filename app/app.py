# ==========================================
# RETAILPULSE DASHBOARD
# ==========================================
# This script builds an interactive web dashboard for retail analytics.
# It lets non-technical users explore sales trends, customer segments,
# churn predictions, demand forecasts, and inventory plans easily.

from pathlib import Path
import json
import re
import pandas as pd
import plotly.express as px
import streamlit as st

# Set up file paths for our project data and saved reports
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"

# Configure the page layout to look wide, clean, and professional
st.set_page_config(
    page_title="RetailPulse | Retail Analytics",
    page_icon="ðŸ“Š",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (UI/UX Upgrades & Typography Hierarchy - Style 1: Modern & Minimalist)
st.markdown("""
<style>
:root {
    color-scheme: light;
    --rp-navy: #0f172a;
    --rp-teal: #0d9488;
    --rp-ink: #334155;
    --rp-muted: #64748b;
    --rp-border: #e2e8f0;
    --rp-canvas: #f8fafc;
    --rp-card-bg: #ffffff;
}

.stApp { background: var(--rp-canvas); color: var(--rp-ink); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.block-container { max-width: 1500px; padding: 2.5rem 2.5rem 3rem; }

/* Clear Typography Scale & Sizes & Hide Annoying Streamlit Anchor Icons */
h1 a, h2 a, h3 a, h4 a { display: none !important; }

.custom-main-title {
    font-size: 2.8rem !important;
    font-weight: 800 !important;
    color: var(--rp-navy) !important;
    letter-spacing: -0.03em !important;
    margin-bottom: 0rem;
    line-height: 1.2;
}
h1 { color: var(--rp-navy); font-weight: 800; font-size: 2.5rem; letter-spacing: -0.03em; margin-bottom: 0.2rem; }
h2 { color: var(--rp-navy); font-weight: 750; font-size: 1.75rem; letter-spacing: -0.02em; border-bottom: 2px solid var(--rp-border); padding-bottom: 0.5rem; margin-top: 2rem; margin-bottom: 1rem; }
h3 { color: var(--rp-navy); font-weight: 700; font-size: 1.35rem; margin-top: 1.5rem; margin-bottom: 0.75rem; }
h4 { color: var(--rp-navy); font-weight: 650; font-size: 1.1rem; margin-top: 1rem; }
p, span, label { color: var(--rp-ink); font-size: 1rem; line-height: 1.5; }

/* Sleek Sidebar Styling & Completely Remove Radio Circles */
[data-testid="stSidebar"] {
    background: #0f172a;
    border-right: 1px solid #1e293b;
    padding-top: 1rem;
}
[data-testid="stSidebar"] * { color: #f8fafc !important; }

/* Completely hide the radio input and its container circle */
[data-testid="stSidebar"] div[role="radiogroup"] label div:first-child {
    display: none !important;
}

/* Transform radio items into clean full-width nav buttons */
[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 0.3rem;
}

[data-testid="stSidebar"] div[role="radiogroup"] label {
    display: flex;
    align-items: center;
    width: 100%;
    padding: 0.65rem 0.9rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
}

/* Hover effect: change background color smoothly */
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(13, 148, 136, 0.2);
    color: #2dd4bf !important;
}

/* Active/Selected menu item pill highlight */
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: rgba(13, 148, 136, 0.35) !important;
    border-radius: 8px;
    font-weight: 600;
}

/* Metric Cards */
div[data-testid="stMetric"] {
    background: var(--rp-card-bg);
    border: 1px solid var(--rp-border);
    border-top: 4px solid var(--rp-teal);
    padding: 1.2rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
div[data-testid="stMetricLabel"] { color: var(--rp-muted); font-weight: 600; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }
div[data-testid="stMetricValue"] { color: var(--rp-navy); font-weight: 800; font-size: 1.85rem; }

/* Data tables, charts, and expandable boxes */
[data-testid="stDataFrame"], [data-testid="stTable"], div[data-testid="stPlotlyChart"] {
    border: 1px solid var(--rp-border);
    border-radius: 12px;
    background: var(--rp-card-bg);
    padding: 0.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}
[data-testid="stExpander"] { background: var(--rp-card-bg); border: 1px solid var(--rp-border); border-radius: 12px; margin-bottom: 1rem; }

/* Buttons */
div.stButton>button, div.stDownloadButton>button {
    border-radius: 8px;
    border: 1px solid var(--rp-border);
    background-color: #ffffff;
    color: var(--rp-navy);
    font-weight: 600;
}
div.stButton>button:hover, div.stDownloadButton>button:hover {
    background-color: #f1f5f9;
    border-color: var(--rp-teal);
    color: var(--rp-teal);
}
hr { border-color: #1e293b; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA LOADING FUNCTIONS
# ==========================================
@st.cache_data(show_spinner=False)
def load_csv(filename):
    """Loads a CSV data file safely. Returns an empty sheet if the file is missing."""
    path = DATA_DIR / filename
    if not path.exists(): return pd.DataFrame()
    try: return pd.read_csv(path, low_memory=False)
    except (OSError, ValueError, pd.errors.ParserError, UnicodeDecodeError): return pd.DataFrame()

@st.cache_data(show_spinner=False)
def read_report(filename):
    """Reads summary text reports generated by the project analysis scripts."""
    path = REPORT_DIR / filename
    try: return path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError: return ""

@st.cache_data(show_spinner=False)
def load_country_sales():
    """Calculates total sales revenue per country from clean transaction records."""
    path = DATA_DIR / "retail_transactions_cleaned.csv.gz"
    if not path.exists(): return pd.DataFrame(columns=["country", "sales_revenue"])
    cols = ["country", "customer_id", "quantity", "unit_price", "line_revenue", "is_cancellation_invoice"]
    try: df = pd.read_csv(path, usecols=cols, low_memory=False)
    except (OSError, ValueError, pd.errors.ParserError): return pd.DataFrame(columns=["country", "sales_revenue"])
    cancel = df["is_cancellation_invoice"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"])
    qty, price, revenue = (pd.to_numeric(df[c], errors="coerce") for c in ["quantity", "unit_price", "line_revenue"])
    keep = df["customer_id"].notna() & df["country"].notna() & (qty > 0) & (price > 0) & (revenue > 0) & ~cancel
    out = df.loc[keep, ["country"]].copy(); out["line_revenue"] = revenue.loc[keep]
    return out.groupby("country", as_index=False)["line_revenue"].sum().rename(columns={"line_revenue":"sales_revenue"}).nlargest(10, "sales_revenue").sort_values("sales_revenue")

def find_column(df, candidates):
    """Finds the correct column name from a list of possible spelling options."""
    lookup = {str(c).lower().replace(" ", "_"): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower().replace(" ", "_") in lookup: return lookup[candidate.lower().replace(" ", "_")]
    return None

def show_table(df, height=350):
    """Displays data neatly in a table format with row and column counts."""
    if df.empty:
        st.info("This dataset is not available yet. Run the relevant project script first."); return
    view = df.copy()
    for col in view.select_dtypes(include=["float"]).columns: view[col] = view[col].round(3)
    st.caption(f"{len(view):,} rows Â· {len(view.columns):,} columns")
    st.dataframe(view, width="stretch", height=height, hide_index=True)

def show_report(filename):
    """Formats text or JSON reports into readable tables or clean text blocks."""
    content = read_report(filename)
    if not content: st.info(f"Report not found: reports/{filename}"); return
    stripped = content.strip()
    if stripped.startswith(("{", "[")):
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict):
                rows = []
                for k, v in obj.items(): rows.append((k, json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v))
                st.dataframe(pd.DataFrame(rows, columns=["Metric", "Value"]), width="stretch", hide_index=True); return
            if isinstance(obj, list): show_table(pd.DataFrame(obj)); return
        except (json.JSONDecodeError, TypeError): pass
    st.markdown(content)

def numeric(df, col): return pd.to_numeric(df[col], errors="coerce")
def empty_message(message): st.info(message)
def add_download(label, df, filename):
    """Provides a button so users can download data tables as CSV files."""
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=filename, mime="text/csv")

# ==========================================
# LOAD DATA FILES AT STARTUP
# ==========================================
customer_features = load_csv("customer_features.csv")
segments = load_csv("customer_rfm_segments.csv")
cluster_summary = load_csv("customer_cluster_summary.csv")
churn_predictions = load_csv("churn_test_predictions.csv")
forecast_evaluation = load_csv("forecast_evaluation.csv")
forecasts = load_csv("demand_forecasts.csv")
inventory = load_csv("inventory_recommendations.csv")
daily_sales_source = load_csv("daily_product_sales.csv")

# ==========================================
# SIDEBAR NAVIGATION & MAIN TITLE
# ==========================================
st.markdown('<p class="custom-main-title">RetailPulse</p>', unsafe_allow_html=True)
st.subheader("AI-Powered Customer Analytics & Demand Forecasting")
st.caption("Retail intelligence for customer engagement, sales planning, and inventory decisions.")

with st.sidebar:
    st.markdown("### ðŸ“Š Navigation Menu")
    st.markdown("---")

    # Styled with icons matching Style 1
    selected_option = st.radio(
        "Select Dashboard Page",
        [
            "ðŸ“Š Executive Overview",
            "ðŸ‘¥ Customer Segmentation",
            "ðŸ“‰ Churn Analysis",
            "ðŸ“ˆ Demand Forecasting",
            "ðŸ“¦ Inventory Planning",
            "âš™ï¸ Model Evaluation",
            "â„¹ï¸ About & Data Notes"
        ],
        label_visibility="collapsed"
    )
    # Strip the leading icon for clean page condition checks
    page = selected_option.split(" ", 1)[1] if " " in selected_option else selected_option

    st.markdown("---")
    st.caption("Analytics based on the project's processed retail transaction dataset.")

# ==========================================
# PAGE 1 â€” EXECUTIVE OVERVIEW
# ==========================================
if page == "Executive Overview":
    st.header("Executive Overview")
    st.write("A quick view of customer activity, product sales, forecasting performance, and overall revenue.")

    report = read_report("eda_summary.txt")
    values = {"revenue":None,"customers":None,"products":None,"invoices":None}
    patterns = {
        "revenue": r"(?:Revenue|Total standard sales revenue):\s*([0-9,]+(?:\.[0-9]+)?)",
        "customers": r"(?:Customers|Unique customers in sales subset):\s*([0-9,]+)",
        "products": r"(?:Products|Unique products in sales subset):\s*([0-9,]+)",
        "invoices": r"(?:Invoices|Invoice count in sales subset):\s*([0-9,]+)"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, report, re.I) if report else None
        if match: values[key] = float(match.group(1).replace(",", ""))

    if values["customers"] is None and not customer_features.empty: values["customers"] = len(customer_features)
    if values["products"] is None and "stock_code" in daily_sales_source: values["products"] = daily_sales_source.stock_code.nunique()
    if values["invoices"] is None and "invoice" in daily_sales_source: values["invoices"] = daily_sales_source.invoice.nunique()

    # Display key metrics in cards at the top
    k = st.columns(4)
    k[0].metric("Customers Analyzed", f"{int(values['customers']):,}" if values["customers"] is not None else "N/A")
    k[1].metric("Products Tracked", f"{int(values['products']):,}" if values["products"] is not None else "N/A")
    k[2].metric("Total Invoices", f"{int(values['invoices']):,}" if values["invoices"] is not None else "N/A")
    k[3].metric("Recorded Revenue", f"${values['revenue']:,.2f}" if values["revenue"] is not None else "N/A")

    if values["revenue"] is None:
        st.warning("Revenue KPI could not be extracted from reports/eda_summary.txt; verify the report before presenting this figure.")

    st.markdown("---")
    st.subheader("Sales Performance")

    ds = daily_sales_source.copy()
    if not ds.empty and {"order_date", "sales_revenue"}.issubset(ds.columns):
        ds["order_date"] = pd.to_datetime(ds["order_date"], errors="coerce")
        ds["sales_revenue"] = numeric(ds, "sales_revenue")
        if "stock_code" not in ds: ds["stock_code"] = "Unknown"
        ds["stock_code"] = ds["stock_code"].astype(str)
        ds = ds.dropna(subset=["order_date", "sales_revenue"])

        monthly = ds.assign(month_start=ds.order_date.dt.to_period("M").dt.to_timestamp()).groupby("month_start", as_index=False).sales_revenue.sum().sort_values("month_start")

        left, right = st.columns(2)
        with left:
            st.markdown("#### Monthly Revenue Trend")
            if not monthly.empty:
                fig = px.line(monthly, x="month_start", y="sales_revenue", markers=True, title="Monthly Sales Revenue", labels={"month_start":"Month","sales_revenue":"Revenue ($)"})
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, width="stretch")
            else:
                empty_message("Monthly revenue data is unavailable.")

        with right:
            st.markdown("#### Top 10 Products by Revenue")
            top = ds.groupby("stock_code", as_index=False).sales_revenue.sum().nlargest(10,"sales_revenue").sort_values("sales_revenue")
            if not top.empty:
                st.plotly_chart(px.bar(top, x="sales_revenue", y="stock_code", orientation="h", title="Highest-Revenue Products", labels={"stock_code":"Product Code","sales_revenue":"Revenue ($)"}), width="stretch")
            else:
                empty_message("Product revenue data is unavailable.")

        st.markdown("#### Top 10 Countries by Revenue")
        countries = load_country_sales()
        if not countries.empty:
            st.plotly_chart(px.bar(countries, x="sales_revenue", y="country", orientation="h", title="Countries Ranked by Sales Revenue", labels={"country":"Country","sales_revenue":"Revenue ($)"}), width="stretch")
        else:
            empty_message("Country sales data is unavailable.")
    else:
        empty_message("Daily product sales data is not available or has an unexpected schema.")

    st.markdown("---")
    left, right = st.columns(2)
    with left:
        st.subheader("Customer Segments")
        cluster = find_column(segments, ["cluster","cluster_id","segment"])
        if not segments.empty and cluster:
            counts = segments[cluster].astype(str).value_counts().rename_axis("Cluster").reset_index(name="Customers")
            st.plotly_chart(px.bar(counts, x="Cluster", y="Customers", color="Cluster", text_auto=True, title="Customers by Cluster"), width="stretch")
        else:
            empty_message("Customer segmentation output is not available.")

    with right:
        st.subheader("Forecast Evaluation")
        if not forecast_evaluation.empty and {"mae","baseline"}.issubset(forecast_evaluation.columns):
            ev = forecast_evaluation.copy()
            ev["mae"] = numeric(ev,"mae")
            chart = ev.groupby("baseline",as_index=False).mae.mean().sort_values("mae")
            st.plotly_chart(px.bar(chart, x="baseline", y="mae", color="baseline", title="Mean Error by Forecast Baseline (Lower is Better)"), width="stretch")
        else:
            empty_message("Forecast evaluation results are not available.")

    with st.expander("Exploratory Data Analysis Report"):
        show_report("eda_summary.txt")

# ==========================================
# PAGE 2 â€” CUSTOMER SEGMENTATION
# ==========================================
elif page == "Customer Segmentation":
    st.header("Customer Segmentation")
    st.write("Explore customer groups using purchase recency, frequency, and total spending behavior.")

    cluster = find_column(segments, ["cluster", "cluster_id", "segment"])
    if not segments.empty and cluster:
        counts = segments[cluster].astype(str).value_counts().rename_axis("Cluster").reset_index(name="Customers")
        a, b = st.columns(2)
        with a: st.plotly_chart(px.bar(counts, x="Cluster", y="Customers", color="Cluster", text_auto=True, title="Customers in Each Cluster"), width="stretch")
        with b: st.plotly_chart(px.pie(counts, names="Cluster", values="Customers", hole=.55, title="Customer Segment Share"), width="stretch")
    else:
        empty_message("Customer-level segment data or cluster column is not available.")

    st.subheader("Cluster Profiles")
    if not cluster_summary.empty: show_table(cluster_summary)
    else: st.info("Cluster profile summary is not available; customer-level segments can still be inspected.")

    if not segments.empty:
        st.subheader("Customer-Level Segments")
        view = segments.copy()
        if cluster:
            options = ["All"] + sorted(segments[cluster].dropna().astype(str).unique().tolist())
            selected = st.selectbox("Filter by cluster", options)
            if selected != "All": view = view[view[cluster].astype(str) == selected]

        nums = [c for c in ["recency", "frequency", "monetary"] if c in view.columns]
        if len(nums) >= 2:
            a, b = st.columns(2)
            with a: xcol = st.selectbox("X-axis", nums, key="segment_x")
            with b: ycol = st.selectbox("Y-axis", [c for c in nums if c != xcol], key="segment_y")
            hover = [c for c in ["customer_id", "R_score", "F_score", "M_score"] if c in view.columns]
            st.plotly_chart(px.scatter(view, x=xcol, y=ycol, color=cluster if cluster else None, hover_data=hover, opacity=.7, title=f"Customer Behavior: {xcol} vs {ycol}"), width="stretch")

        show_table(view, 420)
        add_download("Download displayed customer segments", view, "retailpulse_customer_segments.csv")

    if not customer_features.empty:
        custom = [c for c in customer_features.columns if c.startswith("RP_")]
        if custom:
            st.subheader("Custom Customer Features")
            st.caption("RP_ columns are project-created features. The loyalty index is a heuristic, not a validated business measure.")
            cols = (["customer_id"] if "customer_id" in customer_features else []) + custom
            show_table(customer_features[cols].head(100), 320)
            add_download("Download custom customer features", customer_features[cols], "retailpulse_custom_customer_features.csv")

# ==========================================
# PAGE 3 â€” CHURN ANALYSIS
# ==========================================
elif page == "Churn Analysis":
    st.header("Customer Churn Analysis")
    st.write("The current experiment uses past purchase activity to analyze and predict customer drop-off.")

    with st.expander("Churn Model Report", expanded=True):
        show_report("churn_model_report.txt")

    if not churn_predictions.empty:
        pred = churn_predictions.copy()
        actual = find_column(pred, ["actual_churn", "actual", "y_true"])
        guess = find_column(pred, ["predicted_churn", "prediction", "y_pred"])
        prob = find_column(pred, ["churn_probability", "probability", "predicted_probability"])

        if actual:
            a = pred[actual].astype(str).str.strip().str.lower()
            churn = int(a.isin(["1", "true", "yes", "churn"]).sum())
            active = len(pred) - churn
            k = st.columns(3)
            k[0].metric("Test Customers", f"{len(pred):,}")
            k[1].metric("Actual Churn Cases", f"{churn:,}")
            k[2].metric("Actual Active Cases", f"{active:,}")
            counts = pd.DataFrame({"Outcome": ["Active", "Churn"], "Customers": [active, churn]})
            st.plotly_chart(px.pie(counts, names="Outcome", values="Customers", hole=.55, title="Actual Test-Set Class Balance"), width="stretch")

        if actual and guess:
            matrix = pd.crosstab(pred[actual].astype(str), pred[guess].astype(str), rownames=["Actual"], colnames=["Predicted"])
            st.plotly_chart(px.imshow(matrix, text_auto=True, aspect="auto", color_continuous_scale="Blues", title="Actual vs Predicted â€” Confusion Matrix"), width="stretch")

        if prob:
            pred[prob] = numeric(pred, prob)
            valid = pred.dropna(subset=[prob])
            if not valid.empty:
                st.plotly_chart(px.histogram(valid, x=prob, nbins=20, title="Predicted Churn Probability Distribution"), width="stretch")

        st.subheader("Test-Set Predictions")
        show_table(pred, 420)
        add_download("Download churn predictions", pred, "retailpulse_churn_predictions.csv")
    else:
        empty_message("Churn test predictions are not available.")

    st.warning("These results are historical and do not guarantee future customer behavior. Validate on a later, untouched time period before production use.")

# ==========================================
# PAGE 4 â€” DEMAND FORECASTING
# ==========================================
elif page == "Demand Forecasting":
    st.header("Demand Forecasting")
    st.write("Compare baseline forecast errors and inspect product-level demand predictions.")

    if not forecast_evaluation.empty:
        ev = forecast_evaluation.copy()
        mae = find_column(ev, ["mae"])
        rmse = find_column(ev, ["rmse"])
        model = find_column(ev, ["baseline", "model"])

        if mae and model:
            ev[mae] = numeric(ev, mae)
            a, b = st.columns(2)
            with a:
                chart = ev.groupby(model, as_index=False)[mae].mean().sort_values(mae)
                st.plotly_chart(px.bar(chart, x=model, y=mae, color=model, title="Average Error (MAE) by Baseline â€” Lower is Better"), width="stretch")
            with b:
                if rmse:
                    ev[rmse] = numeric(ev, rmse)
                    chart = ev.groupby(model, as_index=False)[rmse].mean().sort_values(rmse)
                    st.plotly_chart(px.bar(chart, x=model, y=rmse, color=model, title="Average Error (RMSE) by Baseline â€” Lower is Better"), width="stretch")
                else:
                    st.info("RMSE column is not available.")
            st.subheader("Historical Evaluation Results")
            show_table(ev)
        else:
            empty_message("Forecast evaluation file has an unexpected schema.")
    else:
        empty_message("Forecast evaluation output is not available.")

    if not forecasts.empty:
        st.subheader("Product Demand Forecasts")
        prod = find_column(forecasts, ["stock_code", "product_id", "product"])
        date = find_column(forecasts, ["forecast_date", "date", "ds"])
        value = find_column(forecasts, ["predicted_units", "forecast_quantity", "forecast", "predicted_quantity", "prediction"])
        view = forecasts.copy()

        if prod:
            products = sorted(view[prod].dropna().astype(str).unique().tolist())
            if products:
                selected = st.selectbox("Select product", products)
                view = view[view[prod].astype(str) == selected]

        if date and value:
            view[date] = pd.to_datetime(view[date], errors="coerce")
            view[value] = numeric(view, value)
            view = view.dropna(subset=[date, value]).sort_values(date)
            if not view.empty:
                st.plotly_chart(px.line(view, x=date, y=value, markers=True, title="Forecasted Demand by Date", labels={date: "Forecast Date", value: "Predicted Units"}), width="stretch")
                k = st.columns(3)
                k[0].metric("Forecast Days", f"{len(view):,}")
                k[1].metric("Total Predicted Units", f"{view[value].sum():,.1f}")
                k[2].metric("Average Daily Prediction", f"{view[value].mean():,.2f}")
            else:
                empty_message("No valid forecast rows are available for this product.")
        else:
            empty_message("Forecast date or predicted-units column was not found.")

        show_table(view)
        add_download("Download demand forecasts", view, "retailpulse_demand_forecasts.csv")
    else:
        empty_message("Demand forecast output is not available.")

    st.caption("Forecast estimates are not guaranteed future demand. Accuracy varies by product and demand scale.")

# ==========================================
# PAGE 5 â€” INVENTORY PLANNING
# ==========================================
elif page == "Inventory Planning":
    st.header("Inventory Planning")
    st.write("Review restocking recommendations generated from forecasted demand and planning assumptions.")

    if not inventory.empty:
        stock = find_column(inventory, ["stock_code", "product_id", "product"])
        status = find_column(inventory, ["planning_status", "status"])
        replen = find_column(inventory, ["suggested_replenishment_units", "replenishment_units"])
        reorder = find_column(inventory, ["reorder_point"])

        k = st.columns(3)
        k[0].metric("Products Planned", f"{len(inventory):,}")
        if replen:
            units = numeric(inventory, replen).fillna(0)
            k[1].metric("Suggested Restock Units", f"{units.sum():,.0f}")
            k[2].metric("Products Needing Restock", f"{int((units > 0).sum()):,}")
        else:
            k[1].metric("Suggested Restock Units", "N/A")
            k[2].metric("Products Needing Restock", "N/A")

        if status:
            counts = inventory[status].fillna("Unknown").astype(str).value_counts().rename_axis("Status").reset_index(name="Products")
            a, b = st.columns(2)
            with a: st.plotly_chart(px.bar(counts, x="Status", y="Products", color="Status", text_auto=True, title="Products by Planning Status"), width="stretch")
            with b: st.plotly_chart(px.pie(counts, names="Status", values="Products", hole=.55, title="Planning Status Share"), width="stretch")

        if stock and replen:
            chart = inventory.copy()
            chart[replen] = numeric(chart, replen)
            if reorder: chart[reorder] = numeric(chart, reorder)
            chart = chart.dropna(subset=[replen]).nlargest(15, replen).sort_values(replen)
            if not chart.empty:
                st.plotly_chart(px.bar(chart, x=replen, y=stock, orientation="h", title="Top 15 Suggested Restocks", labels={replen: "Suggested Units", stock: "Product Code"}), width="stretch")

        st.subheader("Replenishment Recommendations")
        show_table(inventory, 420)
        add_download("Download inventory recommendations", inventory, "retailpulse_inventory_recommendations.csv")
    else:
        empty_message("Inventory recommendations are not available.")

    st.warning("Lead time, safety stock, and stock-on-hand values are assumptions in this project, not actual warehouse inventory records. Validate unusually large forecasts before acting.")

    with st.expander("Inventory Planning Report"):
        show_report("inventory_planning_summary.txt")

# ==========================================
# PAGE 6 â€” MODEL EVALUATION
# ==========================================
elif page == "Model Evaluation":
    st.header("Consolidated Model Evaluation")
    st.write("Review forecasting comparisons, churn predictions, and overall model performance summaries.")

    if not forecast_evaluation.empty:
        ev = forecast_evaluation.copy()
        model = find_column(ev, ["baseline", "model"])
        mae = find_column(ev, ["mae"])
        rmse = find_column(ev, ["rmse"])
        if model and mae:
            ev[mae] = numeric(ev, mae)
            chart = ev.groupby(model, as_index=False)[mae].mean().sort_values(mae)
            st.plotly_chart(px.bar(chart, x=model, y=mae, color=model, title="Forecast Comparison â€” MAE"), width="stretch")
            if rmse:
                ev[rmse] = numeric(ev, rmse)
                chart = ev.groupby(model, as_index=False)[rmse].mean().sort_values(rmse)
                st.plotly_chart(px.bar(chart, x=model, y=rmse, color=model, title="Forecast Comparison â€” RMSE"), width="stretch")
            show_table(ev)
    else:
        empty_message("Forecast evaluation results are not available.")

    if not churn_predictions.empty:
        actual = find_column(churn_predictions, ["actual_churn", "actual", "y_true"])
        guess = find_column(churn_predictions, ["predicted_churn", "prediction", "y_pred"])
        if actual and guess:
            matrix = pd.crosstab(churn_predictions[actual].astype(str), churn_predictions[guess].astype(str))
            st.subheader("Churn Prediction Snapshot")
            st.plotly_chart(px.imshow(matrix, text_auto=True, aspect="auto", color_continuous_scale="Blues", labels={"x": "Predicted", "y": "Actual", "color": "Customers"}, title="Churn Model Confusion Matrix"), width="stretch")

    with st.expander("Full Model Evaluation Report", expanded=True):
        show_report("model_evaluation_summary.txt")

# ==========================================
# PAGE 7 â€” ABOUT & DATA NOTES
# ==========================================
elif page == "About & Data Notes":
    st.header("About RetailPulse")
    st.write("RetailPulse is a retail analytics portfolio project covering sales trends, customer segmentation, churn classification, demand forecasting, and inventory planning.")

    a, b, c = st.columns(3)
    a.metric("Dashboard Sections", "7")
    b.metric("Customer Records", f"{len(customer_features):,}" if not customer_features.empty else "N/A")
    c.metric("Forecast Products", f"{forecasts['stock_code'].nunique():,}" if "stock_code" in forecasts.columns else "N/A")

    st.subheader("Project Capabilities")
    capabilities = pd.DataFrame([
        ("Exploratory Analysis", "Sales trends, customer counts, products, and countries"),
        ("Customer Segmentation", "RFM-style features and K-Means cluster labels"),
        ("Churn Analysis", "Historical churn classification and test-set predictions"),
        ("Demand Forecasting", "Baseline product forecasts and error evaluations"),
        ("Inventory Planning", "Assumption-based reorder points and restocking estimates"),
        ("Custom Features", "Customer engagement features created for this project")
    ], columns=["Area", "Description"])
    show_table(capabilities, 280)

    st.subheader("Generated Reports")
    names = [
        "dataset_profile.txt", "cleaning_summary.txt", "eda_summary.txt",
        "feature_engineering_summary.txt", "customer_segmentation_summary.txt",
        "churn_model_report.txt", "demand_forecasting_summary.txt",
        "inventory_planning_summary.txt", "model_evaluation_summary.txt"
    ]
    show_table(pd.DataFrame([{"Report": n, "Status": "Available" if (REPORT_DIR / n).exists() else "Missing"} for n in names]), 320)

    st.subheader("Dataset and Limitations")
    st.markdown("""
**Dataset:** UCI Online Retail II.

- Historical transactions do not represent live retail activity.
- Customer cluster IDs are arbitrary labels, not a ranking.
- Churn performance is based on a defined historical evaluation window.
- Forecast accuracy varies by product and demand scale.
- Inventory suggestions rely on assumed stock and lead-time values.
- Estimates should not be treated as guaranteed business outcomes.
""")
    st.markdown("Dataset source: [UCI Machine Learning Repository â€” Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)")

# Footer section
st.markdown("---")
st.caption("RetailPulse | Data Science & Analytics | Team Project")
