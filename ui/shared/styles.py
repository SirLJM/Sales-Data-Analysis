from __future__ import annotations

from typing import Final

SIDEBAR_STYLE: Final[str] = """
<style>
[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 380px;
    max-width: 380px;
}
@media (max-width: 1200px) {
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 300px;
        max-width: 300px;
    }
}
@media (max-width: 768px) {
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 250px;
        max-width: 250px;
    }
}
</style>
"""

DATAFRAME_STYLE: Final[str] = """
<style>
.main .block-container {
    max-width: 95% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
@media (max-width: 768px) {
    .main .block-container {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
}
</style>
"""

SCROLLABLE_DATAFRAME_STYLE: Final[str] = """
<style>
.scrollable-df-wrapper {
    width: 100%;
    overflow-x: auto;
    overflow-y: hidden;
}
.scrollable-df-wrapper::-webkit-scrollbar {
    height: 10px;
}
.scrollable-df-wrapper::-webkit-scrollbar-track {
    background: rgba(128,128,128,0.1);
    border-radius: 5px;
}
.scrollable-df-wrapper::-webkit-scrollbar-thumb {
    background: rgba(128,128,128,0.4);
    border-radius: 5px;
}
.scrollable-df-wrapper::-webkit-scrollbar-thumb:hover {
    background: rgba(128,128,128,0.6);
}
</style>
"""

PATTERN_SECTION_STYLE: Final[str] = """
<style>
.section-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #2c3e50;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.5rem;
}
.success-box {
    border-left: 4px solid #28a745;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
.warning-box {
    border-left: 4px solid #ffc107;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
.info-box {
    border-left: 4px solid #17a2b8;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
</style>
"""

ROTATED_TABLE_STYLE: Final[str] = """
<style>
.rotated-table { overflow-x: auto; }
.rotated-table table { border-collapse: collapse; font-size: 12px; }
.rotated-table th, .rotated-table td {
    border: 1px solid var(--border-color, #ddd);
    padding: 8px;
    text-align: center;
}
.rotated-table th:not(:first-child) {
    writing-mode: vertical-rl;
    text-orientation: mixed;
    white-space: nowrap;
    min-height: 150px;
}
</style>
"""

INPUT_FIELD_STYLE: Final[str] = """
<style>
/* Limit input field widths for compact UI */
[data-testid="stTextInput"] {
    max-width: 200px !important;
}
[data-testid="stNumberInput"] {
    max-width: 150px !important;
}
[data-testid="stSelectbox"] {
    max-width: 250px !important;
}
</style>
"""

RESPONSIVE_TABS_STYLE: Final[str] = """
<style>
/* Tabs root container */
[data-testid="stTabs"] {
    width: 100% !important;
}

/* Tab list container - the div with role="tablist" */
[data-testid="stTabs"] [role="tablist"] {
    overflow-x: auto !important;
    overflow-y: hidden !important;
    flex-wrap: nowrap !important;
    scrollbar-width: thin;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 10px;
    margin-bottom: -2px;
    width: 100% !important;
    display: flex !important;
}

/* Webkit scrollbar styling */
[data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar {
    height: 8px;
}
[data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar-track {
    background: rgba(128,128,128,0.2);
    border-radius: 4px;
}
[data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar-thumb {
    background: rgba(128,128,128,0.5);
    border-radius: 4px;
}
[data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar-thumb:hover {
    background: rgba(128,128,128,0.7);
}

/* Tab buttons - prevent shrinking and wrapping */
[data-testid="stTabs"] button[role="tab"] {
    flex-shrink: 0 !important;
    white-space: nowrap !important;
}

/* General responsive columns */
@media (max-width: 768px) {
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
}

/* Responsive metrics */
@media (max-width: 1200px) {
    [data-testid="stMetric"] {
        padding: 0.5rem !important;
    }
    [data-testid="stMetric"] label {
        font-size: 0.8rem !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
}

/* Responsive expanders */
@media (max-width: 768px) {
    [data-testid="stExpander"] {
        margin-left: 0 !important;
        margin-right: 0 !important;
    }
}

</style>
"""
