# ============================================================
# RETAILPULSE — AI-POWERED RETAIL ANALYTICS DASHBOARD
# ============================================================
# Built around the existing RetailPulse data pipeline and outputs.
# Historical model results and assumption-based inventory values are
# labelled clearly; missing source data is never silently fabricated.

from pathlib import Path
import json
import re
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"
ASSETS_DIR = ROOT / "app" / "assets"
LOGO_PATH = ASSETS_DIR / "retailpulse_logo.png"
APP_ICON_PATH = ASSETS_DIR / "retailpulse_app_icon.png"
CLEAN_DATA_PATH = DATA_DIR / "retail_transactions_cleaned.csv.gz"

st.set_page_config(
    page_title="RetailPulse | Retail Analytics",
    page_icon=str(APP_ICON_PATH) if APP_ICON_PATH.exists() else "📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
.block-container { max-width: 1550px; padding: 2rem 2.2rem 3rem; }
h1 a, h2 a, h3 a, h4 a { display: none !important; }
h1 { color: var(--rp-navy); font-weight: 800; letter-spacing: -0.03em; }
h2 { color: var(--rp-navy); font-weight: 750; border-bottom: 2px solid var(--rp-border); padding-bottom: .45rem; }
h3, h4 { color: var(--rp-navy); font-weight: 700; }

/* RetailPulse sidebar — navy, teal, grouped navigation */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1224 0%, #111c33 100%);
    border-right: 1px solid #263550;
    padding-top: 1rem;
}
[data-testid="stSidebar"] > div:first-child { padding: 1rem .8rem 1.5rem; }
[data-testid="stSidebar"] * { color: #e7edf7; }

[data-testid="stSidebar"] [data-testid="stImage"] {
    display: flex;
    justify-content: center;
    margin: .1rem auto .6rem;
}
.rp-sidebar-heading {
    color: #f8fafc;
    font-size: 1.08rem;
    font-weight: 800;
    letter-spacing: .01em;
    margin: .2rem 0 .7rem;
}
.rp-sidebar-subtitle {
    color: #94a3b8;
    font-size: .74rem;
    line-height: 1.45;
    margin: .15rem 0 .8rem;
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: transparent !important;
    border: 0 !important;
    border-radius: 12px !important;
    margin: .12rem 0 .42rem !important;
    overflow: hidden;
}
[data-testid="stSidebar"] [data-testid="stExpander"] details,
[data-testid="stSidebar"] details {
    background: transparent !important;
    border: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    background: transparent !important;
    border-radius: 10px !important;
    padding: .62rem .5rem !important;
    font-size: .96rem;
    font-weight: 750;
    min-height: 2.8rem;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
    background: rgba(51, 65, 85, .58) !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary svg {
    color: #a7b6cc !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: .18rem;
    padding: 0 .05rem .35rem .25rem;
}
[data-testid="stSidebar"] div[role="radiogroup"] label {
    display: flex;
    align-items: center;
    padding: .52rem .65rem !important;
    border-radius: 9px !important;
    border-left: 3px solid transparent;
    font-size: .86rem !important;
    line-height: 1.25;
    transition: background .15s ease, border-color .15s ease;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(45, 212, 191, .12) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(13,148,136,.38), rgba(13,148,136,.18)) !important;
    border-left-color: #2dd4bf !important;
    font-weight: 750;
}
/* Hide Streamlit's default circular radio markers in the sidebar.
   Keep the radio inputs functional for keyboard/mouse navigation, and use
   the teal left border + tinted background as the selected-state indicator. */
[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child,
[data-testid="stSidebar"] div[role="radiogroup"] label [data-baseweb="radio"] > div:first-child,
[data-testid="stSidebar"] div[role="radiogroup"] label svg,
[data-testid="stSidebar"] div[role="radiogroup"] label input[type="radio"] {
    display: none !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label {
    padding-left: .8rem !important;
    gap: 0 !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    box-shadow: inset 3px 0 0 #2dd4bf;
}
/* Preserve the original dashboard card, metric, table, chart and button styles.
   These selectors intentionally target the main page, not the sidebar. */
[data-testid="stAppViewContainer"] div[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--rp-border);
    border-top: 4px solid var(--rp-teal);
    padding: 1rem;
    border-radius: 12px;
    box-shadow: 0 3px 8px rgba(15,23,42,.04);
}
[data-testid="stAppViewContainer"] div[data-testid="stMetricLabel"] {
    color: var(--rp-muted);
    font-weight: 650;
}
[data-testid="stAppViewContainer"] div[data-testid="stMetricValue"] {
    color: var(--rp-navy);
    font-weight: 800;
}
[data-testid="stAppViewContainer"] [data-testid="stDataFrame"],
[data-testid="stAppViewContainer"] [data-testid="stTable"],
[data-testid="stAppViewContainer"] div[data-testid="stPlotlyChart"] {
    border: 1px solid var(--rp-border);
    border-radius: 12px;
    background: white;
    padding: .35rem;
}
[data-testid="stAppViewContainer"] [data-testid="stExpander"] {
    background: white;
    border: 1px solid var(--rp-border);
    border-radius: 12px;
    margin-bottom: .8rem;
}
[data-testid="stAppViewContainer"] div.stButton > button,
[data-testid="stAppViewContainer"] div.stDownloadButton > button {
    border-radius: 8px;
    border: 1px solid var(--rp-border);
    font-weight: 650;
}

[data-testid="stSidebar"] div.stButton > button {
    background: #17243a !important;
    color: #f8fafc !important;
    border: 1px solid #34445f !important;
    border-radius: 10px !important;
    min-height: 2.45rem;
    white-space: normal;
    opacity: 1 !important;
}
[data-testid="stSidebar"] div.stButton > button p,
[data-testid="stSidebar"] div.stButton > button span {
    color: #f8fafc !important;
    opacity: 1 !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: #0d9488 !important;
    border-color: #2dd4bf !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] hr {
    border-color: #2b3a53 !important;
    margin: .8rem 0 !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #94a3b8 !important;
    font-size: .73rem;
}
</style>
""", unsafe_allow_html=True)

# --------------------------- Data helpers ---------------------------

@st.cache_data(show_spinner=False)
def load_csv(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False)
    except (OSError, ValueError, pd.errors.ParserError, UnicodeDecodeError):
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_transactions():
    if not CLEAN_DATA_PATH.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(CLEAN_DATA_PATH, low_memory=False)
    except (OSError, ValueError, pd.errors.ParserError, UnicodeDecodeError):
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def read_report(filename):
    path = REPORT_DIR / filename
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        return ""


def find_column(df, candidates):
    if df is None or df.empty:
        return None
    lookup = {str(c).lower().replace(" ", "_"): c for c in df.columns}
    for candidate in candidates:
        key = candidate.lower().replace(" ", "_")
        if key in lookup:
            return lookup[key]
    return None


def numeric(df, col):
    return pd.to_numeric(df[col], errors="coerce")



def show_table(df, height=350):
    if df is None or df.empty:
        st.info(
            "No rows are available for this view. "
            "Check that the relevant pipeline script has been run."
        )
        return

    view = df.copy()

    # Fix: normalize mixed-type column names before display
    view.columns = view.columns.map(str)

    for col in view.select_dtypes(include=["float"]).columns:
        view[col] = view[col].round(3)

    st.caption(
        f"{len(view):,} rows · {len(view.columns):,} columns"
    )
    st.dataframe(
        view,
        width="stretch",
        height=height,
        hide_index=True
    )


def show_report(filename):
    content = read_report(filename)
    if not content:
        st.info(f"Report not found: reports/{filename}")
        return
    stripped = content.strip()
    if stripped.startswith(("{", "[")):
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict):
                rows = [(k, json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in obj.items()]
                show_table(pd.DataFrame(rows, columns=["Metric", "Value"]))
                return
            if isinstance(obj, list):
                show_table(pd.DataFrame(obj))
                return
        except (json.JSONDecodeError, TypeError):
            pass
    st.text(content)


def add_download(label, df, filename):
    if df is not None and not df.empty:
        st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=filename, mime="text/csv")


def info_if_missing(df, label):
    if df.empty:
        st.info(f"{label} is unavailable. Run the corresponding RetailPulse pipeline script first.")
        return True
    return False


def make_monthly(daily):
    if daily.empty or not {"order_date", "sales_revenue"}.issubset(daily.columns):
        return pd.DataFrame()
    df = daily.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["sales_revenue"] = pd.to_numeric(df["sales_revenue"], errors="coerce")
    df = df.dropna(subset=["order_date", "sales_revenue"])
    if df.empty:
        return pd.DataFrame()
    df["month_start"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    return df.groupby("month_start", as_index=False)["sales_revenue"].sum().sort_values("month_start")


def display_revenue_kpis(daily):
    if daily.empty or "sales_revenue" not in daily:
        st.info("Revenue metrics are unavailable from daily product sales.")
        return
    rev = pd.to_numeric(daily["sales_revenue"], errors="coerce").fillna(0)
    products = daily["stock_code"].nunique() if "stock_code" in daily else 0
    invoices = pd.to_numeric(daily["invoice_count"], errors="coerce").fillna(0).sum() if "invoice_count" in daily else None
    cols = st.columns(3)
    cols[0].metric("Recorded Sales Revenue", f"{rev.sum():,.2f}")
    cols[1].metric("Products Tracked", f"{products:,}")
    cols[2].metric("Invoice Count (summed daily product records)", f"{invoices:,.0f}" if invoices is not None else "N/A")
    st.caption("Revenue is based on the processed sales subset. Invoice counts may be repeated across product/day rows; do not interpret their sum as unique invoices.")


# --------------------------- Load current pipeline outputs ---------------------------

customer_features = load_csv("customer_features.csv")
segments = load_csv("customer_rfm_segments.csv")
cluster_summary = load_csv("..") if False else pd.DataFrame()
cluster_path = REPORT_DIR / "customer_cluster_summary.csv"
if cluster_path.exists():
    try:
        cluster_summary = pd.read_csv(cluster_path)
    except (OSError, ValueError, pd.errors.ParserError):
        pass
churn_predictions = load_csv("churn_test_predictions.csv")
forecast_evaluation = load_csv("forecast_evaluation.csv")
forecasts = load_csv("demand_forecasts.csv")
inventory = load_csv("inventory_recommendations.csv")
daily_sales = load_csv("daily_product_sales.csv")
transactions = load_transactions()


# --------------------------- Header and navigation ---------------------------

head_logo, head_text = st.columns([1, 4], vertical_alignment="center")
with head_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=210)
with head_text:
    st.title("RetailPulse")
    st.subheader("AI-Powered Customer Analytics & Demand Forecasting")
    st.caption("Retail intelligence for sales performance, customer engagement, demand planning, and inventory decisions.")

pages = [
    "📊 Executive Summary",
    "📈 Sales Trend Analysis",
    "📅 Monthly & Seasonal Sales",
    "🏷️ Product Performance",
    "👥 Customer Analytics",
    "🧭 Customer Behaviour",
    "🌍 Country Analysis",
    "💰 Profit & Revenue Analysis",
    "🧩 Customer Segmentation",
    "📉 Customer Churn",
    "🔮 Demand Forecast",
    "📦 Inventory Planning",
    "⚠️ Inventory Risk",
    "🧾 Orders & Transactions",
    "🧠 Customer Features",
    "🎯 Forecast Evaluation",
    "📦 Product Demand",
    "🎛️ Interactive Filters",
    "🩺 Monitoring",
    "💡 Business Insights",
    "⚙️ Model Evaluation & Notes",
]
with st.sidebar:
    if APP_ICON_PATH.exists():
        st.image(str(APP_ICON_PATH), width=112)

    st.markdown('<div class="rp-sidebar-heading">Navigation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="rp-sidebar-subtitle">Retail intelligence workspace</div>',
        unsafe_allow_html=True,
    )

    # Keep the original page labels and page routing intact; only group the
    # existing navigation choices into collapsible sections.
    navigation_groups = {
        "📊  Dashboards": [
            "📊 Executive Summary",
            "📈 Sales Trend Analysis",
        ],
        "📊  Retail Performance": [
            "🏷️ Product Performance",
            "📦 Product Demand",
            "🔮 Demand Forecast",
            "📦 Inventory Planning",
            "⚠️ Inventory Risk",
        ],
        "👥  Customer Insights": [
            "👥 Customer Analytics",
            "🧭 Customer Behaviour",
            "🧩 Customer Segmentation",
            "📉 Customer Churn",
            "🧠 Customer Features",
        ],
        "💹  Financials": [
            "💰 Profit & Revenue Analysis",
            "📅 Monthly & Seasonal Sales",
        ],
        "⚙️  Advanced Tools": [
            "🌍 Country Analysis",
            "🧾 Orders & Transactions",
            "🎛️ Interactive Filters",
            "💡 Business Insights",
            "🎯 Forecast Evaluation",
            "⚙️ Model Evaluation & Notes",
        ],
        "〰️  Monitoring": [
            "🩺 Monitoring",
        ],
    }

    # The active page is stored separately so changing a radio item in any
    # section immediately routes to the matching existing page.
    if "active_page" not in st.session_state or st.session_state["active_page"] not in pages:
        st.session_state["active_page"] = pages[0]

    def _select_sidebar_page(widget_key):
        chosen_page = st.session_state.get(widget_key)
        if chosen_page in pages:
            st.session_state["active_page"] = chosen_page
        for group_key in navigation_groups:
            other_key = "rp_nav_" + re.sub(r"[^a-z0-9]+", "_", group_key.lower()).strip("_")
            if other_key != widget_key:
                st.session_state[other_key] = None

    for group_index, (group_label, group_pages) in enumerate(navigation_groups.items()):
        widget_key = "rp_nav_" + re.sub(r"[^a-z0-9]+", "_", group_label.lower()).strip("_")
        is_current_group = st.session_state["active_page"] in group_pages
        with st.expander(group_label, expanded=is_current_group):
            st.radio(
                f"{group_label} pages",
                options=group_pages,
                index=group_pages.index(st.session_state["active_page"]) if is_current_group else None,
                key=widget_key,
                label_visibility="collapsed",
                on_change=_select_sidebar_page,
                args=(widget_key,),
            )

    page = st.session_state["active_page"].split(" ", 1)[1]
    st.markdown("---")
    st.caption("Historical Online Retail II data and RetailPulse pipeline outputs.")
    if st.button("↻  Refresh cached data", width="stretch"):
        st.cache_data.clear()
        st.rerun()


# --------------------------- Page 1: Executive summary ---------------------------

if page == "Executive Summary":
    st.header("Executive Summary Dashboard")
    st.write("A high-level view of sales, products, customer groups, churn evaluation, forecasts, and inventory planning.")
    report = read_report("eda_summary.txt")
    patterns = {
        "revenue": r"Total standard sales revenue:\s*([0-9,]+(?:\.[0-9]+)?)",
        "customers": r"Unique customers in sales subset:\s*([0-9,]+)",
        "products": r"Unique products in sales subset:\s*([0-9,]+)",
        "invoices": r"Invoice count:\s*([0-9,]+)",
    }
    values = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, report, re.I) if report else None
        values[key] = float(match.group(1).replace(",", "")) if match else None
    k = st.columns(4)
    k[0].metric("Unique Customers", f"{int(values['customers']):,}" if values["customers"] is not None else (f"{len(customer_features):,}" if not customer_features.empty else "N/A"))
    k[1].metric("Products in Sales Subset", f"{int(values['products']):,}" if values["products"] is not None else (f"{daily_sales.stock_code.nunique():,}" if "stock_code" in daily_sales else "N/A"))
    invoice_count = None
    if not transactions.empty and "invoice" in transactions.columns:
        invoice_count = transactions["invoice"].dropna().nunique()

    k[2].metric(
        "Invoices",
        f"{invoice_count:,}" if invoice_count is not None else "N/A"
    )
    k[3].metric("Standard Sales Revenue", f"{values['revenue']:,.2f}" if values["revenue"] is not None else "N/A")
    if values["revenue"] is None:
        st.warning("Revenue could not be read from reports/eda_summary.txt.")
    st.divider()
    monthly = make_monthly(daily_sales)
    left, right = st.columns(2)
    with left:
        st.subheader("Monthly Revenue Trend")
        if not monthly.empty:
            st.plotly_chart(px.line(monthly, x="month_start", y="sales_revenue", markers=True, title="Monthly Sales Revenue", labels={"month_start": "Month", "sales_revenue": "Revenue"}), width="stretch")
        else:
            st.info("Monthly sales data is unavailable.")
    with right:
        st.subheader("Customer Cluster Distribution")
        cl = find_column(segments, ["cluster", "cluster_id", "segment"])
        if cl:
            counts = segments[cl].astype(str).value_counts().rename_axis("Cluster").reset_index(name="Customers")
            st.plotly_chart(px.bar(counts, x="Cluster", y="Customers", color="Cluster", text_auto=True), width="stretch")
        else:
            st.info("Customer segmentation output is unavailable.")
    st.subheader("Top Products by Revenue")
    if {"stock_code", "sales_revenue"}.issubset(daily_sales.columns):
        top = daily_sales.groupby("stock_code", as_index=False)["sales_revenue"].sum().nlargest(10, "sales_revenue").sort_values("sales_revenue")
        st.plotly_chart(px.bar(top, x="sales_revenue", y="stock_code", orientation="h", text="sales_revenue", labels={"stock_code": "Product Code", "sales_revenue": "Revenue"}), width="stretch")
    else:
        st.info("Product revenue data is unavailable.")
    with st.expander("EDA summary report"):
        show_report("eda_summary.txt")


# --------------------------- Page 2: Sales trend analysis ---------------------------

elif page == "Sales Trend Analysis":
    st.header("Sales Trend Analysis")
    if daily_sales.empty:
        info_if_missing(daily_sales, "Daily product sales")
    else:
        monthly = make_monthly(daily_sales)
        if not monthly.empty:
            st.subheader("Monthly Sales Trend")
            st.plotly_chart(px.line(monthly, x="month_start", y="sales_revenue", markers=True, title="Monthly Revenue", labels={"month_start": "Month", "sales_revenue": "Revenue"}, height=450), width="stretch")
            monthly["year"] = monthly["month_start"].dt.year
            monthly["month"] = monthly["month_start"].dt.strftime("%b")
            pivot = monthly.pivot_table(index="month", columns="year", values="sales_revenue", aggfunc="sum").reset_index()
            st.subheader("Month-by-Year Comparison")
            show_table(pivot, 360)
        else:
            st.info("Required order_date and sales_revenue columns are missing.")
        st.subheader("Daily Revenue Distribution")
        if "sales_revenue" in daily_sales:
            vals = pd.to_numeric(daily_sales["sales_revenue"], errors="coerce").dropna()
            st.plotly_chart(px.histogram(pd.DataFrame({"Revenue per product-day": vals}), x="Revenue per product-day", nbins=40), width="stretch")
        display_revenue_kpis(daily_sales)


# --------------------------- Monthly and seasonal sales ---------------------------

elif page == "Monthly & Seasonal Sales":
    st.header("Monthly & Seasonal Sales Dashboard")
    monthly = make_monthly(daily_sales)
    if monthly.empty:
        info_if_missing(daily_sales, "Monthly sales data")
    else:
        monthly["year"] = monthly["month_start"].dt.year
        monthly["month_number"] = monthly["month_start"].dt.month
        monthly["month_name"] = monthly["month_start"].dt.strftime("%b")
        st.plotly_chart(px.line(monthly, x="month_start", y="sales_revenue", color="year", markers=True,
                                title="Monthly Revenue by Year", labels={"month_start": "Month", "sales_revenue": "Revenue", "year": "Year"}, height=460),
                        width="stretch")
        season = monthly.groupby("month_number", as_index=False)["sales_revenue"].mean()
        season["month_name"] = pd.to_datetime(season["month_number"], format="%m").dt.strftime("%B")
        st.plotly_chart(px.bar(season, x="month_name", y="sales_revenue", title="Average Revenue by Calendar Month",
                               labels={"month_name": "Month", "sales_revenue": "Average Revenue"}),
                        width="stretch")
        show_table(monthly[["month_start", "year", "month_name", "sales_revenue"]], 360)
    st.caption("Seasonality is descriptive historical analysis, not a causal explanation or guarantee of future demand.")


# --------------------------- Page 3: Product performance ---------------------------

elif page == "Product Performance":
    st.header("Product Performance Dashboard")
    if not {"stock_code", "sales_revenue"}.issubset(daily_sales.columns):
        info_if_missing(daily_sales, "Daily product sales")
    else:
        df = daily_sales.copy()
        df["sales_revenue"] = pd.to_numeric(df["sales_revenue"], errors="coerce").fillna(0)
        product = df.groupby("stock_code", as_index=False).agg(sales_revenue=("sales_revenue", "sum"))
        if "units_sold" in df:
            product["units_sold"] = df.groupby("stock_code")["units_sold"].sum().values
        product = product.sort_values("sales_revenue", ascending=False)
        k = st.columns(3)
        k[0].metric("Products", f"{product.stock_code.nunique():,}")
        k[1].metric("Highest Product Revenue", f"{product.sales_revenue.max():,.2f}")
        k[2].metric("Median Product Revenue", f"{product.sales_revenue.median():,.2f}")
        a, b = st.columns(2)
        with a:
            st.plotly_chart(px.bar(product.head(15).sort_values("sales_revenue"), x="sales_revenue", y="stock_code", orientation="h", title="Top 15 Products by Revenue"), width="stretch")
        with b:
            st.plotly_chart(px.histogram(product, x="sales_revenue", nbins=35, title="Product Revenue Distribution"), width="stretch")
        show_table(product, 430)
        add_download("Download product performance", product, "retailpulse_product_performance.csv")


# --------------------------- Page 4: Customer analytics and behaviour ---------------------------

elif page == "Customer Analytics":
    st.header("Customer Analytics Dashboard")
    st.write("Customer-level purchasing patterns, value indicators, and engineered features.")
    if customer_features.empty:
        info_if_missing(customer_features, "Customer features")
    else:
        df = customer_features.copy()
        k = st.columns(4)
        k[0].metric("Customers", f"{len(df):,}")
        for idx, (col, label) in enumerate([
            ("total_spend", "Total Customer Spend"),
            ("invoice_count", "Invoices / Purchases"),
            ("distinct_products", "Distinct Products"),
        ], start=1):
            k[idx].metric(label, f"{pd.to_numeric(df[col], errors='coerce').sum():,.2f}" if col in df else "N/A")
        numeric_cols = [c for c in ["total_spend", "invoice_count", "recency_days", "distinct_products", "average_order_value", "customer_lifetime_days"] if c in df]
        if len(numeric_cols) >= 2:
            a, b = st.columns(2)
            with a:
                x = st.selectbox("Customer chart X-axis", numeric_cols, key="customer_x")
            with b:
                y = st.selectbox("Customer chart Y-axis", [c for c in numeric_cols if c != x], key="customer_y")
            st.plotly_chart(px.scatter(df, x=x, y=y, opacity=.65, title=f"{x} vs {y}", hover_data=[c for c in ["customer_id", "RP_Customer_Value_Band", "RP_Purchase_Recency_Band"] if c in df]), width="stretch")
        st.subheader("Customer Behaviour Bands")
        band_cols = [c for c in df if c.startswith("RP_") and ("Band" in c or "Season" in c)]
        if band_cols:
            chosen_band = st.selectbox("Choose customer behaviour category", band_cols)
            counts = df[chosen_band].fillna("Unknown").astype(str).value_counts().rename_axis("Category").reset_index(name="Customers")
            st.plotly_chart(px.bar(counts, x="Category", y="Customers", color="Category", text_auto=True), width="stretch")
        show_table(df.head(500), 420)
        add_download("Download customer analytics sample (first 500)", df.head(500), "retailpulse_customer_analytics_sample.csv")
        custom = [c for c in df if c.startswith("RP_")]
        if custom:
            with st.expander("Project-engineered customer features"):
                st.caption("RP_ features are project-created. Heuristic scores should not be described as externally validated measures.")
                show_table(df[([ "customer_id"] if "customer_id" in df else []) + custom].head(300))


# --------------------------- Customer behaviour ---------------------------

elif page == "Customer Behaviour":
    st.header("Customer Behaviour Dashboard")
    st.write("Explore recency, purchase frequency, spending, and project-defined customer bands.")
    if customer_features.empty:
        info_if_missing(customer_features, "Customer features")
    else:
        df = customer_features.copy()
        available = [c for c in ["recency_days", "invoice_count", "total_spend", "average_order_value",
                                  "distinct_products", "customer_lifetime_days"] if c in df.columns]
        if available:
            a, b = st.columns(2)
            with a:
                xcol = st.selectbox("Horizontal measure", available, key="behaviour_x")
            with b:
                ycol = st.selectbox("Vertical measure", [c for c in available if c != xcol] or available, key="behaviour_y")
            st.plotly_chart(px.scatter(df, x=xcol, y=ycol, opacity=.65, title=f"Customer Behaviour: {xcol} vs {ycol}",
                                       hover_data=[c for c in ["customer_id", "RP_Customer_Value_Band", "RP_Purchase_Recency_Band"] if c in df]),
                            width="stretch")
        band_cols = [c for c in df if c.startswith("RP_") and ("Band" in c or "Season" in c)]
        if band_cols:
            band = st.selectbox("Behaviour band", band_cols, key="behaviour_band")
            counts = df[band].fillna("Unknown").astype(str).value_counts().rename_axis("Band").reset_index(name="Customers")
            st.plotly_chart(px.bar(counts, x="Band", y="Customers", color="Band", text_auto=True), width="stretch")
        show_table(df.head(500), 400)
        add_download("Download customer behaviour sample", df.head(500), "retailpulse_customer_behaviour.csv")


# --------------------------- Page 5: Country analysis ---------------------------

elif page == "Country Analysis":
    st.header("Region / Country Sales Dashboard")
    if transactions.empty:
        info_if_missing(transactions, "Cleaned transactions")
    elif "country" not in transactions:
        st.info("The cleaned transaction file has no country column.")
    else:
        df = transactions.copy()
        qty = find_column(df, ["quantity"])
        price = find_column(df, ["unit_price", "price"])
        rev = find_column(df, ["line_revenue", "total_price"])
        customer = find_column(df, ["customer_id"])
        cancel = find_column(df, ["is_cancellation_invoice"])
        if rev:
            df[rev] = pd.to_numeric(df[rev], errors="coerce")
            keep = df[rev].notna() & df["country"].notna()
            if qty:
                df[qty] = pd.to_numeric(df[qty], errors="coerce")
                keep &= df[qty] > 0
            if price:
                df[price] = pd.to_numeric(df[price], errors="coerce")
                keep &= df[price] > 0
            if customer:
                keep &= df[customer].notna()
            if cancel:
                keep &= ~df[cancel].astype(str).str.lower().isin(["true", "1", "yes"])
            sales = df.loc[keep].groupby("country", as_index=False)[rev].sum().rename(columns={rev: "sales_revenue"}).sort_values("sales_revenue", ascending=False)
            k = st.columns(3)
            k[0].metric("Countries", f"{sales.country.nunique():,}")
            k[1].metric("Top Country", str(sales.iloc[0]["country"]) if not sales.empty else "N/A")
            k[2].metric("Top Country Revenue", f"{sales.iloc[0]['sales_revenue']:,.2f}" if not sales.empty else "N/A")
            st.plotly_chart(px.bar(sales.head(20).sort_values("sales_revenue"), x="sales_revenue", y="country", orientation="h", title="Top 20 Countries by Standard Sales Revenue"), width="stretch")
            show_table(sales, 420)
            add_download("Download country sales", sales, "retailpulse_country_sales.csv")
        else:
            st.info("A revenue column was not found in the cleaned transaction file.")


# --------------------------- Revenue and profit analysis ---------------------------

elif page == "Profit & Revenue Analysis":
    st.header("Profit & Revenue Analysis")
    st.write("Review available revenue measures and understand which financial measures are missing.")
    if daily_sales.empty or "sales_revenue" not in daily_sales:
        info_if_missing(daily_sales, "Sales revenue data")
    else:
        rev = pd.to_numeric(daily_sales["sales_revenue"], errors="coerce").dropna()
        k = st.columns(3)
        k[0].metric("Recorded Sales Revenue", f"{rev.sum():,.2f}")
        k[1].metric("Average Product-Day Revenue", f"{rev.mean():,.2f}")
        k[2].metric("Maximum Product-Day Revenue", f"{rev.max():,.2f}")
        monthly = make_monthly(daily_sales)
        if not monthly.empty:
            st.plotly_chart(px.area(monthly, x="month_start", y="sales_revenue", title="Historical Revenue Trend",
                                    labels={"month_start": "Month", "sales_revenue": "Revenue"}), width="stretch")
        if {"stock_code", "sales_revenue"}.issubset(daily_sales.columns):
            products = daily_sales.groupby("stock_code", as_index=False)["sales_revenue"].sum().nlargest(15, "sales_revenue")
            st.plotly_chart(px.bar(products.sort_values("sales_revenue"), x="sales_revenue", y="stock_code", orientation="h",
                                   title="Top 15 Products by Revenue", labels={"stock_code": "Product Code", "sales_revenue": "Revenue"},
                                   text="sales_revenue", height=560).update_layout(yaxis={"categoryorder": "total ascending"},
                                   margin={"l": 25, "r": 25, "t": 65, "b": 35}), width="stretch")
    st.caption("Revenue analysis only: verified product cost and margin data are not available in this dataset, so profit metrics are not displayed.")


# --------------------------- Page 6: Customer segmentation ---------------------------

elif page == "Customer Segmentation":
    st.header("Customer Segmentation")
    st.write("Explore K-Means customer clusters and RFM-style profiles.")
    cluster_col = find_column(segments, ["cluster", "cluster_id", "segment"])
    if not segments.empty and cluster_col:
        counts = segments[cluster_col].astype(str).value_counts().rename_axis("Cluster").reset_index(name="Customers")
        a, b = st.columns(2)
        with a:
            st.plotly_chart(px.bar(counts, x="Cluster", y="Customers", color="Cluster", text_auto=True, title="Customers per Cluster"), width="stretch")
        with b:
            st.plotly_chart(px.pie(counts, names="Cluster", values="Customers", hole=.55, title="Cluster Share"), width="stretch")
    else:
        st.info("Customer-level segment output or cluster column is unavailable.")
    st.subheader("Cluster Profiles")
    show_table(cluster_summary)
    if not segments.empty:
        view = segments.copy()
        if cluster_col:
            opts = ["All"] + sorted(view[cluster_col].dropna().astype(str).unique().tolist())
            chosen = st.selectbox("Filter cluster", opts)
            if chosen != "All":
                view = view[view[cluster_col].astype(str) == chosen]
        show_table(view, 420)
        add_download("Download displayed segments", view, "retailpulse_customer_segments.csv")
    st.caption("Cluster IDs are arbitrary; interpret them through the profile metrics rather than treating the ID as a rank.")


# --------------------------- Page 7: Churn ---------------------------

elif page == "Customer Churn":
    st.header("Customer Churn Analysis")
    st.write("Historical churn model evaluation and test-set predictions.")
    report = read_report("model_evaluation_summary.txt")
    if report:
        with st.expander("Churn evaluation details", expanded=True):
            lines = report.splitlines()
            start = next((i for i, line in enumerate(lines) if "1. CUSTOMER CHURN PREDICTION" in line), None)
            end = next((i for i, line in enumerate(lines) if i > (start or 0) and re.match(r"\s*2\.\s+DEMAND FORECASTING", line)), len(lines))
            st.text("\n".join(lines[start:end]) if start is not None else "Churn section not found in consolidated report.")
    if not churn_predictions.empty:
        df = churn_predictions.copy()
        actual = find_column(df, ["actual_churn", "actual", "y_true", "churn"])
        predicted = find_column(df, ["predicted_churn", "prediction", "y_pred"])
        prob = find_column(df, ["churn_probability", "probability", "predicted_probability", "churn_proba"])
        if actual:
            a = df[actual].astype(str).str.strip().str.lower()
            churn_n = int(a.isin(["1", "true", "yes", "churn"]).sum())
            k = st.columns(3)
            k[0].metric("Test Customers", f"{len(df):,}")
            k[1].metric("Actual Churn", f"{churn_n:,}")
            k[2].metric("Actual Active", f"{len(df)-churn_n:,}")
        if actual and predicted:
            matrix = pd.crosstab(df[actual].astype(str), df[predicted].astype(str), rownames=["Actual"], colnames=["Predicted"])
            st.plotly_chart(px.imshow(matrix, text_auto=True, aspect="auto", color_continuous_scale="Blues", title="Churn Confusion Matrix"), width="stretch")
        if prob:
            df[prob] = pd.to_numeric(df[prob], errors="coerce")
            valid = df.dropna(subset=[prob])
            if not valid.empty:
                st.plotly_chart(px.histogram(valid, x=prob, nbins=20, title="Predicted Churn Probability"), width="stretch")
        show_table(df, 420)
        add_download("Download churn test predictions", df, "retailpulse_churn_predictions.csv")
    else:
        st.info("Churn test predictions are unavailable. Run src/models/churn_prediction.py.")
    st.caption("Method note: Churn means no qualifying purchase during the historical three-month observation window; it is not a live churn feed or a guarantee of future behavior.")


# --------------------------- Page 8: Demand forecasting ---------------------------

elif page == "Demand Forecast":
    st.header("Demand Forecasting")
    st.write("Inspect 14-day product forecasts and historical baseline evaluation.")
    if not forecast_evaluation.empty:
        ev = forecast_evaluation.copy()
        model = find_column(ev, ["baseline", "model"])
        mae = find_column(ev, ["mae"])
        rmse = find_column(ev, ["rmse"])
        if model and mae:
            ev[mae] = pd.to_numeric(ev[mae], errors="coerce")
            a, b = st.columns(2)
            with a:
                chart = ev.groupby(model, as_index=False)[mae].mean().sort_values(mae)
                st.plotly_chart(px.bar(chart, x=model, y=mae, color=model, title="Average MAE (lower is better)"), width="stretch")
            with b:
                if rmse:
                    ev[rmse] = pd.to_numeric(ev[rmse], errors="coerce")
                    chart = ev.groupby(model, as_index=False)[rmse].mean().sort_values(rmse)
                    st.plotly_chart(px.bar(chart, x=model, y=rmse, color=model, title="Average RMSE (lower is better)"), width="stretch")
        st.subheader("Evaluation by Product and Baseline")
        show_table(ev, 380)
    else:
        st.info("Forecast evaluation is unavailable. Run src/forecasting/demand_forecasting.py.")
    if not forecasts.empty:
        product = find_column(forecasts, ["stock_code", "product_id", "product"])
        date = find_column(forecasts, ["forecast_date", "date", "ds", "order_date"])
        value = find_column(forecasts, ["predicted_units", "forecast_quantity", "forecast", "predicted_quantity", "prediction", "forecast_units"])
        view = forecasts.copy()
        if product:
            opts = sorted(view[product].dropna().astype(str).unique().tolist())
            if opts:
                chosen = st.selectbox("Select product to inspect", opts)
                view = view[view[product].astype(str) == chosen]
        if date and value:
            view[date] = pd.to_datetime(view[date], errors="coerce")
            view[value] = pd.to_numeric(view[value], errors="coerce")
            view = view.dropna(subset=[date, value]).sort_values(date)
            if not view.empty:
                k = st.columns(3)
                k[0].metric("Forecast Rows / Days", f"{len(view):,}")
                k[1].metric("Forecast Units", f"{view[value].sum():,.1f}")
                k[2].metric("Daily Average", f"{view[value].mean():,.2f}")
                st.plotly_chart(px.line(view, x=date, y=value, markers=True, title="Selected Product Forecast", labels={date: "Forecast Date", value: "Predicted Units"}), width="stretch")
        show_table(view, 380)
        add_download("Download displayed forecasts", view, "retailpulse_demand_forecasts.csv")
    else:
        st.info("Demand forecast output is unavailable.")
    st.caption("The current forecasts are baseline estimates. Evaluation-period selection means these metrics are not an untouched final test.")


# --------------------------- Page 9: Inventory planning ---------------------------

elif page == "Inventory Planning":
    st.header("Inventory Planning")
    st.write("Review forecast-based replenishment estimates.")
    if inventory.empty:
        info_if_missing(inventory, "Inventory recommendations")
    else:
        stock = find_column(inventory, ["stock_code", "product_id", "product"])
        status = find_column(inventory, ["planning_status", "status"])
        replen = find_column(inventory, ["suggested_replenishment_units", "replenishment_units"])
        reorder = find_column(inventory, ["reorder_point"])
        units = pd.to_numeric(inventory[replen], errors="coerce").fillna(0) if replen else pd.Series(dtype=float)
        k = st.columns(3)
        k[0].metric("Products Planned", f"{len(inventory):,}")
        k[1].metric("Suggested Replenishment Units", f"{units.sum():,.0f}" if replen else "N/A")
        k[2].metric("Products with Positive Suggested Restock", f"{int((units > 0).sum()):,}" if replen else "N/A")
        if status:
            counts = inventory[status].fillna("Unknown").astype(str).value_counts().rename_axis("Status").reset_index(name="Products")
            st.plotly_chart(px.bar(counts, x="Status", y="Products", color="Status", text_auto=True, title="Products by Planning Status"), width="stretch")
        if stock and replen:
            chart = inventory.copy()
            chart[replen] = pd.to_numeric(chart[replen], errors="coerce")
            chart = chart.dropna(subset=[replen]).nlargest(15, replen).sort_values(replen)
            st.plotly_chart(px.bar(chart, x=replen, y=stock, orientation="h", title="Suggested Replenishment by Product"), width="stretch")
        show_table(inventory, 420)
        add_download("Download inventory recommendations", inventory, "retailpulse_inventory_recommendations.csv")
        with st.expander("Inventory planning summary"):
            show_report("inventory_planning_summary.txt")
    st.caption("Planning note: Stock on hand, lead time, and safety stock are project assumptions, not verified warehouse records. Validate them before purchasing.")


# --------------------------- Page 10: Inventory risk ---------------------------

elif page == "Inventory Risk":
    st.header("Inventory Risk Dashboard")
    st.write("Prioritize products for review using forecast-based replenishment indicators.")
    if inventory.empty:
        info_if_missing(inventory, "Inventory recommendations")
    else:
        df = inventory.copy()
        reorder = find_column(df, ["reorder_point"])
        onhand = find_column(df, ["assumed_stock_on_hand", "stock_on_hand", "available_stock"])
        replenish = find_column(df, ["suggested_replenishment_units", "replenishment_units"])
        product = find_column(df, ["stock_code", "product_id", "product"])
        if replenish:
            df[replenish] = pd.to_numeric(df[replenish], errors="coerce").fillna(0)
            k = st.columns(3)
            k[0].metric("Products Under Review", f"{len(df):,}")
            k[1].metric("Positive Replenishment Suggestions", f"{int((df[replenish] > 0).sum()):,}")
            k[2].metric("Total Suggested Units", f"{df[replenish].sum():,.0f}")
        if reorder and onhand:
            df[reorder] = pd.to_numeric(df[reorder], errors="coerce")
            df[onhand] = pd.to_numeric(df[onhand], errors="coerce")
            df["risk_gap_units"] = df[reorder] - df[onhand]
            df["risk_indicator"] = df["risk_gap_units"].apply(lambda x: "Review — below reorder point" if pd.notna(x) and x > 0 else "At/above assumed reorder point")
            st.plotly_chart(px.bar(df.sort_values("risk_gap_units", ascending=False), x="risk_gap_units", y=product if product else df.index, orientation="h", color="risk_indicator", title="Gap to Reorder Point (assumption-based)"), width="stretch")
            show_table(df.sort_values("risk_gap_units", ascending=False), 400)
        else:
            st.info("The current file lacks both reorder point and assumed stock-on-hand fields needed for a gap calculation.")
            show_table(df, 400)
    st.caption("This page indicates planning risks from assumptions, not real-time stock-outs or live warehouse monitoring.")


# --------------------------- Page 11: Orders and transactions ---------------------------

elif page == "Orders & Transactions":
    st.header("Order & Transaction Dashboard")
    if transactions.empty:
        info_if_missing(transactions, "Cleaned transaction dataset")
    else:
        df = transactions.copy()
        date_col = find_column(df, ["invoice_date", "order_date", "date"])
        invoice_col = find_column(df, ["invoice", "invoice_no", "invoice_number"])
        qty_col = find_column(df, ["quantity"])
        price_col = find_column(df, ["unit_price", "price"])
        type_col = find_column(df, ["transaction_type"])
        revenue_col = find_column(df, ["total_price", "line_revenue", "sales_revenue"])
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        k = st.columns(4)
        k[0].metric("Transaction Rows", f"{len(df):,}")
        k[1].metric("Unique Invoices", f"{df[invoice_col].nunique():,}" if invoice_col else "N/A")
        k[2].metric("Cancellation Rows", f"{df[find_column(df, ['is_cancellation_invoice'])].astype(str).str.lower().isin(['true','1','yes']).sum():,}" if find_column(df, ["is_cancellation_invoice"]) else "N/A")
        k[3].metric("Transaction Types", f"{df[type_col].nunique():,}" if type_col else "N/A")
        if type_col:
            counts = df[type_col].fillna("Unknown").astype(str).value_counts().rename_axis("Transaction Type").reset_index(name="Rows")
            st.plotly_chart(px.bar(counts, x="Transaction Type", y="Rows", color="Transaction Type", text_auto=True, title="Transaction Types"), width="stretch")
        if date_col:
            dated = df.dropna(subset=[date_col]).copy()
            if not dated.empty:
                dated["month_start"] = dated[date_col].dt.to_period("M").dt.to_timestamp()
                count_col = invoice_col if invoice_col else date_col
                monthly = dated.groupby("month_start").agg(transaction_rows=(count_col, "count")).reset_index()
                st.plotly_chart(px.line(monthly, x="month_start", y="transaction_rows", markers=True, title="Monthly Transaction Rows"), width="stretch")
        if qty_col and price_col:
            df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce")
            df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
            st.caption("Quantity and unit price include returns/cancellations where present; interpret signed or unusual values carefully.")
        if revenue_col:
            df[revenue_col] = pd.to_numeric(df[revenue_col], errors="coerce")
        show_table(df.head(1000), 420)
        add_download("Download filtered transaction sample (first 1,000)", df.head(1000), "retailpulse_transaction_sample.csv")


# --------------------------- Advanced analytics: dedicated pages ---------------------------

elif page == "Customer Features":
    st.header("Customer Features Dashboard")
    st.write("Explore engineered customer profiles, purchase patterns, value bands, and the project-defined loyalty heuristic.")
    if customer_features.empty:
        info_if_missing(customer_features, "Customer features")
    else:
        df = customer_features.copy()
        customer_col = find_column(df, ["customer_id"])
        season_col = find_column(df, ["RP_Purchase_Season"])
        recency_col = find_column(df, ["RP_Purchase_Recency_Band"])
        value_col = find_column(df, ["RP_Customer_Value_Band"])
        diversity_col = find_column(df, ["RP_Product_Diversity_Band"])
        loyalty_col = find_column(df, ["RP_Customer_Loyalty_Index"])
        spend_col = find_column(df, ["total_spend", "monetary", "total_revenue"])
        invoice_col = find_column(df, ["invoice_count", "frequency"])
        kpis = st.columns(4)
        kpis[0].metric("Customers Profiled", f"{len(df):,}")
        if spend_col:
            kpis[1].metric("Total Customer Spend", f"{pd.to_numeric(df[spend_col], errors='coerce').sum():,.2f}")
        if invoice_col:
            kpis[2].metric("Average Invoices / Customer", f"{pd.to_numeric(df[invoice_col], errors='coerce').mean():,.2f}")
        if loyalty_col:
            kpis[3].metric("Average Loyalty Index", f"{pd.to_numeric(df[loyalty_col], errors='coerce').mean():,.1f}")
        # Balanced 2-by-2 chart grid avoids the large blank area caused by
        # stacking two charts in one column while the other column has one.
        top_left, top_right = st.columns(2)
        with top_left:
            if value_col:
                band = df[value_col].fillna("Unknown").astype(str).value_counts().rename_axis("Customer Value Band").reset_index(name="Customers")
                fig = px.bar(band, x="Customer Value Band", y="Customers", color="Customer Value Band",
                    text="Customers", title="Customer Value Distribution", height=360)
                fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=60, b=35))
                st.plotly_chart(fig, width="stretch")
            elif season_col:
                season = df[season_col].fillna("Unknown").astype(str).value_counts().rename_axis("Purchase Season").reset_index(name="Customers")
                fig = px.bar(season, x="Purchase Season", y="Customers", text="Customers", title="Customer Purchase Season", height=360)
                fig.update_layout(margin=dict(l=20, r=20, t=60, b=35))
                st.plotly_chart(fig, width="stretch")
        with top_right:
            if recency_col:
                rec = df[recency_col].fillna("Unknown").astype(str).value_counts().rename_axis("Recency Band").reset_index(name="Customers")
                fig = px.bar(rec, x="Recency Band", y="Customers", color="Recency Band", text="Customers",
                    title="Customer Recency Bands", height=360)
                fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=60, b=35))
                st.plotly_chart(fig, width="stretch")
        bottom_left, bottom_right = st.columns(2)
        with bottom_left:
            if loyalty_col:
                loyalty = pd.to_numeric(df[loyalty_col], errors="coerce").dropna()
                fig = px.histogram(pd.DataFrame({"Loyalty Index": loyalty}), x="Loyalty Index", nbins=20,
                    title="Loyalty Index Distribution", height=360)
                fig.update_layout(margin=dict(l=20, r=20, t=60, b=35))
                st.plotly_chart(fig, width="stretch")
        with bottom_right:
            if diversity_col:
                diversity = df[diversity_col].fillna("Unknown").astype(str).value_counts().rename_axis("Product Diversity Band").reset_index(name="Customers")
                fig = px.bar(diversity, x="Product Diversity Band", y="Customers", color="Product Diversity Band",
                    text="Customers", title="Product Diversity Distribution", height=360)
                fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=60, b=35))
                st.plotly_chart(fig, width="stretch")
            elif season_col:
                season = df[season_col].fillna("Unknown").astype(str).value_counts().rename_axis("Purchase Season").reset_index(name="Customers")
                fig = px.bar(season, x="Purchase Season", y="Customers", text="Customers", title="Purchase Season Distribution", height=360)
                fig.update_layout(margin=dict(l=20, r=20, t=60, b=35))
                st.plotly_chart(fig, width="stretch")
        if season_col and value_col:
            cross = df.groupby([season_col, value_col], dropna=False).size().reset_index(name="Customers")
            st.plotly_chart(px.density_heatmap(cross, x=season_col, y=value_col, z="Customers",
                histfunc="sum", title="Purchase Season vs Customer Value", height=440), width="stretch")
        st.caption("RP_ fields are engineered project features; the loyalty index is a heuristic, not a verified business measurement.")
        chosen_cols = ([customer_col] if customer_col else []) + [c for c in df.columns if c.startswith("RP_")]
        show_table(df[chosen_cols].head(1000) if chosen_cols else df.head(500), 380)
        add_download("Download customer features", df, "retailpulse_customer_features.csv")


elif page == "Forecast Evaluation":
    st.header("Forecast Evaluation Dashboard")
    st.write("Compare the available product-level forecasting evaluation metrics. Lower MAE and RMSE indicate smaller forecast errors.")
    if forecast_evaluation.empty:
        info_if_missing(forecast_evaluation, "Forecast evaluation")
    else:
        df = forecast_evaluation.copy()
        # Convert only columns that are genuinely numeric; pandas no longer supports errors="ignore".
        for col in df.columns:
            if col.lower() not in {"stock_code", "product", "product_code", "selected_model", "model"}:
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().sum() > 0:
                    df[col] = converted
        metric_cols = [c for c in df.columns if any(term in c.lower() for term in ["mae", "rmse", "mape", "wape"])]
        product_col = find_column(df, ["stock_code", "product_code", "product"])
        available_kpis = 2 + int("selected_model" in df) + int(bool(metric_cols))
        kpis = st.columns(max(1, available_kpis))
        kpis[0].metric("Products Evaluated", f"{len(df):,}")
        kpi_idx = 1
        if "selected_model" in df:
            kpis[kpi_idx].metric("Forecast Methods", f"{df['selected_model'].nunique():,}")
            kpi_idx += 1
        if metric_cols:
            first_metric = metric_cols[0]
            kpis[kpi_idx].metric(f"Mean {first_metric.upper()}", f"{pd.to_numeric(df[first_metric], errors='coerce').mean():,.2f}")
        if metric_cols:
            numeric_df = df.copy()
            for col in metric_cols:
                numeric_df[col] = pd.to_numeric(numeric_df[col], errors="coerce")
            if product_col:
                # Product codes are identifiers, not continuous numeric values.
                # Treat them as categories and use horizontal bars for readable labels.
                numeric_df[product_col] = numeric_df[product_col].astype(str)
                show_col = metric_cols[:2]
                plot_df = numeric_df[[product_col] + show_col].dropna(subset=show_col, how="all").copy()
                if not plot_df.empty:
                    plot_df = plot_df.head(15)
                    metric_long = plot_df.melt(id_vars=product_col, value_vars=show_col, var_name="Metric", value_name="Error")
                    fig = px.bar(metric_long, x="Error", y=product_col, color="Metric", barmode="group", orientation="h",
                        title="Forecast Error by Product (up to 15 products)", height=max(420, 30 * len(plot_df) + 140),
                        labels={product_col: "Product Code", "Error": "Forecast Error"})
                    fig.update_layout(yaxis={"type": "category", "categoryorder": "total ascending"},
                        margin=dict(l=25, r=25, t=65, b=35), legend_title_text="Error Metric")
                    st.plotly_chart(fig, width="stretch")
            if len(metric_cols) >= 2:
                compare = numeric_df[metric_cols].mean().rename_axis("Metric").reset_index(name="Mean Error")
                fig = px.bar(compare, x="Metric", y="Mean Error", color="Metric", text_auto=".2f",
                    title="Average Forecast Error by Metric", height=330)
                fig.update_layout(showlegend=False, margin=dict(l=25, r=25, t=60, b=35))
                st.plotly_chart(fig, width="stretch")
        else:
            st.info("No recognizable MAE/RMSE-style columns were found. The evaluation table is shown below.")
        show_table(df, 400)
        add_download("Download forecast evaluation", df, "retailpulse_forecast_evaluation.csv")
    st.caption("Historical baseline evaluation is not an untouched final test set; interpret results as a project comparison, not a guarantee of future accuracy.")


elif page == "Product Demand":
    st.header("Product Demand Dashboard")
    st.write("Explore product-level units and revenue from the daily product sales dataset.")
    if daily_sales.empty:
        info_if_missing(daily_sales, "Daily product sales")
    else:
        df = daily_sales.copy()
        for col in ["units_sold", "sales_revenue", "invoice_count"]:
            if col in df:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        product_col = find_column(df, ["stock_code", "product_code", "product"])
        if not product_col:
            st.warning("A product code column is required for product-level demand charts.")
            show_table(df.head(500), 350)
        else:
            agg = {c: "sum" for c in ["units_sold", "sales_revenue", "invoice_count"] if c in df}
            product = df.groupby(product_col, as_index=False).agg(agg) if agg else df[[product_col]].drop_duplicates()
            kpis = st.columns(4)
            kpis[0].metric("Products", f"{product[product_col].nunique():,}")
            if "units_sold" in product:
                kpis[1].metric("Units Sold (net)", f"{product['units_sold'].sum():,.0f}")
            if "sales_revenue" in product:
                kpis[2].metric("Recorded Revenue", f"{product['sales_revenue'].sum():,.2f}")
            if "invoice_count" in product:
                kpis[3].metric("Product-Day Invoice Count", f"{product['invoice_count'].sum():,.0f}")
            left, right = st.columns(2)
            with left:
                if "units_sold" in product:
                    top_units = product.nlargest(15, "units_sold").sort_values("units_sold")
                    st.plotly_chart(px.bar(top_units, x="units_sold", y=product_col, orientation="h",
                        title="Top 15 Products by Units Sold", labels={product_col: "Product Code", "units_sold": "Units Sold"},
                        text="units_sold", height=560), width="stretch")
            with right:
                if "sales_revenue" in product:
                    top_rev = product.nlargest(15, "sales_revenue").sort_values("sales_revenue")
                    st.plotly_chart(px.bar(top_rev, x="sales_revenue", y=product_col, orientation="h",
                        title="Top 15 Products by Revenue", labels={product_col: "Product Code", "sales_revenue": "Revenue"},
                        text="sales_revenue", height=560), width="stretch")
            date_col = find_column(df, ["order_date", "invoice_date", "date"])
            if date_col and "units_sold" in df:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                trend = df.dropna(subset=[date_col]).groupby(pd.Grouper(key=date_col, freq="MS"), as_index=False)["units_sold"].sum()
                st.plotly_chart(px.line(trend, x=date_col, y="units_sold", markers=True,
                    title="Monthly Units Sold Trend", labels={date_col: "Month", "units_sold": "Units Sold"}, height=430),
                    width="stretch")
            show_table(product.sort_values("sales_revenue", ascending=False).head(100) if "sales_revenue" in product else product.head(100), 400)
            add_download("Download product demand summary", product, "retailpulse_product_demand.csv")


# --------------------------- Page 13: Interactive filters ---------------------------

elif page == "Interactive Filters":
    st.header("Interactive Filter Dashboard")
    st.write("Filter the available transaction data by date, country, product, and transaction type.")
    if transactions.empty:
        info_if_missing(transactions, "Cleaned transaction dataset")
    else:
        df = transactions.copy()
        date_col = find_column(df, ["invoice_date", "order_date", "date"])
        country_col = find_column(df, ["country"])
        product_col = find_column(df, ["stock_code", "product_id", "product"])
        type_col = find_column(df, ["transaction_type"])
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        if country_col:
            country_options = ["All"] + sorted(df[country_col].dropna().astype(str).unique().tolist())
            chosen_country = st.selectbox("Country", country_options)
            if chosen_country != "All":
                df = df[df[country_col].astype(str) == chosen_country]
        if product_col:
            product_options = ["All"] + sorted(df[product_col].dropna().astype(str).unique().tolist())
            chosen_product = st.selectbox("Product code", product_options)
            if chosen_product != "All":
                df = df[df[product_col].astype(str) == chosen_product]
        if type_col:
            type_options = ["All"] + sorted(df[type_col].dropna().astype(str).unique().tolist())
            chosen_type = st.selectbox("Transaction type", type_options)
            if chosen_type != "All":
                df = df[df[type_col].astype(str) == chosen_type]
        if date_col and df[date_col].notna().any():
            min_date = df[date_col].min().date()
            max_date = df[date_col].max().date()
            date_range = st.date_input("Invoice date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
                df = df[(df[date_col] >= start) & (df[date_col] < end)]
        k = st.columns(3)
        k[0].metric("Filtered Rows", f"{len(df):,}")
        k[1].metric("Unique Customers", f"{df['customer_id'].nunique():,}" if "customer_id" in df else "N/A")
        rev_col = find_column(df, ["line_revenue", "total_price"])
        k[2].metric("Signed Revenue / Value", f"{pd.to_numeric(df[rev_col], errors='coerce').sum():,.2f}" if rev_col else "N/A")
        show_table(df.head(1000), 420)
        add_download("Download filtered transaction sample", df.head(1000), "retailpulse_filtered_transactions.csv")
        st.caption("Filters apply to this page's transaction view; they do not silently change other pages.")


# --------------------------- Page 14: Monitoring ---------------------------

elif page == "Monitoring":
    st.header("RetailPulse Pipeline Monitoring")
    st.write("Check whether expected data outputs and reports exist. This is file-status monitoring, not live infrastructure monitoring.")
    expected_data = [
        "retail_transactions_cleaned.csv.gz",
        "customer_features.csv",
        "daily_product_sales.csv",
        "customer_rfm_segments.csv",
        "churn_test_predictions.csv",
        "forecast_evaluation.csv",
        "demand_forecasts.csv",
        "forecast_excluded_products.csv",
        "inventory_recommendations.csv",
    ]
    expected_reports = [
        "dataset_profile.txt",
        "cleaning_summary.txt",
        "eda_summary.txt",
        "feature_engineering_summary.txt",
        "demand_forecasting_summary.txt",
        "inventory_planning_summary.txt",
        "model_evaluation_summary.txt",
    ]
    rows = []
    for name in expected_data:
        path = DATA_DIR / name
        rows.append({"Type": "Data", "File": name, "Status": "Available" if path.exists() else "Missing", "Size (MB)": round(path.stat().st_size / (1024 * 1024), 2) if path.exists() else None})
    for name in expected_reports:
        path = REPORT_DIR / name
        rows.append({"Type": "Report", "File": name, "Status": "Available" if path.exists() else "Missing", "Size (MB)": round(path.stat().st_size / (1024 * 1024), 2) if path.exists() else None})
    status_df = pd.DataFrame(rows)
    available = int((status_df["Status"] == "Available").sum())
    k = st.columns(3)
    k[0].metric("Expected Outputs", f"{len(status_df):,}")
    k[1].metric("Available", f"{available:,}")
    k[2].metric("Missing", f"{len(status_df)-available:,}")
    st.plotly_chart(px.pie(status_df, names="Status", hole=.55, title="Pipeline Output Availability"), width="stretch")
    show_table(status_df, 420)
    if (status_df["Status"] == "Missing").any():
        st.warning("Some expected files are missing. Run the relevant pipeline steps to regenerate them.")
    else:
        st.success("All files in this checklist are present.")
    if st.button("Clear cache and re-check files"):
        st.cache_data.clear()
        st.rerun()


# --------------------------- Page 15: Business insights ---------------------------

elif page == "Business Insights":
    st.header("Business Insights")
    st.write("Evidence-based observations calculated from the available project outputs.")
    insights = []
    monthly = make_monthly(daily_sales)
    if not monthly.empty:
        best = monthly.loc[monthly["sales_revenue"].idxmax()]
        worst = monthly.loc[monthly["sales_revenue"].idxmin()]
        insights.append(("Peak revenue month", f"{best['month_start']:%B %Y}: {best['sales_revenue']:,.2f} in standard sales revenue."))
        insights.append(("Lowest revenue month", f"{worst['month_start']:%B %Y}: {worst['sales_revenue']:,.2f} in standard sales revenue."))
    if not daily_sales.empty and {"stock_code", "sales_revenue"}.issubset(daily_sales.columns):
        top = daily_sales.groupby("stock_code")["sales_revenue"].sum().sort_values(ascending=False)
        if not top.empty:
            insights.append(("Highest-revenue product", f"Product {top.index[0]} has recorded sales revenue of {top.iloc[0]:,.2f} in the processed daily sales table."))
    if not cluster_summary.empty:
        customer_col = find_column(cluster_summary, ["customers"])
        cluster_col = find_column(cluster_summary, ["cluster"])
        if customer_col and cluster_col:
            tmp = cluster_summary.copy()
            tmp[customer_col] = pd.to_numeric(tmp[customer_col], errors="coerce")
            largest = tmp.loc[tmp[customer_col].idxmax()]
            insights.append(("Largest customer cluster", f"Cluster {largest[cluster_col]} contains {int(largest[customer_col]):,} customers. Cluster IDs are arbitrary."))
    if not forecast_evaluation.empty:
        model = find_column(forecast_evaluation, ["baseline", "model"])
        mae = find_column(forecast_evaluation, ["mae"])
        if model and mae:
            tmp = forecast_evaluation.copy()
            tmp[mae] = pd.to_numeric(tmp[mae], errors="coerce")
            compare = tmp.groupby(model)[mae].mean().dropna().sort_values()
            if not compare.empty:
                insights.append(("Lowest average forecast MAE", f"{compare.index[0]} has the lowest mean MAE ({compare.iloc[0]:,.3f}) among the evaluated baselines."))
    if not inventory.empty:
        replen = find_column(inventory, ["suggested_replenishment_units"])
        if replen:
            total = pd.to_numeric(inventory[replen], errors="coerce").fillna(0).sum()
            insights.append(("Planning quantity", f"The current inventory plan suggests {total:,.0f} replenishment units across the selected products, based on assumed stock and lead times."))
    if insights:
        for title, body in insights:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.write(body)
    else:
        st.info("Business insights will appear when the corresponding data outputs are available.")
    st.subheader("Recommended follow-up actions")
    st.markdown("""
- Validate the high-level sales pattern with the business owner before using it for decisions.
- Review the largest customer clusters and design separate retention approaches for each profile.
- Prioritize churn outreach based on the model's predicted risk only after validating on a later time period.
- Verify actual on-hand stock, supplier lead times, and stock constraints before placing replenishment orders.
- Improve forecast evaluation with an untouched chronological test period.
""")


# --------------------------- Page 16: Model evaluation and notes ---------------------------

elif page == "Model Evaluation & Notes":
    st.header("Model Evaluation & Project Notes")
    report = read_report("model_evaluation_summary.txt")
    if report:
        st.subheader("Consolidated Evaluation Report")
        st.text(report)
    else:
        st.info("Consolidated evaluation report is unavailable. Run src/models/evaluate_models.py.")
    st.subheader("Forecast baseline comparison")
    if not forecast_evaluation.empty:
        model = find_column(forecast_evaluation, ["baseline", "model"])
        mae = find_column(forecast_evaluation, ["mae"])
        rmse = find_column(forecast_evaluation, ["rmse"])
        if model and mae:
            ev = forecast_evaluation.copy()
            ev[mae] = pd.to_numeric(ev[mae], errors="coerce")
            summary = ev.groupby(model, as_index=False)[mae].mean().sort_values(mae)
            st.plotly_chart(px.bar(summary, x=model, y=mae, title="Mean Absolute Error by Baseline (lower is better)"), width="stretch")
            if rmse:
                ev[rmse] = pd.to_numeric(ev[rmse], errors="coerce")
                summary_rmse = ev.groupby(model, as_index=False)[rmse].mean().sort_values(rmse)
                st.plotly_chart(px.bar(summary_rmse, x=model, y=rmse, title="Root Mean Squared Error by Baseline (lower is better)"), width="stretch")
    st.subheader("Project capabilities and data notes")
    capabilities = pd.DataFrame([
        ("Sales analysis", "Monthly sales trends and product performance from processed positive sales"),
        ("Customer analytics", "Customer-level RFM-style features and project-defined customer bands"),
        ("Customer segmentation", "K-Means clusters with descriptive cluster profiles"),
        ("Churn prediction", "Historical classification experiment with held-out test predictions"),
        ("Demand forecasting", "Baseline forecasts for selected products over 14 days"),
        ("Inventory planning", "Assumption-based reorder point and replenishment estimates"),
        ("Monitoring", "Presence check for generated data and report files"),
    ], columns=["Capability", "Description"])
    show_table(capabilities, 300)
    st.markdown("""
**Dataset:** UCI Online Retail II historical transaction data.

**Limitations**
- Historical data does not represent live retail activity.
- Cluster IDs are arbitrary labels, not a ranking.
- Churn uses a defined historical observation window and excludes customers first appearing after the feature window.
- Forecast evaluation-period selection means reported baseline metrics are not an untouched final test.
- Inventory recommendations use assumed stock and lead-time values, not verified warehouse records.
- The source dataset does not provide verified product cost or margin data, so profit cannot be calculated reliably.
- Do not describe these results as production performance without further validation.
""")
    st.markdown("Dataset source: [UCI Machine Learning Repository — Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)")


st.divider()
st.caption("RetailPulse | AI-Powered Customer Analytics & Demand Forecasting | Historical analytics — validate before business use.")