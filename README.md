# Stock Monitor 3

A comprehensive Streamlit-based inventory management and sales analytics application for retail and manufacturing
businesses. The system uses statistical methods to analyze historical sales, forecast future demand, and optimize
ordering decisions to maximize sales while minimizing stockouts and excess inventory.

## Table of Contents

- [Features Overview](#features-overview)
- [Quick Start](#quick-start)
- [Application Tabs](#application-tabs)
- [Statistical Calculations Explained](#statistical-calculations-explained)
- [Pattern Optimization Algorithm](#pattern-optimization-algorithm)
- [Priority Scoring System](#priority-scoring-system)
- [Configuration Parameters](#configuration-parameters)
- [Data Requirements](#data-requirements)
- [Architecture](#architecture)

---

## Features Overview

| Feature                   | Description                                                           |
|---------------------------|-----------------------------------------------------------------------|
| **Sales Analysis**        | Statistical analysis with Safety Stock and Reorder Point calculations |
| **Stock Projection**      | Visual forecasting of when items will reach critical levels           |
| **Pattern Optimizer**     | Cutting pattern optimization for manufacturing                        |
| **Order Recommendations** | Priority-based ordering system with intelligent scoring               |
| **Weekly Analysis**       | Week-over-week sales comparison and trending                          |
| **Monthly Analysis**      | Year-over-year category performance                                   |
| **Order Creation**        | Transform recommendations into production orders                      |

---

## Quick Start

### Prerequisites

- Python 3.13+
- Virtual environment (recommended)

### Installation

```bash
# Clone or navigate to project directory
cd stockMonitor3

# Create and activate virtual environment
python -m venv src/venv
src\venv\Scripts\activate  # Windows
source src/venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r src/requirements.txt
```

### Configuration

1. **File-based mode** (default):
   ```bash
   # Copy and configure paths file
   cp src/sales_data/paths_to_files.txt.example src/sales_data/paths_to_files.txt
   # Edit paths_to_files.txt with your data directories
   ```

2. **Database mode** (optional):
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env with your database connection
   # DATA_SOURCE_MODE=database
   # DATABASE_URL=postgresql://user:password@localhost:5432/inventory_db
   ```

### Run the Application

```bash
cd src
py -V:3.13 -m streamlit run app.py
```

The application opens at `http://localhost:8501`

---

## Application Tabs

### Tab 1: Sales & Inventory Analysis

The main analytics dashboard providing comprehensive inventory visibility.

**Features:**

- SKU or Model-level data views (toggle in sidebar)
- Filtering: search, below ROP, bestsellers, product type, overstock
- Safety Stock (SS) and Reorder Point (ROP) calculations
- Stock projection charts showing when items reach critical levels
- CSV export capability

**Key Columns Explained:**
| Column | Description |
|--------|-------------|
| `MONTHS` | Number of months with sales history |
| `QUANTITY` | Total units sold (lifetime) |
| `AVERAGE SALES` | Mean monthly sales |
| `SD` | Standard deviation of monthly sales |
| `CV` | Coefficient of Variation (SD / Average) - measures demand variability |
| `TYPE` | Product classification: new, basic, seasonal, or regular |
| `SS` | Safety Stock - buffer inventory to prevent stockouts |
| `ROP` | Reorder Point - stock level that triggers a new order |
| `STOCK` | Current inventory level |
| `FORECAST_LEADTIME` | Predicted demand during the lead time period |

**Stock Projection Chart:**
Enter a SKU or Model code to visualize projected stock depletion over time. The chart shows:

- Current stock trajectory based on forecast demand
- ROP threshold line
- Dates when stock reaches ROP and zero

---

### Tab 2: Size Pattern Optimizer

Standalone tool for optimizing cutting patterns in manufacturing.

**Concepts:**

- **Pattern Set**: A collection of cutting patterns (e.g., "Adults", "Kids")
- **Pattern**: A specific size combination that can be cut together (e.g., "L + XL")
- **Minimum Order**: Minimum quantity per pattern to be economical

**Workflow:**

1. Create/select a pattern set
2. Define available sizes (XL, L, M, S, XS, etc.)
3. Define cutting patterns with size combinations
4. Enter desired quantities by size
5. Run optimization to get pattern allocation

**Output:**

- Which patterns to order and how many
- Total units produced per size
- Excess production (overproduction)
- Minimum order violations

---

### Tab 3: Weekly Analysis

Week-over-week sales trends and product performance.

**Features:**

- **Rising Stars**: Products with increasing sales vs. the same week last year
- **Falling Stars**: Products with declining sales
- **New Products Monitor**: Track sales of products introduced in the last 60 days

**Calculation:**

```
Percent Change = ((Current Week - Same Week Last Year) / Same Week Last Year) * 100
```

Special cases:

- No sales last year, sales now: +999% (new performer)
- Sales last year, none now: -100% (stopped selling)

---

### Tab 4: Monthly Analysis

Year-over-year category-level performance comparison.

**Features:**

- Compare sales by category (Podgrupa) and subcategory (Kategoria)
- Automatically excludes the current incomplete month
- Rising/falling category identification
- CSV export with period comparison

---

### Tab 5: Order Recommendations

**The Most Important Feature** - Automated priority-based ordering system.

**Requirements:**

- Stock data must be loaded
- Forecast data must be loaded

**How It Works:**

1. Analyzes all SKUs considering current stock, ROP, forecast demand, and product type
2. Calculates a priority score for each item
3. Aggregates by MODEL+COLOR for ordering
4. Shows top N recommendations with size breakdowns

**Output Table:**
| Column | Description |
|--------|-------------|
| Model | 5-character model code |
| Color | 2-character color code |
| Priority | Calculated priority score (higher = more urgent) |
| Deficit | How much below ROP |
| Forecast | Predicted demand during lead time |
| Sizes | Size breakdown (e.g., "08:15, 12:25, 13:30") |
| Urgent | Flag for zero-stock items with demand |

---

### Tab 6: Order Creation

Transform recommendations into actionable production orders.

**Workflow:**

1. Select items in Tab 5 using checkboxes
2. Click "Create Order" or enter model code manually
3. System automatically:
    - Loads pattern set matching the model name
    - Displays production metadata (facility, material, weight)
    - Includes all urgent colors for the model
    - Runs pattern optimization for each color
    - Shows last 4 months of sales history

**Order Summary Includes:**

- Pattern allocation (e.g., "Adult:2, Kids:3")
- Total patterns and excess production
- SS, ROP, forecast, deficit values
- Monthly sales history
- Size breakdown with aliases (e.g., "XS:10, S:15, M:20")

---

## Statistical Calculations Explained

### Product Type Classification

Products are classified into four types based on their sales characteristics:

| Type         | Criteria                   | Description                         |
|--------------|----------------------------|-------------------------------------|
| **New**      | First sale < 12 months ago | Recently introduced products        |
| **Basic**    | CV < 0.6                   | Stable, predictable demand          |
| **Seasonal** | CV > 1.0                   | High variability, seasonal patterns |
| **Regular**  | 0.6 ≤ CV ≤ 1.0             | Moderate variability                |

**Classification Order:** New is checked first, then Basic/Seasonal, with Regular as fallback.

### Coefficient of Variation (CV)

Measures demand variability relative to the average:

```
CV = Standard Deviation / Average Monthly Sales
```

- **Low CV (< 0.6)**: Stable demand, easy to forecast
- **Medium CV (0.6 - 1.0)**: Moderate variability
- **High CV (> 1.0)**: Highly variable, often seasonal

### Safety Stock (SS)

Buffer inventory to prevent stockouts during demand variability:

```
SS = Z-score × Standard Deviation × √(Lead Time)
```

**Components:**

- **Z-score**: Service level factor (higher = more safety stock)
    - Basic: 2.5 (99.38% service level)
    - Regular: 1.645 (95% service level)
    - Seasonal In-Season: 1.85 (96.8% service level)
    - Seasonal Out-of-Season: 1.5 (93.3% service level)
    - New: 1.8 (96.4% service level)
- **Standard Deviation**: Variability of monthly demand
- **Lead Time**: Time in months from order to receipt (default: 1.36 months)

**Example:**

```
SD = 50 units/month
Z-score = 1.645 (regular product)
Lead Time = 1.36 months

SS = 1.645 × 50 × √1.36
SS = 1.645 × 50 × 1.166
SS = 95.9 units
```

### Reorder Point (ROP)

Stock level that triggers a new order:

```
ROP = (Average Sales × Lead Time) + Safety Stock
```

**Example:**

```
Average Sales = 200 units/month
Lead Time = 1.36 months
Safety Stock = 95.9 units

ROP = (200 × 1.36) + 95.9
ROP = 272 + 95.9
ROP = 367.9 units
```

**Interpretation:** When the stock falls to 368 units, place a new order.

### Seasonal Detection

For seasonal products, the system determines if the current month is "in season":

```
Seasonal Index = Monthly Average Sales / Overall Average Sales
In Season = Seasonal Index > 1.2
```

**Example:**

```
Overall Average = 100 units/month
December Average = 180 units/month

Seasonal Index = 180 / 100 = 1.8
In Season = True (1.8 > 1.2)
```

Seasonal products use different Z-scores:

- **In-Season**: Higher Z-score (1.85) for more safety stock
- **Out-of-Season**: Lower Z-score (1.5) for less capital tied up

### Forecast Metrics

The system calculates demand forecast for the lead time period:

```
FORECAST_LEADTIME = Sum of daily forecasts from today to (today + lead time)
```

If lead time = 1.36 months (~41 days), the system sums forecast for the next 41 days.

### Stock Projection

Simulates future stock levels based on forecast:

```
For each future period:
    Projected Stock = Previous Stock - Forecast Demand
    Check if Projected Stock ≤ ROP → ROP Reached
    Check if Projected Stock ≤ 0 → Stockout
```

This creates a time-series visualization showing:

- When stock will cross the ROP threshold
- When stock will reach zero (stockout)

---

## Pattern Optimization Algorithm

The pattern optimizer finds the best allocation of cutting patterns to meet size demands while minimizing waste.

### Algorithm Modes

**1. Greedy Overshoot (Default)**

- Prioritizes complete coverage
- Allows some excess production
- Better for critical items

**2. Greedy Classic**

- Minimizes excess production
- May undercover some sizes
- Better for cost-sensitive items

### Scoring Function

Each pattern is scored based on how well it fills the remaining demand:

```
Score = Σ(min(pattern_produces, remaining_need) × 10 + priority_bonus) - excess_penalty

Where:
- priority_bonus = size_priority × pattern_produces × 5
- excess_penalty = units_not_needed × 1
```

### Optimization Process

1. Calculate minimum patterns needed: `max(quantities) / 2`
2. For each total pattern count from minimum to `min + 100`:
   a. Try to allocate patterns to cover all sizes
   b. If successful, calculate total excess
   c. Track the best solution (the lowest excess while covering all sizes)
3. If no perfect solution is found, use a greedy algorithm

### Minimum Order Constraint

Patterns must be ordered in minimum quantities (default: 5):

- First allocation of a pattern: minimum order
- Subsequent allocations: single units

### Output Explanation

| Field                  | Description                                             |
|------------------------|---------------------------------------------------------|
| `allocation`           | {pattern_id: count} - How many of each pattern to order |
| `produced`             | {size: qty} - Total units produced per size             |
| `excess`               | {size: qty} - Overproduction per size                   |
| `total_patterns`       | Sum of all pattern orders                               |
| `total_excess`         | Total units of overproduction                           |
| `all_covered`          | True if all demanded sizes are fully covered            |
| `min_order_violations` | Patterns ordered below minimum quantity                 |

---

## Priority Scoring System

The order recommendation system uses a multifactor priority score.

### Priority Score Formula

```
Priority Score = (Stockout Risk × W₁ + Revenue Impact × W₂ + Demand × W₃) × Type Multiplier
```

**Default Weights:**

- W₁ (Stockout Risk): 0.5
- W₂ (Revenue Impact): 0.3
- W₃ (Demand Forecast): 0.2

### Stockout Risk Calculation

```
If Stock = 0 AND Forecast > 0:
    Stockout Risk = 100 (zero_stock_penalty)

If 0 < Stock < ROP:
    Stockout Risk = ((ROP - Stock) / ROP) × 80 (below_rop_max_penalty)

Otherwise:
    Stockout Risk = 0
```

**Example:**

```
ROP = 100 units
Stock = 30 units

Stockout Risk = ((100 - 30) / 100) × 80
Stockout Risk = 0.7 × 80
Stockout Risk = 56
```

### Revenue Impact Calculation

```
If Price available:
    Revenue at Risk = Forecast × Price
    Revenue Impact = (Revenue at Risk / Max Revenue at Risk) × 100

If Price not available:
    Revenue Impact = (Forecast / Max Forecast) × 100
```

### Type Multipliers

Boost priority based on the product type:

| Type     | Multiplier | Effect                               |
|----------|------------|--------------------------------------|
| New      | 1.2        | +20% priority (protect new launches) |
| Seasonal | 1.3        | +30% priority (time-sensitive)       |
| Regular  | 1.0        | Baseline                             |
| Basic    | 0.9        | -10% priority (stable, less urgent)  |

### Complete Example

```
Stock = 0 units (zero stock)
Forecast = 80 units
Price = $25
Max Revenue at Risk = $10,000
Type = Seasonal

Stockout Risk = 100 (zero stock with demand)
Revenue at Risk = 80 × $25 = $2,000
Revenue Impact = ($2,000 / $10,000) × 100 = 20
Demand = min(80, 100) = 80 (capped at demand_cap)

Raw Score = (100 × 0.5) + (20 × 0.3) + (80 × 0.2)
Raw Score = 50 + 6 + 16 = 72

Priority Score = 72 × 1.3 (seasonal multiplier)
Priority Score = 93.6
```

### Aggregation by Model+Color

SKU-level priorities are aggregated to MODEL+COLOR level:

```
Priority Score = Mean of SKU scores
Deficit = Sum of SKU deficits
Forecast = Sum of SKU forecasts
Coverage Gap = max(0, Forecast - Stock)
Urgent = Any SKU is urgent
```

---

## Configuration Parameters

### settings.json

Located at `src/settings.json`, all parameters can be adjusted in the UI sidebar.

```json
{
  "lead_time": 1.36,
  "forecast_time": 5,
  "sync_forecast_with_lead_time": false,

  "cv_thresholds": {
    "basic": 0.6,
    "seasonal": 1.0
  },

  "z_scores": {
    "basic": 2.5,
    "regular": 1.645,
    "seasonal_in": 1.85,
    "seasonal_out": 1.5,
    "new": 1.8
  },

  "new_product_threshold_months": 12,

  "optimizer": {
    "min_order_per_pattern": 5,
    "algorithm_mode": "greedy_overshoot"
  },

  "order_recommendations": {
    "stockout_risk": {
      "zero_stock_penalty": 100,
      "below_rop_max_penalty": 80
    },
    "priority_weights": {
      "stockout_risk": 0.5,
      "revenue_impact": 0.3,
      "demand_forecast": 0.2
    },
    "type_multipliers": {
      "new": 1.2,
      "seasonal": 1.3,
      "regular": 1.0,
      "basic": 0.9
    },
    "demand_cap": 100
  }
}
```

### Parameter Descriptions

| Parameter                      | Default | Description                                |
|--------------------------------|---------|--------------------------------------------|
| `lead_time`                    | 1.36    | Months between order placement and receipt |
| `forecast_time`                | 5       | Months to look ahead for demand            |
| `cv_thresholds.basic`          | 0.6     | CV below this = basic product              |
| `cv_thresholds.seasonal`       | 1.0     | CV above this = seasonal product           |
| `z_scores.*`                   | varies  | Service level factors by product type      |
| `new_product_threshold_months` | 12      | Products younger than this are "new"       |
| `min_order_per_pattern`        | 5       | Minimum units per pattern order            |
| `demand_cap`                   | 100     | Maximum demand value for scoring           |

---

## Data Requirements

### Sales Data

**Required Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `order_id` | string | Order identifier |
| `data` | datetime | Sale date |
| `sku` | string | 9-character SKU code |
| `ilosc` | numeric | Quantity sold |
| `cena` | numeric | Unit price |
| `razem` | numeric | Total amount |

### Stock Data

**Required Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `sku` | string | 9-character SKU code |
| `nazwa` | string | Product description |
| `stock` | numeric | Total stock |
| `available_stock` | numeric | Available stock (used for calculations) |
| `aktywny` | 0/1 | Active flag (only active items loaded) |

### Forecast Data

**Required Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `data` | datetime | Forecast date |
| `sku` | string | 9-character SKU code |
| `forecast` | numeric | Predicted quantity |

### SKU Structure

All SKUs must be 9 characters:

```
XXXXXCCSS
│││││││││
├────┴ MODEL (characters 1-5): Product family
│    ├─┴ COLOR (characters 6-7): Color code
│       └─┴ SIZE (characters 8-9): Numeric size code
```

**Example:** `ABC12BL03`

- Model: ABC12
- Color: BL
- Size: 03

---

## Architecture

### Module Structure

```
src/
├── app.py                      # Main Streamlit application
├── settings.json               # User configuration
│
├── sales_data/                 # Data layer
│   ├── analyzer.py             # SalesAnalyzer wrapper class
│   ├── data_source.py          # Abstract DataSource interface
│   ├── file_source.py          # File-based implementation
│   ├── db_source.py            # Database implementation
│   ├── data_source_factory.py  # Factory pattern
│   └── analysis/               # Analysis modules
│       ├── aggregation.py      # SKU/Model aggregation
│       ├── classification.py   # Product type classification
│       ├── inventory_metrics.py # SS, ROP calculations
│       ├── order_priority.py   # Priority scoring
│       ├── projection.py       # Stock projection
│       ├── reports.py          # Weekly/monthly analysis
│       └── utils.py            # Shared utilities
│
├── ui/                         # Presentation layer
│   ├── tab_sales_analysis.py
│   ├── tab_pattern_optimizer.py
│   ├── tab_weekly_analysis.py
│   ├── tab_monthly_analysis.py
│   ├── tab_order_recommendations.py
│   ├── tab_order_creation.py
│   └── shared/                 # Shared UI components
│
├── utils/                      # Utilities
│   ├── pattern_optimizer.py    # Pattern optimization
│   ├── settings_manager.py     # Configuration management
│   ├── order_manager.py        # Order persistence
│   └── order_repository.py     # Repository pattern
│
└── migration/                  # Database setup (optional)
    ├── setup_database.py
    ├── import_all.py
    └── sql/                    # SQL scripts
```

### Data Flow

```
Sales Files                 Stock Files               Forecast Files
     │                           │                          │
     ▼                           ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DataSource (Abstract)                        │
│         FileSource (default) │ DatabaseSource (optional)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SalesAnalyzer                              │
│  Aggregation → Classification → SS/ROP → Forecast Integration   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        Tab 1: Analysis  Tab 3-4: Reports  Tab 5: Recommendations
                                                  │
                                                  ▼
                                          Tab 6: Order Creation
                                                  │
                                                  ▼
                                          Pattern Optimizer
```

### Data Source Switching

The application supports two data source modes:

**File Mode (Default):**

- Reads from Excel/CSV files
- Configure via `paths_to_files.txt`
- No additional setup is required

**Database Mode:**

- PostgreSQL with materialized views
- Better performance for large datasets
- Configure via `.env` file
- Requires migration scripts to set up

Switch modes by setting `DATA_SOURCE_MODE` in `.env`:

```bash
DATA_SOURCE_MODE=file      # Use Excel/CSV files
DATA_SOURCE_MODE=database  # Use PostgreSQL
```

---

## Tips for Best Results

1. **Accurate Lead Time**: Set lead time to match your actual supply chain
2. **Tune Z-scores**: Higher Z-scores = more safety stock = fewer stockouts but more capital
3. **Watch CV Thresholds**: Adjust based on your product mix characteristics
4. **Review Seasonal Products**: Verify seasonal items are correctly classified
5. **Pattern Sets**: Create pattern sets that match your actual manufacturing capabilities
6. **Weekly Review**: Check order recommendations weekly for optimal inventory

---

## Troubleshooting

**"No data loaded" error:**

- Verify `paths_to_files.txt` points to valid data files
- Ensure data files have required columns and formats

**Recommendations empty:**

- Both stock AND forecast data must be loaded
- Check that SKUs in the forecast match SKUs in sales data

**Pattern optimization fails:**

- Ensure the pattern set exists with a matching model name
- Verify size names in the pattern set match your data

**High/low priority scores:**

- Adjust weights in the sidebar (should sum to ~1.0)
- Review type multipliers for your business context

---

## License

Proprietary – All rights reserved.
