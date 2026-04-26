# =============================================================
# DEMAND PLANNING AGENT — FalkorDB Graph Schema + Seed
# File: db/falkordb/falkordb_seed.py
# =============================================================

import sys
import falkordb

# -----------------------------------------------------------
# CONNECTION
# -----------------------------------------------------------
FALKORDB_HOST = "localhost"
FALKORDB_PORT = 6379
GRAPH_NAME = "demand_planning_graph"

# -----------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------
PAN_INDIA = "Pan India"
TIER_1 = "Tier 1"
TIER_2 = "Tier 2"

SUPER_STOCKIST = "Super Stockist"
REGIONAL_DISTRIBUTOR = "Regional Distributor"

HIGH = "High"
MEDIUM = "Medium"
LOW = "Low"

MALKIST_CHEESE = "MALKIST CHEESE"
BENG_BENG = "BENG BENG"
KOPIKO_CAPPUCCINO = "KOPIKO CAPPUCCINO"
MALKIST_SUGAR = "MALKIST SUGAR"


def get_graph():
    client = falkordb.FalkorDB(host=FALKORDB_HOST, port=FALKORDB_PORT)
    return client.select_graph(GRAPH_NAME)


# -----------------------------------------------------------
# SEED DATA
# -----------------------------------------------------------
OEM = {
    "oem_id": "OEM01",
    "name": "OEM Manufacturer"
}

DISTRIBUTORS = [
    {"distributor_id": "D01", "name": "Distributor D01", "tier": TIER_2, "channel": SUPER_STOCKIST, "region": PAN_INDIA, "priority": MEDIUM},
    {"distributor_id": "D02", "name": "Distributor D02", "tier": TIER_2, "channel": REGIONAL_DISTRIBUTOR, "region": PAN_INDIA, "priority": MEDIUM},
    {"distributor_id": "D03", "name": "Distributor D03", "tier": TIER_1, "channel": SUPER_STOCKIST, "region": PAN_INDIA, "priority": HIGH},
    {"distributor_id": "D04", "name": "Distributor D04", "tier": TIER_2, "channel": REGIONAL_DISTRIBUTOR, "region": PAN_INDIA, "priority": MEDIUM},
    {"distributor_id": "D05", "name": "Distributor D05", "tier": TIER_2, "channel": REGIONAL_DISTRIBUTOR, "region": PAN_INDIA, "priority": MEDIUM},
]

SKUS = [
    {"sku_id": "SKU01", "name": "MALKIST CHEESE 48 PCS X 72", "category": MALKIST_CHEESE},
    {"sku_id": "SKU02", "name": "MALKIST CHEESE G", "category": MALKIST_CHEESE},
    {"sku_id": "SKU03", "name": "MALKIST CHEESE FAMILY 10", "category": MALKIST_CHEESE},
    {"sku_id": "SKU04", "name": "BENG BENG WAFER 22GM", "category": BENG_BENG},
    {"sku_id": "SKU05", "name": "BENG BENG WAFER GB", "category": BENG_BENG},
    {"sku_id": "SKU06", "name": "KOPIKO CAPPU EXTRA", "category": KOPIKO_CAPPUCCINO},
    {"sku_id": "SKU07", "name": "KOPIKO CAPPU + MALKIST", "category": KOPIKO_CAPPUCCINO},
    {"sku_id": "SKU08", "name": "KOPIKO CAPPUCCINO", "category": KOPIKO_CAPPUCCINO},
    {"sku_id": "SKU09", "name": "MALKIST SUGAR GB", "category": MALKIST_SUGAR},
    {"sku_id": "SKU10", "name": "MALKIST SUGAR CRACKERS", "category": MALKIST_SUGAR},
]

CATEGORIES = [
    MALKIST_CHEESE,
    BENG_BENG,
    KOPIKO_CAPPUCCINO,
    MALKIST_SUGAR
]

DISTRIBUTES = [
    {"dist": "D01", "sku": "SKU01", "priority": HIGH, "avg_dispatch": 119759.20},
    {"dist": "D01", "sku": "SKU02", "priority": HIGH, "avg_dispatch": 122214.40},
    {"dist": "D01", "sku": "SKU03", "priority": HIGH, "avg_dispatch": 458304.00},
    {"dist": "D01", "sku": "SKU04", "priority": MEDIUM, "avg_dispatch": 91660.80},
    {"dist": "D01", "sku": "SKU05", "priority": MEDIUM, "avg_dispatch": 109992.96},

    {"dist": "D02", "sku": "SKU01", "priority": MEDIUM, "avg_dispatch": 123032.80},
    {"dist": "D02", "sku": "SKU02", "priority": MEDIUM, "avg_dispatch": 123032.80},
    {"dist": "D02", "sku": "SKU03", "priority": HIGH, "avg_dispatch": 461373.00},

    {"dist": "D03", "sku": "SKU01", "priority": HIGH, "avg_dispatch": 119188.80},
    {"dist": "D03", "sku": "SKU02", "priority": HIGH, "avg_dispatch": 120795.84},

    {"dist": "D04", "sku": "SKU01", "priority": MEDIUM, "avg_dispatch": 123851.20},
    {"dist": "D04", "sku": "SKU02", "priority": MEDIUM, "avg_dispatch": 123851.20},

    {"dist": "D05", "sku": "SKU01", "priority": MEDIUM, "avg_dispatch": 124669.60},
    {"dist": "D05", "sku": "SKU02", "priority": MEDIUM, "avg_dispatch": 124669.60},
]


# -----------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------
def drop_existing_graph(graph):
    try:
        graph.delete()
        print("Dropped existing graph")
    except Exception:
        print("No existing graph")


def create_oem_node(graph):
    graph.query(
        "CREATE (:OEM {oem_id:$oem_id,name:$name})",
        OEM
    )


def create_category_nodes(graph):
    for category in CATEGORIES:
        graph.query(
            "CREATE (:Category {name:$name})",
            {"name": category}
        )


def create_distributor_nodes(graph):
    for distributor in DISTRIBUTORS:
        graph.query(
            """
            CREATE (:Distributor {
                distributor_id:$distributor_id,
                name:$name,
                tier:$tier,
                channel:$channel,
                region:$region,
                priority:$priority
            })
            """,
            distributor
        )


def create_sku_nodes(graph):
    for sku in SKUS:
        graph.query(
            """
            CREATE (:SKU {
                sku_id:$sku_id,
                name:$name,
                category:$category
            })
            """,
            sku
        )


def create_oem_edges(graph):
    for sku in SKUS:
        graph.query(
            """
            MATCH (o:OEM {oem_id:$oem_id}),
                  (s:SKU {sku_id:$sku_id})
            CREATE (o)-[:MANUFACTURES]->(s)
            """,
            {"oem_id": OEM["oem_id"], "sku_id": sku["sku_id"]}
        )


def create_category_edges(graph):
    for sku in SKUS:
        graph.query(
            """
            MATCH (s:SKU {sku_id:$sku_id}),
                  (c:Category {name:$category})
            CREATE (s)-[:BELONGS_TO]->(c)
            """,
            {"sku_id": sku["sku_id"], "category": sku["category"]}
        )


def create_distributor_edges(graph):
    for row in DISTRIBUTES:
        graph.query(
            """
            MATCH (d:Distributor {distributor_id:$dist}),
                  (s:SKU {sku_id:$sku})
            CREATE (d)-[:DISTRIBUTES {
                priority:$priority,
                avg_dispatch_value:$avg_dispatch
            }]->(s)
            """,
            row
        )


def create_same_tier_edges(graph):
    tier2 = [d["distributor_id"] for d in DISTRIBUTORS if d["tier"] == TIER_2]

    for i in range(len(tier2)):
        for j in range(i + 1, len(tier2)):
            graph.query(
                """
                MATCH (a:Distributor {distributor_id:$a}),
                      (b:Distributor {distributor_id:$b})
                CREATE (a)-[:SAME_TIER {tier:$tier}]->(b)
                """,
                {"a": tier2[i], "b": tier2[j], "tier": TIER_2}
            )


def verify_graph(graph):
    result = graph.query("MATCH (n) RETURN labels(n), count(n)")
    for row in result.result_set:
        print(row)


def main():
    graph = get_graph()

    drop_existing_graph(graph)

    create_oem_node(graph)
    create_category_nodes(graph)
    create_distributor_nodes(graph)
    create_sku_nodes(graph)

    create_oem_edges(graph)
    create_category_edges(graph)
    create_distributor_edges(graph)
    create_same_tier_edges(graph)

    verify_graph(graph)

    print("FalkorDB seeded successfully")


if __name__ == "__main__":
    main()