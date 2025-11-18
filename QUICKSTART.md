# Quick Start Guide

## Setup (First Time Only)

1. **Install UV** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone or download this project**

3. **Add your Excel files** to the `data/` directory:
   - Files must follow naming pattern: `YYYYMMDD_YYYYMMDD.xlsx`
   - Example: `20240101_20241231.xlsx`

## Running the Project

### Basic Consolidation

Run the main script to consolidate all data files:

```bash
uv run python main.py
```

This will:
- Find all Excel files in the `data/` directory
- Load and consolidate them
- Save the result to `output/consolidated_sales_data.xlsx`

### View All Features

Run the demo script to see all available features:

```bash
uv run python demo.py
```

## Common Use Cases

### Scenario 1: Daily Data Updates

You have a file that gets updated daily with a new end date:

```
data/
├── 20230101_20231231.xlsx  # Full 2023 data
├── 20240101_20241231.xlsx  # Full 2024 data
└── 20250101_20251117.xlsx  # Current year (updated daily)
```

**What happens:**
- The script automatically finds the latest file for 2025
- All three files are consolidated
- You get complete historical + current data

### Scenario 2: Multiple Years

You have separate files for each complete year:

```
data/
├── 20220101_20221231.xlsx
├── 20230101_20231231.xlsx
└── 20240101_20241231.xlsx
```

**What happens:**
- All files are loaded in chronological order
- Data is combined into one dataset
- Perfect for multi-year analysis

### Scenario 3: Programmatic Use

Use the loader in your own Python scripts:

```python
from sales_data import SalesDataLoader

# Initialize
loader = SalesDataLoader(data_directory="data")

# Get all data
df = loader.get_aggregated_data()

# Now use pandas for your analysis
print(df.describe())
print(df.groupby('product_id').sum())
```

## Troubleshooting

### No files found
- Check that Excel files are in the `data/` directory
- Verify filenames match the pattern `YYYYMMDD_YYYYMMDD.xlsx`

### Invalid date range
- Ensure start date comes before end date
- Format must be exactly 8 digits: YYYYMMDD

### Empty output
- Check that Excel files contain data
- Verify the header rows are correct (default: 4 rows skipped)

## Output Files

After running, you'll find:

- `output/consolidated_sales_data.xlsx` - Your consolidated dataset

## Next Steps

1. Modify `main.py` to add your custom analysis
2. Create additional scripts in the project root
3. Import `SalesDataLoader` in your analysis notebooks
4. Add more features to the `src/sales_data/` module

## Getting Help

- Review the main README.md for detailed documentation
- Run `python demo.py` to see examples
- Check the docstrings in `src/sales_data/loader.py`
