# Settings Management System

## Overview

The application now uses a centralized `settings.json` file to store and persist all configurable parameters. This
allows you to:

- Save custom parameter configurations
- Share settings across team members
- Reset to default values easily
- Maintain consistent calculations across app sessions

## Settings File Location

The settings file is located at:

```
src/settings.json
```

The settings manager module is located at:

```
src/utils/settings_manager.py
```

## Settings Structure

The `settings.json` file contains the following parameters:

```json
{
  "lead_time": 1.36,
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
    "min_order_per_pattern": 5
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

## Parameter Descriptions

### Lead Time

- **Key**: `lead_time`
- **Type**: float
- **Description**: Time in months between order placement and receipt
- **Default**: 1.36
- **Used in**: Safety Stock and ROP calculations

### CV Thresholds

Classification thresholds for product types based on Coefficient of Variation:

- **basic**: Maximum CV for "basic" products (low variability)
    - Default: 0.6
- **seasonal**: Minimum CV for "seasonal" products (high variability)
    - Default: 1.0
- Products with CV between these values are classified as "regular"

### Z-Scores

Service level multipliers for Safety Stock calculations:

- **basic**: Z-score for basic products
    - Default: 2.05 (~98% service level)
- **regular**: Z-score for regular products
    - Default: 1.645 (~95% service level)
- **seasonal_in**: Z-score for seasonal products during peak season
    - Default: 1.75 (~96% service level)
- **seasonal_out**: Z-score for seasonal products off-season
    - Default: 1.6 (~95% service level)
- **new**: Z-score for new products (< threshold months)
    - Default: 1.8 (~96% service level)

### New Product Threshold

- **Key**: `new_product_threshold_months`
- **Type**: integer
- **Description**: Number of months since first sale to classify as "new"
- **Default**: 12

### Optimizer Settings

Pattern optimization parameters:

- **min_order_per_pattern**: Minimum quantity required per cutting pattern
    - Default: 5
    - **Used in**: Tab 2 (Pattern Optimizer)

### Order Recommendations Settings

Advanced parameters for the priority calculation algorithm in Tab 3:

#### Stockout Risk

Controls how aggressively to penalize low/zero stock situations:

- **zero_stock_penalty**: Risk score for SKUs with zero stock and forecast demand
    - Default: 100 (maximum penalty)
    - Range: 0-100+
    - Higher values = more urgency for out-of-stock items

- **below_rop_max_penalty**: Maximum risk score for SKUs below ROP
    - Default: 80
    - Range: 0-100
    - Actual penalty scales proportionally to how far below ROP

#### Priority Weights

Adjusts the relative importance of different factors in the priority score calculation:

- **stockout_risk**: Weight for the stockout risk factor
    - Default: 0.5 (50% of score)

- **revenue_impact**: Weight for the revenue impact factor
    - Default: 0.3 (30% of score)

- **demand_forecast**: Weight for the demand forecast factor
    - Default: 0.2 (20% of score)

**Note**: Weights should sum to 1.0 for balanced scoring but can be adjusted for emphasis.

**Priority Score Formula**:

```
Priority Score = (
    (Stockout Risk × weight_stockout) +
    (Revenue Impact × weight_revenue) +
    (Demand Forecast × weight_demand)
) × Type Multiplier
```

#### Type Multipliers

Adjusts priority based on product classification:

- **new**: Multiplier for new products (< threshold months)
    - Default: 1.2 (20% boost)

- **seasonal**: Multiplier for seasonal products (high CV)
    - Default: 1.3 (30% boost)

- **regular**: Multiplier for regular products (moderate CV)
    - Default: 1.0 (no adjustment)

- **basic**: Multiplier for basic products (low CV, stable demand)
    - Default: 0.9 (10% reduction)

Higher multipliers = higher priority for that product type.

#### Demand Cap

- **demand_cap**: Maximum forecast demand value used in priority calculation
    - Default: 100
    - Prevents extremely high forecast values from dominating the score
    - Forecast values are clipped to this maximum before weighting

## Using Settings in the UI

### Tab 1: Sidebar Controls

At the top of the sidebar in Tab 1, you'll find two buttons:

1. **💾 Save**: Saves current parameter values to `settings.json`
    - All sidebar parameters are automatically synced to the session state
    - Click "Save" to persist them to disk
    - Settings will be loaded automatically on the next app start

2. **🔄 Reset**: Resets all parameters to default values
    - Overwrites `settings.json` with defaults from `settings_manager.py`
    - Immediately reloads the app with default values

### Modifying Parameters

Adjust any parameter in the sidebar:

- Lead time slider
- CV threshold inputs
- Z-score inputs
- New product threshold

Changes are immediately reflected in calculations. Click **💾 Save** to persist them.

### Tab 3: Order Recommendations Parameters

In Tab 3, you can adjust all order recommendation parameters through an interactive UI:

1. **Access Controls**: Expand the "⚙ Recommendation Parameters" section
2. **Parameter Groups**:
    - **Priority Weights** (three sliders): Control the contribution of each factor to the final priority score
        - Stockout Risk (0.0–1.0)
        - Revenue Impact (0.0-1.0)
        - Demand Forecast (0.0–1.0)
        - Shows sum indicator (should ideally equal 1.0)
    - **Type Multipliers** (four sliders): Adjust priority boost by product type
        - New Products (0.5–2.0)
        - Seasonal (0.5-2.0)
        - Regular (0.5-2.0)
        - Basic (0.5-2.0)
    - **Stockout Risk & Other** (three sliders): Fine-tune urgency penalties
        - Zero Stock Penalty (50-150)
        - Below ROP Max Penalty (40-100)
        - Demand Cap (50-300)

3. **Help Tooltips**: Every slider has a help icon (ℹ️) with detailed explanation
4. **Live Updates**: Changes apply immediately when you click "Generate Recommendations"
5. **Persistence**: Click **💾 Save** in Tab 1 sidebar to persist changes to `settings.json`

This UI approach is recommended over editing `settings.json` directly, as it provides:

- Immediate visual feedback
- Input validation (min/max ranges)
- Contextual help for each parameter
- No risk of JSON syntax errors

## Tuning Order Recommendations

The order recommendations system can be tuned based on your business priorities:

### Scenario: Prioritize Stockouts Over Revenue

If preventing stockouts is more important than revenue optimization:

```json
"priority_weights": {
"stockout_risk": 0.7, // Increase from 0.5
"revenue_impact": 0.2, // Decrease from 0.3
"demand_forecast": 0.1    // Decrease from 0.2
}
```

### Scenario: Prioritize High-Value Items

To focus on revenue-generating products:

```json
"priority_weights": {
"stockout_risk": 0.3,
"revenue_impact": 0.5, // Increase
"demand_forecast": 0.2
}
```

### Scenario: Boost Seasonal Products During Peak Season

Increase urgency for seasonal items:

```json
"type_multipliers": {
"seasonal": 1.5, // Increase from 1.3
"new": 1.2,
"regular": 1.0,
"basic": 0.9
}
```

### Scenario: More Aggressive Stockout Penalties

Make the system react more strongly to low stock:

```json
"stockout_risk": {
"zero_stock_penalty": 120, // Increase from 100
"below_rop_max_penalty": 95 // Increase from 80
}
```

### Scenario: Handle High-Volume Products

Increase demand cap for high-volume operations:

```json
"demand_cap": 200  // Increase from 100
```

### Testing Your Changes

After modifying `order_recommendations` settings:

**Option 1: Using UI Sliders (Recommended)**

1. Go to Tab 3 (Order Recommendations)
2. Expand "⚙️ Recommendation Parameters"
3. Adjust any sliders to tune the algorithm (each has helpful tooltips)
4. Click "Generate Recommendations"
5. Review the new priority scores and rankings in the compact table
6. Compare with previous results to validate changes
7. Click **💾 Save** in the Tab 1 sidebar to persist changes

**Option 2: Edit Settings File Directly**

1. Edit `settings.json` directly or through code
2. Go to Tab 3 (Order Recommendations)
3. Click "Generate Recommendations"
4. Review the new priority scores and rankings
5. Click **💾 Save** in the Tab 1 sidebar to persist changes

## Future Enhancements

Potential improvements to the settings system:

- [ ] Settings presets (e.g., "Conservative", "Aggressive", "Seasonal")
- [ ] Import/export settings from UI
- [ ] Settings history/versioning
- [ ] Per-user settings with profiles
- [ ] Settings validation with min/max ranges
- [x] Settings documentation tooltips in UI (implemented in Tab 3)
