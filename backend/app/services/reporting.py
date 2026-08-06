import csv
import io
from typing import Any


def generate_sales_csv(orders: list[dict[str, Any]]) -> str:
    """Generates a CSV string for sales reporting."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Order ID", "Date", "Customer ID", "Total Amount", "Status", "Payment Method"])

    for order in orders:
        writer.writerow([
            order.get("id"),
            order.get("created_at"),
            order.get("customer_id"),
            order.get("total_amount"),
            order.get("status"),
            order.get("payment_method")
        ])

    return output.getvalue()

def generate_driver_performance_csv(drivers_data: list[dict[str, Any]]) -> str:
    """Generates a CSV string for driver performance metrics."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Driver ID", "Name", "Total Deliveries", "Average Rating"])

    for driver in drivers_data:
        writer.writerow([
            driver.get("id"),
            driver.get("full_name"),
            driver.get("delivery_count"),
            driver.get("avg_rating")
        ])

    return output.getvalue()
