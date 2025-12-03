from typing import Dict

import pandas as pd


def load_size_aliases_from_excel(sizes_file_path) -> Dict[str, str]:
    df = pd.read_excel(sizes_file_path)
    df = df[["size", "metric"]].copy()
    df.columns = ["size_code", "size_alias"]
    df["size_code"] = df["size_code"].astype(str).str.zfill(2)
    df["size_alias"] = df["size_alias"].astype(str)
    return dict(zip(df["size_code"], df["size_alias"]))
