import re


def parse_text_demand(body_text):
    demand_data = []

    lines = body_text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r"(.+?)\s*-\s*(\d+)", line)
        if match:
            product_name = match.group(1).strip()
            quantity = int(match.group(2))

            demand_data.append({
                "product_name": product_name,
                "quantity": quantity
            })

    return demand_data


if __name__ == "__main__":
    sample_text = """Product A - 100
Product B - 250
Product C - 75"""

    parsed = parse_text_demand(sample_text)
    print(parsed)