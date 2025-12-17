from __future__ import annotations

from typing import Final

SIDEBAR_STYLE: Final[str] = """
<style>
[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 380px;
    max-width: 380px;
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
section[data-testid="stDataFrame"] {
    width: 100% !important;
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
