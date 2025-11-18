from pathlib import Path
from sales_data import SalesDataLoader


def main() -> None:
    print("=" * 60)
    print("Sales Data Consolidation Tool")
    print("=" * 60)

    loader = SalesDataLoader(data_directory="data")

    print("\nConsolidating all sales data files...")
    print("-" * 60)

    try:
        consolidated_data = loader.get_aggregated_data()

        print("\n" + "=" * 60)
        print("CONSOLIDATION SUMMARY")
        print("=" * 60)
        print(f"Total records: {len(consolidated_data):,}")
        print(f"Number of columns: {len(consolidated_data.columns)}")
        print(f"Unique orders: {consolidated_data['order_id'].nunique():,}")
        print(f"Unique products (SKUs): {consolidated_data['sku'].nunique():,}")
        print(f"Date range: {consolidated_data['data'].min()} to {consolidated_data['data'].max()}")
        print(f"Total revenue: {consolidated_data['razem'].sum():,.2f}")

        print("\nFirst 5 rows of consolidated data:")
        print(consolidated_data[['order_id', 'data', 'sku', 'ilosc', 'cena', 'razem']].head())

        output_file = Path("output/consolidated_sales_data.csv")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        output_columns = ['order_id', 'data', 'sku', 'ilosc', 'cena', 'razem']
        consolidated_data[output_columns].to_csv(output_file, index=False)
        print(f"\n✓ Consolidated data saved to: {output_file}")

        # Save with metadata for reference for debugging
        # metadata_file = Path("output/consolidated_sales_data_with_metadata.csv")
        # consolidated_data.to_csv(metadata_file, index=False)
        # print(f"✓ Data with metadata saved to: {metadata_file}")

    except ValueError as e:
        print(f"\nError: {e}")
        print("\nPlease ensure your CSV files are in the 'data' directory")
        print("Expected filename format: YYYYMMDD-YYYYMMDD.csv")
        print("Example: 20250101-20251116.csv")
        return

    print("\n" + "=" * 60)
    print("Process completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
