from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from utils.logging_config import get_logger
from utils.parallel_loader import parallel_load

from .dtype_optimizer import optimize_dtypes
from .loader import SalesDataLoader

logger = get_logger("stock_history_cache")

_CACHE_COLUMNS = ["sku", "snapshot_date", "available_stock"]


class StockHistoryCache:
    def __init__(self, cache_path: Path, loader: SalesDataLoader) -> None:
        self.cache_path = cache_path
        self.loader = loader

    def get_history(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pd.DataFrame:
        self._sync()

        if not self.cache_path.exists():
            return pd.DataFrame(columns=pd.Index(_CACHE_COLUMNS))

        df = pd.read_parquet(self.cache_path)

        if start_date is not None:
            df = pd.DataFrame(df[df["snapshot_date"] >= start_date])
        if end_date is not None:
            df = pd.DataFrame(df[df["snapshot_date"] <= end_date])

        df = df.reset_index(drop=True)
        return optimize_dtypes(df)

    def _sync(self) -> None:
        stock_files = self.loader.find_stock_files()
        if not stock_files:
            return

        cached_dates = self._read_cached_dates()
        missing = [(path, d) for path, d in stock_files if d.date() not in cached_dates]

        if not missing:
            return

        logger.info("Stock history cache: %d new snapshot(s) to load", len(missing))

        new_frames = parallel_load(
            missing, self._load_snapshot, desc="Building stock history cache"
        )
        if not new_frames:
            return

        new_df = pd.concat(new_frames, ignore_index=True)

        if self.cache_path.exists():
            existing = pd.read_parquet(self.cache_path)
            combined_raw = pd.concat([existing, new_df], ignore_index=True)
            combined = pd.DataFrame(
                combined_raw.drop_duplicates(subset=["sku", "snapshot_date"], keep="last")
            )
        else:
            combined = new_df

        combined = combined.sort_values("snapshot_date").reset_index(drop=True)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_parquet(self.cache_path, compression="snappy", index=False)
        logger.info(
            "Stock history cache updated: %d rows across %d snapshot(s)",
            len(combined),
            combined["snapshot_date"].nunique(),
        )

    def _read_cached_dates(self) -> set[date]:
        if not self.cache_path.exists():
            return set()
        df = pd.read_parquet(self.cache_path, columns=["snapshot_date"])
        return set(pd.to_datetime(df["snapshot_date"]).dt.date.unique())

    def _load_snapshot(self, file_info: tuple[Path, datetime]) -> pd.DataFrame | None:
        file_path, snapshot_date = file_info
        try:
            df = self.loader.load_stock_file(file_path)
            df["snapshot_date"] = pd.Timestamp(snapshot_date)
            return pd.DataFrame(df[_CACHE_COLUMNS].copy())
        except Exception as e:
            logger.warning("Failed to load stock file %s: %s", file_path, e)
            return None
