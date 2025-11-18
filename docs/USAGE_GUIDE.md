# Complete Usage Guide

## Table of Contents
1. [Installation & Setup](#installation--setup)
2. [File Preparation](#file-preparation)
3. [Running the Project](#running-the-project)
4. [Real-World Scenarios](#real-world-scenarios)
5. [Programmatic Usage](#programmatic-usage)
6. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Step 1: Install UV (First Time Only)

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Navigate to Project

```bash
cd sales-data-analysis
```

### Step 3: Verify Installation

```bash
# This will automatically set up the Python environment
uv run python --version
```

---

## File Preparation

### Naming Convention

Your Excel files **must** follow this exact pattern:

```
YYYYMMDD_YYYYMMDD.xlsx
```

**Examples:**
- ✅ `20240101_20241231.xlsx` (Full year 2024)
- ✅ `20250101_20251117.xlsx` (Year-to-date 2025)
- ✅ `20230601_20231130.xlsx` (6 months in 2023)
- ❌ `2024_sales.xlsx` (Wrong format)
- ❌ `20241231_20240101.xlsx` (End before start)
- ❌ `240101_241231.xlsx` (Not enough digits)

### File Location

Place all your Excel files in the `data/` directory:

```
sales-data-analysis/
└── data/
    ├── 20220101_20221231.xlsx
    ├── 20230101_20231231.xlsx
    ├── 20240101_20241231.xlsx
    └── 20250101_20251117.xlsx
```

---

## Running the Project

### Quick Start (Command Line)

**Basic consolidation:**
```bash
uv run python main.py
```

**See all features:**
```bash
uv run python demo.py
```

**Custom analysis examples:**
```bash
uv run python examples.py
```

### What Happens

1. Script scans the `data/` directory
2. Finds all files matching the pattern
3. Loads each file (skipping header rows)
4. Consolidates data into one dataset
5. Saves output to `output/consolidated_sales_data.xlsx`
6. Displays summary statistics

---

## Real-World Scenarios

### Scenario 1: First Time Setup

**Situation:** You have historical data for 2023 and 2024.

**Files:**
```
data/
├── 20230101_20231231.xlsx  (365 days of 2023)
└── 20240101_20241231.xlsx  (366 days of 2024)
```

**Action:**
```bash
uv run python main.py
```

**Result:**
- Both files loaded and consolidated
- Output contains all 2023 + 2024 data
- Single file: `output/consolidated_sales_data.xlsx`

---

### Scenario 2: Daily Updates

**Situation:** Every day, your system generates a new file for the current year.

**Monday's files:**
```
data/
├── 20240101_20241231.xlsx     (Last year's complete data)
└── 20250101_20251117.xlsx     (Current year to Monday)
```

**Tuesday's files:**
```
data/
├── 20240101_20241231.xlsx     (Last year's complete data)
├── 20250101_20251117.xlsx     (Old - can be deleted)
└── 20250101_20251118.xlsx     (Current year to Tuesday - NEW)
```

**Action:**
```bash
uv run python main.py
```

**Result:**
- Script automatically finds latest 2025 file (20251118)
- Ignores older 2025 file (20251117)
- Consolidates 2024 + latest 2025 data
- You get the most current dataset

**Best Practice:**
- You can delete old current-year files
- Or keep them - script will pick the latest anyway

---

### Scenario 3: Adding Historical Data

**Situation:** You get access to older data and want to add it.

**Before:**
```
data/
└── 20240101_20241231.xlsx
```

**After adding 2022 and 2023:**
```
data/
├── 20220101_20221231.xlsx  (NEW)
├── 20230101_20231231.xlsx  (NEW)
└── 20240101_20241231.xlsx
```

**Action:**
```bash
uv run python main.py
```

**Result:**
- All three years consolidated
- Data sorted chronologically
- Complete historical view

---

### Scenario 4: Partial Year Data

**Situation:** You only have data for specific periods.

**Files:**
```
data/
├── 20240101_20240630.xlsx  (Q1 + Q2 2024)
└── 20240701_20241231.xlsx  (Q3 + Q4 2024)
```

**Action:**
```bash
uv run python main.py
```

**Result:**
- Both files loaded
- Data combined for full year 2024
- Script handles any date ranges

---

### Scenario 5: Testing with Sample Data

**Situation:** You want to test with a subset before running on all data.

**Action:**
```bash
# Create a test directory
mkdir data_test
cp data/20240101_20241231.xlsx data_test/

# Test with custom directory
python3 -c "
import sys
sys.path.insert(0, 'src')
from sales_data import SalesDataLoader

loader = SalesDataLoader(data_directory='data_test')
df = loader.get_aggregated_data()
print(f'Test successful! Loaded {len(df)} rows')
"
```

---

## Programmatic Usage

### Example 1: Basic Script

```python
from sales_data import SalesDataLoader

# Load data
loader = SalesDataLoader(data_directory="data")
df = loader.get_aggregated_data()

# Your analysis
print(f"Total records: {len(df)}")
print(f"Unique products: {df['product_id'].nunique()}")
print(df.head())
```

### Example 2: Filter and Export

```python
from sales_data import SalesDataLoader

# Load data
loader = SalesDataLoader(data_directory="data")
df = loader.get_aggregated_data()

# Filter for 2024 only
df_2024 = df[df['file_start_date'].dt.year == 2024]

# Export
df_2024.to_excel('output/sales_2024.xlsx', index=False)
print(f"Exported {len(df_2024)} records")
```

### Example 3: Product Analysis

```python
from sales_data import SalesDataLoader
import pandas as pd

# Load data
loader = SalesDataLoader(data_directory="data")
df = loader.get_aggregated_data()

# Get products starting with 'CH'
ch_products = df[df['product_id'].str.startswith('CH')]

# Analyze
print(f"CH Products: {len(ch_products)}")
print(ch_products['product_id'].value_counts().head(10))

# Export
ch_products.to_excel('output/ch_products_analysis.xlsx', index=False)
```

### Example 4: Monthly Aggregation

```python
from sales_data import SalesDataLoader
import pandas as pd

# Load data
loader = SalesDataLoader(data_directory="data")
df = loader.get_aggregated_data()

# If your data has monthly columns, aggregate them
# This depends on your specific data structure
numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns

# Calculate totals
totals = df[numeric_cols].sum()
print("Monthly totals:")
print(totals)

# Save summary
totals.to_excel('output/monthly_summary.xlsx')
```

### Example 5: File-by-File Processing

```python
from sales_data import SalesDataLoader

loader = SalesDataLoader(data_directory="data")
files_info = loader.find_data_files()

# Process each file separately
for file_path, start_date, end_date in files_info:
    df = loader.load_excel_file(file_path)
    
    # Your per-file analysis
    print(f"\n{file_path.name}")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    print(f"  Records: {len(df)}")
    
    # Save per-year files
    year = start_date.year
    df.to_excel(f'output/sales_{year}.xlsx', index=False)
```

---

## Troubleshooting

### Issue: "No data files found"

**Cause:** Files not in data directory or wrong naming format

**Solution:**
```bash
# Check if files exist
ls data/*.xlsx

# Verify naming pattern
# Should be: YYYYMMDD_YYYYMMDD.xlsx
# Example: 20240101_20241231.xlsx
```

### Issue: "Invalid date range"

**Cause:** End date is before start date, or invalid date

**Solution:**
- Start date must be before end date
- Dates must be valid (no Feb 30, etc.)
- Use exactly 8 digits for each date

**Fix example:**
```
Wrong: 20241231_20240101.xlsx  (end before start)
Right: 20240101_20241231.xlsx
```

### Issue: "Empty output file"

**Cause:** Excel files might have different header structure

**Solution:**
Adjust skip_rows parameter:

```python
from sales_data import SalesDataLoader

loader = SalesDataLoader(data_directory="data")

# Try different skip_rows values
# Default is 4, try 3 or 5 if data looks wrong
df = loader.load_excel_file(file_path, skip_rows=5)
```

### Issue: "Missing columns or wrong data"

**Cause:** Excel file structure different than expected

**Solution:**
Check your Excel file structure:

```python
import pandas as pd

# Load raw file to inspect
df = pd.read_excel('data/20240101_20241231.xlsx')
print(df.head(10))

# Adjust skip_rows based on where real data starts
```

### Issue: "Out of memory"

**Cause:** Too many files or very large files

**Solution:**
Process files in batches:

```python
from sales_data import SalesDataLoader

loader = SalesDataLoader(data_directory="data")
files = loader.find_data_files()

# Process in chunks
for file_path, start_date, end_date in files[:10]:  # First 10 files
    df = loader.load_excel_file(file_path)
    # Process df...
```

---

## Output Files

After running, check the `output/` directory:

```
output/
├── consolidated_sales_data.xlsx    # Main output from main.py
├── products_CH.xlsx                # From examples.py
├── products_GIFT.xlsx              # From examples.py
└── [your_custom_files].xlsx        # From your scripts
```

---

## Tips & Best Practices

### 1. Keep Files Organized

```
data/
├── archive/              # Move old files here
│   └── 20220101_20221231.xlsx
└── 20240101_20241231.xlsx    # Keep active files here
```

### 2. Regular Backups

```bash
# Backup your consolidated data
cp output/consolidated_sales_data.xlsx output/backup_$(date +%Y%m%d).xlsx
```

### 3. Version Control

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Your data files are ignored by .gitignore
```

### 4. Document Your Analysis

Create a `notebooks/` directory for Jupyter notebooks:

```python
# In a Jupyter notebook
from sales_data import SalesDataLoader

loader = SalesDataLoader(data_directory="../data")
df = loader.get_aggregated_data()

# Your analysis with visualizations...
```

---

## Need Help?

1. **Check the demo script**: `uv run python demo.py`
2. **Review examples**: `uv run python examples.py`
3. **Read the main README**: `README.md`
4. **Check docstrings**: `python -c "from sales_data import SalesDataLoader; help(SalesDataLoader)"`

---

**That's it! You're ready to consolidate and analyze your sales data. 🚀**
