import json
from pathlib import Path


ORDERS_FILE = Path(__file__).parent.parent / "data" / "orders.json"


def get_order_details(order_id: str):
    """
    Retrieve order details using an order ID.

    Returns:
        dict: Order details if found.
        None: If the order does not exist.
    """

    with open(ORDERS_FILE, "r", encoding="utf-8") as file:
        orders = json.load(file)
        #print(orders)

    return orders.get(order_id.strip().upper())