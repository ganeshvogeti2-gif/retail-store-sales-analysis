import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="Retail Store Sales Analysis",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #0b1120;
    color: #ffffff;
}
[data-testid="stMetric"] {
    background: #17243a;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #28456a;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Retail Store Sales Analysis")
st.caption("Interactive Sales Analytics Dashboard")

uploaded = st.sidebar.file_uploader(
    "Upload your retail CSV file",
    type=["csv"]
)

if uploaded:
    df = pd.read_csv(uploaded)
else:
    st.info("Upload your retail_store_sales.csv file in the sidebar to analyze your data.")
    df = pd.DataFrame({
        "Category": ["Food", "Clothing", "Electronics", "Food", "Clothing"],
        "Item": ["Rice", "Shirt", "Headphones", "Milk", "Jeans"],
        "Quantity": [5, 2, 1, 3, 2],
        "Price Per Unit": [10, 25, 80, 4, 30],
        "Total Spent": [50, 50, 80, 12, 60]
    })

required = ["Category", "Quantity", "Price Per Unit", "Total Spent"]

if all(col in df.columns for col in required):
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Price Per Unit"] = pd.to_numeric(
        df["Price Per Unit"], errors="coerce"
    )
    df["Total Spent"] = pd.to_numeric(
        df["Total Spent"], errors="coerce"
    )
    df = df.dropna(subset=required)

    if not df.empty:
        revenue = df["Total Spent"].sum()
        units = df["Quantity"].sum()
        transactions = len(df)
        average = df["Total Spent"].mean()

        a, b, c, d = st.columns(4)
        a.metric("Total Revenue", f"${revenue:,.2f}")
        b.metric("Transactions", f"{transactions:,}")
        c.metric("Units Sold", f"{units:,.0f}")
        d.metric("Average Sale", f"${average:,.2f}")

        st.divider()

        left, right = st.columns(2)

        with left:
            st.subheader("Revenue by Category")
            category = df.groupby(
                "Category", as_index=False
            )["Total Spent"].sum()

            fig = px.bar(
                category,
                x="Category",
                y="Total Spent",
                color="Category",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("Sales Distribution")
            fig = px.pie(
                category,
                names="Category",
                values="Total Spent",
                hole=0.45,
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Sales Data")
        st.dataframe(df, use_container_width=True)

        st.download_button(
            "Download analyzed data",
            df.to_csv(index=False),
            file_name="retail_sales_data.csv",
            mime="text/csv"
        )
    else:
        st.error("No valid sales rows found. Check your CSV data.")
else:
    st.error(
        "Your CSV is missing required columns: "
        + ", ".join(required)
    )
