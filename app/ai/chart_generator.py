import os
import logging
import re
import uuid
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional

logger = logging.getLogger("statbotpro.ai.chart_generator")

CHARTS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'charts'))
os.makedirs(CHARTS_DIR, exist_ok=True)

CHART_KEYWORDS = ("plot", "graph", "chart", "trend", "visualize")
NUMERIC_PRIORITY = ("Sales_Amount", "Quantity_Sold", "Unit_Price")
CATEGORY_PRIORITY = ("Product_Category", "Region", "Customer_Type", "Sales_Channel", "Payment_Method", "Sales_Rep")
DATE_PRIORITY = ("Sale_Date", "Date", "Order_Date", "Invoice_Date")
ID_KEYWORDS = ("id", "serial", "sku", "code", "number", "no")
COUNT_VALUE = "__count__"


def query_needs_chart(query: str) -> bool:
    lowered = query.lower()
    return any(keyword in lowered for keyword in CHART_KEYWORDS)


def infer_chart_type(query: str) -> str:
    lowered = query.lower()
    if "pie" in lowered:
        return "pie"
    if "line" in lowered or "trend" in lowered:
        return "line"
    return "bar"


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _is_id_like(column: str) -> bool:
    normalized = _normalize(column)
    return any(keyword in normalized for keyword in ID_KEYWORDS)


def _ranked_existing_columns(columns: list[str], priority: tuple[str, ...]) -> list[str]:
    by_normalized = {_normalize(column): column for column in columns}
    ranked = [by_normalized[_normalize(name)] for name in priority if _normalize(name) in by_normalized]
    return ranked + [column for column in columns if column not in ranked]


def _find_column_from_query(query: str, columns: list[str]) -> Optional[str]:
    normalized_query = query.lower()
    for column in columns:
        readable_name = str(column).lower().replace("_", " ")
        pattern = r"\b" + re.escape(readable_name) + r"\b"
        if re.search(pattern, normalized_query) or _normalize(column) in _normalize(query):
            return column
    return None


def _first(columns: list[str], priority: tuple[str, ...]) -> Optional[str]:
    ranked = _ranked_existing_columns(columns, priority)
    return ranked[0] if ranked else None


def infer_chart_columns(df: pd.DataFrame, query: str, chart_type: str) -> tuple[str, str, Optional[str]]:
    columns = list(df.columns)
    if not columns:
        raise ValueError("Dataset has no columns.")

    lowered = query.lower()
    intent_trend = "trend" in lowered or "over time" in lowered or "by date" in lowered
    intent_distribution = "distribution" in lowered or chart_type == "pie"
    intent_top_sales = "top" in lowered and ("sale" in lowered or "revenue" in lowered)

    numeric_columns = [column for column in df.select_dtypes(include="number").columns if not _is_id_like(column)]
    categorical_columns = [
        column
        for column in columns
        if column not in numeric_columns and not _is_id_like(column)
    ]
    known_date_columns = set(_ranked_existing_columns(columns, DATE_PRIORITY)[: len(DATE_PRIORITY)])
    date_columns = [column for column in columns if column in known_date_columns or "date" in str(column).lower()]

    numeric_columns = _ranked_existing_columns(numeric_columns, NUMERIC_PRIORITY)
    categorical_columns = _ranked_existing_columns(categorical_columns, CATEGORY_PRIORITY)
    date_columns = _ranked_existing_columns(date_columns, DATE_PRIORITY)

    query_category = _find_column_from_query(query, categorical_columns)
    query_numeric = _find_column_from_query(query, numeric_columns)
    group_col = None

    if intent_trend:
        x_col = _first(date_columns, DATE_PRIORITY) or query_category or (categorical_columns[0] if categorical_columns else columns[0])
        y_col = query_numeric or _first(numeric_columns, NUMERIC_PRIORITY)
        group_col = query_category
        return x_col, y_col, group_col

    if intent_distribution:
        x_col = query_category or _first(categorical_columns, CATEGORY_PRIORITY)
        y_col = query_numeric or (_first(numeric_columns, NUMERIC_PRIORITY) if any(
            word in lowered for word in ("sale", "sales", "revenue", "amount", "quantity", "price")
        ) else COUNT_VALUE)
        return x_col, y_col, None

    if intent_top_sales:
        x_col = query_category or _first(categorical_columns, CATEGORY_PRIORITY)
        y_col = query_numeric or _first(numeric_columns, NUMERIC_PRIORITY)
        return x_col, y_col, None

    x_col = query_category or _find_column_from_query(query, columns) or (categorical_columns[0] if categorical_columns else columns[0])
    y_col = query_numeric or _first(numeric_columns, NUMERIC_PRIORITY)

    if not x_col:
        x_col = categorical_columns[0] if categorical_columns else columns[0]
    if not y_col:
        y_col = numeric_columns[0] if numeric_columns else columns[-1]
    if x_col == y_col:
        alternatives = [column for column in numeric_columns if column != x_col]
        y_col = alternatives[0] if alternatives else y_col

    if chart_type == "pie" and x_col == y_col:
        raise ValueError("Pie charts need separate label and value columns.")

    return x_col, y_col, group_col


def generate_chart_from_query(df: pd.DataFrame, query: str, title: str = "AI Generated Chart") -> str:
    chart_type = infer_chart_type(query)
    x_col, y_col, group_col = infer_chart_columns(df, query, chart_type)
    return generate_chart(df, chart_type, x_col, y_col, title, group_col)


def generate_chart(
    df: pd.DataFrame,
    chart_type: str,
    x_col: str,
    y_col: str,
    title: str = "Chart",
    group_col: Optional[str] = None,
) -> str:
    try:
        if x_col not in df.columns or (y_col != COUNT_VALUE and y_col not in df.columns):
            raise ValueError("Selected chart columns were not found in the dataset.")

        selected_columns = [x_col] + ([] if y_col == COUNT_VALUE else [y_col])
        selected_columns += [group_col] if group_col and group_col in df.columns else []
        data = df[selected_columns].dropna()
        if data.empty:
            raise ValueError("No chartable data found for selected columns.")
        if y_col != COUNT_VALUE:
            data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
            data = data.dropna(subset=[y_col])
            if data.empty:
                raise ValueError("Selected value column must contain numeric data.")
        value_label = "Count" if y_col == COUNT_VALUE else y_col

        if chart_type in {"bar", "pie"}:
            if y_col == COUNT_VALUE:
                data = data.groupby(x_col).size().reset_index(name=value_label)
            else:
                data = data.groupby(x_col, as_index=False)[y_col].sum().rename(columns={y_col: value_label})
            data = data.sort_values(value_label, ascending=False).head(20)
        if chart_type == "line":
            if "date" in str(x_col).lower():
                data[x_col] = pd.to_datetime(data[x_col], errors="coerce")
                data = data.dropna(subset=[x_col]).sort_values(x_col)
            if group_col and group_col in data.columns:
                top_groups = data.groupby(group_col)[y_col].sum().nlargest(6).index
                data = data[data[group_col].isin(top_groups)]
                data = data.groupby([x_col, group_col], as_index=False)[y_col].sum().rename(columns={y_col: value_label})
            else:
                data = data.groupby(x_col, as_index=False)[y_col].sum().rename(columns={y_col: value_label}).head(200)

        plt.figure(figsize=(13, 7))
        if chart_type == "line":
            if group_col and group_col in data.columns:
                for label, group_data in data.groupby(group_col):
                    plt.plot(group_data[x_col], group_data[value_label], marker="o", linewidth=2, label=str(label))
                plt.legend(title=group_col)
            else:
                plt.plot(data[x_col], data[value_label], marker="o", linewidth=2)
        elif chart_type == "bar":
            plt.bar(data[x_col].astype(str), data[value_label], color="#2E86AB")
            plt.xticks(rotation=35, ha="right")
        elif chart_type == "pie":
            plt.pie(data[value_label], labels=data[x_col].astype(str), autopct='%1.1f%%')
        else:
            raise ValueError("Unsupported chart type.")
        plt.title(title)
        if chart_type != "pie":
            plt.xlabel(x_col)
            plt.ylabel(value_label)
            plt.grid(axis="y", alpha=0.25)
        safe_title = re.sub(r"[^a-zA-Z0-9_-]+", "_", title).strip("_").lower() or "chart"
        chart_path = os.path.join(CHARTS_DIR, f"{safe_title}_{chart_type}_{uuid.uuid4().hex[:8]}.png")
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()
        logger.info("Chart saved: %s", chart_path)
        return chart_path
    except Exception as e:
        logger.error("Chart generation error: %s", e)
        raise
