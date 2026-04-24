from app.core.falkor_db import graph


def load_data():
    print("🚀 Loading graph data...")

    # Clear old graph (optional)
    graph.query("MATCH (n) DETACH DELETE n")

    # Create distributors
    distributors = ["D01", "D02", "D03", "D04", "D05"]

    for d in distributors:
        graph.query(f"""
        CREATE (:Distributor {{id: '{d}'}})
        """)

    # Create SKUs
    skus = [
        "MALKIST CHEESE JUMBO PACK",
        "MALKIST CHEESE + CHOCOLATE",
        "BENG BENG WAFER CHOCOLATE",
        "KOPIKO BLANCA CANDY",
        "MALKIST SUGAR CRACKER",
        "KOPIKO CAPPUCCINO",
    ]

    for sku in skus:
        graph.query(f"""
        CREATE (:SKU {{name: '{sku}'}})
        """)

    # Create relationships (BOUGHT)
    graph.query("""
    MATCH (d:Distributor {id: 'D01'}), (s:SKU {name: 'MALKIST CHEESE JUMBO PACK'})
    CREATE (d)-[:BOUGHT]->(s)
    """)

    graph.query("""
    MATCH (d:Distributor {id: 'D01'}), (s:SKU {name: 'BENG BENG WAFER CHOCOLATE'})
    CREATE (d)-[:BOUGHT]->(s)
    """)

    graph.query("""
    MATCH (d:Distributor {id: 'D02'}), (s:SKU {name: 'MALKIST CHEESE JUMBO PACK'})
    CREATE (d)-[:BOUGHT]->(s)
    """)

    graph.query("""
    MATCH (d:Distributor {id: 'D02'}), (s:SKU {name: 'KOPIKO BLANCA CANDY'})
    CREATE (d)-[:BOUGHT]->(s)
    """)

    graph.query("""
    MATCH (d:Distributor {id: 'D03'}), (s:SKU {name: 'MALKIST CHEESE JUMBO PACK'})
    CREATE (d)-[:BOUGHT]->(s)
    """)

    graph.query("""
    MATCH (d:Distributor {id: 'D03'}), (s:SKU {name: 'KOPIKO CAPPUCCINO'})
    CREATE (d)-[:BOUGHT]->(s)
    """)

    graph.query("""
    MATCH (d:Distributor {id: 'D04'}), (s:SKU {name: 'MALKIST CHEESE JUMBO PACK'})
    CREATE (d)-[:BOUGHT]->(s)
    """)

    graph.query("""
    MATCH (d:Distributor {id: 'D04'}), (s:SKU {name: 'MALKIST SUGAR CRACKER'})
    CREATE (d)-[:BOUGHT]->(s)
    """)

    graph.query("""
    MATCH (d:Distributor {id: 'D05'}), (s:SKU {name: 'BENG BENG WAFER CHOCOLATE'})
    CREATE (d)-[:BOUGHT]->(s)
    """)

    print("✅ Graph data loaded successfully!")


if __name__ == "__main__":
    load_data()