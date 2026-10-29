
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

DATA_FILES = [
    BASE_DIR / "sales_data2.csv",
    BASE_DIR / "data" / "sales_data2.csv",
    BASE_DIR / "sales_data.csv",
    BASE_DIR / "data" / "sales_data.csv",
]

REQUIRED_COLUMNS = [
    "Order Date",
    "Sales",
    "Profit",
    "Category",
    "Region",
    "Product",
]

import pandas as pd



def load_data(file=None):
    """Load sales data from an uploaded file or project CSV."""

    if file is not None:
        if hasattr(file, "read"):
            return pd.read_csv(file)

        path = Path(file)

        if not path.is_absolute():
            path = BASE_DIR / path

        if not path.is_file():
            raise FileNotFoundError(
                f"Sales data file not found: {path}"
            )

        return pd.read_csv(path)

    for path in DATA_FILES:
        if path.is_file():
            return pd.read_csv(path)

    raise FileNotFoundError(
        "Sales CSV not found. Add sales_data2.csv or "
        "sales_data.csv to the project folder or data folder."
    )


def prepare_data(df):
    """Calculate revenue, cost, and profit."""
    df = df.copy()

    required_columns = [
        "Quantity",
        "Unit_Price",
        "Unit_Cost",
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}"
        )

    for column in required_columns:
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )

    # Remove rows without essential sales values
    df = df.dropna(subset=required_columns)

    # Calculate financial metrics
    df["Revenue"] = df["Quantity"] * df["Unit_Price"]
    df["Total_Cost"] = df["Quantity"] * df["Unit_Cost"]
    df["Profit"] = df["Revenue"] - df["Total_Cost"]

    return df


def get_kpis(df):
    """Calculate key performance indicators."""
    total_revenue = df["Revenue"].sum()
    total_cost = df["Total_Cost"].sum()
    total_profit = df["Profit"].sum()
    total_quantity = df["Quantity"].sum()

    total_orders = (
        df["Order_ID"].nunique()
        if "Order_ID" in df.columns
        else len(df)
    )

    profit_margin = (
        (total_profit / total_revenue) * 100
        if total_revenue != 0
        else 0
    )

    return {
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "total_quantity": total_quantity,
        "total_orders": total_orders,
        "profit_margin": profit_margin,
    }


def sales_by_region(df):
    """Summarize revenue and profit by region."""
    if "Region" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("Region", dropna=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Quantity=("Quantity", "sum"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )


def sales_by_category(df):
    """Summarize revenue and profit by category."""
    if "Category" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("Category", dropna=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Quantity=("Quantity", "sum"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )


def sales_by_product(df):
    """Summarize performance by product."""
    if "Product" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("Product", dropna=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Quantity=("Quantity", "sum"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )


def monthly_sales(df):
    """Calculate monthly revenue and profit."""
    if "Order_Date" not in df.columns:
        return pd.DataFrame()

    data = df.dropna(subset=["Order_Date"]).copy()

    data["Month"] = (
        data["Order_Date"].dt.to_period("M").astype(str)
    )

    return (
        data.groupby("Month")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
        )
        .reset_index()
        .sort_values("Month")
    )


def monthly_growth(df):
    """Calculate month-over-month sales and profit growth."""

    result = monthly_sales(df)

    result["Sales Growth (%)"] = (
        result["Sales"].pct_change(fill_method=None) * 100
    )

    result["Profit Growth (%)"] = (
        result["Profit"].pct_change(fill_method=None) * 100
    )

    return result



def get_insights(df):
    """Generate descriptive business insights from sales data."""

    if df is None or df.empty:
        return ["No records available for analysis."]

    insights = []

    category_data = sales_by_category(df)
    region_data = sales_by_region(df)
    product_data = sales_by_product(df)

    best_category = category_data.loc[
        category_data["Revenue"].idxmax()
    ]

    best_region = region_data.loc[
        region_data["Revenue"].idxmax()
    ]

    best_product = product_data.loc[
        product_data["Revenue"].idxmax()
    ]

    insights.append(
        f"Top category by revenue: {best_category['Category']} "
        f"({best_category['Revenue']:,.2f})."
    )

    insights.append(
        f"Top region by revenue: {best_region['Region']} "
        f"({best_region['Revenue']:,.2f})."
    )

    insights.append(
        f"Top product by revenue: {best_product['Product']} "
        f"({best_product['Revenue']:,.2f})."
    )

    kpis = get_kpis(df)

    insights.append(
        f"Overall profit margin: "
        f"{kpis['profit_margin']:.2f}%."
    )

    if kpis["total_profit"] < 0:
        insights.append(
            "Overall profit is negative. Investigate "
            "loss-making products and regions."
        )

    # Identify the most profitable category
    best_profit_category = category_data.loc[
        category_data["Profit"].idxmax()
    ]

    insights.append(
        f"Most profitable category: "
        f"{best_profit_category['Category']} "
        f"({best_profit_category['Profit']:,.2f} profit)."
    )

    return insights
