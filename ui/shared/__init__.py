from __future__ import annotations

from ui.shared.data_loaders import (
    load_category_mappings,
    load_color_aliases,
    load_data,
    load_forecast,
    load_model_metadata,
    load_size_aliases,
    load_size_aliases_reverse,
    load_stock,
)
from ui.shared.display_helpers import (
    create_download_button,
    display_error,
    display_info,
    display_metrics_row,
    display_optimization_metrics,
    display_star_product,
    display_success,
    display_warning,
    format_number,
)
from ui.shared.session_manager import (
    get_active_pattern_set,
    get_data_source,
    get_pattern_sets,
    get_session_value,
    get_settings,
    initialize_session_state,
    set_session_value,
)
from ui.shared.sku_utils import (
    add_sku_components,
    extract_color,
    extract_model,
    extract_size,
    parse_sku,
)
from ui.shared.styles import (
    DATAFRAME_STYLE,
    PATTERN_SECTION_STYLE,
    ROTATED_TABLE_STYLE,
    SIDEBAR_STYLE,
)
