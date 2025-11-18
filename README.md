# Sales Data Analysis

A Python project for consolidating and analyzing sales data from multiple Excel files with date-range naming patterns.

## Overview

This project handles sales data files that follow a specific naming convention: `YYYYMMDD_YYYYMMDD.xlsx` (e.g., `20240101_20241231.xlsx`). It automatically:

1. **Loads all historical year files** from the data directory
2. **Identifies the latest file for the current year** (handles daily updates)
3. **Consolidates all data** into a single dataset for analysis

## Project Structure

```
sales-data-analysis/
├── data/                      # Place your Excel files here
│   └── YYYYMMDD_YYYYMMDD.xlsx
├── output/                    # Consolidated output files
│   └── consolidated_sales_data.xlsx
├── src/
│   └── sales_data/
│       ├── __init__.py
│       └── loader.py          # Main data loading module
├── main.py                    # Main script
├── pyproject.toml
└── README.md
```

## Installation

This project uses UV for Python project management. 

1. Ensure you have UV installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. The project will automatically manage dependencies when you run it.

## Usage

### Basic Usage

1. **Place your Excel files** in the `data/` directory:
   - Historical files: `20240101_20241231.xlsx`, `20230101_20231231.xlsx`, etc.
   - Current year file: `20250101_20251117.xlsx` (or latest date)

2. **Run the consolidation script**:
```bash
uv run python main.py
```

3. **Find your output** in `output/consolidated_sales_data.xlsx`

### Programmatic Usage

```python
from sales_data import SalesDataLoader

# Initialize the loader
loader = SalesDataLoader(data_directory="data")

# Get all consolidated data
consolidated_data = loader.get_aggregated_data()

# Work with your data
print(f"Total records: {len(consolidated_data)}")
print(f"Unique products: {consolidated_data['product_id'].nunique()}")
```

## File Format Requirements

### Naming Convention
- Files must follow the pattern: `YYYYMMDD_YYYYMMDD.xlsx`
- Start date must come before end date
- Example: `20240101_20241231.xlsx` (Jan 1, 2024 to Dec 31, 2024)

### File Structure
- Excel files with pivot table format
- First column contains product IDs
- Subsequent columns contain data (e.g., monthly values)
- Header rows are automatically skipped (default: 4 rows)

## Key Features

### 1. **Automatic Current Year Detection**
The system automatically identifies and uses the most recent file for the current year, making it perfect for daily data updates.

### 2. **Historical Data Consolidation**
Easily combine multiple years of data into a single dataset for comprehensive analysis.

### 3. **Flexible File Discovery**
The loader intelligently finds all matching files in your data directory and sorts them chronologically.

## Example Scenario

### Daily Operations
Your data pipeline updates the current year file daily:
- Monday: `20250101_20251117.xlsx`
- Tuesday: `20250101_20251118.xlsx`
- Wednesday: `20250101_20251119.xlsx`

The loader automatically picks up the latest file each time you run the script.

## Requirements

- Python 3.12+
- pandas
- openpyxl (for Excel file handling)

These are automatically managed by UV through `pyproject.toml`.
