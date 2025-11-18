from sales_data import SalesDataLoader, SalesAnalyzer

loader = SalesDataLoader()
df = loader.get_aggregated_data()

analyzer = SalesAnalyzer(df)
sku_summary = analyzer.aggregate_by_sku()

sku_summary.to_csv('output/sku_summary.csv', index=False)

print("Top 20 SKUs:")
print(sku_summary.head(20))
print(f"\nSaved to: output/sku_summary.csv")
