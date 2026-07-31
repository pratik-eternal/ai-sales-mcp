"""
STEP 3 — MCP server: define tools and run

Flow:
  Cursor asks a question
    → picks a tool below
    → tool calls get_erp_data()
    → returns JSON to Cursor

Run:  uv run python server.py
"""

from fastmcp import FastMCP

from erp_api import get_erp_data, to_json

# ---------------------------------------------------------------------------
# Create the MCP server (name shown in Cursor)
# ---------------------------------------------------------------------------
mcp = FastMCP("ai-sales-erp")


# ---------------------------------------------------------------------------
# EMPLOYEE & SALES TOOLS
# ---------------------------------------------------------------------------

@mcp.tool
async def search_employees(query: str) -> str:
    """Search employees by name or employee code."""
    data = await get_erp_data("/employees", {"search": query, "pageSize": 10})
    return to_json(data)


@mcp.tool
async def list_sales(
    employee_id: str = "",
    customer_id: str = "",
    from_date: str = "",
    to_date: str = "",
) -> str:
    """List sales. Optional filters: employee_id, customer_id, from_date, to_date (YYYY-MM-DD)."""
    params: dict = {"pageSize": 20}
    if employee_id:
        params["employeeId"] = employee_id
    if customer_id:
        params["customerId"] = customer_id
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    data = await get_erp_data("/sales", params)
    return to_json(data)


# ---------------------------------------------------------------------------
# CUSTOMER TOOLS
# ---------------------------------------------------------------------------

@mcp.tool
async def search_customers(query: str) -> str:
    """Search customers by name, company, email, or code."""
    data = await get_erp_data("/customers", {"search": query, "pageSize": 10})
    return to_json(data)


# ---------------------------------------------------------------------------
# ANALYTICS TOOLS
# ---------------------------------------------------------------------------

@mcp.tool
async def get_dashboard() -> str:
    """Dashboard: revenue, orders, customers, products, employees."""
    data = await get_erp_data("/analytics/dashboard")
    return to_json(data)


@mcp.tool
async def top_customers(limit: str = "10", from_date: str = "", to_date: str = "") -> str:
    """Top customers by revenue. limit is a number string, e.g. "10". Dates: YYYY-MM-DD."""
    params: dict = {"limit": int(limit) if limit.isdigit() else 10}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    data = await get_erp_data("/analytics/top-customers", params)
    return to_json(data)


@mcp.tool
async def top_products(limit: str = "10", from_date: str = "", to_date: str = "") -> str:
    """Top products by revenue. limit is a number string, e.g. "10". Dates: YYYY-MM-DD."""
    params: dict = {"limit": int(limit) if limit.isdigit() else 10}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    data = await get_erp_data("/analytics/top-products", params)
    return to_json(data)


# ---------------------------------------------------------------------------
# Start server (stdio — used by Cursor)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
