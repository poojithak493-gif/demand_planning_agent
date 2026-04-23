from save_to_postgres import get_all_valid_replies, get_all_invalid_replies


def print_table(headers, rows):
    if not rows:
        print("\nNo data found.\n")
        return

    rows = [[("" if v is None else str(v)) for v in row] for row in rows]
    headers = [str(h) for h in headers]

    col_widths = []
    for i in range(len(headers)):
        width = len(headers[i])
        for row in rows:
            width = max(width, len(row[i]))
        col_widths.append(width)

    def format_row(row):
        return " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))

    separator = "-+-".join("-" * w for w in col_widths)

    print(format_row(headers))
    print(separator)

    for row in rows:
        print(format_row(row))
    print()


def main():
    print("\n" + "=" * 90)
    print("VALID REPLIES TABLE")
    print("=" * 90)

    valid_rows = get_all_valid_replies()
    print_table(
        ["Distributor ID", "SKU ID", "Product Description", "Quantity"],
        valid_rows
    )

    print("\n" + "=" * 90)
    print("INVALID REPLIES TABLE")
    print("=" * 90)

    invalid_rows = get_all_invalid_replies()
    print_table(
        ["Distributor ID", "SKU ID", "Product Description", "Quantity", "Issue Type", "Issue Message"],
        invalid_rows
    )


if __name__ == "__main__":
    main()