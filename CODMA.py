import pandas as pd
import os
import re
import shutil
from collections import defaultdict


# ============================================================
# FIND INPUT FILES
# ============================================================

root_dir = os.getcwd()

txt_files = [f for f in os.listdir(root_dir) if f.lower().endswith(".txt")]
csv_files = [f for f in os.listdir(root_dir) if f.lower().endswith(".csv")]

if len(txt_files) != 1:
    raise RuntimeError(
        f"Expected exactly one .txt file, found {len(txt_files)}"
    )

if len(csv_files) != 1:
    raise RuntimeError(
        f"Expected exactly one .csv file, found {len(csv_files)}"
    )

raw_txt = txt_files[0]
plate_map_csv = csv_files[0]

run_name = os.path.splitext(raw_txt)[0]

run_dir = os.path.join(root_dir, run_name)
temp_dir = os.path.join(run_dir, "temp")
wells_dir = os.path.join(temp_dir, "wells")
triplicates_dir = os.path.join(temp_dir, "triplicates")

os.makedirs(wells_dir, exist_ok=True)
os.makedirs(triplicates_dir, exist_ok=True)

print(f"\n[INFO] Creating run directory: {run_name}")

# ============================================================
# MOVE INPUT FILES INTO TEMP
# ============================================================

txt_path = os.path.join(root_dir, raw_txt)
csv_path = os.path.join(root_dir, plate_map_csv)

temp_txt = os.path.join(temp_dir, raw_txt)
temp_csv = os.path.join(temp_dir, plate_map_csv)

shutil.move(txt_path, temp_txt)
shutil.move(csv_path, temp_csv)

# ============================================================
# STEP 1 : SPLIT PER WELL
# ============================================================

print("\n[STEP 1] Splitting wells")

df = pd.read_csv(temp_txt, sep="\t")

df.columns = df.columns.str.strip()

cycle_col = [c for c in df.columns if "cycle" in c.lower()][0]
well_col = [c for c in df.columns if "well position" in c.lower()][0]

df[well_col] = (
    df[well_col]
    .astype(str)
    .str.strip()
    .str.upper()
)

df[cycle_col] = pd.to_numeric(df[cycle_col], errors="coerce")

signal_cols = ["ROX", "FAM", "CY5", "VIC", "TAMRA"]
signal_cols = [c for c in signal_cols if c in df.columns]

for col in signal_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

for well, g in df.groupby(well_col):

    g = g.dropna(subset=signal_cols, how="all")
    g = g[g[cycle_col].between(1, 40)]
    g = g.sort_values(cycle_col)

    if len(g) == 0:
        continue

    outfile = os.path.join(wells_dir, f"{well}.txt")
    g.to_csv(outfile, sep="\t", index=False)

print("[DONE] Well files generated")

# ============================================================
# STEP 2 : BUILD TRIPLICATE FILES
# ============================================================

print("\n[STEP 2] Building grouped replicates")

plate_map = pd.read_csv(temp_csv, index_col=0)

plate_map = plate_map.dropna(how="all")
plate_map = plate_map.dropna(axis=1, how="all")

plate_map.index = plate_map.index.astype(str).str.strip().str.upper()

plate_map.columns = (
    pd.Series(plate_map.columns)
    .astype(str)
    .str.strip()
    .str.replace(".0", "", regex=False)
)

plate_map = plate_map[[c for c in plate_map.columns if c.isdigit()]]
plate_map = plate_map[
    sorted(plate_map.columns, key=lambda x: int(x))
]

plate_map = plate_map.iloc[:8, :12]


def parse_well(w):
    m = re.match(r"([A-H])(\d{1,2})", w)
    return (m.group(1), str(int(m.group(2)))) if m else (None, None)


well_files = [
    f for f in os.listdir(wells_dir)
    if f.endswith(".txt")
]

well_map = {}

for f in well_files:
    name = os.path.splitext(f)[0].upper()
    row, col = parse_well(name)

    if row:
        well_map[(row, col)] = f

groups = defaultdict(list)

for row in plate_map.index:
    for col in plate_map.columns:

        val = plate_map.loc[row, col]

        if pd.isna(val):
            continue

        if str(val).strip() == "":
            continue

        key = (row, col)

        if key in well_map:
            groups[str(val)].append(key)

for group_id, wells in groups.items():

    dfs = []

    for w in wells:

        path = os.path.join(
            wells_dir,
            well_map[w]
        )

        df = pd.read_csv(path, sep="\t")

        cycle_candidates = [
            c for c in df.columns
            if "cycle" in c.lower()
        ]

        cycle_col = cycle_candidates[0]

        df[cycle_col] = pd.to_numeric(
            df[cycle_col],
            errors="coerce"
        )

        dfs.append(df)

    if not dfs:
        continue

    cycle_col = [
        c for c in dfs[0].columns
        if "cycle" in c.lower()
    ][0]

    channels = ["ROX", "FAM", "VIC", "TAMRA"]

    if group_id in {"Oligo_only", "EndoQ"}:
        channels.insert(2, "CY5")

    rep_tables = []

    for i, df in enumerate(dfs, start=1):

        cols = [cycle_col] + [
            c for c in channels
            if c in df.columns
        ]

        temp = df[cols].copy()

        rename_map = {cycle_col: "Cycle"}

        for ch in channels:
            if ch in temp.columns:
                rename_map[ch] = f"{ch}{i}"

        temp = temp.rename(columns=rename_map)

        rep_tables.append(temp)

    merged = rep_tables[0]

    for temp in rep_tables[1:]:
        merged = pd.merge(
            merged,
            temp,
            on="Cycle",
            how="left"
        )

    ordered = ["Cycle"]

    for ch in ["ROX", "FAM", "CY5", "VIC", "TAMRA"]:

        if ch not in channels:
            continue

        for i in range(1, len(rep_tables) + 1):

            col = f"{ch}{i}"

            if col in merged.columns:
                ordered.append(col)

    merged = merged[ordered]

    merged["Wells"] = "_".join(
        [f"{r}{c}" for r, c in wells]
    )

    outfile = os.path.join(
        triplicates_dir,
        f"{group_id}.txt"
    )

    merged.to_csv(
        outfile,
        sep="\t",
        index=False
    )

    print(f"[SAVED] {group_id}")

# ============================================================
# STEP 3 : BUILD COMBINED WORKBOOK
# ============================================================

print("\n[STEP 3] Writing Excel workbook")

combined_xlsx = os.path.join(
    temp_dir,
    "combined.xlsx"
)

txt_files = sorted(
    f for f in os.listdir(triplicates_dir)
    if f.endswith(".txt")
)

with pd.ExcelWriter(combined_xlsx) as writer:

    for f in txt_files:

        path = os.path.join(
            triplicates_dir,
            f
        )

        df = pd.read_csv(path, sep="\t")

        sheet_name = os.path.splitext(f)[0][:31]

        df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False,
        )

print("[DONE] combined.xlsx created")

# ============================================================
# STEP 4 : CLEANUP
# ============================================================

print("\n[STEP 4] Cleanup")

shutil.move(
    temp_txt,
    os.path.join(run_dir, raw_txt)
)

shutil.move(
    temp_csv,
    os.path.join(run_dir, plate_map_csv)
)

shutil.move(
    combined_xlsx,
    os.path.join(run_dir, "combined.xlsx")
)

shutil.rmtree(temp_dir)

print("\n✅ COMPLETE")
print(f"Output directory:\n{run_dir}")
