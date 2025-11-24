## Project Overview

This is a comprehensive Streamlit-based inventory management and sales analytics application with three main features:

1. **Sales & Inventory Analysis**: Statistical analysis of sales data with Safety Stock (SS) and Reorder Point (ROP) calculations
2. **Size Pattern Optimizer**: Cutting pattern optimization for manufacturing/ordering
3. **Order Recommendations**: Automated priority-based ordering system that integrates with pattern matching

The application uses statistical methods to analyze historical sales, forecast future demand, and optimize ordering decisions to maximize sales while minimizing stockouts and excess inventory.


### Running the Application

**On macOS/Linux:**
```bash
python3 -m streamlit run app.py
```

**On Windows:**
```cmd
cd src
py V:3.13 -m streamlit run app.py
```

### Environment Setup

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```cmd
py V:3.13 -m venv venv
venv\Scripts\activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

## Application Structure

The application has three main tabs:

### Tab 1: 📊 Sales & Inventory Analysis

Main analytics dashboard showing:
- **Data Table**: SKU/Model-level inventory data with filtering (search, below ROP, bestsellers, product type, overstock)
- **Stock Projection Chart**: Time-series visualization showing when individual SKUs will reach ROP and zero stock based on forecast
- **Statistics**: Product type distribution, stock status metrics, pie charts
- **Configurable Parameters** (sidebar):
    - Lead time (months)
    - CV thresholds for product classification
    - Z-scores for each product type (basic, regular, seasonal, new)
    - View options (SKU vs. Model grouping)

**Key Features**:
- Enter a SKU to see projected stock depletion over time
- Visual indicators for when the stock crosses ROP and reaches zero
- Warnings with specific dates for critical events
- Download CSV export of analysis

### Tab 2: 📦 Size Pattern Optimizer

Standalone cutting pattern optimization tool:
- **Pattern Sets**: Create and manage multiple pattern sets (e.g., "adults", "kids")
- **Size Definitions**: Define which sizes exist in each pattern set (XL, L, M, S, XS, etc.)
- **Cutting Patterns**: Define how sizes can be cut together (e.g., "XL + L", "M + M")
- **Optimization**: Input desired quantities by size, get optimal pattern allocation
- **Constraints**: Minimum order quantities per pattern
- **Results**: Shows which patterns to order, excess production, and coverage status

**Pattern Sets** are stored in `saved_pattern_sets.json` and can be:
- Created, edited, and deleted through the UI
- Reused across different order scenarios
- Associated with specific product models in Tab 3

### Tab 3: 🎯 Order Recommendations

**Most Important Feature**: Automated priority-based ordering system that determines what to order first and how much.

#### How It Works:

1. **Click "Generate Recommendations"**: Analyzes all SKUs considering:
    - Current stock vs ROP (Reorder Point)
    - Forecast demand during lead time
    - Product type urgency (new, seasonal, basic, regular)
    - Revenue at risk (forecast × price)

2. **Priority Scoring Algorithm**:
   ```
   Priority Score = (Stockout Risk × 0.5) + (Revenue Impact × 0.3) + (Demand × 0.2) × Type Multiplier

   Where:
   - Stockout Risk: 100 if stock = 0 with forecast > 0; 0-80 if below ROP (proportional to deficit)
   - Revenue Impact: Normalized forecast revenue (forecast × price)
   - Demand: Forecast quantity during lead time (capped at 100)
   - Type Multiplier: Seasonal=1.3, New=1.2, Regular=1.0, Basic=0.9
   ```

3. **Model-First Grouping**: Results are grouped by **MODEL** (first five chars of SKU), then broken down by **COLOR** (chars 6–7)

4. **Pattern Set Selection**: For each model, select the appropriate pattern set (adults/kids/etc.)

5. **Size Analysis**: For each color, shows ALL sizes from the selected pattern set, including:
    - Sizes that exist in inventory (with the calculated deficit)
    - Sizes that don't exist yet (shown as zero quantity)
    - This ensures complete size runs can be ordered

6. **Pattern Optimization**: Click "🎯 Optimize Cutting Patterns" to:
    - Automatically run the pattern matcher
    - See which cutting patterns to order and how many
    - View production vs. required breakdown
    - Identify excess and coverage gaps

#### Order Recommendations Workflow:

```
1. Load Data (Tab 1) → Ensure stock + forecast data are loaded
2. Go to Tab 3
3. Click "Generate Recommendations" → System calculates priorities
4. Review top priority models (sorted by urgency score)
5. For each model:
   a. Select pattern set (adults/kids)
   b. Review colors within that model
   c. For each color:
      - Review size quantities needed
      - Click "Optimize Cutting Patterns"
      - See optimal pattern allocation
      - Make ordering decision
6. Download full priority report (CSV) for records
```

### Key Design Patterns

**Product Classification System**: Products are classified into four types based on statistical properties:
1. **New**: Products with first sale within the last 12 months (configurable)
2. **Basic**: Low variability (CV < 0.6, configurable)—stable demand
3. **Seasonal**: High variability (CV > 1.0, configurable)—seasonal patterns
4. **Regular**: Everything else - moderate variability

The classification is sequential: new items are classified first, then basic/seasonal, with regular as the fallback.

### Statistical Calculations

**Safety Stock Formula**:
```
SS = Z-score × Standard_Deviation × √(Lead_Time)
```

**Reorder Point Formula**:
```
ROP = (Average_Sales × Lead_Time) + Safety_Stock
```

**Seasonal Detection**: The `determine_seasonal_months()` method calculates a seasonal index by comparing monthly average sales (last 2 years) to overall average. Months with index > 1.2 are considered "in season". Seasonal items use different Z-scores depending on whether the current month is in-season or out-of-season.

**Z-Score Application**: Each product type has a different Z-score representing different service levels. Seasonal items use two Z-scores (in-season and out-of-season), dynamically selected based on the current month.

