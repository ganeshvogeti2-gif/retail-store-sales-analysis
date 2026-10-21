import base64
import html
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Retail Store Sales Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------- Styling ---------------------------
st.markdown(
    """
    <style>
    :root { color-scheme: dark; }
    .stApp { background: #0b1120; color: #e8eef8; }
    [data-testid="stSidebar"] { background: #101b2e; border-right: 1px solid #223653; }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #14243a, #101b2e);
        padding: 18px 20px; border-radius: 14px;
        border: 1px solid #294365;
    }
    [data-testid="stMetricLabel"] { color: #a9bdd7; }
    [data-testid="stMetricValue"] { color: #f5f9ff; }
    .hero {
        padding: 1.35rem 1.5rem; border-radius: 16px;
        background: linear-gradient(120deg, #102544, #123c67);
        border: 1px solid #2a527d; margin-bottom: 1rem;
    }
    .dashboard-label { margin: 0 0 .65rem 0; color: #c5d7ee; font-size: 1.15rem; font-weight: 700; letter-spacing: .02em; }
    .hero h1 { margin: 0 0 .35rem 0; color: #ffffff; }
    .hero p { margin: 0; color: #c5d7ee; }
    .small-note { color: #9fb4ce; font-size: .9rem; }
    div[data-testid="stDataFrame"] { border: 1px solid #243b59; border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="dashboard-label">Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero"><h1>📊 Retail Store Sales Analysis</h1>'
    '<p>Interactive business intelligence dashboard · Clean, explore, analyze and export retail data</p></div>',
    unsafe_allow_html=True,
)

# --------------------------- Data helpers ---------------------------
REQUIRED_CORE = ["Quantity", "Price Per Unit", "Total Spent"]
DATE_CANDIDATES = ["Transaction Date", "Date", "Order Date", "Purchase Date"]
CATEGORY_CANDIDATES = ["Category", "Product Category", "Item Category"]
ITEM_CANDIDATES = ["Item", "Product", "Product Name"]
PAYMENT_CANDIDATES = ["Payment Method", "Payment Type", "Payment"]
CUSTOMER_CANDIDATES = ["Customer ID", "Customer", "Customer Name", "Customer ID/Name"]
CHANNEL_CANDIDATES = ["Channel", "Sales Channel", "Store Type"]


def first_matching(columns, candidates):
    lookup = {str(c).strip().lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def money(value):
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


def standalone_html(title, body):
    page = f"""<!doctype html><html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <style>
    body{{margin:0;padding:24px;background:#0b1120;color:#e8eef8;font-family:Arial,sans-serif}}
    h1{{color:#fff}} .wrap{{max-width:1400px;margin:auto}}
    table{{border-collapse:collapse;width:100%;font-size:14px;background:#101b2e}}
    th,td{{border:1px solid #294365;padding:9px;text-align:left}}
    th{{background:#16365b;color:#fff;position:sticky;top:0}}
    tr:nth-child(even){{background:#132239}}
    .note{{color:#a9bdd7}}
    </style></head><body><div class="wrap"><h1>{html.escape(title)}</h1>{body}</div></body></html>"""
    return page


def open_new_tab_link(label, title, body):
    # Data URLs keep the generated full view self-contained and do not require a server file.
    page = standalone_html(title, body)
    encoded = base64.b64encode(page.encode("utf-8")).decode("ascii")
    st.markdown(
        f'<a href="data:text/html;base64,{encoded}" target="_blank" rel="noopener" '
        'style="display:inline-block;background:#1d65ad;color:white;padding:9px 14px;'
        'border-radius:8px;text-decoration:none;font-weight:600;border:1px solid #4a8ac7;">'
        f'{html.escape(label)} ↗</a>',
        unsafe_allow_html=True,
    )


def show_table(title, frame, preview_rows=10, key_prefix="table"):
    # Keep the page compact: show at most 10 rows, with the remainder available separately.
    st.markdown(
        f'<h3 title="{html.escape(str(title))} · {len(frame):,} rows total">{html.escape(str(title))}</h3>',
        unsafe_allow_html=True,
    )
    if len(frame) <= 10:
        st.dataframe(frame, use_container_width=True, hide_index=True)
    else:
        st.dataframe(frame.head(10), use_container_width=True, hide_index=True)
        remaining = frame.iloc[10:]
        table_html = remaining.to_html(index=False, escape=True, border=0)
        open_new_tab_link("View remaining data in a new tab", f"{title} — remaining data", table_html)


def show_plot(title, fig, row_count=None):
    st.markdown(
        f'<h3 title="{html.escape(str(title))}">{html.escape(str(title))}</h3>',
        unsafe_allow_html=True,
    )
    # Disable hover popups/highlight data across chart types.
    fig.update_layout(hovermode=False)
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{title}")


def infer_date_column(frame):
    return first_matching(frame.columns, DATE_CANDIDATES)


def clean_data(raw):
    cleaned = raw.copy()
    original_rows = len(cleaned)
    original_duplicates = int(cleaned.duplicated().sum())
    cleaned = cleaned.drop_duplicates().copy()

    date_col = infer_date_column(cleaned)
    if date_col:
        cleaned[date_col] = pd.to_datetime(cleaned[date_col], errors="coerce")

    numeric_cols = [
        c for c in cleaned.columns
        if any(token in str(c).lower() for token in ["quantity", "price", "spent", "sales", "revenue", "amount", "discount"])
    ]
    for col in numeric_cols:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    # Recalculate Total Spent where quantity and unit price are available.
    qty_col = first_matching(cleaned.columns, ["Quantity", "Qty", "Units Sold"])
    price_col = first_matching(cleaned.columns, ["Price Per Unit", "Unit Price", "Price"])
    total_col = first_matching(cleaned.columns, ["Total Spent", "Total Sales", "Revenue", "Sales", "Amount"])
    if qty_col and price_col and total_col:
        missing_total = cleaned[total_col].isna() & cleaned[qty_col].notna() & cleaned[price_col].notna()
        cleaned.loc[missing_total, total_col] = cleaned.loc[missing_total, qty_col] * cleaned.loc[missing_total, price_col]

    # Fill numeric missing values with median; categorical values with mode, leaving all-empty columns unchanged.
    for col in cleaned.columns:
        if cleaned[col].isna().any():
            if pd.api.types.is_numeric_dtype(cleaned[col]):
                median = cleaned[col].median()
                if pd.notna(median):
                    cleaned[col] = cleaned[col].fillna(median)
            else:
                modes = cleaned[col].mode(dropna=True)
                if not modes.empty:
                    cleaned[col] = cleaned[col].fillna(modes.iloc[0])

    before_dropna = len(cleaned)
    cleaned = cleaned.dropna(how="all").copy()
    report = {
        "rows_before": original_rows,
        "rows_after": len(cleaned),
        "duplicates_removed": original_duplicates,
        "rows_removed": original_rows - len(cleaned),
        "date_column": date_col,
        "numeric_columns_converted": numeric_cols,
        "all_null_rows_removed": before_dropna - len(cleaned),
    }
    return cleaned, report


def make_demo_data():
    dates = pd.date_range("2025-01-01", periods=30, freq="D")
    items = ["Rice", "Milk", "Shirt", "Jeans", "Headphones", "Notebook"]
    categories = {
        "Rice": "Food", "Milk": "Food", "Shirt": "Clothing",
        "Jeans": "Clothing", "Headphones": "Electronics", "Notebook": "Stationery"
    }
    prices = {"Rice": 10.0, "Milk": 4.0, "Shirt": 25.0, "Jeans": 30.0, "Headphones": 80.0, "Notebook": 3.0}
    rows = []
    for i, date in enumerate(dates):
        item = items[i % len(items)]
        qty = (i % 5) + 1
        rows.append({
            "Transaction Date": date,
            "Transaction ID": f"T{i+1:04d}",
            "Customer ID": f"C{(i % 12)+1:03d}",
            "Item": item,
            "Category": categories[item],
            "Quantity": qty,
            "Price Per Unit": prices[item],
            "Total Spent": qty * prices[item],
            "Payment Method": ["Cash", "Card", "UPI"][i % 3],
            "Channel": ["In-store", "Online"][i % 2],
        })
    return pd.DataFrame(rows)


# --------------------------- Data source ---------------------------
with st.sidebar:
    st.markdown("## Navigation")
    page = st.radio(
        "Choose a section",
        [
            "Executive Overview", "Sales Trends", "Product & Category Analysis",
            "Customer Analysis", "Payment Analysis", "Exploratory Data Analysis",
            "Data Quality & Cleaning", "Data Explorer", "Reports & Downloads",
            "Project Information",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    uploaded = st.file_uploader("Upload retail CSV", type=["csv"])
    use_demo = st.toggle("Use demo data when no CSV is uploaded", value=True)
    st.caption("CSV files are processed for this app session.")

if uploaded is not None:
    try:
        raw_df = pd.read_csv(uploaded)
        data_source = uploaded.name
    except Exception as exc:
        st.error(f"Could not read the uploaded CSV: {exc}")
        st.stop()
elif use_demo:
    raw_df = make_demo_data()
    data_source = "Built-in demonstration dataset"
else:
    st.info("Upload your retail sales CSV using the sidebar to begin.")
    st.stop()

if raw_df.empty:
    st.warning("The selected dataset contains no rows.")
    st.stop()

df, cleaning_report = clean_data(raw_df)
if df.empty:
    st.error("No usable rows remain after cleaning.")
    st.stop()

date_col = infer_date_column(df)
category_col = first_matching(df.columns, CATEGORY_CANDIDATES)
item_col = first_matching(df.columns, ITEM_CANDIDATES)
payment_col = first_matching(df.columns, PAYMENT_CANDIDATES)
customer_col = first_matching(df.columns, CUSTOMER_CANDIDATES)
channel_col = first_matching(df.columns, CHANNEL_CANDIDATES)
qty_col = first_matching(df.columns, ["Quantity", "Qty", "Units Sold"])
price_col = first_matching(df.columns, ["Price Per Unit", "Unit Price", "Price"])
total_col = first_matching(df.columns, ["Total Spent", "Total Sales", "Revenue", "Sales", "Amount"])

# Global filters
with st.sidebar:
    st.markdown("## Filters")
    filtered = df.copy()
    if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
        valid_dates = df[date_col].dropna()
        if not valid_dates.empty:
            start_date, end_date = st.date_input(
                "Transaction date range",
                value=(valid_dates.min().date(), valid_dates.max().date()),
                min_value=valid_dates.min().date(),
                max_value=valid_dates.max().date(),
            )
            if start_date and end_date:
                filtered = filtered[
                    filtered[date_col].isna()
                    | ((filtered[date_col].dt.date >= start_date) & (filtered[date_col].dt.date <= end_date))
                ]
    if category_col:
        categories = sorted(df[category_col].dropna().astype(str).unique().tolist())
        selected_categories = st.multiselect("Category", categories, default=categories)
        filtered = filtered[filtered[category_col].astype(str).isin(selected_categories)]
    st.caption(f"Source: {data_source}")
    st.caption(f"{len(filtered):,} filtered rows / {len(df):,} cleaned rows")

if filtered.empty:
    st.warning("No rows match the current filters. Adjust the filters in the sidebar.")
    st.stop()

revenue = float(filtered[total_col].sum()) if total_col else 0.0
transactions = len(filtered)
units = float(filtered[qty_col].sum()) if qty_col else 0.0
avg_sale = float(filtered[total_col].mean()) if total_col else 0.0

# --------------------------- Pages ---------------------------
if page == "Executive Overview":
    st.header("Executive Overview")
    st.caption("A quick summary of the selected retail dataset and active filters.")
    a, b, c, d = st.columns(4)
    a.metric("Total Revenue", f"{revenue:,.2f}" if total_col else "N/A")
    b.metric("Transactions / Rows", f"{transactions:,}")
    c.metric("Units Sold", f"{units:,.0f}" if qty_col else "N/A")
    d.metric("Average Sale", f"{avg_sale:,.2f}" if total_col else "N/A")
    st.divider()
    left, right = st.columns(2)
    with left:
        if category_col and total_col:
            cat = filtered.groupby(category_col, dropna=False)[total_col].sum().reset_index().sort_values(total_col, ascending=False)
            fig = px.bar(cat, x=category_col, y=total_col, title="Revenue by Category", template="plotly_dark", color=category_col)
            show_plot("Revenue by Category", fig, len(cat))
        else:
            st.info("Category revenue chart needs category and sales/revenue columns.")
    with right:
        if date_col and total_col:
            trend = filtered.dropna(subset=[date_col]).groupby(filtered[date_col].dt.to_period("M").astype(str))[total_col].sum().reset_index()
            trend.columns = ["Month", total_col]
            fig = px.line(trend, x="Month", y=total_col, markers=True, title="Monthly Revenue", template="plotly_dark")
            show_plot("Monthly Revenue", fig, len(trend))
        else:
            st.info("Monthly trend needs a date column and a sales/revenue column.")
    if total_col:
        st.subheader("Quick insights")
        best = filtered.groupby(category_col)[total_col].sum().idxmax() if category_col else None
        if best is not None:
            st.write(f"• Highest-revenue category in the current selection: **{best}**.")
        st.write(f"• Average recorded sale: **{avg_sale:,.2f}**.")
        st.write(f"• Current view includes **{len(filtered):,}** rows after cleaning and filtering.")

elif page == "Sales Trends":
    st.header("Sales Trends")
    if not date_col or not total_col:
        st.warning("This section needs a recognizable date column and a sales/revenue column.")
    else:
        dated = filtered.dropna(subset=[date_col]).copy()
        if dated.empty:
            st.info("No valid dates are available in the filtered data.")
        else:
            frequency = st.selectbox("Trend frequency", ["Daily", "Weekly", "Monthly"], index=2)
            if frequency == "Daily":
                dated["_Period"] = dated[date_col].dt.strftime("%Y-%m-%d")
            elif frequency == "Weekly":
                dated["_Period"] = dated[date_col].dt.to_period("W").astype(str)
            else:
                dated["_Period"] = dated[date_col].dt.to_period("M").astype(str)
            trend = dated.groupby("_Period", as_index=False)[total_col].sum()
            fig = px.line(trend, x="_Period", y=total_col, markers=True, template="plotly_dark", title=f"{frequency} Sales")
            show_plot(f"{frequency} Sales", fig, len(trend))
            show_table("Trend summary", trend, key_prefix="trend")

elif page == "Product & Category Analysis":
    st.header("Product & Category Analysis")
    if category_col and total_col:
        cat = filtered.groupby(category_col, dropna=False).agg(
            Revenue=(total_col, "sum"),
            Transactions=(total_col, "size"),
        ).reset_index().sort_values("Revenue", ascending=False)
        if qty_col:
            qty = filtered.groupby(category_col, dropna=False)[qty_col].sum().reset_index(name="Units")
            cat = cat.merge(qty, on=category_col, how="left")
        left, right = st.columns(2)
        with left:
            fig = px.bar(cat, x=category_col, y="Revenue", color=category_col, template="plotly_dark", title="Revenue by Category")
            show_plot("Revenue by Category", fig, len(cat))
        with right:
            fig = px.pie(cat, names=category_col, values="Revenue", hole=0.45, template="plotly_dark", title="Category Revenue Share")
            show_plot("Category Revenue Share", fig, len(cat))
        show_table("Category performance", cat)
    else:
        st.info("Category analysis needs category and sales/revenue columns.")
    if item_col and total_col:
        st.subheader("Product performance")
        product = filtered.groupby(item_col, dropna=False).agg(Revenue=(total_col, "sum"), Transactions=(total_col, "size")).reset_index().sort_values("Revenue", ascending=False)
        if qty_col:
            product = product.merge(filtered.groupby(item_col, dropna=False)[qty_col].sum().reset_index(name="Units"), on=item_col, how="left")
        top_n = st.slider("Products to display in chart", 5, min(30, max(5, len(product))), min(10, max(5, len(product))))
        top = product.head(top_n)
        fig = px.bar(top, x=item_col, y="Revenue", template="plotly_dark", title=f"Top {len(top)} Products by Revenue")
        show_plot("Top Products by Revenue", fig, len(top))
        show_table("All product results", product)

elif page == "Customer Analysis":
    st.header("Customer Analysis")
    if not customer_col:
        st.info("No customer identifier was detected in this dataset. Add a column such as Customer ID to enable customer-level analysis.")
    elif total_col:
        customer = filtered.groupby(customer_col, dropna=False).agg(
            Total_Spent=(total_col, "sum"),
            Transactions=(total_col, "size"),
        ).reset_index().sort_values("Total_Spent", ascending=False)
        if qty_col:
            customer = customer.merge(filtered.groupby(customer_col, dropna=False)[qty_col].sum().reset_index(name="Units"), on=customer_col, how="left")
        a, b, c = st.columns(3)
        a.metric("Unique Customers", f"{filtered[customer_col].nunique(dropna=True):,}")
        b.metric("Revenue", f"{revenue:,.2f}")
        c.metric("Average per Customer", f"{customer['Total_Spent'].mean():,.2f}" if not customer.empty else "—")
        fig = px.bar(customer.head(10), x=customer_col, y="Total_Spent", template="plotly_dark", title="Top 10 Customers by Spend")
        show_plot("Top Customers", fig, min(10, len(customer)))
        show_table("Customer summary", customer)
    else:
        st.info("Customer analysis needs a sales/revenue column.")

elif page == "Payment Analysis":
    st.header("Payment Analysis")
    if not payment_col:
        st.info("No payment-method column was detected. Expected examples: Payment Method, Payment Type or Payment.")
    else:
        pay = filtered.groupby(payment_col, dropna=False).size().reset_index(name="Transactions")
        if total_col:
            rev = filtered.groupby(payment_col, dropna=False)[total_col].sum().reset_index(name="Revenue")
            pay = pay.merge(rev, on=payment_col, how="left").sort_values("Revenue", ascending=False)
        left, right = st.columns(2)
        with left:
            fig = px.bar(pay, x=payment_col, y="Transactions", color=payment_col, template="plotly_dark", title="Transactions by Payment Method")
            show_plot("Transactions by Payment Method", fig, len(pay))
        with right:
            if "Revenue" in pay:
                fig = px.pie(pay, names=payment_col, values="Revenue", hole=0.45, template="plotly_dark", title="Revenue by Payment Method")
                show_plot("Revenue by Payment Method", fig, len(pay))
        show_table("Payment summary", pay)

elif page == "Exploratory Data Analysis":
    st.header("Exploratory Data Analysis")
    st.subheader("Dataset shape and types")
    a, b = st.columns(2)
    a.metric("Rows", f"{len(filtered):,}")
    b.metric("Columns", f"{filtered.shape[1]:,}")
    schema = pd.DataFrame({"Column": filtered.columns, "Data Type": [str(x) for x in filtered.dtypes], "Non-null Values": [int(filtered[c].notna().sum()) for c in filtered.columns], "Unique Values": [int(filtered[c].nunique(dropna=True)) for c in filtered.columns]})
    show_table("Column profile", schema)
    st.subheader("Descriptive statistics")
    numeric = filtered.select_dtypes(include=np.number)
    if not numeric.empty:
        show_table("Numeric summary", numeric.describe().T.reset_index(names="Column"))
        numeric_cols = numeric.columns.tolist()
        chosen = st.selectbox("Choose a numeric column distribution", numeric_cols)
        fig = px.histogram(filtered, x=chosen, nbins=30, template="plotly_dark", title=f"Distribution of {chosen}")
        show_plot(f"Distribution of {chosen}", fig, len(filtered))
        if len(numeric_cols) > 1:
            corr = numeric.corr(numeric_only=True)
            fig = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale="Blues", template="plotly_dark", title="Numeric Correlation Matrix")
            show_plot("Correlation Matrix", fig, len(corr))
    else:
        st.info("No numeric columns are available for statistical analysis.")
    cat_cols = filtered.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        chosen_cat = st.selectbox("Categorical column", cat_cols)
        counts = filtered[chosen_cat].astype(str).value_counts(dropna=False).head(20).reset_index()
        counts.columns = [chosen_cat, "Count"]
        fig = px.bar(counts, x=chosen_cat, y="Count", template="plotly_dark", title=f"Top values in {chosen_cat}")
        show_plot(f"Top values in {chosen_cat}", fig, len(counts))

elif page == "Data Quality & Cleaning":
    st.header("Data Quality & Cleaning")
    before_missing = raw_df.isna().sum()
    after_missing = df.isna().sum()
    a, b, c, d = st.columns(4)
    a.metric("Original Rows", f"{cleaning_report['rows_before']:,}")
    b.metric("Cleaned Rows", f"{cleaning_report['rows_after']:,}")
    c.metric("Duplicates Found", f"{cleaning_report['duplicates_removed']:,}")
    d.metric("Rows Removed", f"{cleaning_report['rows_removed']:,}")
    st.caption("Cleaning steps: duplicate removal, date parsing, numeric conversion, derivation of missing totals where possible, and conservative missing-value filling.")
    quality = pd.DataFrame({
        "Column": raw_df.columns,
        "Missing Before": [int(before_missing[c]) for c in raw_df.columns],
        "Missing After": [int(after_missing.get(c, 0)) for c in raw_df.columns],
        "Type Before": [str(raw_df[c].dtype) for c in raw_df.columns],
        "Type After": [str(df[c].dtype) if c in df.columns else "removed" for c in raw_df.columns],
    })
    show_table("Data quality report", quality)
    st.subheader("Cleaned data preview")
    show_table("Cleaned records", df)
    st.download_button("Download cleaned CSV", df.to_csv(index=False).encode("utf-8"), "cleaned_retail_store_sales.csv", "text/csv")

elif page == "Data Explorer":
    st.header("Data Explorer")
    st.caption("Search, choose columns, and inspect the currently filtered records.")
    search = st.text_input("Search across all columns")
    explorer = filtered.copy()
    if search.strip():
        mask = explorer.astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False)).any(axis=1)
        explorer = explorer[mask]
    chosen_cols = st.multiselect("Columns to display", list(explorer.columns), default=list(explorer.columns))
    if chosen_cols:
        explorer = explorer[chosen_cols]
    show_table("Filtered data", explorer)
    st.download_button("Download explorer results (CSV)", explorer.to_csv(index=False).encode("utf-8"), "retail_data_explorer.csv", "text/csv")

elif page == "Reports & Downloads":
    st.header("Reports & Downloads")
    st.write("Download the dataset and analysis summaries for your report or project review.")
    st.download_button("Download current filtered data (CSV)", filtered.to_csv(index=False).encode("utf-8"), "retail_sales_filtered.csv", "text/csv")
    st.download_button("Download cleaned full dataset (CSV)", df.to_csv(index=False).encode("utf-8"), "cleaned_retail_store_sales.csv", "text/csv")
    if total_col:
        summary = {
            "source": data_source,
            "rows_in_filtered_view": int(len(filtered)),
            "total_revenue": float(revenue),
            "average_sale": float(avg_sale),
            "transactions": int(transactions),
            "units_sold": float(units) if qty_col else None,
            "date_column": date_col,
            "category_column": category_col,
            "item_column": item_col,
            "payment_column": payment_col,
        }
        st.download_button("Download KPI summary (JSON)", json.dumps(summary, indent=2).encode("utf-8"), "retail_sales_summary.json", "application/json")
    if category_col and total_col:
        category_summary = filtered.groupby(category_col, dropna=False)[total_col].agg(["sum", "mean", "count"]).reset_index()
        category_summary.columns = [category_col, "Total Revenue", "Average Sale", "Transactions"]
        st.download_button("Download category summary (CSV)", category_summary.to_csv(index=False).encode("utf-8"), "category_summary.csv", "text/csv")
    st.info("For college documentation, include screenshots of the overview, trends, data-quality report and downloads.")

elif page == "Project Information":
    st.header("Project Information")
    st.markdown("""
    ### Retail Store Sales Analysis
    **Objective:** Analyze retail transaction data to understand sales performance, product/category contribution, customer spending patterns, payment usage and data quality.

    **Technology stack**
    - Python
    - Streamlit for the interactive website
    - Pandas and NumPy for data processing
    - Plotly for interactive charts

    **Methodology**
    1. Upload a retail CSV file or use the demonstration dataset.
    2. Inspect columns, types, missing values and duplicates.
    3. Clean and prepare the data for analysis.
    4. Explore sales by time, category, product, customer and payment method when the relevant columns exist.
    5. Export cleaned data and summaries.

    **Data note:** Analysis sections depend on the columns in the uploaded CSV. The app will explain when a required column is unavailable rather than inventing results.
    """)
    st.subheader("Current dataset columns")
    show_table("Available columns", pd.DataFrame({"Column": df.columns, "Data Type": [str(x) for x in df.dtypes]}))

st.markdown("---")
st.markdown('<p class="small-note">Retail Store Sales Analysis · Interactive academic project dashboard</p>', unsafe_allow_html=True)
