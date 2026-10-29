
import pandas as pd
import streamlit as st
import plotly.express as px

from analysis import (
    load_data,
    prepare_data,
    get_kpis,
    sales_by_region,
    sales_by_category,
    sales_by_product,
    monthly_sales,
    get_insights,
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Sales Analytics Dashboard")
st.caption(
    "Business Intelligence | Revenue | Profitability | "
    "Product Performance"
)


# ==================================================
# LOAD AND PREPARE DATA
# ==================================================

try:
    df = prepare_data(load_data())
    df["Order_Date"] = pd.to_datetime(
        df["Order_Date"], errors="coerce"
    )
    df = df.dropna(subset=["Order_Date"]).copy()

except Exception as exc:
    st.error(f"Could not load the sales dataset: {exc}")
    st.info(
        "Check the CSV file and the column names in analysis.py."
    )
    st.stop()

if df.empty:
    st.error("No valid sales records or order dates were found.")
    st.stop()

required_columns = [
    "Order_Date", "Revenue", "Profit",
    "Category", "Region", "Product",
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(f"Missing dataset columns: {missing_columns}")
    st.stop()


# ==================================================
# SIDEBAR FILTERS
# ==================================================

st.sidebar.title("📊 Dashboard Filters")

min_date = df["Order_Date"].min().date()
max_date = df["Order_Date"].max().date()

date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

categories = sorted(df["Category"].dropna().unique().tolist())
regions = sorted(df["Region"].dropna().unique().tolist())
products = sorted(df["Product"].dropna().unique().tolist())

selected_categories = st.sidebar.multiselect(
    "Category", categories, default=categories
)
selected_regions = st.sidebar.multiselect(
    "Region", regions, default=regions
)
selected_products = st.sidebar.multiselect(
    "Product", products, default=products
)

if len(date_range) != 2:
    st.warning("Select both a start date and an end date.")
    st.stop()

start_date, end_date = date_range

if start_date > end_date:
    st.error("The start date must not be after the end date.")
    st.stop()

filtered_df = df[
    (df["Order_Date"].dt.date >= start_date)
    & (df["Order_Date"].dt.date <= end_date)
    & df["Category"].isin(selected_categories)
    & df["Region"].isin(selected_regions)
    & df["Product"].isin(selected_products)
].copy()

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()


# ==================================================
# KPI CARDS
# ==================================================

st.subheader("Executive Overview")

kpis = get_kpis(filtered_df)

c1, c2, c3, c4 = st.columns(4)

c1.metric("💰 Total Revenue", f"{kpis['total_revenue']:,.2f}")
c2.metric("📈 Total Profit", f"{kpis['total_profit']:,.2f}")
c3.metric("🎯 Profit Margin", f"{kpis['profit_margin']:.2f}%")
c4.metric("📦 Total Orders", f"{kpis['total_orders']:,}")

st.caption(
    f"{len(filtered_df):,} rows | "
    f"{filtered_df['Category'].nunique()} categories | "
    f"{filtered_df['Region'].nunique()} regions"
)


# ==================================================
# MONTHLY REVENUE AND PROFIT
# ==================================================

st.divider()
st.subheader("📈 Monthly Performance")

monthly = monthly_sales(filtered_df)

if not monthly.empty:
    revenue_column = (
        "Revenue" if "Revenue" in monthly.columns else "Sales"
    )

    if revenue_column in monthly.columns:
        revenue_fig = px.line(
            monthly,
            x="Month",
            y=revenue_column,
            markers=True,
            title="Monthly Revenue",
            template="plotly_white",
            color_discrete_sequence=["#2878B5"],
        )
        st.plotly_chart(revenue_fig, use_container_width=True)

    if "Profit" in monthly.columns:
        profit_fig = px.bar(
            monthly,
            x="Month",
            y="Profit",
            title="Monthly Profit",
            template="plotly_white",
            color="Profit",
            color_continuous_scale="Teal",
        )
        st.plotly_chart(profit_fig, use_container_width=True)

    # Calculate growth using the actual monthly revenue column.
    if revenue_column in monthly.columns:
        monthly_growth_data = monthly.sort_values("Month").copy()

        monthly_growth_data["Revenue Growth (%)"] = (
            monthly_growth_data[revenue_column]
            .pct_change(fill_method=None)
            .mul(100)
        )

        if "Profit" in monthly_growth_data.columns:
            monthly_growth_data["Profit Growth (%)"] = (
                monthly_growth_data["Profit"]
                .pct_change(fill_method=None)
                .mul(100)
            )

        st.subheader("📊 Month-over-Month Growth")

        display_columns = [
            "Month",
            "Revenue Growth (%)",
        ]

        if "Profit Growth (%)" in monthly_growth_data.columns:
            display_columns.append("Profit Growth (%)")

        st.dataframe(
            monthly_growth_data[display_columns].tail(12),
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info("No monthly data is available for this selection.")


# ==================================================
# CATEGORY AND REGION ANALYSIS
# ==================================================

st.divider()
st.subheader("🌍 Category and Regional Performance")

category_data = sales_by_category(filtered_df)
region_data = sales_by_region(filtered_df)

category_revenue = (
    "Revenue" if "Revenue" in category_data.columns else "Sales"
)
region_revenue = (
    "Revenue" if "Revenue" in region_data.columns else "Sales"
)

left, right = st.columns(2)

with left:
    category_fig = px.bar(
        category_data,
        x="Category",
        y=category_revenue,
        color="Category",
        title="Revenue by Category",
        template="plotly_white",
    )
    category_fig.update_layout(showlegend=False)
    st.plotly_chart(category_fig, use_container_width=True)

with right:
    region_fig = px.bar(
        region_data,
        x=region_revenue,
        y="Region",
        orientation="h",
        color="Profit" if "Profit" in region_data.columns else None,
        title="Revenue by Region",
        template="plotly_white",
    )
    st.plotly_chart(region_fig, use_container_width=True)


# ==================================================
# TOP PRODUCTS
# ==================================================

st.divider()
st.subheader("🏆 Top 10 Products by Revenue")

product_data = sales_by_product(filtered_df)

product_revenue = (
    "Revenue" if "Revenue" in product_data.columns else "Sales"
)

top_products = (
    product_data
    .sort_values(product_revenue, ascending=False)
    .head(10)
    .sort_values(product_revenue, ascending=True)
)

product_fig = px.bar(
    top_products,
    x=product_revenue,
    y="Product",
    orientation="h",
    color="Profit" if "Profit" in top_products.columns else None,
    title="Product Performance",
    template="plotly_white",
)

st.plotly_chart(product_fig, use_container_width=True)


# ==================================================
# BUSINESS INSIGHTS
# ==================================================

st.divider()
st.subheader("💡 Business Insights")

for insight in get_insights(filtered_df):
    st.info(insight)


# ==================================================
# DATA EXPLORER AND DOWNLOAD
# ==================================================

st.divider()
st.subheader("📋 Sales Data Explorer")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    label="⬇️ Download Filtered Data",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_sales_data.csv",
    mime="text/csv",
)

st.caption("Built with Python, Pandas, Plotly and Streamlit")
