from utils.router import rule_based_route


def test_rule_based_route_basic():
    rewritten = "show all customers and orders"
    table_summaries = {
        "CUSTOMER": "customer details and IDs",
        "ORDERS": "order details",
        "PAYMENT": "payment transactions",
    }
    tables = rule_based_route(rewritten, table_summaries)
    assert isinstance(tables, list)
    assert len(tables) <= 4
    assert "CUSTOMER" in tables or "ORDERS" in tables
