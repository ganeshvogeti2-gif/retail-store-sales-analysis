# =============================================================================
# RETAIL STORE SALES ANALYSIS — Streamlit Dashboard
# =============================================================================
#
# WHAT IS THIS FILE?
#   This is the main Python file that runs the entire Retail Store Sales
#   Analysis website. When you run "streamlit run app.py" in your terminal,
#   Streamlit reads this file and builds an interactive web page from it.
#
# LIBRARIES USED (we import them at the very top):
#   - streamlit  : Builds the interactive website (buttons, tables, charts,
#                  sidebar, file uploader, etc.). Think of it as the "frame"
#                  of the website.
#   - pandas     : Loads CSV files into tables (called DataFrames), cleans
#                  data, filters rows, groups records, and calculates totals.
#   - numpy      : Does fast number calculations — we use it for year-on-year
#                  growth (np.diff), rounding (np.round), and conditional
#                  labels (np.where).
#   - plotly     : Creates interactive bar charts, line charts, pie charts,
#                  histograms, and heatmaps that users can hover over.
#   - matplotlib : Creates static charts (bar charts, scatter plots, box
#                  plots, histograms). Required by project documentation.
#   - seaborn    : A library built on top of matplotlib that makes statistical
#                  charts (box plots, heatmaps) look nicer with less code.
#   - base64     : Converts HTML content into a safe string so we can open it
#                  in a new browser tab without saving a file.
#   - html       : Escapes special characters (like < and >) to prevent broken
#                  HTML output.
#   - io         : Lets us save matplotlib charts into memory (a buffer)
#                  instead of saving them to a file on disk.
#   - json       : Converts Python dictionaries to JSON format for downloads.
#   - pathlib    : Provides a clean way to work with file/folder paths.
# =============================================================================

# ---------- Standard library imports (built into Python, no install needed) --
import base64          # For encoding HTML pages as data URLs (new-tab links)
import html            # For safely escaping text inside HTML
import io              # For saving matplotlib charts to memory
import json            # For creating JSON download files
from pathlib import Path  # For working with folder paths cleanly

# ---------- Third-party library imports (need: pip install -r requirements.txt) --
import numpy as np                  # Numerical calculations
import pandas as pd                 # Data loading, cleaning, analysis
import plotly.express as px         # Easy interactive charts
import plotly.graph_objects as go   # Advanced interactive chart customisation
import streamlit as st              # The web framework that builds the site

# Matplotlib and Seaborn: for documentation-required static charts
import matplotlib
matplotlib.use("Agg")               # Use non-interactive backend (no GUI window)
import matplotlib.pyplot as plt
import seaborn as sns

# =============================================================================
# PAGE CONFIGURATION
# This must be the FIRST Streamlit call — it sets the browser tab title,
# icon, page layout (wide = uses full browser width), and sidebar state.
# =============================================================================
st.set_page_config(
    page_title="Retail Store Sales Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CSS STYLING
# We inject custom CSS (Cascading Style Sheets) into the page to control
# colors, fonts, and layout. st.markdown with unsafe_allow_html=True lets us
# embed raw HTML and CSS directly into the Streamlit page.
# The theme uses a dark navy-blue background (#0b1120) throughout.
# =============================================================================
st.markdown(
    """
    <style>
    /* ---- Global colour scheme ---- */
    :root { color-scheme: dark; }
    .stApp { background: #0b1120; color: #e8eef8; }

    /* ---- Sidebar styling ---- */
    [data-testid="stSidebar"] { background: #101b2e; border-right: 1px solid #223653; }

    /* ---- Metric card styling ---- */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #14243a, #101b2e);
        padding: 18px 20px; border-radius: 14px;
        border: 1px solid #294365;
    }
    [data-testid="stMetricLabel"] { color: #a9bdd7; }
    [data-testid="stMetricValue"] { color: #f5f9ff; }

    /* ---- Hero banner (main page header) ---- */
    .hero {
        padding: 1.35rem 1.5rem; border-radius: 16px;
        background: linear-gradient(120deg, #102544, #123c67);
        border: 1px solid #2a527d; margin-bottom: 1rem;
    }
    .hero h1 { margin: 0 0 .35rem 0; color: #ffffff; }
    .hero p  { margin: 0; color: #c5d7ee; }

    /* ---- Small caption text ---- */
    .small-note { color: #9fb4ce; font-size: .9rem; }

    /* ---- Data table border ---- */
    div[data-testid="stDataFrame"] { border: 1px solid #243b59; border-radius: 10px; }

    /* ---- Tooltip: hover over a heading to see a description ---- */
    .tooltip-wrap {
        position: relative; display: inline-block; cursor: help;
    }
    .tooltip-wrap .tooltip-text {
        visibility: hidden; background: #16365b; color: #e8eef8;
        border: 1px solid #4a8ac7; border-radius: 8px;
        padding: 8px 12px; font-size: 0.82rem; width: 280px;
        position: absolute; z-index: 999; bottom: 130%; left: 0;
        white-space: normal; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        transition: visibility 0s, opacity 0.2s;
        opacity: 0;
    }
    .tooltip-wrap:hover .tooltip-text { visibility: visible; opacity: 1; }
    .tooltip-icon { color: #4a8ac7; font-size: 0.85rem; margin-left: 5px; }

    /* ---- Page section title shown above the hero banner ---- */
    .page-title {
        font-size: 1.6rem; font-weight: 700; color: #c5d7ee;
        margin-bottom: 0.4rem; letter-spacing: 0.5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# HERO BANNER
# This banner appears at the top of every page. It shows the project title
# and a short description. We use raw HTML via st.markdown so we can apply
# the .hero CSS class defined above.
# =============================================================================
st.markdown(
    '<div class="hero">'
    '<h1>📊 Retail Store Sales Analysis</h1>'
    '<p>Interactive business intelligence dashboard · '
    'Clean, explore, analyze and export retail data</p>'
    '</div>',
    unsafe_allow_html=True,
)


# =============================================================================
# HELPER FUNCTIONS
# These are reusable pieces of code. Instead of repeating the same logic many
# times, we write it once as a function and call it wherever we need it.
# =============================================================================

# --- Column name detection helpers ---
# These lists contain common names that different CSV files use for the same
# type of column. For example, a date column might be called "Transaction Date"
# in one CSV and "Order Date" in another.
REQUIRED_CORE       = ["Quantity", "Price Per Unit", "Total Spent"]
DATE_CANDIDATES     = ["Transaction Date", "Date", "Order Date", "Purchase Date"]
CATEGORY_CANDIDATES = ["Category", "Product Category", "Item Category"]
ITEM_CANDIDATES     = ["Item", "Product", "Product Name"]
PAYMENT_CANDIDATES  = ["Payment Method", "Payment Type", "Payment"]
CUSTOMER_CANDIDATES = ["Customer ID", "Customer", "Customer Name", "Customer ID/Name"]
CHANNEL_CANDIDATES  = ["Channel", "Sales Channel", "Store Type"]
LOCATION_CANDIDATES = ["Location", "City", "Store", "Branch", "Region"]
DISCOUNT_CANDIDATES = ["Discount Applied", "Discount", "Promo", "Coupon"]


def first_matching(columns, candidates):
    """
    Searches the DataFrame's column list for the first name that matches
    any of the candidate names (case-insensitive).

    WHY: Different CSV files use different names for the same column.
         This function makes the app work with many file formats without
         asking the user to rename columns.

    Example:
        columns   = ["Date", "Customer ID", "Total Spent"]
        candidates = ["Transaction Date", "Date", "Order Date"]
        Returns   -> "Date"  (the first match found)
    """
    # Build a dictionary: lowercase column name -> actual column name
    lookup = {str(c).strip().lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None   # Returns None if no match is found


def money(value):
    """
    Formats a number as a currency string with commas and 2 decimal places.
    Returns "—" if the value cannot be converted to a number.

    Example: money(12500.5) -> "12,500.50"
    """
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


def tooltip_heading(heading_text, tip_text, level="subheader"):
    """
    Displays a heading with a small i icon. When the user hovers over the
    icon, a tooltip box appears explaining what the section shows.

    WHY: Tooltips help examiners and users understand what each section
         does without cluttering the main content.

    Parameters:
        heading_text : The visible heading text.
        tip_text     : The explanation shown in the tooltip on hover.
        level        : "header" uses a larger font; "subheader" is smaller.
    """
    tag = "h2" if level == "header" else "h3"
    html_block = (
        f'<{tag} style="color:#e8eef8;margin-bottom:0.3rem;">'
        f'{html.escape(heading_text)}'
        f'<span class="tooltip-wrap">'
        f'  <span class="tooltip-icon">&#9432;</span>'
        f'  <span class="tooltip-text">{html.escape(tip_text)}</span>'
        f'</span>'
        f'</{tag}>'
    )
    st.markdown(html_block, unsafe_allow_html=True)


def page_title_above_hero(section_name):
    """
    Displays the section name as a styled title.
    This appears directly below the hero banner on each page, making it
    clear which section the user is currently viewing.
    """
    st.markdown(
        f'<div class="page-title">&#128204; {html.escape(section_name)}</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# TABLE DISPLAY WITH "VIEW IN NEW TAB" FEATURE
# =============================================================================

def standalone_html(title, body):
    """
    Creates a complete HTML page (with dark styling) that can be opened
    in a new browser tab. Used for showing full tables when there are more
    than 10 rows.

    WHY: Streamlit shows tables inside a small box with scrolling. For large
         tables (hundreds of rows), it is easier to open the full table in a
         new tab where the user can see everything and use Ctrl+F to search.
    """
    page = (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{html.escape(title)}</title>"
        "<style>"
        "body{margin:0;padding:24px;background:#0b1120;color:#e8eef8;font-family:Arial,sans-serif}"
        "h1{color:#fff} .wrap{max-width:1400px;margin:auto}"
        "table{border-collapse:collapse;width:100%;font-size:14px;background:#101b2e}"
        "th,td{border:1px solid #294365;padding:9px;text-align:left}"
        "th{background:#16365b;color:#fff;position:sticky;top:0}"
        "tr:nth-child(even){background:#132239}"
        ".note{color:#a9bdd7}"
        "</style></head><body><div class=\"wrap\">"
        f"<h1>{html.escape(title)}</h1>{body}</div></body></html>"
    )
    return page


def open_new_tab_link(label, title, body):
    """
    Creates a clickable button-style link that opens a full-page HTML view
    in a new browser tab.

    HOW IT WORKS:
    1. We call standalone_html() to build a complete HTML page as a string.
    2. We encode that string using base64 (a way to convert any text to a
       safe sequence of letters and numbers).
    3. We embed it as a "data URL" in a hyperlink. The browser reads the
       encoded data directly — no file is saved to disk.

    WHY: Streamlit does not have a built-in "open in new tab" feature for
         tables, so we build our own using this base64 trick.
    """
    page = standalone_html(title, body)
    # Encode the HTML page to base64 ASCII string
    encoded = base64.b64encode(page.encode("utf-8")).decode("ascii")
    st.markdown(
        f'<a href="data:text/html;base64,{encoded}" target="_blank" rel="noopener" '
        'style="display:inline-block;background:#1d65ad;color:white;padding:9px 14px;'
        'border-radius:8px;text-decoration:none;font-weight:600;border:1px solid #4a8ac7;">'
        f'{html.escape(label)}</a>',
        unsafe_allow_html=True,
    )


def show_table(title, frame, preview_rows=10, tip="", key_prefix="table"):
    """
    Displays a data table with a heading and an optional tooltip.

    BEHAVIOUR:
    - If the table has 10 or fewer rows: shows all rows directly.
    - If the table has more than 10 rows: shows the first 10 rows, then
      shows a caption like "Showing 10 of 350 rows" and a link to open
      ALL rows in a new browser tab.

    WHY THIS LIMIT: Showing thousands of rows in a small dashboard is
    overwhelming. Preview + new-tab link gives the best of both worlds.

    Parameters:
        title       : Heading text shown above the table.
        frame       : The Pandas DataFrame to display.
        preview_rows: How many rows to show as preview (default 10).
        tip         : Optional tooltip description for the heading.
        key_prefix  : Used internally by Streamlit to give each widget a
                      unique identifier.
    """
    # Show a heading with tooltip if a tip was provided
    if tip:
        tooltip_heading(title, tip, level="subheader")
    else:
        st.subheader(title)

    total_rows = len(frame)

    if total_rows <= 10:
        # Small table: show everything directly
        st.dataframe(frame, use_container_width=True, hide_index=True)
    else:
        # Large table: show preview + link to full view
        st.dataframe(frame.head(preview_rows), use_container_width=True, hide_index=True)
        st.caption(
            f"Showing {min(preview_rows, total_rows)} of {total_rows:,} rows — "
            "click the link below to see all rows."
        )
        # Convert the full DataFrame to an HTML table string
        table_html = frame.to_html(index=False, escape=True, border=0)
        # Open the full table in a new browser tab
        open_new_tab_link(f"&#8599; View remaining data in a new tab", title, table_html)


def show_plot(title, fig, tip=""):
    """
    Displays a Plotly interactive chart with an optional tooltip heading.

    NOTE: Graphs are always shown in full — we do NOT limit or hide charts
          based on row count. Only tables get the 10-row preview treatment.

    Parameters:
        title : Heading text above the chart.
        fig   : The Plotly figure object to render.
        tip   : Optional tooltip description for the heading.
    """
    if tip:
        tooltip_heading(title, tip, level="subheader")
    else:
        st.subheader(title)
    # Use a unique key so Streamlit does not confuse charts with the same title
    unique_key = f"chart_{title}_{id(fig)}"
    st.plotly_chart(fig, use_container_width=True, key=unique_key)


def mpl_fig_to_st(fig, caption=""):
    """
    Converts a Matplotlib figure into an image and displays it in Streamlit.

    WHY: Streamlit cannot directly render a Matplotlib figure object — we
         need to save it to a memory buffer (BytesIO) as a PNG image first,
         then pass that image to st.image().

    Parameters:
        fig     : The Matplotlib figure object.
        caption : Optional text shown below the image.
    """
    buf = io.BytesIO()                 # Create an in-memory byte buffer
    fig.savefig(buf, format="png",     # Save the figure into the buffer
                bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)                        # Move cursor back to start of buffer
    st.image(buf, use_container_width=True)
    if caption:
        st.caption(caption)
    plt.close(fig)                     # Free memory by closing the figure


# =============================================================================
# DATA LOADING — DEMO DATA
# If the user has not uploaded a CSV file, we generate a small sample dataset
# so they can explore the dashboard features immediately.
# =============================================================================

def make_demo_data():
    """
    Creates a small demonstration dataset with 30 rows of retail sales data.

    WHY: New users need to see what the dashboard looks like before they
         have their own CSV file. The demo data covers all the columns used
         by the analysis so every chart and table works right away.

    Returns:
        A Pandas DataFrame with 30 sample transactions.
    """
    # Generate 30 consecutive dates starting from 2025-01-01
    dates = pd.date_range("2025-01-01", periods=30, freq="D")

    # Sample items, their categories, and fixed prices
    items      = ["Rice", "Milk", "Shirt", "Jeans", "Headphones", "Notebook"]
    categories = {
        "Rice": "Food",        "Milk": "Food",
        "Shirt": "Clothing",   "Jeans": "Clothing",
        "Headphones": "Electronics", "Notebook": "Stationery"
    }
    prices = {
        "Rice": 10.0, "Milk": 4.0, "Shirt": 25.0,
        "Jeans": 30.0, "Headphones": 80.0, "Notebook": 3.0
    }

    rows = []
    for i, date in enumerate(dates):
        item = items[i % len(items)]     # Cycle through items
        qty  = (i % 5) + 1              # Quantity cycles from 1 to 5
        rows.append({
            "Transaction Date": date,
            "Transaction ID":   f"T{i+1:04d}",
            "Customer ID":      f"C{(i % 12)+1:03d}",
            "Item":             item,
            "Category":         categories[item],
            "Location":         ["Mumbai", "Delhi", "Bangalore", "Hyderabad"][i % 4],
            "Quantity":         qty,
            "Price Per Unit":   prices[item],
            "Total Spent":      qty * prices[item],
            "Payment Method":   ["Cash", "Card", "UPI"][i % 3],
            "Discount Applied": ["Yes", "No", "No"][i % 3],
            "Channel":          ["In-store", "Online"][i % 2],
        })
    return pd.DataFrame(rows)


# =============================================================================
# DATA CLEANING FUNCTION
# =============================================================================

def clean_data(raw):
    """
    Cleans the raw DataFrame and returns a cleaned copy plus a report.

    CLEANING STEPS (in order):
    1. Remove duplicate rows using drop_duplicates().
    2. Parse the date column into proper datetime format using pd.to_datetime().
    3. Convert text-based number columns to numeric using pd.to_numeric().
    4. Recover missing Total Spent = Quantity x Price Per Unit where possible.
    5. Recover missing Price Per Unit = Total Spent / Quantity where possible.
    6. Recover missing Quantity = Total Spent / Price Per Unit where possible.
    7. Fill remaining missing numbers with the column median.
    8. Fill remaining missing text values with the column mode (most common value).
    9. Convert Discount Applied column values to readable labels (Yes/No/Unknown).
    10. Remove rows where every single column is empty (fully blank rows).

    WHY EACH STEP IS NEEDED:
    - Duplicates: Counting the same sale twice would inflate totals.
    - Date parsing: We need proper date objects to group data by month/year.
    - Numeric conversion: CSV files store everything as text; we need numbers
      to do arithmetic.
    - Recovering missing values: Instead of losing rows, we estimate missing
      numbers from the values that ARE available.
    - Filling with median/mode: A conservative way to handle missing values
      without distorting the data too much.

    Returns:
        cleaned (DataFrame): The cleaned data.
        report  (dict)     : Statistics about what was changed during cleaning.
    """
    cleaned = raw.copy()                # Work on a copy, never the original
    original_rows = len(cleaned)
    original_duplicates = int(cleaned.duplicated().sum())

    # STEP 1 — Remove duplicate rows
    cleaned = cleaned.drop_duplicates().copy()

    # STEP 2 — Parse the date column into proper datetime objects
    date_col = first_matching(cleaned.columns, DATE_CANDIDATES)
    if date_col:
        # errors="coerce" turns invalid dates into NaT (Not a Time) instead
        # of crashing the program
        cleaned[date_col] = pd.to_datetime(cleaned[date_col], errors="coerce")

    # STEP 3 — Convert number-like columns from text to numeric values
    numeric_cols = [
        c for c in cleaned.columns
        if any(token in str(c).lower()
               for token in ["quantity", "price", "spent", "sales",
                              "revenue", "amount", "discount"])
    ]
    for col in numeric_cols:
        # errors="coerce" turns non-numeric text (like "N/A") into NaN
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    # Identify the key columns we will use for value recovery
    qty_col   = first_matching(cleaned.columns, ["Quantity", "Qty", "Units Sold"])
    price_col = first_matching(cleaned.columns, ["Price Per Unit", "Unit Price", "Price"])
    total_col = first_matching(cleaned.columns, ["Total Spent", "Total Sales",
                                                  "Revenue", "Sales", "Amount"])

    # STEP 4 — Recover missing Total Spent = Quantity x Price Per Unit
    if qty_col and price_col and total_col:
        mask = (cleaned[total_col].isna()
                & cleaned[qty_col].notna()
                & cleaned[price_col].notna()
                & (cleaned[qty_col] > 0)
                & (cleaned[price_col] > 0))
        cleaned.loc[mask, total_col] = (
            cleaned.loc[mask, qty_col] * cleaned.loc[mask, price_col]
        )

    # STEP 5 — Recover missing Price Per Unit = Total Spent / Quantity
    if qty_col and price_col and total_col:
        mask = (cleaned[price_col].isna()
                & cleaned[total_col].notna()
                & cleaned[qty_col].notna()
                & (cleaned[qty_col] > 0))          # Avoid division by zero
        cleaned.loc[mask, price_col] = (
            cleaned.loc[mask, total_col] / cleaned.loc[mask, qty_col]
        )

    # STEP 6 — Recover missing Quantity = Total Spent / Price Per Unit
    if qty_col and price_col and total_col:
        mask = (cleaned[qty_col].isna()
                & cleaned[total_col].notna()
                & cleaned[price_col].notna()
                & (cleaned[price_col] > 0))        # Avoid division by zero
        cleaned.loc[mask, qty_col] = (
            cleaned.loc[mask, total_col] / cleaned.loc[mask, price_col]
        )

    # STEP 7 and 8 — Fill remaining missing values with median (numbers) or
    #               mode (text/categories)
    for col in cleaned.columns:
        if cleaned[col].isna().any():
            if pd.api.types.is_numeric_dtype(cleaned[col]):
                median_val = cleaned[col].median()
                if pd.notna(median_val):
                    cleaned[col] = cleaned[col].fillna(median_val)
            else:
                mode_vals = cleaned[col].mode(dropna=True)
                if not mode_vals.empty:
                    cleaned[col] = cleaned[col].fillna(mode_vals.iloc[0])

    # STEP 9 — Standardise Discount Applied column to Yes / No / Unknown
    # np.where works like: if condition is True -> use value1, else -> use value2
    # We nest two np.where calls to handle three possible outcomes.
    discount_col = first_matching(cleaned.columns, DISCOUNT_CANDIDATES)
    if discount_col:
        disc_str = cleaned[discount_col].astype(str).str.strip().str.lower()
        cleaned[discount_col] = np.where(
            disc_str.isin(["yes", "true", "1", "y"]),    "Yes",
            np.where(
                disc_str.isin(["no", "false", "0", "n"]), "No",
                "Unknown"
            )
        )

    # STEP 10 — Remove rows where EVERY column is empty (fully blank rows)
    before_dropna = len(cleaned)
    cleaned = cleaned.dropna(how="all").copy()

    # Build and return the cleaning report
    report = {
        "rows_before":               original_rows,
        "rows_after":                len(cleaned),
        "duplicates_removed":        original_duplicates,
        "rows_removed":              original_rows - len(cleaned),
        "date_column":               date_col,
        "numeric_columns_converted": numeric_cols,
        "all_null_rows_removed":     before_dropna - len(cleaned),
    }
    return cleaned, report


def infer_date_column(frame):
    """Finds the date column in a DataFrame using the candidate list."""
    return first_matching(frame.columns, DATE_CANDIDATES)


# =============================================================================
# SIDEBAR — NAVIGATION AND DATA UPLOAD
# The sidebar appears on the left side of every page. It contains:
#   1. The "Dashboard" heading
#   2. The section radio buttons (navigation)
#   3. File uploader for CSV
#   4. Demo data toggle
#   5. Global date and category filters
# =============================================================================
with st.sidebar:
    # Changed from "Navigation" to "Dashboard" as requested
    st.markdown("## Dashboard")

    # Radio buttons let the user pick which section to view
    page = st.radio(
        "Choose a section",
        [
            "Executive Overview",
            "Sales Trends",
            "Product & Category Analysis",
            "Customer Analysis",
            "Payment Analysis",
            "Exploratory Data Analysis",
            "Data Quality & Cleaning",
            "Data Explorer",
            "Reports & Downloads",
            "Project Information",
        ],
        label_visibility="collapsed",
    )
    st.divider()

    # File uploader: the user can drag-and-drop or browse for a CSV file
    uploaded = st.file_uploader("Upload retail CSV", type=["csv"])

    # Toggle: use built-in demo data when no file is uploaded
    use_demo = st.toggle("Use demo data when no CSV is uploaded", value=True)
    st.caption("CSV files are processed for this app session only.")


# =============================================================================
# DATA LOADING
# Decide which dataset to use: uploaded CSV, demo data, or nothing.
# st.stop() stops the rest of the code from running if there is no data.
# =============================================================================

if uploaded is not None:
    # The user has uploaded a file — try to read it as a CSV
    try:
        raw_df = pd.read_csv(uploaded)
        data_source = uploaded.name    # Remember the file name for display
    except Exception as exc:
        st.error(f"Could not read the uploaded CSV: {exc}")
        st.stop()
elif use_demo:
    # No file uploaded but demo mode is ON — generate sample data
    raw_df = make_demo_data()
    data_source = "Built-in demonstration dataset"
else:
    # No file and demo mode OFF — ask the user to upload a file
    st.info("Upload your retail sales CSV using the sidebar to begin.")
    st.stop()

# Safety check: make sure the DataFrame is not empty
if raw_df.empty:
    st.warning("The selected dataset contains no rows.")
    st.stop()


# =============================================================================
# DATA CLEANING
# Call the clean_data() function defined above. It returns:
#   df              -> the cleaned DataFrame we use for all analysis
#   cleaning_report -> a dictionary of cleaning statistics
# =============================================================================
df, cleaning_report = clean_data(raw_df)

if df.empty:
    st.error("No usable rows remain after cleaning.")
    st.stop()


# =============================================================================
# COLUMN DETECTION
# After cleaning, detect which columns exist so we can use them in analysis.
# Each variable is either a column name (string) or None if not found.
# =============================================================================
date_col     = infer_date_column(df)
category_col = first_matching(df.columns, CATEGORY_CANDIDATES)
item_col     = first_matching(df.columns, ITEM_CANDIDATES)
payment_col  = first_matching(df.columns, PAYMENT_CANDIDATES)
customer_col = first_matching(df.columns, CUSTOMER_CANDIDATES)
channel_col  = first_matching(df.columns, CHANNEL_CANDIDATES)
location_col = first_matching(df.columns, LOCATION_CANDIDATES)
discount_col = first_matching(df.columns, DISCOUNT_CANDIDATES)
qty_col      = first_matching(df.columns, ["Quantity", "Qty", "Units Sold"])
price_col    = first_matching(df.columns, ["Price Per Unit", "Unit Price", "Price"])
total_col    = first_matching(df.columns, ["Total Spent", "Total Sales",
                                            "Revenue", "Sales", "Amount"])


# =============================================================================
# GLOBAL SIDEBAR FILTERS
# After detecting columns, we add date and category filters to the sidebar.
# These filters affect ALL sections of the dashboard — everything you see is
# based on the filtered data, not the full dataset.
# =============================================================================
with st.sidebar:
    st.markdown("## Filters")
    filtered = df.copy()   # Start with all cleaned rows

    # --- Date range filter ---
    if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
        valid_dates = df[date_col].dropna()
        if not valid_dates.empty:
            # Show a date picker; default range covers the full dataset
            start_date, end_date = st.date_input(
                "Transaction date range",
                value=(valid_dates.min().date(), valid_dates.max().date()),
                min_value=valid_dates.min().date(),
                max_value=valid_dates.max().date(),
            )
            if start_date and end_date:
                # Keep rows where date is NaT (missing) OR within the range
                filtered = filtered[
                    filtered[date_col].isna()
                    | ((filtered[date_col].dt.date >= start_date)
                       & (filtered[date_col].dt.date <= end_date))
                ]

    # --- Category filter ---
    if category_col:
        all_cats = sorted(df[category_col].dropna().astype(str).unique().tolist())
        selected_categories = st.multiselect(
            "Category", all_cats, default=all_cats
        )
        filtered = filtered[
            filtered[category_col].astype(str).isin(selected_categories)
        ]

    # Show the current data source and row counts
    st.caption(f"Source: {data_source}")
    st.caption(f"{len(filtered):,} filtered rows / {len(df):,} cleaned rows")

# Safety check: stop if all rows were filtered out
if filtered.empty:
    st.warning("No rows match the current filters. Adjust the filters in the sidebar.")
    st.stop()


# =============================================================================
# GLOBAL KPI CALCULATIONS
# These four summary numbers are used on multiple pages.
# We calculate them here once so we do not repeat the same code later.
# =============================================================================

# Total revenue: sum of the Total Spent column across all filtered rows
revenue = float(filtered[total_col].sum()) if total_col else 0.0

# Total transactions: simply the number of rows in the filtered data
transactions = len(filtered)

# Total units sold: sum of the Quantity column
units = float(filtered[qty_col].sum()) if qty_col else 0.0

# Average sale value: mean of Total Spent
avg_sale = float(filtered[total_col].mean()) if total_col else 0.0


# =============================================================================
# =============================================================================
#
#   DASHBOARD PAGES
#   Each "elif page == ..." block renders one of the 10 navigation sections.
#   Only the block that matches the currently selected page is executed.
#
# =============================================================================
# =============================================================================


# =============================================================================
# PAGE 1 — EXECUTIVE OVERVIEW
# Shows the top-level KPIs (Key Performance Indicators) and two summary charts.
# Think of this as the "homepage" of the dashboard.
# =============================================================================
if page == "Executive Overview":
    page_title_above_hero("Executive Overview")
    tooltip_heading(
        "Executive Overview",
        "High-level summary of revenue, transactions, units sold, "
        "and average sale value for the selected data range and filters.",
        level="header"
    )
    st.caption("A quick summary of the selected retail dataset and active filters.")

    # --- KPI metrics row (4 cards side by side) ---
    a, b, c, d = st.columns(4)
    a.metric("Total Revenue",       f"Rs {revenue:,.2f}"  if total_col else "N/A")
    b.metric("Transactions / Rows", f"{transactions:,}")
    c.metric("Units Sold",          f"{units:,.0f}"        if qty_col   else "N/A")
    d.metric("Average Sale",        f"Rs {avg_sale:,.2f}" if total_col else "N/A")

    # --- Additional KPIs ---
    st.divider()
    if customer_col:
        unique_customers = filtered[customer_col].nunique(dropna=True)
    else:
        unique_customers = None

    # First and last transaction dates
    if date_col and pd.api.types.is_datetime64_any_dtype(filtered[date_col]):
        valid_d = filtered[date_col].dropna()
        first_date = valid_d.min().strftime("%d %b %Y") if not valid_d.empty else "N/A"
        last_date  = valid_d.max().strftime("%d %b %Y") if not valid_d.empty else "N/A"
    else:
        first_date = last_date = "N/A"

    e, f_, g = st.columns(3)
    e.metric("First Transaction", first_date)
    f_.metric("Last Transaction",  last_date)
    if unique_customers is not None:
        g.metric("Unique Customers", f"{unique_customers:,}")

    # --- Year-on-Year Revenue and Growth using NumPy ---
    # np.diff() calculates the difference between consecutive values in an array.
    # For example: np.diff([100, 150, 120]) -> [50, -30]
    # This tells us how revenue changed from one year to the next.
    if date_col and total_col and pd.api.types.is_datetime64_any_dtype(filtered[date_col]):
        dated_f = filtered.dropna(subset=[date_col]).copy()
        if not dated_f.empty:
            dated_f["_Year"] = dated_f[date_col].dt.year
            yearly = (
                dated_f.groupby("_Year", as_index=False)
                .agg(Revenue=(total_col, "sum"), Transactions=(total_col, "size"))
                .sort_values("_Year")
            )
            if len(yearly) > 1:
                # Calculate year-on-year revenue changes using np.diff
                rev_array = yearly["Revenue"].values
                diffs = np.diff(rev_array)           # Differences between consecutive years
                # Percentage growth: (change / previous year) * 100
                growth_pct = np.round(diffs / rev_array[:-1] * 100, 2)
                # First year has no previous year, so its growth is None
                yearly["YoY Growth (%)"] = [None] + list(growth_pct)
            show_table(
                "Yearly Revenue & Growth",
                yearly,
                tip="Revenue and transaction count grouped by calendar year. "
                    "YoY Growth is calculated using np.diff()."
            )

    st.divider()

    # --- Two summary charts side by side ---
    left_col, right_col = st.columns(2)

    with left_col:
        if category_col and total_col:
            # Group the filtered data by category and sum Total Spent
            cat_rev = (
                filtered
                .groupby(category_col, dropna=False)[total_col]
                .sum()
                .reset_index()
                .sort_values(total_col, ascending=False)
            )
            fig = px.bar(
                cat_rev, x=category_col, y=total_col,
                title="Revenue by Category",
                template="plotly_dark", color=category_col
            )
            show_plot(
                "Revenue by Category", fig,
                tip="Total revenue earned from each product category."
            )
        else:
            st.info("Category revenue chart needs category and sales/revenue columns.")

    with right_col:
        if date_col and total_col:
            # Group by month (convert date to "YYYY-MM" string for grouping)
            monthly_rev = (
                filtered
                .dropna(subset=[date_col])
                .groupby(filtered[date_col].dt.to_period("M").astype(str))[total_col]
                .sum()
                .reset_index()
            )
            monthly_rev.columns = ["Month", total_col]
            fig = px.line(
                monthly_rev, x="Month", y=total_col,
                markers=True, title="Monthly Revenue", template="plotly_dark"
            )
            show_plot(
                "Monthly Revenue", fig,
                tip="Revenue aggregated by calendar month. "
                    "Helps identify seasonal patterns."
            )
        else:
            st.info("Monthly trend needs a date column and a sales/revenue column.")

    # --- Quick text insights ---
    if total_col:
        tooltip_heading(
            "Quick Insights",
            "Automatically generated observations based on the filtered data.",
            level="subheader"
        )
        if category_col:
            best_cat = (
                filtered.groupby(category_col, dropna=False)[total_col]
                .sum().idxmax()
            )
            st.write(f"- Highest-revenue category in the current selection: **{best_cat}**.")
        st.write(f"- Average recorded sale: **Rs {avg_sale:,.2f}**.")
        st.write(f"- Current view includes **{len(filtered):,}** rows after cleaning and filtering.")


# =============================================================================
# PAGE 2 — SALES TRENDS
# Shows how sales change over time (daily, weekly, or monthly).
# Also shows monthly breakdowns: revenue, transaction count, avg sale, weekday.
# =============================================================================
elif page == "Sales Trends":
    page_title_above_hero("Sales Trends")
    tooltip_heading(
        "Sales Trends",
        "Visualises how total revenue changes over time at daily, weekly, "
        "or monthly frequency. Use the date filter in the sidebar to zoom in.",
        level="header"
    )

    if not date_col or not total_col:
        st.warning("This section needs a recognizable date column and a "
                   "sales/revenue column.")
    else:
        # Drop rows where the date is missing (NaT)
        dated = filtered.dropna(subset=[date_col]).copy()

        if dated.empty:
            st.info("No valid dates are available in the filtered data.")
        else:
            # Let the user choose the time frequency
            frequency = st.selectbox(
                "Trend frequency", ["Daily", "Weekly", "Monthly"], index=2
            )

            # Create a period label column based on the chosen frequency
            if frequency == "Daily":
                dated["_Period"] = dated[date_col].dt.strftime("%Y-%m-%d")
            elif frequency == "Weekly":
                dated["_Period"] = dated[date_col].dt.to_period("W").astype(str)
            else:
                dated["_Period"] = dated[date_col].dt.to_period("M").astype(str)

            # Group by period and sum revenue
            trend = dated.groupby("_Period", as_index=False)[total_col].sum()

            # Main trend line chart
            fig = px.line(
                trend, x="_Period", y=total_col,
                markers=True, template="plotly_dark",
                title=f"{frequency} Sales Revenue"
            )
            show_plot(f"{frequency} Sales Revenue", fig,
                      tip=f"Total revenue grouped by {frequency.lower()} period.")
            show_table("Trend Summary", trend,
                       tip="Underlying numbers behind the trend chart.")

            # --- Monthly breakdown (always calculated at monthly level) ---
            dated["_Month"]  = dated[date_col].dt.to_period("M").astype(str)
            dated["_MonthN"] = dated[date_col].dt.month_name()

            # Monthly revenue, transaction count, and average transaction value
            monthly_agg = dated.groupby("_Month", as_index=False).agg(
                Monthly_Revenue     =(total_col, "sum"),
                Monthly_Transactions=(total_col, "size"),
                Avg_Transaction     =(total_col, "mean"),
            )

            st.divider()
            tooltip_heading(
                "Monthly Revenue Details",
                "Revenue, transaction count, and average sale value for each month.",
                level="subheader"
            )
            left2, right2 = st.columns(2)
            with left2:
                fig2 = px.bar(
                    monthly_agg, x="_Month", y="Monthly_Revenue",
                    title="Monthly Revenue", template="plotly_dark"
                )
                show_plot("Monthly Revenue Bar", fig2,
                          tip="Total revenue per calendar month.")
            with right2:
                fig3 = px.line(
                    monthly_agg, x="_Month", y="Monthly_Transactions",
                    markers=True, title="Monthly Transaction Count",
                    template="plotly_dark"
                )
                show_plot("Monthly Transaction Count", fig3,
                          tip="Number of sales transactions each month.")

            # Average transaction value per month
            fig4 = px.line(
                monthly_agg, x="_Month", y="Avg_Transaction",
                markers=True, title="Average Transaction Value by Month",
                template="plotly_dark"
            )
            show_plot("Average Transaction Value by Month", fig4,
                      tip="Mean value of each sale, grouped by month.")

            show_table("Monthly Aggregation Table", monthly_agg,
                       tip="Monthly revenue, transaction count, and average sale.")

            # --- Revenue by day of week ---
            # Monday through Sunday in order (not alphabetical order)
            WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday",
                             "Thursday", "Friday", "Saturday", "Sunday"]
            dated["_Weekday"] = dated[date_col].dt.day_name()
            weekday_rev = (
                dated.groupby("_Weekday", as_index=False)[total_col]
                .sum()
                .set_index("_Weekday")
                .reindex([d for d in WEEKDAY_ORDER
                          if d in dated["_Weekday"].unique()])
                .reset_index()
            )
            if not weekday_rev.empty:
                best_weekday = weekday_rev.loc[
                    weekday_rev[total_col].idxmax(), "_Weekday"
                ]
                fig5 = px.bar(
                    weekday_rev, x="_Weekday", y=total_col,
                    title="Revenue by Day of Week", template="plotly_dark",
                    color="_Weekday"
                )
                show_plot("Revenue by Day of Week", fig5,
                          tip="Which day of the week generates the most revenue.")
                st.info(f"Best performing weekday: **{best_weekday}**")

            # --- Best month by revenue ---
            if not monthly_agg.empty:
                best_month_row = monthly_agg.loc[
                    monthly_agg["Monthly_Revenue"].idxmax()
                ]
                st.info(
                    f"Best month: **{best_month_row['_Month']}** "
                    f"with revenue Rs {best_month_row['Monthly_Revenue']:,.2f}"
                )


# =============================================================================
# PAGE 3 — PRODUCT & CATEGORY ANALYSIS
# Shows revenue, units sold, and transaction counts broken down by product
# category and by individual product/item.
# =============================================================================
elif page == "Product & Category Analysis":
    page_title_above_hero("Product & Category Analysis")
    tooltip_heading(
        "Product & Category Analysis",
        "Compares revenue, units sold, and transaction count across product "
        "categories and individual items. Use the sidebar filters to narrow the view.",
        level="header"
    )

    # --- Category-level analysis ---
    if category_col and total_col:
        # groupby + agg calculates multiple summary stats in one step.
        # "sum" = total revenue, "size" = number of rows, "mean" = average
        cat = filtered.groupby(category_col, dropna=False).agg(
            Revenue     =(total_col, "sum"),
            Transactions=(total_col, "size"),
            Avg_Sale    =(total_col, "mean"),
        ).reset_index().sort_values("Revenue", ascending=False)

        # Add units sold column if quantity column exists
        if qty_col:
            qty_grp = (
                filtered.groupby(category_col, dropna=False)[qty_col]
                .sum().reset_index(name="Units")
            )
            cat = cat.merge(qty_grp, on=category_col, how="left")

        # Two charts side by side
        left_c, right_c = st.columns(2)
        with left_c:
            fig = px.bar(
                cat, x=category_col, y="Revenue",
                color=category_col, template="plotly_dark",
                title="Revenue by Category"
            )
            show_plot("Revenue by Category", fig,
                      tip="Total sales revenue for each category.")
        with right_c:
            fig = px.pie(
                cat, names=category_col, values="Revenue",
                hole=0.45, template="plotly_dark",
                title="Category Revenue Share"
            )
            show_plot("Category Revenue Share", fig,
                      tip="Each category's share of total revenue as a percentage.")

        show_table("Category Performance", cat,
                   tip="Revenue, transactions, avg sale, and units sold per category.")
    else:
        st.info("Category analysis needs category and sales/revenue columns.")

    # --- Item/Product-level analysis ---
    if item_col and total_col:
        tooltip_heading(
            "Product Performance",
            "Revenue and transaction count for each individual product. "
            "Use the slider to control how many products appear in the chart.",
            level="subheader"
        )

        # Aggregate by product
        product = (
            filtered.groupby(item_col, dropna=False)
            .agg(Revenue=(total_col, "sum"), Transactions=(total_col, "size"))
            .reset_index()
            .sort_values("Revenue", ascending=False)
        )
        if qty_col:
            prod_qty = (
                filtered.groupby(item_col, dropna=False)[qty_col]
                .sum().reset_index(name="Units")
            )
            product = product.merge(prod_qty, on=item_col, how="left")

        # Slider: choose how many top products to show in the chart
        max_products     = min(30, max(5, len(product)))
        default_products = min(10, max(5, len(product)))
        top_n = st.slider(
            "Products to display in chart", 5, max_products, default_products
        )
        top = product.head(top_n)

        # Top N products bar chart (from project documentation)
        fig = px.bar(
            top, x=item_col, y="Revenue",
            template="plotly_dark",
            title=f"Top {len(top)} Products by Revenue"
        )
        show_plot(f"Top {len(top)} Products by Revenue", fig,
                  tip=f"The {len(top)} highest-revenue products in the current filter.")

        show_table("All Products", product,
                   tip="Revenue, transactions, and units for every product.")


# =============================================================================
# PAGE 4 — CUSTOMER ANALYSIS
# Shows spending patterns by individual customer.
# =============================================================================
elif page == "Customer Analysis":
    page_title_above_hero("Customer Analysis")
    tooltip_heading(
        "Customer Analysis",
        "Breaks down revenue and transaction counts by customer ID. "
        "Shows top spenders and repeat customer rate.",
        level="header"
    )

    if not customer_col:
        st.info(
            "No customer identifier was detected in this dataset. "
            "Add a column such as 'Customer ID' to enable customer-level analysis."
        )
    elif total_col:
        # Aggregate by customer: total spend, number of transactions
        customer = (
            filtered.groupby(customer_col, dropna=False)
            .agg(Total_Spent=(total_col, "sum"), Transactions=(total_col, "size"))
            .reset_index()
            .sort_values("Total_Spent", ascending=False)
        )
        if qty_col:
            cust_qty = (
                filtered.groupby(customer_col, dropna=False)[qty_col]
                .sum().reset_index(name="Units")
            )
            customer = customer.merge(cust_qty, on=customer_col, how="left")

        # Average transaction value per customer
        customer["Avg_Transaction"] = (
            customer["Total_Spent"] / customer["Transactions"]
        )

        # KPI cards
        a, b, c = st.columns(3)
        a.metric("Unique Customers",
                 f"{filtered[customer_col].nunique(dropna=True):,}")
        b.metric("Total Revenue", f"Rs {revenue:,.2f}")
        avg_per_cust = customer["Total_Spent"].mean() if not customer.empty else None
        c.metric("Average per Customer",
                 f"Rs {avg_per_cust:,.2f}" if avg_per_cust else "—")

        # --- Repeat customer percentage ---
        # A "repeat" customer is one who made more than 1 transaction
        repeat_customers = int((customer["Transactions"] > 1).sum())
        total_customers  = len(customer)
        if total_customers > 0:
            repeat_pct = round(repeat_customers / total_customers * 100, 1)
            st.info(
                f"Repeat customers: **{repeat_customers}** out of "
                f"**{total_customers}** ({repeat_pct}%)"
            )

        # Top 10 customers bar chart (from project documentation)
        top10_cust = customer.head(10)
        fig = px.bar(
            top10_cust, x=customer_col, y="Total_Spent",
            template="plotly_dark", title="Top 10 Customers by Spend"
        )
        show_plot("Top 10 Customers by Spend", fig,
                  tip="The 10 customers who spent the most in total.")

        show_table("Customer Summary", customer,
                   tip="Every customer's total spend, transactions, units, "
                       "and average transaction value.")
    else:
        st.info("Customer analysis needs a sales/revenue column.")


# =============================================================================
# PAGE 5 — PAYMENT ANALYSIS
# Shows how customers paid (Cash, Card, UPI, etc.) and related revenue.
# Also includes location analysis and discount usage analysis.
# =============================================================================
elif page == "Payment Analysis":
    page_title_above_hero("Payment Analysis")
    tooltip_heading(
        "Payment Analysis",
        "Shows transaction counts and revenue split by payment method. "
        "Also shows location revenue and discount usage.",
        level="header"
    )

    if not payment_col:
        st.info(
            "No payment-method column was detected. "
            "Expected examples: Payment Method, Payment Type, or Payment."
        )
    else:
        # Aggregate by payment method: count transactions
        pay = (
            filtered.groupby(payment_col, dropna=False)
            .size().reset_index(name="Transactions")
        )
        if total_col:
            pay_rev = (
                filtered.groupby(payment_col, dropna=False)[total_col]
                .agg(Revenue="sum", Avg_Sale="mean").reset_index()
            )
            pay = pay.merge(pay_rev, on=payment_col, how="left")
            pay = pay.sort_values("Revenue", ascending=False)

        # Two charts side by side
        left_p, right_p = st.columns(2)
        with left_p:
            fig = px.bar(
                pay, x=payment_col, y="Transactions",
                color=payment_col, template="plotly_dark",
                title="Transactions by Payment Method"
            )
            show_plot("Transactions by Payment Method", fig,
                      tip="How many transactions used each payment method.")
        with right_p:
            if "Revenue" in pay.columns:
                fig = px.pie(
                    pay, names=payment_col, values="Revenue",
                    hole=0.45, template="plotly_dark",
                    title="Revenue by Payment Method"
                )
                show_plot("Revenue by Payment Method", fig,
                          tip="Revenue share for each payment method.")

        show_table("Payment Summary", pay,
                   tip="Transactions, revenue, and average sale by payment method.")

        # --- Location analysis ---
        if location_col and total_col:
            st.divider()
            tooltip_heading(
                "Revenue by Location",
                "Revenue and transaction count broken down by store/city location.",
                level="subheader"
            )
            loc_agg = (
                filtered.groupby(location_col, dropna=False)
                .agg(Revenue=(total_col, "sum"),
                     Transactions=(total_col, "size"),
                     Avg_Sale=(total_col, "mean"))
                .reset_index()
                .sort_values("Revenue", ascending=False)
            )
            fig = px.bar(
                loc_agg, x=location_col, y="Revenue",
                color=location_col, template="plotly_dark",
                title="Revenue by Location"
            )
            show_plot("Revenue by Location", fig,
                      tip="Total revenue earned at each store/city.")
            show_table("Location Summary", loc_agg,
                       tip="Revenue, transactions, and avg sale by location.")

        # --- Discount analysis ---
        if discount_col and total_col:
            st.divider()
            tooltip_heading(
                "Discount Usage",
                "Compares transaction counts and revenue for discounted vs "
                "non-discounted transactions. Labels use Yes/No/Unknown.",
                level="subheader"
            )
            disc_agg = (
                filtered.groupby(discount_col, dropna=False)
                .agg(Transactions=(total_col, "size"),
                     Revenue=(total_col, "sum"),
                     Avg_Sale=(total_col, "mean"))
                .reset_index()
                .sort_values("Revenue", ascending=False)
            )
            fig = px.bar(
                disc_agg, x=discount_col, y="Transactions",
                color=discount_col, template="plotly_dark",
                title="Transactions by Discount Status"
            )
            show_plot("Transactions by Discount Status", fig,
                      tip="How many transactions had a discount applied.")
            show_table("Discount Summary", disc_agg,
                       tip="Discount vs no-discount comparison of revenue and average sale.")


# =============================================================================
# PAGE 6 — EXPLORATORY DATA ANALYSIS (EDA)
# EDA means exploring the dataset to understand its structure and find patterns.
# We show: column types, statistics, distribution histograms, correlation matrix,
# pivot table, and seaborn visualisations from the project documentation.
# =============================================================================
elif page == "Exploratory Data Analysis":
    page_title_above_hero("Exploratory Data Analysis")
    tooltip_heading(
        "Exploratory Data Analysis",
        "Understand the dataset structure, statistical properties, correlations, "
        "and patterns across categories, locations, and time.",
        level="header"
    )

    # --- Dataset shape ---
    a, b = st.columns(2)
    a.metric("Rows (after filter)", f"{len(filtered):,}")
    b.metric("Columns",             f"{filtered.shape[1]:,}")

    # Column profile table
    schema = pd.DataFrame({
        "Column":        filtered.columns,
        "Data Type":     [str(x) for x in filtered.dtypes],
        "Non-null":      [int(filtered[c].notna().sum()) for c in filtered.columns],
        "Unique Values": [int(filtered[c].nunique(dropna=True)) for c in filtered.columns],
    })
    show_table("Column Profile", schema,
               tip="Shows data type, non-null count, and number of distinct values "
                   "for each column.")

    # --- Descriptive statistics ---
    tooltip_heading(
        "Descriptive Statistics",
        "Count, mean, standard deviation, min, max, and quartiles for each "
        "numeric column. Helps identify data ranges and outliers.",
        level="subheader"
    )
    numeric = filtered.select_dtypes(include=np.number)

    if not numeric.empty:
        show_table("Numeric Summary", numeric.describe().T.reset_index(names="Column"),
                   tip="Statistical summary: mean, std, min, 25%, 50%, 75%, max.")

        numeric_col_list = numeric.columns.tolist()

        # Distribution histogram for a chosen column
        chosen = st.selectbox("Choose a numeric column to view distribution",
                              numeric_col_list)
        # A histogram groups values into bins and counts how many fall in each bin.
        # It helps us see the shape of the data (normal, skewed, multi-peak, etc.)
        fig = px.histogram(
            filtered, x=chosen, nbins=30,
            template="plotly_dark", title=f"Distribution of {chosen}"
        )
        show_plot(f"Distribution of {chosen}", fig,
                  tip=f"Histogram showing how {chosen} values are spread. "
                      "Helps spot skew or unusual clusters.")

        # --- Correlation Matrix ---
        # A correlation matrix shows how strongly two numeric columns are related.
        # Values close to +1 = strong positive relationship (both go up together)
        # Values close to -1 = strong negative relationship (one up, other down)
        # Values near 0     = little to no relationship
        if len(numeric_col_list) > 1:
            tooltip_heading(
                "Correlation Matrix",
                "Correlation measures how two numeric columns change together. "
                "+1 = perfect positive, -1 = perfect negative, 0 = no relationship.",
                level="subheader"
            )
            corr = numeric.corr(numeric_only=True)
            fig_corr = px.imshow(
                corr, text_auto=True, aspect="auto",
                color_continuous_scale="Blues",
                template="plotly_dark",
                title="Numeric Correlation Matrix"
            )
            show_plot("Correlation Matrix", fig_corr,
                      tip="Heat-map of correlation coefficients between all "
                          "numeric columns.")

        # --- Box Plot: Transaction value by category (Seaborn) ---
        # A box plot shows the spread of values:
        #   - The box covers the middle 50% of data (the interquartile range)
        #   - The line inside the box is the median (middle value)
        #   - Whiskers extend to the minimum and maximum reasonable values
        #   - Dots outside the whiskers are outliers (unusually high/low values)
        if category_col and total_col:
            st.divider()
            tooltip_heading(
                "Transaction Value by Category (Box Plot)",
                "Box plots compare the spread and median of transaction values "
                "across categories. The box covers the middle 50% of values; "
                "dots outside the whiskers are outliers.",
                level="subheader"
            )
            fig_box, ax_box = plt.subplots(figsize=(10, 5))
            fig_box.patch.set_facecolor("#0b1120")
            ax_box.set_facecolor("#0b1120")

            sns.boxplot(
                data=filtered.dropna(subset=[category_col, total_col]),
                x=category_col, y=total_col,
                palette="Blues_d", ax=ax_box
            )
            ax_box.set_title("Transaction Value by Category", color="white")
            ax_box.set_xlabel(category_col, color="white")
            ax_box.set_ylabel(total_col,    color="white")
            ax_box.tick_params(colors="white", axis="both")
            for spine in ax_box.spines.values():
                spine.set_edgecolor("#294365")
            plt.tight_layout()
            mpl_fig_to_st(fig_box,
                          "Box plot: spread of transaction values per category.")

        # --- Scatter Plot: Price Per Unit vs Total Spent (Matplotlib) ---
        # Each dot represents one transaction.
        # If expensive items also have high totals, we expect a positive slope.
        if price_col and total_col:
            st.divider()
            tooltip_heading(
                "Price Per Unit vs Total Spent",
                "Scatter plot showing the relationship between unit price and "
                "total sale value. Each dot is one transaction.",
                level="subheader"
            )
            scatter_data = filtered[[price_col, total_col]].dropna()
            fig_sc, ax_sc = plt.subplots(figsize=(8, 5))
            fig_sc.patch.set_facecolor("#0b1120")
            ax_sc.set_facecolor("#0b1120")
            ax_sc.scatter(
                scatter_data[price_col], scatter_data[total_col],
                alpha=0.5, color="#4a8ac7", edgecolors="none", s=30
            )
            ax_sc.set_title("Price Per Unit vs Total Spent", color="white")
            ax_sc.set_xlabel(price_col,  color="white")
            ax_sc.set_ylabel(total_col,  color="white")
            ax_sc.tick_params(colors="white", axis="both")
            for spine in ax_sc.spines.values():
                spine.set_edgecolor("#294365")
            plt.tight_layout()
            mpl_fig_to_st(fig_sc,
                          "Each point is one transaction. Higher priced items "
                          "tend to have higher total sales.")

        # --- Revenue Heatmap by Category and Month (Seaborn) ---
        # A heatmap uses colours to show values in a grid.
        # pd.pivot_table() builds the grid: rows = categories, cols = months.
        if (category_col and total_col and date_col
                and pd.api.types.is_datetime64_any_dtype(filtered[date_col])):
            st.divider()
            tooltip_heading(
                "Revenue Heatmap: Category x Month",
                "A pivot table shown as a colour map. Rows = categories, "
                "columns = months. Darker cells = higher revenue.",
                level="subheader"
            )
            heat_df = filtered.dropna(
                subset=[date_col, category_col, total_col]
            ).copy()
            heat_df["_Month"] = heat_df[date_col].dt.to_period("M").astype(str)

            # pivot_table: rows=category, columns=month, values=sum of revenue
            pivot = pd.pivot_table(
                heat_df, values=total_col,
                index=category_col, columns="_Month",
                aggfunc="sum", fill_value=0
            )

            if not pivot.empty:
                fig_heat, ax_heat = plt.subplots(
                    figsize=(max(8, len(pivot.columns)),
                             max(4, len(pivot) * 0.8))
                )
                fig_heat.patch.set_facecolor("#0b1120")
                ax_heat.set_facecolor("#0b1120")
                sns.heatmap(
                    pivot, annot=True, fmt=".0f",
                    cmap="Blues", ax=ax_heat,
                    linewidths=0.5, linecolor="#101b2e",
                    annot_kws={"color": "white", "size": 8}
                )
                ax_heat.set_title("Revenue Heatmap: Category x Month", color="white")
                ax_heat.set_xlabel("Month",      color="white")
                ax_heat.set_ylabel(category_col, color="white")
                ax_heat.tick_params(colors="white", axis="both")
                plt.tight_layout()
                mpl_fig_to_st(fig_heat,
                              "Revenue (Rs) for each category per month.")

                # Also show the pivot table as a downloadable table
                show_table("Revenue Pivot (Category x Month)",
                           pivot.reset_index(),
                           tip="Revenue summary table: rows = categories, "
                               "columns = calendar months.")

        # --- Category vs Location Grouped Bar Chart (Matplotlib) ---
        # A grouped bar chart places multiple bars side by side for each
        # category, one bar per location — easy comparison.
        if category_col and location_col and total_col:
            st.divider()
            tooltip_heading(
                "Revenue: Category x Location",
                "Grouped bar chart comparing revenue for each category "
                "across different locations/cities.",
                level="subheader"
            )
            grp_df = filtered.dropna(
                subset=[category_col, location_col, total_col]
            )
            grp_pivot = (
                grp_df.groupby([category_col, location_col])[total_col]
                .sum().unstack(fill_value=0)
            )
            if not grp_pivot.empty:
                fig_grp, ax_grp = plt.subplots(figsize=(10, 5))
                fig_grp.patch.set_facecolor("#0b1120")
                ax_grp.set_facecolor("#0b1120")
                grp_pivot.plot(kind="bar", ax=ax_grp,
                               colormap="Blues_r", width=0.7)
                ax_grp.set_title("Revenue by Category and Location", color="white")
                ax_grp.set_xlabel(category_col, color="white")
                ax_grp.set_ylabel("Revenue",    color="white")
                ax_grp.tick_params(colors="white", axis="both", labelrotation=30)
                ax_grp.legend(title=location_col, labelcolor="white",
                              facecolor="#101b2e", edgecolor="#294365",
                              title_fontsize=9)
                for spine in ax_grp.spines.values():
                    spine.set_edgecolor("#294365")
                plt.tight_layout()
                mpl_fig_to_st(fig_grp,
                              "Grouped bars compare revenue per category "
                              "across locations.")

    else:
        st.info("No numeric columns are available for statistical analysis.")

    # --- Categorical column value explorer ---
    cat_cols = filtered.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        st.divider()
        tooltip_heading(
            "Categorical Column Explorer",
            "Pick any text/category column to see the most common values.",
            level="subheader"
        )
        chosen_cat = st.selectbox(
            "Choose a categorical column to explore", cat_cols
        )
        counts = (
            filtered[chosen_cat].astype(str)
            .value_counts(dropna=False).head(20)
            .reset_index()
        )
        counts.columns = [chosen_cat, "Count"]
        fig = px.bar(
            counts, x=chosen_cat, y="Count",
            template="plotly_dark",
            title=f"Top values in '{chosen_cat}'"
        )
        show_plot(f"Top values in '{chosen_cat}'", fig,
                  tip=f"The most frequent values in the {chosen_cat} column "
                      "(up to top 20).")


# =============================================================================
# PAGE 7 — DATA QUALITY & CLEANING
# Shows before-and-after statistics from the cleaning process.
# =============================================================================
elif page == "Data Quality & Cleaning":
    page_title_above_hero("Data Quality & Cleaning")
    tooltip_heading(
        "Data Quality & Cleaning",
        "Shows how many duplicates were removed, how missing values were "
        "filled, and the current state of the dataset after cleaning.",
        level="header"
    )

    # Count missing values before and after cleaning
    before_missing = raw_df.isna().sum()
    after_missing  = df.isna().sum()

    # KPI cards showing cleaning summary
    a, b, c, d = st.columns(4)
    a.metric("Original Rows",    f"{cleaning_report['rows_before']:,}")
    b.metric("Cleaned Rows",     f"{cleaning_report['rows_after']:,}")
    c.metric("Duplicates Found", f"{cleaning_report['duplicates_removed']:,}")
    d.metric("Rows Removed",     f"{cleaning_report['rows_removed']:,}")

    st.caption(
        "Cleaning steps: duplicate removal -> date parsing -> numeric conversion -> "
        "recovery of missing totals (Qty x Price) -> median/mode filling -> "
        "standardise Discount Applied labels (Yes/No/Unknown) -> remove fully blank rows."
    )

    # Per-column quality report table
    quality = pd.DataFrame({
        "Column":         raw_df.columns,
        "Missing Before": [int(before_missing[c]) for c in raw_df.columns],
        "Missing After":  [int(after_missing.get(c, 0)) for c in raw_df.columns],
        "Type Before":    [str(raw_df[c].dtype) for c in raw_df.columns],
        "Type After":     [str(df[c].dtype) if c in df.columns else "removed"
                           for c in raw_df.columns],
    })
    show_table("Data Quality Report", quality,
               tip="Compares missing value counts and data types before and "
                   "after cleaning for every column.")

    # Cleaned data preview
    tooltip_heading(
        "Cleaned Data Preview",
        "Shows the first 10 rows of the cleaned dataset. "
        "Click the link to see all rows in a new tab.",
        level="subheader"
    )
    show_table("Cleaned Records", df)

    # Download the cleaned CSV
    st.download_button(
        "Download cleaned CSV",
        df.to_csv(index=False).encode("utf-8"),
        "cleaned_retail_store_sales.csv",
        "text/csv",
    )


# =============================================================================
# PAGE 8 — DATA EXPLORER
# Lets the user search through the filtered data, choose which columns to show,
# and download the result.
# =============================================================================
elif page == "Data Explorer":
    page_title_above_hero("Data Explorer")
    tooltip_heading(
        "Data Explorer",
        "Search and browse the filtered records. Choose which columns to "
        "display and download the result as a CSV.",
        level="header"
    )
    st.caption("Search, choose columns, and inspect the currently filtered records.")

    # Free-text search across all columns
    search = st.text_input("Search across all columns (type any keyword)")
    explorer = filtered.copy()

    if search.strip():
        # Convert all values to strings, then check if any column in each
        # row contains the search word (case-insensitive)
        mask = (
            explorer.astype(str)
            .apply(lambda col: col.str.contains(search.strip(), case=False, na=False))
            .any(axis=1)
        )
        explorer = explorer[mask]

    # Column selector: choose which columns to display
    chosen_cols = st.multiselect(
        "Columns to display",
        list(explorer.columns),
        default=list(explorer.columns)
    )
    if chosen_cols:
        explorer = explorer[chosen_cols]

    show_table("Filtered Data", explorer,
               tip="The currently filtered and searched records. "
                   "Modify sidebar filters or the search box to change this view.")

    # Download the current explorer result
    st.download_button(
        "Download explorer results (CSV)",
        explorer.to_csv(index=False).encode("utf-8"),
        "retail_data_explorer.csv",
        "text/csv",
    )


# =============================================================================
# PAGE 9 — REPORTS & DOWNLOADS
# Provides download buttons for cleaned data, filtered data, and a JSON
# summary of KPIs.
# =============================================================================
elif page == "Reports & Downloads":
    page_title_above_hero("Reports & Downloads")
    tooltip_heading(
        "Reports & Downloads",
        "Download the dataset and analysis summaries to use in your project "
        "report, documentation, or presentations.",
        level="header"
    )
    st.write(
        "Download the dataset and analysis summaries for your "
        "report or project review."
    )

    # st.download_button: when clicked, the user's browser downloads the file
    st.download_button(
        "Download current filtered data (CSV)",
        filtered.to_csv(index=False).encode("utf-8"),
        "retail_sales_filtered.csv",
        "text/csv",
    )
    st.download_button(
        "Download cleaned full dataset (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        "cleaned_retail_store_sales.csv",
        "text/csv",
    )

    # Build a JSON summary dictionary and offer it as a download
    if total_col:
        summary = {
            "source":                data_source,
            "rows_in_filtered_view": int(len(filtered)),
            "total_revenue":         float(revenue),
            "average_sale":          float(avg_sale),
            "transactions":          int(transactions),
            "units_sold":            float(units) if qty_col else None,
            "date_column":           date_col,
            "category_column":       category_col,
            "item_column":           item_col,
            "payment_column":        payment_col,
            "location_column":       location_col,
        }
        st.download_button(
            "Download KPI summary (JSON)",
            json.dumps(summary, indent=2).encode("utf-8"),
            "retail_sales_summary.json",
            "application/json",
        )

    # Category-level summary CSV
    if category_col and total_col:
        cat_summary = (
            filtered.groupby(category_col, dropna=False)[total_col]
            .agg(["sum", "mean", "count"])
            .reset_index()
        )
        cat_summary.columns = [
            category_col, "Total Revenue", "Average Sale", "Transactions"
        ]
        st.download_button(
            "Download category summary (CSV)",
            cat_summary.to_csv(index=False).encode("utf-8"),
            "category_summary.csv",
            "text/csv",
        )

    st.info(
        "For college documentation, include screenshots of the Overview, "
        "Trends, Data Quality, and Downloads pages."
    )


# =============================================================================
# PAGE 10 — PROJECT INFORMATION
# Describes the project objectives, methodology, and technology stack.
# Useful for viva/review presentations.
# =============================================================================
elif page == "Project Information":
    page_title_above_hero("Project Information")
    tooltip_heading(
        "Project Information",
        "Overview of the project objectives, technology used, methodology, "
        "and the columns the app expects in a retail CSV file.",
        level="header"
    )
    st.markdown("""
    ### Retail Store Sales Analysis

    **Objective:**
    Analyze retail transaction data to understand sales performance,
    product/category contribution, customer spending patterns,
    payment method usage, and data quality.

    ---

    **Technology Stack**

    | Library     | Purpose |
    |-------------|---------|
    | Python      | Core programming language |
    | Streamlit   | Interactive web dashboard |
    | Pandas      | Data loading, cleaning, aggregation |
    | NumPy       | Numerical operations (np.diff, np.round, np.where) |
    | Plotly      | Interactive bar, line, pie, scatter, heatmap charts |
    | Matplotlib  | Static charts (scatter, box, grouped bar) |
    | Seaborn     | Statistical charts (box plot, heatmap with annotations) |

    ---

    **Methodology**
    1. Upload a retail CSV file or use the built-in demonstration dataset.
    2. The app automatically detects common column names (date, category, etc.).
    3. Data is cleaned: duplicates removed, dates parsed, missing values filled.
    4. KPIs are calculated: revenue, transactions, units, average sale.
    5. Each dashboard section presents a different analytical perspective.
    6. Cleaned data and summaries can be downloaded for reporting.

    ---

    **Data note:**
    Analysis sections depend on the columns in your CSV file. The app will
    explain when a required column is missing rather than inventing results.

    | Data Type    | Recognised Column Names |
    |--------------|-------------------------|
    | Date         | Transaction Date, Date, Order Date, Purchase Date |
    | Category     | Category, Product Category, Item Category |
    | Item         | Item, Product, Product Name |
    | Customer     | Customer ID, Customer, Customer Name |
    | Payment      | Payment Method, Payment Type, Payment |
    | Location     | Location, City, Store, Branch, Region |
    | Discount     | Discount Applied, Discount, Promo, Coupon |
    | Quantity     | Quantity, Qty, Units Sold |
    | Unit Price   | Price Per Unit, Unit Price, Price |
    | Total Value  | Total Spent, Total Sales, Revenue, Sales, Amount |
    """)

    tooltip_heading(
        "Current Dataset Columns",
        "Lists all columns found in the cleaned dataset with their data types.",
        level="subheader"
    )
    show_table("Available Columns",
               pd.DataFrame({
                   "Column":    df.columns,
                   "Data Type": [str(x) for x in df.dtypes]
               }),
               tip="These are the columns detected in your uploaded CSV "
                   "or the demo dataset.")


# =============================================================================
# PAGE FOOTER
# A small footer line shown at the bottom of every page.
# =============================================================================
st.markdown("---")
st.markdown(
    '<p class="small-note">Retail Store Sales Analysis · '
    'Interactive academic project dashboard</p>',
    unsafe_allow_html=True,
)
