# utils/_query_with_csv.py

import time
import re
import duckdb
import pandas as pd
from pathlib import Path
from ._connection_functions import connect_to_db


class PandasDFCreator:
    """Generate DataFrames from DuckDB based on a mapping_db_views.csv"""

    def __init__(self, db_source: str, mapping_csv: str, is_url: bool = False, use_cache: bool = True):
        self.db_source = db_source
        self.mapping_csv_path = Path(mapping_csv)
        if not self.mapping_csv_path.exists():
            raise FileNotFoundError(f"Mapping CSV not found: {self.mapping_csv_path}")

        self.filter_cols = [
            "model", "scen", "sector", "subsector", "service", "techgroup", "comgroup",
            "topic", "attr", "prc", "com", "all_ts", "regfrom", "regto", "year"
        ]
        self.is_url = is_url
        self.use_cache = use_cache

    def load_mapping_data(self):
        df = pd.read_csv(self.mapping_csv_path)
        df.replace("", pd.NA, inplace=True)
        return df

    def build_filter_conditions(self, row: pd.Series) -> list:
        conditions = []
        for col in self.filter_cols:
            val = row.get(col)
            if pd.notna(val):
                val_str = str(val)
                if val_str.startswith("^") or any(x in val_str for x in ["(", "|", ")", ".*", "$", "[", "]", "?"]):
                    patterns = [p.strip() for p in val_str.split(",") if p.strip()]
                    sub_conditions = []
                    for pattern in patterns:
                        safe_pattern = pattern.replace("'", "''")
                        neg_lookahead_match = re.match(r"^(.*)\(\?!\.\*(.+?)\)\.\*(.*)$", safe_pattern)
                        if neg_lookahead_match:
                            before = neg_lookahead_match.group(1)
                            excludes = neg_lookahead_match.group(2).split("|")
                            after = neg_lookahead_match.group(3)
                            safe_pattern2 = before + ".*" + after
                            exclude_clauses = [f"tr.{col} NOT LIKE '%{exc}%'" for exc in excludes]
                            sub_conditions.append(
                                f"(REGEXP_MATCHES(tr.{col}, '{safe_pattern2}') AND {' AND '.join(exclude_clauses)})"
                            )
                        else:
                            sub_conditions.append(f"REGEXP_MATCHES(tr.{col}, '{safe_pattern}')")
                    if sub_conditions:
                        conditions.append(f"({' OR '.join(sub_conditions)})")
                elif col == "year":
                    conditions.append(f"tr.year = {int(val)}")
                else:
                    values = [v.strip() for v in val_str.split(",") if v.strip()]
                    sub_conds = []
                    for v in values:
                        if v.endswith("*"):
                            # Wildcard match
                            v_pattern = v[:-1]  # remove '*'
                            sub_conds.append(f"tr.{col} LIKE '{v_pattern}%'")
                        else:
                            # Exact match
                            sub_conds.append(f"tr.{col} = '{v}'")
                    if len(sub_conds) > 1:
                        conditions.append(f"({' OR '.join(sub_conds)})")
                    else:
                        conditions.append(sub_conds[0]) # single condition
                        return conditions

    def get_label_expression(self, row: pd.Series, table_name: str) -> str:
        label_col = str(row.get("label")).strip().lower() if pd.notna(row.get("label")) else None
        if label_col == "table":
            return f"'{table_name}'"
        label_mapping = {
            'scen': "tr.scen",
            'sector': "tr.sector",
            'subsector': "tr.subsector",
            'service': "tr.service",
            'techgroup': "tr.techgroup",
            'comgroup': "tr.comgroup",
            'topic': "tr.topic",
            'attr': "tr.attr",
            'prc': "tr.prc",
            'com': 'tr."com"',
            'all_ts': "tr.all_ts",
            'regfrom': "tr.regfrom",
            'regto': "tr.regto",
            'year': "CAST(tr.year AS TEXT)",
            'vntg': "tr.vntg",
            'unit': "tr.unit",
            'cur': "tr.cur"
        }
        return label_mapping.get(label_col, "NULL")

    def create_dataframe_for_table(self, con: duckdb.DuckDBPyConnection, table_name: str, group_df: pd.DataFrame) -> pd.DataFrame:
        """Run SQL for a single mapping table and return as DataFrame"""
        dfs = []
        for _, row in group_df.iterrows():
            conditions = self.build_filter_conditions(row)
            label_expr = self.get_label_expression(row, table_name)
            sql = f"SELECT tr.*, {label_expr} AS label FROM timesreport_facts tr"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            df = con.sql(sql).df()
            dfs.append(df)
        if dfs:
            return pd.concat(dfs, ignore_index=True)
        else:
            return pd.DataFrame()  # empty DF if no data matched

    def create_all_dataframes(self, con: duckdb.DuckDBPyConnection, map_df: pd.DataFrame) -> dict:
        """Return a dictionary of table_name -> DataFrame"""
        result = {}
        for table_name, group_df in map_df.groupby("table"):
            try:
                result[table_name] = self.create_dataframe_for_table(con, table_name, group_df)
                print(f"Created DataFrame for {table_name}, shape: {result[table_name].shape}")
            except Exception as e:
                print(f"Error creating DataFrame for {table_name}: {e}")
        return result

    def run(self) -> dict:
        print("Starting DataFrame creation...")
        t0 = time.time()

        con = connect_to_db(
            self.db_source,
            is_url=self.is_url,
            use_cache=self.use_cache,
            **{"message_callback": lambda level, text: print(f"[{level.upper()}] {text}")}
        )

        map_df = self.load_mapping_data()
        print(f"Loaded {len(map_df)} mapping entries from {self.mapping_csv_path}")

        all_dfs = self.create_all_dataframes(con, map_df)
        print(f"Successfully created {len(all_dfs)} DataFrames in {time.time() - t0:.2f} seconds")

        con.close()
        return all_dfs


# --- Usage ---
if __name__ == "__main__":
    db_file = "https://speedlocal.flowcore.app/api/duckdb/share/fa45bb6b7d2a92f71d53968d181f6c7b"
    mapping_csv = "inputs/mapping_db_views.csv"

    creator = PandasDFCreator(db_file, mapping_csv, is_url=True)
    dfs_dict = creator.run()

    # Example: access the 'emissions' DataFrame
    if "emissions" in dfs_dict:
        print(dfs_dict["emissions"].head())
