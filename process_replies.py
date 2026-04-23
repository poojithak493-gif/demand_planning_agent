import re
import os
import pandas as pd

from read_replies import get_latest_mail_per_distributor
from save_to_postgres import (
    create_tables,
    clear_latest_run_data,
    upsert_product,
    save_valid_reply,
    save_invalid_reply,
)

PRIMARY_SALES_FILE = "sample_data/Primary_Sales.xlsx"
RECOMMENDED_PRODUCTS_FILE = "sample_data/30_Recommended_New_Products.xlsx"


def normalize_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def normalize_key(value):
    if value is None:
        return None
    return str(value).strip().lower()


def find_matching_column(columns, candidates):
    normalized = {str(c).strip().lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    return None


def is_excel_file(filename):
    if not filename:
        return False
    filename = filename.lower().strip()
    return filename.endswith(".xlsx") or filename.endswith(".xls")


def standardize_sku_id(value):
    """
    Convert SKU011, sku011, SKU11, sku 011 -> sku11
    """
    text = normalize_text(value)
    if not text:
        return None

    cleaned = re.sub(r"[\s_-]+", "", text).lower()
    match = re.match(r"sku0*(\d+)$", cleaned)
    if match:
        return f"sku{int(match.group(1))}"

    return cleaned


def standardize_description(value):
    """
    Make description matching more flexible.
    """
    text = normalize_text(value)
    if not text:
        return None

    text = text.lower()
    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_products_master():
    frames = []

    for path in [PRIMARY_SALES_FILE, RECOMMENDED_PRODUCTS_FILE]:
        if path and os.path.exists(path):
            try:
                df = pd.read_excel(path)
                frames.append(df)
            except Exception as exc:
                print(f"Could not read {path}: {exc}")

    if not frames:
        raise FileNotFoundError("No product master Excel files found.")

    combined = pd.concat(frames, ignore_index=True, sort=False)

    sku_id_col = find_matching_column(
        combined.columns,
        ["sku_id", "sku code", "skuid", "item_code", "product_code"]
    )
    sku_name_col = find_matching_column(
        combined.columns,
        ["sku_name", "product_name", "item_name", "name"]
    )
    sku_desc_col = find_matching_column(
        combined.columns,
        ["sku_description", "product_description", "description", "desc"]
    )

    if not sku_id_col:
        raise ValueError("No SKU ID column found in product master.")
    if not sku_name_col:
        raise ValueError("No SKU name column found in product master.")

    products_by_id = {}
    products_by_name = {}

    for _, row in combined.iterrows():
        sku_id = normalize_text(row.get(sku_id_col))
        sku_name = normalize_text(row.get(sku_name_col))
        sku_description = normalize_text(row.get(sku_desc_col)) if sku_desc_col else sku_name

        if not sku_id or not sku_name:
            continue

        product = {
            "sku_id": sku_id,
            "sku_name": sku_name,
            "sku_description": sku_description or sku_name
        }

        # direct id match
        products_by_id[normalize_key(sku_id)] = product

        # standardized id match
        std_sku = standardize_sku_id(sku_id)
        if std_sku:
            products_by_id[std_sku] = product

        # direct name/desc matches
        products_by_name[normalize_key(sku_name)] = product
        products_by_name[normalize_key(product["sku_description"])] = product

        # flexible name/desc matches
        std_name = standardize_description(sku_name)
        std_desc = standardize_description(product["sku_description"])

        if std_name:
            products_by_name[std_name] = product
        if std_desc:
            products_by_name[std_desc] = product

    for product in products_by_id.values():
        if isinstance(product, dict) and product.get("sku_id"):
            upsert_product(
                product["sku_id"],
                product["sku_name"],
                product["sku_description"]
            )

    unique_products = {}
    for product in products_by_id.values():
        if isinstance(product, dict) and product.get("sku_id"):
            unique_products[product["sku_id"]] = product

    print(f"Loaded {len(unique_products)} products into database.")
    return products_by_id, products_by_name


def clean_reply_body(body):
    if not body:
        return ""

    lines = body.splitlines()
    cleaned = []

    for line in lines:
        text = line.strip()

        if not text:
            cleaned.append("")
            continue

        lower = text.lower()

        if lower.startswith("on ") and " wrote:" in lower:
            break
        if text.startswith(">"):
            continue

        cleaned.append(text)

    return "\n".join(cleaned).strip()


def extract_distributor_id(text):
    if not text:
        return None
    match = re.search(r"\bD\d{2}\b", text.upper())
    if match:
        return match.group(0)
    return None


def parse_item_line(line):
    text = line.strip()
    if not text:
        return None

    # sku01 20
    m = re.match(r"^(sku\d+)\s*[-:\s]\s*([0-9]+|-)\b", text, re.IGNORECASE)
    if m:
        return {
            "sku_id": m.group(1).upper(),
            "product_description": None,
            "quantity": m.group(2)
        }

    # Product Name - 50
    m = re.match(r"^(.+?)\s*[-:]\s*([0-9]+|-)\b", text)
    if m:
        return {
            "sku_id": None,
            "product_description": m.group(1).strip(),
            "quantity": m.group(2)
        }

    # Product Name 50 pieces
    m = re.match(r"^(.+?)\s+([0-9]+|-)\s*(pieces|pcs|units)?$", text, re.IGNORECASE)
    if m:
        return {
            "sku_id": None,
            "product_description": m.group(1).strip(),
            "quantity": m.group(2)
        }

    return None


def parse_reply_body(reply):
    cleaned_body = clean_reply_body(reply.get("body", ""))
    lines = [line.strip() for line in cleaned_body.splitlines() if line.strip()]

    extracted_distributor_id = extract_distributor_id(cleaned_body)

    items = []
    for line in lines:
        parsed = parse_item_line(line)
        if parsed:
            items.append(parsed)

    return {
        "source": "body",
        "cleaned_body": cleaned_body,
        "extracted_distributor_id": extracted_distributor_id,
        "items": items
    }


def parse_excel_attachment(file_path):
    all_items = []

    excel_file = pd.ExcelFile(file_path)
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        if df.empty:
            continue

        df.columns = [str(c).strip() for c in df.columns]

        sku_id_col = find_matching_column(
            df.columns,
            ["sku_id", "sku code", "skuid", "item_code", "product_code"]
        )
        desc_col = find_matching_column(
            df.columns,
            [
                "sku_description",
                "product_description",
                "description",
                "desc",
                "sku_name",
                "product_name",
                "item_name",
                "name"
            ]
        )
        qty_col = find_matching_column(
            df.columns,
            [
                "quantity",
                "qty",
                "demand_qty",
                "demand quantity",
                "required_qty",
                "required quantity"
            ]
        )

        if not qty_col:
            continue

        for _, row in df.iterrows():
            sku_id = normalize_text(row.get(sku_id_col)) if sku_id_col else None
            desc = normalize_text(row.get(desc_col)) if desc_col else None
            qty = row.get(qty_col)

            if qty is None or (isinstance(qty, float) and pd.isna(qty)):
                continue

            item = {
                "sku_id": sku_id,
                "product_description": desc,
                "quantity": str(qty).strip()
            }

            if item["sku_id"] or item["product_description"]:
                all_items.append(item)

    return all_items


def parse_reply_with_attachments(reply):
    attachments = reply.get("attachments", []) or []

    excel_items = []
    for attachment in attachments:
        filename = attachment.get("filename")
        file_path = attachment.get("file_path")

        if is_excel_file(filename) and file_path and os.path.exists(file_path):
            try:
                items = parse_excel_attachment(file_path)
                if items:
                    excel_items.extend(items)
                    print(f"Read Excel attachment: {filename} -> {len(items)} items")
            except Exception as exc:
                print(f"Could not read attachment {filename}: {exc}")

    body_data = parse_reply_body(reply)

    if excel_items:
        return {
            "source": "excel",
            "cleaned_body": body_data["cleaned_body"],
            "extracted_distributor_id": body_data["extracted_distributor_id"],
            "items": excel_items
        }

    return body_data


def validate_and_save(reply, parsed_data, products_by_id, products_by_name):
    from_email = reply.get("from_email")
    message_id = reply.get("message_id")
    expected_distributor_id = reply.get("distributor_id")
    extracted_distributor_id = parsed_data.get("extracted_distributor_id")
    items = parsed_data.get("items", [])

    if extracted_distributor_id and extracted_distributor_id != expected_distributor_id:
        save_invalid_reply(
            expected_distributor_id,
            None,
            None,
            None,
            from_email,
            message_id,
            "INVALID_DISTRIBUTOR_ID",
            f"Distributor ID in mail body is {extracted_distributor_id}, expected {expected_distributor_id}"
        )

    if not items:
        save_invalid_reply(
            expected_distributor_id,
            None,
            None,
            None,
            from_email,
            message_id,
            "NO_ITEMS_FOUND",
            "No valid items found in latest distributor reply"
        )
        return

    for item in items:
        raw_sku_id = normalize_text(item.get("sku_id"))
        raw_desc = normalize_text(item.get("product_description"))
        raw_qty = normalize_text(item.get("quantity"))

        qty_text = (raw_qty or "").strip()

        # Treat '-' or empty as zero demand
        if qty_text == "-" or qty_text == "":
            quantity = 0
        elif qty_text.replace(".0", "").isdigit():
            quantity = int(qty_text.replace(".0", ""))
        else:
            save_invalid_reply(
                expected_distributor_id,
                raw_sku_id,
                raw_desc,
                raw_qty,
                from_email,
                message_id,
                "INVALID_QUANTITY",
                "Quantity is not a valid number"
            )
            continue

        product = None

        # Try SKU match
        if raw_sku_id:
            product = products_by_id.get(normalize_key(raw_sku_id))
            if not product:
                product = products_by_id.get(standardize_sku_id(raw_sku_id))

        # Try description match
        if not product and raw_desc:
            product = products_by_name.get(normalize_key(raw_desc))
            if not product:
                product = products_by_name.get(standardize_description(raw_desc))

        if not product:
            save_invalid_reply(
                expected_distributor_id,
                raw_sku_id,
                raw_desc,
                raw_qty,
                from_email,
                message_id,
                "INVALID_SKU_OR_DESCRIPTION",
                "SKU ID or product description not found in product master"
            )
            continue

        final_sku_id = product["sku_id"]
        final_description = product["sku_description"]

        save_valid_reply(
            expected_distributor_id,
            final_sku_id,
            final_description,
            quantity,
            from_email,
            message_id
        )


def main():
    print("\nCreating tables...")
    create_tables()

    print("Clearing previous run data...")
    clear_latest_run_data()

    print("Loading product master from Excel...")
    products_by_id, products_by_name = load_products_master()

    print("Reading latest reply mail from each distributor...")
    replies = get_latest_mail_per_distributor()

    if not replies:
        print("No distributor replies found.")
        return

    print(f"Total latest replies found: {len(replies)}")

    for reply in replies:
        print("\n" + "=" * 80)
        print(f"Processing {reply.get('distributor_id')} - {reply.get('from_email')}")
        print("=" * 80)

        parsed_data = parse_reply_with_attachments(reply)
        print("Source:", parsed_data["source"])
        print("Parsed Items:", parsed_data["items"])

        validate_and_save(reply, parsed_data, products_by_id, products_by_name)

    print("\nProcessing completed successfully.")


if __name__ == "__main__":
    main()