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
- [Business Guide](#business-guide)

---

## Features Overview

| Feature                   | Description                                                                |
|---------------------------|----------------------------------------------------------------------------|
| **Sales Analysis**        | Statistical analysis with Safety Stock and Reorder Point calculations      |
| **Stock Projection**      | Visual forecasting of when items will reach critical levels                |
| **Pattern Optimizer**     | Cutting pattern optimization with automatic sales history loading          |
| **Order Recommendations** | Priority-based ordering with facility filters and active order filtering   |
| **Weekly Analysis**       | Week-over-week sales comparison and trending                               |
| **Monthly Analysis**      | Year-over-year category performance                                        |
| **Order Creation**        | Transform recommendations into production orders with manual entry support |
| **Order Tracking**        | Track, manage, and archive production orders with delivery countdown       |
| **Forecast Accuracy**     | Monitor forecast quality vs actual sales with accuracy metrics             |
| **Forecast Comparison**   | Generate internal forecasts and compare with external forecasts            |
| **ML Forecast**           | Machine learning forecasts with auto-model selection per entity            |

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
4. Enter desired quantities by size OR load automatically from sales history
5. Run optimization to get pattern allocation

**Automatic Sales History Loading:**

Instead of manually entering size quantities, you can load historical sales data:

1. Enter a model code (e.g., "CH031") in the "Model" field
2. Click the "Load" button
3. System automatically aggregates the last 4 months of sales by size for all colors of the model
4. Size quantities are populated in the input fields

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
4. Automatically filters out models with active orders
5. Shows top N recommendations with size breakdowns

**Facility Filters:**

- **Include Facilities**: Show only items from selected production facilities
- **Exclude Facilities**: Hide items from selected facilities (takes precedence over include)
- Filters use model metadata (SZWALNIA GŁÓWNA) to match production facility

**Output Table:**
| Column | Description |
|--------|-------------|
| Model | 5-character model code |
| Color | 2-character color code |
| Color Name | Human-readable color name from aliases |
| Priority | Calculated priority score (higher = more urgent) |
| Deficit | How much below ROP |
| Forecast | Predicted demand during lead time |
| Sizes | Size breakdown (e.g., "08:15, 12:25, 13:30") |
| Szwalnia | Production facility (if metadata available) |

**Active Order Filtering:**

Items are automatically excluded from recommendations if they have an active order in the Order Tracking tab. This
prevents duplicate ordering.

---

### Tab 6: Order Creation

Transform recommendations into actionable production orders.

**Two Entry Methods:**

1. **From Recommendations**: Select items in Tab 5 using checkboxes, then navigate to this tab
2. **Manual Entry**: Enter any model code directly in the "Manual Order Creation" section

**Workflow:**

1. Enter model code manually OR select items from Tab 5
2. Click "Create Order"
3. System automatically:
    - Loads pattern set matching the model name
    - Displays production metadata (facility, material, weight)
    - Includes all urgent colors for the model
    - Runs pattern optimization for each color
    - Shows last 4 months of sales history

**Order Summary Includes:**

- Pattern allocation (e.g., "Adult:2, Kids:3")
- Total patterns and excess production
- Stock, SS, ROP, forecast, deficit, coverage gap values
- Monthly sales history (last 4 months)
- Size breakdown with aliases (e.g., "XS:10, S:15, M:20")

**Size × Color Production Table:**

A visual matrix showing pattern allocations across all colors for the model, with sizes in rows and colors in columns.

**Actions:**

- **Save to Database**: Stores order with full JSON data
- **Download CSV**: Export order summary as CSV file
- **Cancel**: Clear selections and start over

---

### Tab 7: Order Tracking

Track and manage created production orders with delivery countdown.

**Features:**

- **Manual Order Entry**: Add orders directly by entering model code and date
- **Active Orders List**: View all orders with status and days elapsed
- **Delivery Countdown**: Shows days until expected delivery (default threshold: 41 days)
- **Archive Function**: Move completed orders to the archive

**Order Status Indicators:**

- **Ready for Delivery**: Order has exceeded delivery threshold days
- **X days left**: Countdown to expected delivery

**Table Columns:**
| Column | Description |
|--------|-------------|
| Order ID | Unique order identifier (ORD_MODEL_TIMESTAMP) |
| Model | 5-character model code |
| Order Date | When the order was placed |
| Days Elapsed | Days since order placement |
| Status | Delivery status with countdown |
| Archive | Checkbox to archive completed orders |

**Workflow:**

1. Orders appear automatically when saved from Tab 6
2. Track delivery progress via days elapsed
3. When the order arrives (>= threshold days), the status shows "Ready for Delivery"
4. Archive orders to remove from an active list

---

### Tab 8: Forecast Accuracy

**Purpose:** Measure how accurate your external forecast was compared to what actually sold. This answers the question:
*"How good was our forecast?"*

**When to Use:**

- Monthly review to assess forecast quality
- After a season ends to evaluate prediction accuracy
- When investigating why certain products had stockouts or overstock

**Key Concept:**
This tab looks **backwards in time**. It compares a **past forecast** against **actual sales that already happened**.
You're measuring historical accuracy, not predicting the future.

#### Step-by-Step Workflow

1. **Set Analysis Period** (the time range you want to evaluate):
    - Example: If today is January 15, 2025, you might analyze October 1 - December 31, 2024
    - This is the period where you'll compare forecast vs. actual sales
    - Minimum recommended: at least 30 days for meaningful results

2. **Set Forecast Lookback** (how far back to find the forecast file):
    - Default: 4 months before analysis starts
    - The system looks for a forecast file generated before your analysis period
    - Example: For analysis starting Oct 1, it looks for the forecast from ~June 2024
    - This simulates real-world conditions where you make forecasts months ahead

3. **Choose View Level**:
    - **SKU**: Granular analysis of each size/color variant
    - **Model**: Aggregated analysis at product family level (recommended for overview)

4. **Click "Generate Accuracy Report"**

#### Understanding the Results

**Overall Metrics (top of page):**

| Metric             | What It Means                                       | Target        |
|--------------------|-----------------------------------------------------|---------------|
| MAPE               | Average error as percentage                         | < 20% = Good  |
| BIAS               | Positive = over-forecast, Negative = under-forecast | Close to 0%   |
| Missed Opportunity | Units that could have sold during stockouts         | Minimize      |
| Volume Accuracy    | Total forecast vs total actual                      | Close to 100% |

**Color Indicators:**

- 🟢 Green (MAPE < 20%): Excellent - forecast is reliable
- 🟡 Yellow (MAPE 20–40%): Acceptable - room for improvement
- 🔴 Red (MAPE > 40%): Poor - investigate why

**Accuracy by Product Type Chart:**
Shows which product categories forecast well vs. poorly. Common patterns:

- Basic products usually have the lowest MAPE (stable demand)
- New products often have highest MAPE (limited history)
- Seasonal products vary based on timing

**Trend Chart:**
Shows how accuracy changed over time during the analysis period. Look for:

- Consistent low MAPE = reliable forecasting
- Spikes = investigate specific weeks/events
- Improving trend = forecasting process getting better

**Detail Table:**
Click on any SKU/Model to see:

- Actual sales vs forecast per period
- When stockouts occurred
- MAPE breakdown by week/month

#### Practical Example

*Scenario: Q4 2024 review (Oct – Dec)*

1. Set Analysis Start: October 1, 2024
2. Set Analysis End: December 31, 2024
3. Lookback: 4 months (finds ~June 2024 forecast)
4. Generate a report

*Results interpretation:*

- Overall MAPE: 28% → Acceptable, but could improve
- BIAS: +15% → Consistently over-forecasting (ordered too much)
- Basic products: 18% MAPE → Good
- Seasonal products: 45% MAPE → Poor (Christmas spike underestimated)

*Action: Adjust seasonal Z-scores and review seasonal detection parameters*

---

### Tab 9: Forecast Comparison

**Purpose:** Generate your own statistical forecasts and compare them against external/vendor forecasts. This answers:
*"Could we forecast better internally?"*

**When to Use:**

- Evaluating whether to switch forecast providers
- Testing if internal models outperform vendor forecasts
- Building a historical record of forecast experiments
- Identifying which product types work best with which methods

**Key Concept:**
This tab generates **new forecasts looking forward**, then compares them to external forecasts. It uses statistical
methods (Moving Average, Exponential Smoothing, Holt-Winters, SARIMA) automatically selected based on a product type.

#### Two Sub-tabs

**1. Generate New** - Create fresh internal forecasts
**2. Historical Forecasts** - Review previously saved forecast experiments

---

#### Generate New Tab: Step-by-Step

1. **Set Forecast Horizon**:
    - How many months ahead to forecast (1–12)
    - Default: matches your lead time setting
    - Recommendation: Match your typical planning horizon (e.g., 2–3 months)

2. **Choose Entity Level**:
    - **Model** (recommended): Faster, more stable results, aggregates by product family
    - **SKU**: Detailed but slower, may have sparse data for low-volume items

3. **Set Top N**:
    - Limit analysis to top N entities by sales volume
    - Recommendation: Start with 50–100 for quick analysis, increase for comprehensive review
    - Full analysis of all items can take several minutes

4. **Click "Generate Comparison"**

#### Understanding Comparison Results

**Overall Summary Box:**

```
Internal Wins: 45 (45%)
External Wins: 38 (38%)
Ties: 17 (17%)
```

Higher internal win % suggests your statistical models outperform the vendor forecast.

**Breakdown by Product Type Table:**

| Type     | Total | Internal Wins | External Wins | Internal Win % | Avg Int MAPE | Avg Ext MAPE |
|----------|-------|---------------|---------------|----------------|--------------|--------------|
| basic    | 30    | 20            | 8             | 67%            | 15%          | 22%          |
| regular  | 40    | 18            | 18            | 45%            | 25%          | 26%          |
| seasonal | 20    | 5             | 12            | 25%            | 38%          | 28%          |
| new      | 10    | 2             | 0             | 20%            | 45%          | 52%          |

*Interpretation: Internal models excel for basic products but struggle with seasonal items.*

**Detailed Comparison Table:**
Each row shows one entity (SKU or Model) with:

- Internal MAPE vs External MAPE
- Winner indicator
- Improvement % (how much better the winner was)
- Methods used (which statistical method was applied)

**Comparison Chart:**
Select any entity to see a visual comparison:

- Gray line: Actual historical sales
- Blue line: Internal forecast
- Red line: External forecast
- Shaded area: Forecast period

#### Saving Forecasts to History

After generating, you can save results for future reference:

1. Add optional notes (e.g., "Q1 2025 baseline", "After parameter tuning")
2. Click "Save Forecast to History"
3. Saved forecasts include:
    - All generated forecast values
    - Parameters used
    - Comparison metrics
    - Timestamp

**Why Save?**

- Track improvements over time
- Compare before/after parameter changes
- Build evidence for forecast provider decisions
- Audit the trail of forecasting experiments

---

#### Historical Forecasts Tab: Step-by-Step

1. **Select Saved Forecast** from the dropdown (sorted by date, newest first)

2. **Review Batch Info:**
    - Generated date/time
    - Entity type (SKU/Model)
    - Forecast horizon
    - Success/failure counts
    - Methods used breakdown

3. **Click "Load and Compare"** to recalculate metrics against current actual data

4. **Or "Delete"** to remove a historical forecast

**Why Reload?**
As more actual sales data becomes available, you can recalculate the accuracy of old forecasts to see true performance.

---

#### Forecasting Methods Explained

The system automatically selects the best method for each entity:

| Method                    | When Used                         | How It Works                     | Best For                     |
|---------------------------|-----------------------------------|----------------------------------|------------------------------|
| **Moving Average**        | New products (< 6 months history) | Weighted average of recent sales | Limited data situations      |
| **Exponential Smoothing** | Basic products (CV < 0.6)         | Trend-following with decay       | Stable, trending products    |
| **Holt-Winters**          | Regular products (0.6 ≤ CV ≤ 1.0) | Trend + seasonality              | Products with clear patterns |
| **SARIMA**                | Seasonal products (CV > 1.0)      | Full seasonal ARIMA model        | Complex seasonal patterns    |

*Fallback behavior: If a complex method fails (insufficient data), the system automatically tries simpler methods.*

---

#### Practical Examples

**Example 1: Quarterly Vendor Evaluation**

*Goal: Should we renew the contract with a forecast vendor?*

1. Generate New → Model level → Top 200 → Horizon: 3 months
2. Review overall summary: Internal wins 55%, External wins 35%
3. Check by product type: Internals much better for basic/regular
4. Save with note: "Q4 2024 vendor evaluation"
5. Decision: Consider bringing forecasting in-house for stable products

**Example 2: Before/After Parameter Tuning**

*Goal: Did adjusting seasonal Z-scores improve forecasting?*

1. Before changes: Save forecast with the note "Before seasonal tuning"
2. Adjust parameters in sidebar
3. After changes: Generate a new comparison
4. Save with the note "After seasonal tuning"
5. Load both from history and compare win rates

**Example 3: Method Performance Analysis**

*Goal: Which forecasting method works best for our product mix?*

1. Generate comparison at Model level → Top 500
2. Export detailed table to CSV
3. Analyze externally: Group by "Method Used" column
4. Find: SARIMA has the lowest MAPE for seasonal items, Moving Average struggles
5. Action: Investigate why some entities fall back to simpler methods

---

#### Key Differences: Tab 8 vs Tab 9

| Aspect                | Tab 8: Forecast Accuracy          | Tab 9: Forecast Comparison        |
|-----------------------|-----------------------------------|-----------------------------------|
| **Direction**         | Looks backwards                   | Looks forwards                    |
| **Purpose**           | Measure past performance          | Generate new forecasts            |
| **Compares**          | External forecast vs actual sales | Internal vs external forecasts    |
| **Question Answered** | "How accurate was our forecast?"  | "Could we forecast better?"       |
| **Output**            | Accuracy metrics (MAPE, BIAS)     | Winner analysis + saved forecasts |
| **Typical Use**       | Monthly/quarterly review          | Vendor evaluation, method testing |

---

### Tab 10: ML Forecast

**Purpose:** Train machine learning models to generate forecasts with automatic model selection per SKU/Model. Uses
cross-validation to select the best performing model for each entity.

**When to Use:**

- When you have sufficient historical data (12+ months recommended)
- To compare ML-based forecasts against statistical or external forecasts
- To leverage advanced feature engineering for better predictions
- When demand patterns may be captured by lagged features and rolling statistics

**Key Concept:**
This tab trains multiple ML models (LightGBM, RandomForest, Ridge, Lasso) plus optional statistical models (SARIMA,
Holt-Winters, Exponential Smoothing) for each entity and selects the best performer via time-series cross-validation.

#### Three Sub-tabs

**1. Train Models** - Train and select the best models per entity
**2. Generate Forecasts** - Use trained models to generate predictions
**3. Manage Models** - View, compare, and delete saved models

---

#### Train Models Tab: Step-by-Step

1. **Select Entity Level**:
    - **Model** (recommended): Faster training, more stable results
    - **SKU**: Granular but requires more data per entity

2. **Set Top N**:
    - Limit training to top N entities by sales volume
    - Start with 50–100 for testing, increase for production use

3. **Select Models to Train**:
    - **LightGBM**: Gradient boosting, handles complex patterns well
    - **RandomForest**: Ensemble method, robust to outliers
    - **Ridge/Lasso**: Regularized linear models, fast training
    - **Statistical**: Includes SARIMA, Holt-Winters, ETS (optional)

4. **Configure Cross-Validation**:
    - **CV Splits**: Number of time-series splits (default: 3)
    - **Test Size**: Months per test fold (default: 3)
    - **Metric**: MAPE (default) or MAE/RMSE

5. **Click "Train Models"**

#### Feature Engineering

The system automatically creates features for ML models:

| Feature Type      | Description                                   |
|-------------------|-----------------------------------------------|
| **Time Features** | Month, quarter, day of week, is_month_end     |
| **Lag Features**  | Sales from 1, 2, 3, 6, 12 months ago          |
| **Rolling Stats** | 3-month and 6-month moving averages and stdev |
| **YoY Features**  | Year-over-year change and ratio               |
| **Product Info**  | Product type encoding (basic, seasonal, etc.) |

#### Understanding Training Results

**Training Progress:**

- Shows entity-by-entity progress
- Displays the best model selected for each entity
- Reports CV score (MAPE) for the winning model

**Training Summary:**

- Total entities trained
- Model distribution (how many chose each model type)
- Average CV MAPE across all entities
- Training time

**Model Storage:**

- Models saved to `data/ml_models/` directory
- Each model includes metadata (CV score, features used, training date)
- Models persist across sessions

---

#### Generate Forecasts Tab: Step-by-Step

1. **Select Trained Models**:
    - System shows available trained models
    - Select entities to forecast (or all)

2. **Set Forecast Horizon**:
    - Months ahead to predict (default: matches lead time)
    - Maximum: 12 months

3. **Click "Generate Forecasts"**

#### Forecast Output

**Forecast Table:**
| Column | Description |
|------------------|---------------------------------------|
| Entity | SKU or Model code |
| Forecast Month | Target prediction month |
| Predicted Qty | Model prediction |
| Lower Bound | 95% confidence interval lower |
| Upper Bound | 95% confidence interval upper |
| Model Used | Which ML model made the prediction |

**Prediction Intervals:**

- Based on cross-validation residuals
- 95% confidence level by default (configurable in settings)

---

#### Manage Models Tab: Step-by-Step

1. **View Saved Models**:
    - List of all trained models with metadata
    - Training date, CV score, features used

2. **Model Statistics**:
    - Distribution by model type
    - Average performance metrics
    - Age of models (days since training)

3. **Delete Models**:
    - Remove outdated or poor-performing models
    - Clear all models to retrain from scratch

---

#### Integration with Order Recommendations

ML forecasts can be used in Tab 5 (Order Recommendations):

1. Train models in Tab 10
2. Go to Tab 5: Order Recommendations
3. Select "ML" as a forecast source (dropdown shows the count of available models)
4. Generate recommendations using ML predictions

**Fallback Behavior:**

- If the ML model is unavailable for an entity, it falls back to external forecast
- Mixed sources are clearly indicated in the output

---

#### ML Models Explained

| Model            | Strengths                       | Best For                        |
|------------------|---------------------------------|---------------------------------|
| **LightGBM**     | Fast, handles nonlinearity      | Complex patterns, large data    |
| **RandomForest** | Robust, feature importance      | General use, outlier resistance |
| **Ridge**        | Fast, interpretable             | Linear trends, quick baseline   |
| **Lasso**        | Feature selection built-in      | Sparse patterns                 |
| **SARIMA**       | Captures seasonality explicitly | Strong seasonal patterns        |
| **Holt-Winters** | Trend + seasonality             | Clear growth/decline trends     |
| **ExpSmoothing** | Smooth predictions              | Stable demand patterns          |

---

#### Practical Examples

**Example 1: Initial ML Setup**

*Goal: Train ML models for top-selling items*

1. Train Models → Model level → Top 100
2. Select: LightGBM + RandomForest (fastest, most reliable)
3. CV Settings: three splits, 3-month test size
4. Click "Train Models"
5. Review summary: ~60% LightGBM wins, ~30% RandomForest, ~10% Ridge
6. Generate Forecasts → All trained models → 3-month horizon

**Example 2: Compare ML vs Statistical**

*Goal: Are ML models better than statistical methods?*

1. Train Models with statistical methods included
2. Review model distribution:
    - If ML dominates (>70%), ML adds value
    - If statistically competitive, consider hybrid
3. Compare Tab 9 internal forecasts vs. Tab 10 ML forecasts

**Example 3: Use ML for Order Recommendations**

*Goal: Replace external forecast with ML predictions*

1. Ensure models are trained for relevant entities
2. Tab 5 → Select "ML (N models)" as a forecast source
3. Generate recommendations
4. Compare priority scores with an external forecast source
5. Monitor accuracy over time via Tab 8

---

#### Key Differences: Tab 9 vs Tab 10

| Aspect              | Tab 9: Forecast Comparison   | Tab 10: ML Forecast            |
|---------------------|------------------------------|--------------------------------|
| **Methods**         | Statistical only             | ML + Statistical               |
| **Model Selection** | Rule-based by product type   | Cross-validation per entity    |
| **Feature Eng.**    | None (time series methods)   | Lags, rolling stats, YoY       |
| **Persistence**     | Forecast batches saved       | Individual models saved        |
| **Primary Use**     | Compare internal vs external | Production forecasting         |
| **Best When**       | Evaluating forecast sources  | Maximizing prediction accuracy |

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
  "data_source": {
    "mode": "database",
    "fallback_to_file": true,
    "pool_size": 10,
    "pool_recycle": 3600,
    "echo_sql": false
  },
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
  "weekly_analysis": {
    "lookback_days": 60
  },
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

| Parameter                       | Default          | Description                                      |
|---------------------------------|------------------|--------------------------------------------------|
| `data_source.mode`              | database         | Data source mode: "file" or "database"           |
| `data_source.fallback_to_file`  | true             | Fall back to file mode if database unavailable   |
| `lead_time`                     | 1.36             | Months between order placement and receipt       |
| `forecast_time`                 | 5                | Months to look ahead for demand                  |
| `cv_thresholds.basic`           | 0.6              | CV below this = basic product                    |
| `cv_thresholds.seasonal`        | 1.0              | CV above this = seasonal product                 |
| `z_scores.*`                    | varies           | Service level factors by product type            |
| `new_product_threshold_months`  | 12               | Products younger than this are "new"             |
| `weekly_analysis.lookback_days` | 60               | Days to look back for new products monitor       |
| `min_order_per_pattern`         | 5                | Minimum units per pattern order                  |
| `algorithm_mode`                | greedy_overshoot | Optimizer algorithm: greedy_overshoot or classic |
| `demand_cap`                    | 100              | Maximum demand value for scoring                 |

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
│   ├── loader.py               # File I/O operations
│   ├── validator.py            # Data schema validation
│   └── analysis/               # Analysis modules
│       ├── aggregation.py      # SKU/Model aggregation
│       ├── classification.py   # Product type classification
│       ├── forecast_accuracy.py # Forecast accuracy metrics
│       ├── forecast_comparison.py # Internal vs external forecast comparison
│       ├── internal_forecast.py # Internal forecast generation (statsmodels)
│       ├── inventory_metrics.py # SS, ROP calculations
│       ├── order_priority.py   # Priority scoring
│       ├── pattern_helpers.py  # Pattern optimization helpers
│       ├── projection.py       # Stock projection
│       ├── reports.py          # Weekly/monthly analysis
│       ├── ml_feature_engineering.py  # ML feature creation
│       ├── ml_model_selection.py      # Cross-validation model selection
│       ├── ml_forecast.py             # ML training and prediction
│       └── utils.py            # Shared utilities
│
├── ui/                         # Presentation layer
│   ├── sidebar.py              # Sidebar configuration
│   ├── constants.py            # UI constants and config
│   ├── tab_sales_analysis.py
│   ├── tab_pattern_optimizer.py
│   ├── tab_weekly_analysis.py
│   ├── tab_monthly_analysis.py
│   ├── tab_order_recommendations.py
│   ├── tab_order_creation.py
│   ├── tab_order_tracking.py
│   ├── tab_forecast_accuracy.py
│   ├── tab_forecast_comparison.py
│   ├── tab_ml_forecast.py      # ML forecast UI
│   └── shared/                 # Shared UI components
│       ├── data_loaders.py     # Cached data loading
│       ├── display_helpers.py  # Display utilities
│       ├── forecast_accuracy_loader.py
│       ├── session_manager.py  # Session state management
│       ├── sku_utils.py        # SKU parsing utilities
│       └── styles.py           # CSS styles
│
├── utils/                      # Utilities
│   ├── pattern_optimizer.py    # Pattern optimization
│   ├── settings_manager.py     # Configuration management
│   ├── order_manager.py        # Order persistence facade
│   ├── order_repository.py     # Repository pattern (abstract)
│   ├── order_repository_factory.py # Repository factory
│   ├── internal_forecast_repository.py # Internal forecast storage
│   ├── ml_model_repository.py  # ML model persistence
│   ├── import_utils.py         # Import helpers
│   └── logging_config.py       # Logging setup (LOG_LEVEL from .env)
│
└── migration/                  # Database setup (optional)
    ├── setup_database.py
    ├── import_all.py
    ├── populate_cache.py
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
LOG_LEVEL=INFO             # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

## Business Guide

This section explains how to use Stock Monitor 3 from a business perspective, without requiring technical knowledge.

### Understanding Your Inventory Health

#### What the Numbers Mean

**Safety Stock (SS)** - Your insurance policy against running out of stock

- Think of it as a buffer that protects you from unexpected demand spikes
- Higher SS = fewer stockouts but more money tied up in inventory
- Lower SS = less capital required but higher risk of losing sales

**Reorder Point (ROP)** - Your "order now" alarm

- When inventory drops to this level, it's time to place an order
- Accounts for both your lead time AND safety buffer
- Items below ROP need immediate attention

**Coefficient of Variation (CV)** - How predictable is demand?

- Low CV (under 0.6): Very predictable, steady sellers - your "bread and butter"
- Medium CV (0.6–1.0): Somewhat variable - normal products
- High CV (over 1.0): Highly unpredictable - often seasonal items

### Product Categories Explained

| Category     | What It Means                  | Business Implication                          |
|--------------|--------------------------------|-----------------------------------------------|
| **Basic**    | Steady, predictable sellers    | Stock consistently; low risk of overstock     |
| **Regular**  | Normal variability             | Standard inventory management                 |
| **Seasonal** | Sales spike in certain periods | Build stock before season; reduce after       |
| **New**      | Less than 12 months of history | Monitor closely; limited data for forecasting |

### Daily Workflow Recommendations

#### Morning Check (5 minutes)

1. Open **Tab 1: Sales Analysis**
2. Filter by "Below ROP" to see critical items
3. Note any urgent items (zero stock with demand)
4. Check **Tab 7: Order Tracking** for orders ready for delivery

#### Weekly Planning (30 minutes)

1. **Tab 5: Order Recommendations** - Generate top 20–30 priorities
2. Use facility filters to focus on specific production facilities
3. Review the priority list - highest scores need action first
4. Select items and navigate to **Tab 6: Order Creation**
5. Review pattern allocations and save orders
6. Archive delivered orders in **Tab 7**

#### Monthly Review (1 hour)

1. **Tab 3: Weekly Analysis** - Identify rising and falling products
2. **Tab 4: Monthly Analysis** - Check category performance vs. last year
3. **Tab 8: Forecast Accuracy** - Review forecast quality (target < 20% MAPE)
4. Review and adjust settings if needed (lead time, Z-scores)

### Reading the Priority Score

The priority score (0–150+) tells you what to order first:

| Score Range  | Urgency  | Action                                 |
|--------------|----------|----------------------------------------|
| **80+**      | Critical | Order immediately - high stockout risk |
| **50-80**    | High     | Order this week                        |
| **30-50**    | Medium   | Plan for next order cycle              |
| **Under 30** | Low      | Monitor, no immediate action           |

**What drives high scores:**

- Zero stock with expected demand = highest urgency
- Stock below ROP = moderate urgency
- High forecast demand = increasing score
- Seasonal/New products = boosted priority (time-sensitive)

### Making Smarter Ordering Decisions

#### When to Increase Safety Stock

- Products with frequent stockouts
- High-margin items where lost sales hurt
- Seasonal items entering their peak period
- Unreliable suppliers with variable lead times

#### When to Decrease Safety Stock

- Slow-moving items tying up capital
- Products being phased out
- Items with very stable, predictable demand
- Seasonal items leaving their peak period

#### Understanding the Trade-offs

| More Safety Stock    | Less Safety Stock     |
|----------------------|-----------------------|
| Fewer stockouts      | More stockouts        |
| Higher service level | Lower service level   |
| More capital tied up | Less capital required |
| Risk of obsolescence | Risk of lost sales    |

### Seasonal Planning

The system automatically detects seasonal patterns, but here's how to use that information:

**Before Peak Season:**

1. Check which items are classified as "Seasonal"
2. Note their in-season months (visible in detailed analysis)
3. Build inventory 1–2 months before the season starts
4. Use a higher Z-score (in-season setting) during peak

**After Peak Season:**

1. System automatically switches to out-of-season Z-score
2. Lower safety stock reduces capital tied up
3. Monitor for excess inventory that may need clearance

### Pattern Optimizer for Production

If you manufacture or order in cutting patterns:

**Setting Up Patterns:**

1. Create a pattern set for each product type (e.g., "Adults", "Kids")
2. Define the sizes available (XL, L, M, S, XS)
3. Add patterns that match your production capabilities

**Reading Optimization Results:**

- **Allocation**: How many of each pattern to produce
- **Excess**: Overproduction per size (minimize this)
- **All Covered**: Green = all sizes fulfilled; Red = some sizes short

**Tip:** Name pattern sets to match model codes for automatic matching during order creation.

### Key Performance Indicators to Watch

| KPI             | What to Monitor                 | Target    | Where to Check |
|-----------------|---------------------------------|-----------|----------------|
| Items Below ROP | Count of critical items         | Minimize  | Tab 1 filter   |
| Stockout Rate   | Items at zero with demand       | Under 5%  | Tab 5 urgent   |
| Overstock Items | Stock > 6 months of demand      | Under 10% | Tab 1 filter   |
| Forecast MAPE   | Mean Absolute Percentage Error  | Under 20% | Tab 8          |
| Forecast Bias   | Over/under forecasting tendency | Near 0%   | Tab 8          |
| Internal vs Ext | Internal forecast win rate      | Track     | Tab 9          |
| ML Model MAPE   | Average CV MAPE of ML models    | Under 25% | Tab 10         |
| Active Orders   | Orders in production            | Track     | Tab 7          |
| Orders Ready    | Orders past delivery threshold  | Process   | Tab 7          |

### Common Business Scenarios

#### Scenario 1: New Product Launch

1. System classifies as "New" (higher priority multiplier)
2. Limited history means forecasts are less reliable
3. **Action:** Monitor weekly, adjust orders based on actual sales

#### Scenario 2: Seasonal Spike Coming

1. Check which items have upcoming "in-season" months
2. Review current stock vs. increased ROP (in-season calculation)
3. **Action:** Pre-order to build inventory before the rush

#### Scenario 3: Slow-Moving Inventory

1. Filter Tab 1 by "Overstock" to find excess
2. Check if items are Basic (predictable) or declining
3. **Action:** Consider promotions, reduce future orders

#### Scenario 4: Supplier Delay

1. Increase lead time setting temporarily
2. System recalculates higher SS and ROP
3. **Action:** Order earlier to compensate for longer delivery

#### Scenario 5: Poor Forecast Accuracy

1. Open **Tab 8: Forecast Accuracy**
2. Set analysis period: last 90 days (or last completed quarter)
3. Set lookback: 4 months (to find the forecast that was used)
4. Generate report and review overall MAPE
5. Check MAPE by product type - identify problem categories
6. Review BIAS:
    - Positive (+) = over-forecasting = ordered too much = excess inventory
    - Negative (-) = under-forecasting = ordered too little = stockouts
7. **Action:** For categories with high MAPE:
    - Seasonal with poor accuracy → Review seasonal detection parameters
    - New products with poor accuracy → Expected, monitor more closely
    - Basic products with poor accuracy → Investigate data quality issues

#### Scenario 6: Order Delivery Tracking

1. Open **Tab 7: Order Tracking**
2. Review orders with "Ready for Delivery" status
3. Verify delivery arrival and update stock
4. Archive processed orders to keep the list clean
5. **Action:** Check Tab 5 - archived models will reappear in recommendations if needed

#### Scenario 7: Evaluating Forecast Sources (Quarterly Review)

*Goal: Should we use external vendor forecasts or build internal models?*

1. Open **Tab 9: Forecast Comparison**
2. Set parameters: Model level, Top 200, Horizon = lead time
3. Click "Generate Comparison" and wait for analysis
4. Review overall summary:
    - Internal wins > 50%? → Internal models may be better
    - External wins > 50%? → Vendor forecast is adding value
5. Check the breakdown by product type:
    - Internal often wins for basic products (stable patterns)
    - External may win for seasonal (vendor may have market intelligence)
6. Save with note: "Q4 2024 vendor review"
7. **Action:** Consider hybrid approach - use internal for basic, external for seasonal

#### Scenario 8: Tracking Forecast Improvement Over Time

*Goal: Are our forecasting adjustments making things better?*

1. Open **Tab 9: Forecast Comparison** → Historical Forecasts tab
2. Load the oldest saved forecast
3. Note the internal win rate and average MAPE
4. Load the newest saved forecast
5. Compare win rates and MAPE values
6. **Action:** If improving, continue the current approach; if not, review parameter changes

#### Scenario 9: Setting Up ML Forecasting

*Goal: Start using ML models for forecasting*

1. Open **Tab 10: ML Forecast** → Train Models tab
2. Select Model level (faster), Top 100 entities
3. Select LightGBM + RandomForest (the best combination)
4. Keep default CV settings (three splits, 3-month test)
5. Click "Train Models" and wait for completion
6. Review model distribution: which model types won most often
7. Go to the Generate Forecasts tab → generate a 3-month horizon
8. **Action:** Compare ML forecasts with external forecasts in Tab 9

#### Scenario 10: Using ML Forecasts for Order Recommendations

*Goal: Replace external forecast with ML predictions*

1. Ensure ML models are trained (Tab 10)
2. Open **Tab 5: Order Recommendations**
3. Select "ML (N models)" from the forecast source dropdown
4. Click "Generate Recommendations"
5. Compare results with an external forecast source
6. **Action:** If ML recommendations align better with business intuition, switch permanently

### Adjusting Settings for Your Business

**Conservative Approach** (fewer stockouts, more inventory):

- Higher Z-scores (2.0+ for basic, 2.5+ for seasonal)
- Higher stockout risk weight (0.6–0.7)
- Lower demand cap

**Aggressive Approach** (less inventory, accept some stockouts):

- Lower Z-scores (1.5 for basic, 1.8 for seasonal)
- Higher demand forecast weight (0.3–0.4)
- Higher demand cap

**Balanced Approach** (default):

- Standard Z-scores as configured
- Equal weight distribution
- Suitable for most businesses

### Quick Reference Card

| I Want To...                  | Go To... | Do This...                                       |
|-------------------------------|----------|--------------------------------------------------|
| See what needs ordering       | Tab 5    | Generate recommendations, use facility filters   |
| Check a specific product      | Tab 1    | Search by SKU/Model, view projection chart       |
| Find trending products        | Tab 3    | Check Rising/Falling Stars                       |
| Compare to last year          | Tab 4    | Review category YoY performance                  |
| Create a production order     | Tab 6    | Select items from Tab 5 or enter model manually  |
| Set up cutting patterns       | Tab 2    | Create pattern set, define sizes and patterns    |
| Load sales history for sizes  | Tab 2    | Enter model code, click Load                     |
| Track order delivery          | Tab 7    | View active orders, check days elapsed           |
| Add manual order              | Tab 7    | Enter model code and date                        |
| Archive completed order       | Tab 7    | Check archive checkbox, click Archive button     |
| Check forecast quality        | Tab 8    | Set analysis period + lookback, generate report  |
| See forecast accuracy trend   | Tab 8    | Generate report, scroll to Trend Chart section   |
| Compare internal vs external  | Tab 9    | Generate New → set horizon → Generate Comparison |
| Save forecast for history     | Tab 9    | After generating, add notes, Save to History     |
| Load historical forecast      | Tab 9    | Historical Forecasts tab → select → Load         |
| Train ML models               | Tab 10   | Train Models tab → select models → Train         |
| Generate ML forecasts         | Tab 10   | Generate Forecasts tab → select horizon          |
| Use ML for recommendations    | Tab 5    | Select "ML" as forecast source                   |
| Filter by production facility | Tab 5    | Use Include/Exclude facility filters             |

---

## Tips for Best Results

1. **Accurate Lead Time**: Set lead time to match your actual supply chain
2. **Tune Z-scores**: Higher Z-scores = more safety stock = fewer stockouts but more capital
3. **Watch CV Thresholds**: Adjust based on your product mix characteristics
4. **Review Seasonal Products**: Verify seasonal items are correctly classified
5. **Pattern Sets**: Create pattern sets that match your actual manufacturing capabilities (name = model code)
6. **Weekly Review**: Check order recommendations weekly for optimal inventory
7. **Use Facility Filters**: Focus on one production facility at a time for efficient ordering
8. **Track Orders**: Keep Tab 7 updated - archive delivered orders to prevent duplicate recommendations
9. **Monitor Forecast Accuracy**: Check Tab 8 monthly - target MAPE under 20%
10. **Manual Orders**: Use Tab 7 for orders placed outside the system to maintain accurate filtering
11. **Compare Forecasts**: Use Tab 9 to evaluate if internal models could improve forecast accuracy
12. **Save Forecast History**: Regularly save internal forecasts to track accuracy improvements over time
13. **ML Training**: Retrain ML models monthly to capture recent demand patterns
14. **ML Model Selection**: Start with LightGBM + RandomForest for best results with reasonable training time

---

## Troubleshooting

**"No data loaded" error:**

- Verify `paths_to_files.txt` points to valid data files
- Ensure data files have required columns and formats

**Recommendations empty:**

- Both stock AND forecast data must be loaded
- Check that SKUs in the forecast match SKUs in sales data
- Check if facility filters are excluding all items

**Items missing from recommendations:**

- Model may have an active order in Tab 7 - archive it if delivered
- Check facility filters - model may be excluded

**Pattern optimization fails:**

- Ensure the pattern set exists with a matching model name
- Verify size names in the pattern set match your data

**High/low priority scores:**

- Adjust weights in the sidebar (should sum to ~1.0)
- Review type multipliers for your business context

**Forecast accuracy shows no data:**

- Ensure an analysis period is at least as long as the lead time
- Check that a forecast file exists for the lookback period
- Verify SKUs match between sales and forecast data

**Order tracking issues:**

- Orders only filter recommendations by model code
- Archive orders when items are received to re-enable recommendations

**Forecast comparison issues:**

- Ensure both sales data and external forecast data are loaded
- Internal forecasts require at least 3 months of sales history per entity
- SARIMA method may fail for entities with sparse data - the system falls back to simpler methods
- Historical forecasts require database mode or write access to data/internal_forecasts/ directory

**ML Forecast issues:**

- Require lightgbm and scikit-learn packages installed
- Training requires at least 12 months of sales history for reliable features
- Models are saved in data/ml_models/ directory
- Cross-validation may fail for sparse data - increase minimum data requirements

**Pattern optimizer sales history not loading:**

- Ensure model code exists in sales data
- System aggregates all colors for the model
- Requires at least 4 months of sales history

---

## License

Proprietary – All rights reserved.
