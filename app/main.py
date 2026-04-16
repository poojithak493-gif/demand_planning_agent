from app.controllers.validation_controller import run_primary_sales_validation


def main():
    results = run_primary_sales_validation()

    print("\n--- PRIMARY SALES VALIDATION RESULTS ---")
    print("Total records:", results["total_records"])
    print("Duplicate rows:", results["duplicate_rows"])
    print("Negative sales values:", results["negative_sales_values"])
    print("Priority distribution:", results["priority_distribution"])
    print("Unique distributors:", results["unique_distributors"])
    print("Cleaned file saved at:", results["cleaned_file_path"])
    print("\n--- SKU RECOMMENDATIONS ---")
    for r in results["recommendations"][:10]:
        print(r)


if __name__ == "__main__":
    main()