from __future__ import annotations

import streamlit as st

from ui.constants import AlgorithmModes, Config, Icons, SessionKeys
from ui.shared.data_loaders import load_size_aliases, load_size_aliases_reverse
from ui.shared.display_helpers import display_optimization_metrics
from ui.shared.session_manager import get_data_source, get_settings
from ui.shared.styles import PATTERN_SECTION_STYLE
from utils.logging_config import get_logger
from utils.pattern_optimizer import (
    Pattern,
    PatternSet,
    get_min_order_per_pattern,
    load_pattern_sets,
    optimize_patterns,
    save_pattern_sets,
)

logger = get_logger("tab_pattern_optimizer")


def render() -> None:
    try:
        _render_content()
    except Exception as e:
        logger.exception("Error in Pattern Optimizer")
        st.error(f"{Icons.ERROR} Error in Pattern Optimizer: {str(e)}")


def _render_content() -> None:
    st.title("Size Pattern Optimizer")

    _initialize_pattern_session_state()

    st.markdown(PATTERN_SECTION_STYLE, unsafe_allow_html=True)

    min_order_per_pattern = get_min_order_per_pattern()
    st.markdown(
        f'<div class="info-box">Minimum order per pattern: {min_order_per_pattern} units</div>',
        unsafe_allow_html=True,
    )

    active_set = _get_active_pattern_set()
    sizes = active_set.size_names if active_set else ["XL", "L", "M", "S", "XS"]

    col1, col2 = st.columns([1, 1])

    with col1:
        quantities, sales_history = _render_quantities_section(sizes, active_set)
        _render_pattern_sets_section()

    with col2:
        _render_optimization_section(quantities, sizes, min_order_per_pattern, sales_history)


def _initialize_pattern_session_state() -> None:
    if SessionKeys.PATTERN_SETS not in st.session_state:
        st.session_state[SessionKeys.PATTERN_SETS] = load_pattern_sets()

    pattern_sets = st.session_state[SessionKeys.PATTERN_SETS]

    if SessionKeys.ACTIVE_SET_ID not in st.session_state:
        st.session_state[SessionKeys.ACTIVE_SET_ID] = pattern_sets[0].id if pattern_sets else None

    if SessionKeys.SHOW_ADD_PATTERN_SET not in st.session_state:
        st.session_state[SessionKeys.SHOW_ADD_PATTERN_SET] = False

    if SessionKeys.EDIT_SET_ID not in st.session_state:
        st.session_state[SessionKeys.EDIT_SET_ID] = None

    if SessionKeys.NUM_PATTERNS not in st.session_state:
        st.session_state[SessionKeys.NUM_PATTERNS] = Config.DEFAULT_NUM_PATTERNS

    if SessionKeys.NUM_SIZES not in st.session_state:
        st.session_state[SessionKeys.NUM_SIZES] = Config.DEFAULT_NUM_SIZES


def _get_active_pattern_set() -> PatternSet | None:
    active_id = st.session_state.get(SessionKeys.ACTIVE_SET_ID)
    if active_id is None:
        return None
    pattern_sets = st.session_state.get(SessionKeys.PATTERN_SETS, [])
    return next((ps for ps in pattern_sets if ps.id == active_id), None)


def _render_quantities_section(sizes: list[str], active_set: PatternSet | None) -> tuple[dict[str, int], dict[str, int]]:
    st.markdown('<div class="section-header">Order Quantities</div>', unsafe_allow_html=True)

    if active_set:
        st.info(f"Using sizes from: {active_set.name}")

    quantities = {}
    num_cols = min(len(sizes), 5)
    cols = st.columns(num_cols)

    for i, size in enumerate(sizes):
        col_idx = i % num_cols
        with cols[col_idx]:
            quantities[size] = st.number_input(size, min_value=0, value=0, step=1, key=f"qty_{size}")

    st.markdown('<div class="section-header">Sales History (last 4 months)</div>', unsafe_allow_html=True)
    st.caption("Enter total sales per size or load automatically. Sizes with < 3 sales will be excluded.")

    sales_history = _render_sales_history_section(sizes, active_set)

    return quantities, sales_history


def _render_sales_history_section(sizes: list[str], active_set: PatternSet | None) -> dict[str, int]:
    col_model, col_load = st.columns([3, 1])

    with col_model:
        model_code = st.text_input(
            "Model", placeholder="e.g., CH031", key="sales_history_model"
        )
    with col_load:
        st.write("")
        st.write("")
        load_clicked = st.button("Load", key="load_sales_history")

    if load_clicked and model_code:
        loaded_history = _load_sales_history_for_model(model_code.upper(), active_set)
        if loaded_history:
            for size in sizes:
                st.session_state[f"sales_{size}"] = loaded_history.get(size, 0)
            st.session_state["loaded_sales_history_message"] = f"Loaded sales history for {model_code.upper()} (all colors)"
            st.rerun()
        else:
            st.warning(f"No sales data found for {model_code.upper()}")

    if st.session_state.get("loaded_sales_history_message"):
        st.success(st.session_state.pop("loaded_sales_history_message"))

    sales_history = {}
    num_cols = min(len(sizes), 5)
    cols = st.columns(num_cols)

    for i, size in enumerate(sizes):
        col_idx = i % num_cols
        with cols[col_idx]:
            sales_history[size] = st.number_input(
                f"{size} sales", min_value=0, value=0, step=1, key=f"sales_{size}"
            )

    return sales_history


def _load_sales_history_for_model(model: str, active_set: PatternSet | None) -> dict[str, int]:
    try:
        data_source = get_data_source()
        monthly_agg = data_source.get_monthly_aggregations()

        if monthly_agg is None or monthly_agg.empty:
            return {}

        size_aliases = _build_size_aliases(active_set)

        history = _calculate_model_size_sales_history(monthly_agg, model, size_aliases, months=4)

        return history
    except Exception as e:
        logger.warning("Failed to load sales history: %s", e)
        return {}


def _calculate_model_size_sales_history(
    monthly_agg, model: str, size_aliases: dict[str, str] | None, months: int = 4
) -> dict[str, int]:
    df = monthly_agg.copy()

    sku_col = _find_column(df, ["sku", "SKU", "entity_id"])
    if sku_col is None:
        return {}

    df["_model"] = df[sku_col].astype(str).str[:5]
    df["_size"] = df[sku_col].astype(str).str[7:9]

    filtered = df[df["_model"] == model]
    if filtered.empty:
        return {}

    month_col = _find_column(filtered, ["year_month", "month", "MONTH"])
    qty_col = _find_column(filtered, ["total_quantity", "TOTAL_QUANTITY", "ilosc"])

    if month_col is None or qty_col is None:
        return {}

    sorted_months = sorted(filtered[month_col].unique(), reverse=True)[:months]
    recent = filtered[filtered[month_col].isin(sorted_months)]

    size_sales = recent.groupby("_size")[qty_col].sum().to_dict()

    if size_aliases:
        aliased = {}
        for size_code, sales in size_sales.items():
            alias = size_aliases.get(str(size_code), str(size_code))
            aliased[alias] = aliased.get(alias, 0) + int(sales)
        return aliased

    return {str(k): int(v) for k, v in size_sales.items()}


def _find_column(df, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _build_size_aliases(active_set: PatternSet | None) -> dict[str, str]:
    if not active_set:
        return {}

    try:
        all_aliases = load_size_aliases()

        if not all_aliases:
            return {}

        reverse_aliases = load_size_aliases_reverse()
        size_aliases = {}

        for size_name in active_set.size_names:
            if size_name in reverse_aliases:
                size_code = reverse_aliases[size_name]
                size_aliases[size_code] = size_name

        return size_aliases
    except Exception as e:
        logger.warning("Failed to build size aliases: %s", e)
        return {}


@st.fragment
def _render_pattern_sets_section() -> None:
    st.markdown('<div class="section-header">Pattern Sets</div>', unsafe_allow_html=True)

    _render_pattern_set_buttons()

    pattern_sets = st.session_state.get(SessionKeys.PATTERN_SETS, [])

    if pattern_sets:
        active_set = _render_pattern_set_selector(pattern_sets)
        if active_set:
            _render_active_set_details(active_set)
    else:
        st.info("No pattern sets defined. Create a pattern set to get started!")

    if st.session_state.get(SessionKeys.SHOW_ADD_PATTERN_SET):
        _render_pattern_editor()


def _render_pattern_set_buttons() -> None:
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("New Set", key="new_set_btn"):
            st.session_state[SessionKeys.SHOW_ADD_PATTERN_SET] = True
            st.session_state[SessionKeys.EDIT_SET_ID] = None
            st.session_state[SessionKeys.NUM_PATTERNS] = Config.DEFAULT_NUM_PATTERNS
            st.session_state[SessionKeys.NUM_SIZES] = Config.DEFAULT_NUM_SIZES
    with btn_col2:
        if st.button("Save All", key="save_all_btn"):
            save_pattern_sets(st.session_state[SessionKeys.PATTERN_SETS])
            st.success("Pattern sets saved!")
    with btn_col3:
        if st.button("Reload", key="reload_btn"):
            st.session_state[SessionKeys.PATTERN_SETS] = load_pattern_sets()
            pattern_sets = st.session_state[SessionKeys.PATTERN_SETS]
            st.session_state[SessionKeys.ACTIVE_SET_ID] = pattern_sets[0].id if pattern_sets else None
            st.rerun()


def _render_pattern_set_selector(pattern_sets: list[PatternSet]) -> PatternSet | None:
    set_options = {ps.name: ps.id for ps in pattern_sets}

    current_index = 0
    active_id = st.session_state.get(SessionKeys.ACTIVE_SET_ID)
    if active_id:
        for idx, (name, ps_id) in enumerate(set_options.items()):
            if ps_id == active_id:
                current_index = idx
                break

    selected_set_name = st.selectbox(
        "Select Active Pattern Set:",
        options=list(set_options.keys()),
        index=current_index,
        key="pattern_set_selector",
    )

    new_active_id = set_options[selected_set_name]
    if new_active_id != st.session_state.get(SessionKeys.ACTIVE_SET_ID):
        st.session_state[SessionKeys.ACTIVE_SET_ID] = new_active_id
        st.rerun()

    return next((ps for ps in pattern_sets if ps.id == new_active_id), None)


def _render_active_set_details(active_set: PatternSet) -> None:
    st.write(f"**{active_set.name}**")
    st.write(f"Sizes: {', '.join(active_set.size_names)}")
    st.write(f"Patterns: {len(active_set.patterns)}")

    for pattern in active_set.patterns:
        sizes_str = " + ".join([f"{count} × {size}" for size, count in pattern.sizes.items()])
        st.markdown(f"  • **{pattern.name}** : *{sizes_str}*")

    btn_edit, btn_delete = st.columns(2)
    with btn_edit:
        if st.button("Edit Set", key="edit_set"):
            st.session_state[SessionKeys.SHOW_ADD_PATTERN_SET] = True
            st.session_state[SessionKeys.EDIT_SET_ID] = st.session_state[SessionKeys.ACTIVE_SET_ID]
            st.session_state[SessionKeys.NUM_PATTERNS] = len(active_set.patterns)
            st.session_state[SessionKeys.NUM_SIZES] = len(active_set.size_names)
            st.rerun()
    with btn_delete:
        if st.button("Delete Set", key="delete_set"):
            st.session_state[SessionKeys.PATTERN_SETS] = [
                ps for ps in st.session_state[SessionKeys.PATTERN_SETS]
                if ps.id != st.session_state[SessionKeys.ACTIVE_SET_ID]
            ]
            remaining = st.session_state[SessionKeys.PATTERN_SETS]
            st.session_state[SessionKeys.ACTIVE_SET_ID] = remaining[0].id if remaining else None
            st.rerun()


def _render_pattern_editor() -> None:
    editing_set = None
    edit_id = st.session_state.get(SessionKeys.EDIT_SET_ID)
    if edit_id:
        editing_set = next(
            (ps for ps in st.session_state[SessionKeys.PATTERN_SETS] if ps.id == edit_id), None
        )

    st.markdown("---")
    st.subheader("Create/Edit Pattern Set")

    set_name = st.text_input(
        "Set Name",
        placeholder="e.g., Kids Collection",
        value=editing_set.name if editing_set else "",
        key="set_name_input",
    )

    size_names = _render_size_inputs(editing_set)
    patterns = _render_pattern_inputs(editing_set, size_names)

    _render_editor_buttons(set_name, size_names, patterns, editing_set)


def _render_size_inputs(editing_set: PatternSet | None) -> list[str]:
    num_sizes = st.number_input(
        "Number of size categories",
        min_value=1,
        max_value=20,
        value=len(editing_set.size_names) if editing_set else st.session_state[SessionKeys.NUM_SIZES],
        step=1,
        key="num_sizes_input",
    )

    if num_sizes != st.session_state[SessionKeys.NUM_SIZES]:
        st.session_state[SessionKeys.NUM_SIZES] = int(num_sizes)
        st.rerun()

    st.write("**Define size categories:**")
    size_names = []
    size_cols = st.columns(min(int(num_sizes), 5))

    for i in range(int(num_sizes)):
        col_idx = i % len(size_cols)
        with size_cols[col_idx]:
            default_name = (
                editing_set.size_names[i]
                if editing_set and i < len(editing_set.size_names)
                else f"size_{i + 1}"
            )
            size_name = st.text_input(f"Size {i + 1}", value=default_name, key=f"size_name_{i}")
            if size_name:
                size_names.append(size_name)

    return size_names


def _get_num_patterns_value(editing_set: PatternSet | None) -> int:
    if editing_set:
        return len(editing_set.patterns)
    return st.session_state[SessionKeys.NUM_PATTERNS]


def _get_existing_pattern(editing_set: PatternSet | None, index: int) -> Pattern | None:
    if editing_set and index < len(editing_set.patterns):
        return editing_set.patterns[index]
    return None


def _build_placeholder_text(size_names: list[str]) -> str:
    first = size_names[0] if size_names else "Size1"
    second = size_names[1] if len(size_names) > 1 else "Size2"
    return f"e.g., {first} + {second}"


def _render_size_quantity_inputs(
    pattern_index: int, size_names: list[str], existing_pattern: Pattern | None
) -> dict[str, int]:
    pattern_sizes = {}
    p_cols = st.columns(min(len(size_names), 5)) if size_names else st.columns(1)

    for j, size in enumerate(size_names):
        col_idx = j % len(p_cols)
        with p_cols[col_idx]:
            default_val = existing_pattern.sizes.get(size, 0) if existing_pattern else 0
            qty = st.number_input(
                size,
                min_value=0,
                value=default_val,
                key=f"p{pattern_index}_{size}",
                label_visibility="visible",
            )
            if qty > 0:
                pattern_sizes[size] = qty
    return pattern_sizes


def _render_single_pattern(
    index: int, size_names: list[str], editing_set: PatternSet | None
) -> Pattern | None:
    existing_pattern = _get_existing_pattern(editing_set, index)
    pattern_name = st.text_input(
        "Pattern Name",
        placeholder=_build_placeholder_text(size_names),
        key=f"pname_{index}",
        value=existing_pattern.name if existing_pattern else "",
    )

    st.write("Quantities per size:")
    pattern_sizes = _render_size_quantity_inputs(index, size_names, existing_pattern)

    if pattern_name and pattern_sizes:
        return Pattern(index + 1, pattern_name, pattern_sizes)
    return None


def _render_pattern_inputs(editing_set: PatternSet | None, size_names: list[str]) -> list[Pattern]:
    num_patterns = st.number_input(
        "Number of patterns in this set",
        min_value=1,
        max_value=20,
        value=_get_num_patterns_value(editing_set),
        step=1,
        key="num_patterns_input",
    )

    if num_patterns != st.session_state[SessionKeys.NUM_PATTERNS]:
        st.session_state[SessionKeys.NUM_PATTERNS] = int(num_patterns)
        st.rerun()

    patterns = []
    for i in range(int(num_patterns)):
        with st.expander(f"Pattern {i + 1}", expanded=(i < 3)):
            pattern = _render_single_pattern(i, size_names, editing_set)
            if pattern:
                patterns.append(pattern)

    return patterns


def _render_editor_buttons(
        set_name: str, size_names: list[str], patterns: list[Pattern], editing_set: PatternSet | None
) -> None:
    num_sizes = st.session_state[SessionKeys.NUM_SIZES]
    num_patterns = st.session_state[SessionKeys.NUM_PATTERNS]

    col_submit, col_cancel = st.columns(2)
    with col_submit:
        if st.button("Save Pattern Set", key="submit_set"):
            if set_name and len(size_names) == num_sizes and len(patterns) == num_patterns:
                if editing_set:
                    editing_set.name = set_name
                    editing_set.size_names = size_names
                    editing_set.patterns = patterns
                else:
                    new_id = max([ps.id for ps in st.session_state[SessionKeys.PATTERN_SETS]], default=0) + 1
                    st.session_state[SessionKeys.PATTERN_SETS].append(
                        PatternSet(new_id, set_name, size_names, patterns)
                    )
                    st.session_state[SessionKeys.ACTIVE_SET_ID] = new_id

                st.session_state[SessionKeys.SHOW_ADD_PATTERN_SET] = False
                st.session_state[SessionKeys.EDIT_SET_ID] = None
                st.rerun()
            else:
                st.error(
                    f"Please complete all fields: set name, {int(num_sizes)} size names, and {int(num_patterns)} patterns!"
                )

    with col_cancel:
        if st.button("Cancel", key="cancel_set"):
            st.session_state[SessionKeys.SHOW_ADD_PATTERN_SET] = False
            st.session_state[SessionKeys.EDIT_SET_ID] = None
            st.rerun()


def _render_optimization_section(
    quantities: dict[str, int],
    sizes: list[str],
    min_order_per_pattern: int,
    sales_history: dict[str, int],
) -> None:
    st.markdown('<div class="section-header">Optimization</div>', unsafe_allow_html=True)

    settings = get_settings()
    current_algorithm = settings.get("optimizer", {}).get("algorithm_mode", "greedy_overshoot")
    algorithm_display = (
        AlgorithmModes.GREEDY_OVERSHOOT if current_algorithm == "greedy_overshoot" else AlgorithmModes.CLASSIC_GREEDY
    )
    st.info(f"Using algorithm: **{algorithm_display}** (change in sidebar)")

    if st.button("Run Optimization", type="primary", key="run_optimization"):
        _run_optimization(quantities, sizes, min_order_per_pattern, current_algorithm, sales_history)


def _run_optimization(
    quantities: dict[str, int],
    sizes: list[str],
    min_order_per_pattern: int,
    algorithm: str,
    sales_history: dict[str, int],
) -> None:
    pattern_sets = st.session_state.get(SessionKeys.PATTERN_SETS, [])
    active_id = st.session_state.get(SessionKeys.ACTIVE_SET_ID)

    if not pattern_sets:
        st.error("Please add at least one pattern set before optimizing!")
        return

    if active_id is None:
        st.error("Please select an active pattern set!")
        return

    if not any(quantities.values()):
        st.warning("Please enter quantities to optimize!")
        return

    active_set = next((ps for ps in pattern_sets if ps.id == active_id), None)

    if not active_set:
        st.error("Active pattern set not found!")
        return

    size_sales = sales_history if any(sales_history.values()) else None

    result = optimize_patterns(
        quantities,
        active_set.patterns,
        min_order_per_pattern,
        algorithm,
        size_sales_history=size_sales,
    )

    display_optimization_metrics(result)
    _display_optimization_results(result, active_set, quantities, sizes, min_order_per_pattern)


def _display_optimization_results(
        result: dict, active_set: PatternSet, quantities: dict[str, int], sizes: list[str], min_order_per_pattern: int
) -> None:
    excluded_sizes = result.get("excluded_sizes", [])
    if excluded_sizes:
        st.warning(f"Excluded sizes (sales < 3 in last 4 months): {', '.join(excluded_sizes)}")

    has_violations = len(result["min_order_violations"]) > 0

    if result["all_covered"] and not has_violations:
        st.markdown(
            '<div class="success-box">All requirements covered and minimum orders met!</div>',
            unsafe_allow_html=True,
        )
    elif has_violations:
        violation_text = ", ".join([f"{name} ({count})" for name, count in result["min_order_violations"]])
        st.markdown(
            f'<div class="warning-box">Minimum order violations (need {min_order_per_pattern} per pattern): {violation_text}</div>',
            unsafe_allow_html=True,
        )
    elif not result["all_covered"]:
        st.markdown(
            '<div class="warning-box">Some requirements not covered</div>',
            unsafe_allow_html=True,
        )

    _display_pattern_allocation(result, active_set, min_order_per_pattern)
    _display_production_comparison(result, quantities, sizes, excluded_sizes)


def _display_pattern_allocation(result: dict, active_set: PatternSet, min_order_per_pattern: int) -> None:
    st.markdown("### Pattern Allocation")
    allocation_data = []

    for pattern in active_set.patterns:
        count = result["allocation"].get(pattern.id, 0)
        if count > 0:
            sizes_str = " + ".join([f"{c}×{s}" for s, c in pattern.sizes.items()])
            status = Icons.WARNING if count < min_order_per_pattern else Icons.SUCCESS
            allocation_data.append({
                "Pattern": pattern.name,
                "Count": count,
                "Composition": sizes_str,
                "Status": status,
            })

    if allocation_data:
        st.dataframe(allocation_data, hide_index=True)
    else:
        st.info("No patterns allocated")


def _display_production_comparison(
    result: dict, quantities: dict[str, int], sizes: list[str], excluded_sizes: list[str] | None = None
) -> None:
    st.markdown("### Production vs Required")
    production_data = []
    excluded_sizes = excluded_sizes or []

    for size in sizes:
        if size in excluded_sizes:
            production_data.append({
                "Size": size,
                "Required": quantities[size],
                "Produced": 0,
                "Excess": "-",
                "Status": "⛔ excluded",
            })
        else:
            produced = result["produced"].get(size, 0)
            required = quantities[size]
            excess = result["excess"].get(size, 0)
            status = Icons.SUCCESS if produced >= required else Icons.ERROR
            production_data.append({
                "Size": size,
                "Required": required,
                "Produced": produced,
                "Excess": f"{excess:+d}",
                "Status": status,
            })

    active_sizes = [s for s in sizes if s not in excluded_sizes]
    total_required = sum(quantities[size] for size in active_sizes)
    total_produced = sum(result["produced"].get(size, 0) for size in active_sizes)
    total_excess = sum(result["excess"].get(size, 0) for size in active_sizes)
    production_data.append({
        "Size": "**TOTAL**",
        "Required": total_required,
        "Produced": total_produced,
        "Excess": f"{total_excess:+d}",
        "Status": "",
    })

    st.dataframe(production_data, hide_index=True)
