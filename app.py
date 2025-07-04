import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import matplotlib.colors as mcolors

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------
df = pd.read_csv("test data.csv")

# --------------------------------------------------
# 2. SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.header("Filters")

batsman   = st.sidebar.selectbox("Select Batsman",       ["All"] + sorted(df["BatsmanName"].unique()))
delivery  = st.sidebar.selectbox("Select Delivery Type", ["All"] + sorted(df["DeliveryType"].unique()))
bat_team  = st.sidebar.selectbox("Select Batting Team",  ["All"] + sorted(df["BattingTeam"].unique()))
bowl_team = st.sidebar.selectbox("Select Bowling Team",  ["All"] + sorted(df["BowlingTeam"].unique()))

# Apply filters
filtered = df.copy()
if batsman   != "All": filtered = filtered[filtered["BatsmanName"]   == batsman]
if delivery  != "All": filtered = filtered[filtered["DeliveryType"]  == delivery]
if bat_team  != "All": filtered = filtered[filtered["BattingTeam"]   == bat_team]
if bowl_team != "All": filtered = filtered[filtered["BowlingTeam"]   == bowl_team]

# --------------------------------------------------
# 3. CHOOSE ZONE MAP (Right‑ or Left‑handed)
# --------------------------------------------------
zones_right = {                       # (x1, y1, x2, y2)
    "Zone 1": (-0.72, 0.00, -0.45, 1.91),
    "Zone 2": (-0.45, 0.00, -0.18, 0.71),
    "Zone 3": (-0.18, 0.00,  0.18, 0.71),
    "Zone 4": (-0.45, 0.71, -0.18, 1.31),
    "Zone 5": (-0.18, 0.71,  0.18, 1.31),
    "Zone 6": (-0.45, 1.31,  0.18, 1.91),
}

zones_left = {
    "Zone 1": ( 0.45, 0.00,  0.72, 1.91),          # mirrored
    "Zone 2": ( 0.18, 0.00,  0.45, 0.71),
    "Zone 3": (-0.18, 0.00,  0.18, 0.71),          # unchanged
    "Zone 4": ( 0.18, 0.71,  0.45, 1.31),
    "Zone 5": (-0.18, 0.71,  0.18, 1.31),          # unchanged
    "Zone 6": (-0.18, 1.31,  0.45, 1.91),          # above zones 4 & 5
}

# Decide which map to use (default to right‑hand if mixed/empty)
is_right = True
if not filtered.empty:
    is_right = bool(filtered["IsBatsmanRightHanded"].iloc[0])

zones_layout = zones_right if is_right else zones_left

# --------------------------------------------------
# 4. ASSIGN ZONES
# --------------------------------------------------
def assign_zone(row):
    x, y = row["CreaseY"], row["CreaseZ"]
    for zone, (x1, y1, x2, y2) in zones_layout.items():
        if x1 <= x <= x2 and y1 <= y <= y2:
            return zone
    return "Other"

filtered["Zone"] = filtered.apply(assign_zone, axis=1)
filtered = filtered[filtered["Zone"] != "Other"]

# --------------------------------------------------
# 5. SUMMARY STATS
# --------------------------------------------------
summary = (
    filtered.groupby("Zone")
    .agg(
        Runs    = ("Runs",   "sum"),
        Wickets = ("Wicket", lambda s: (s == True).sum())
    )
    .reindex(["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Zone 6"])
    .fillna(0)
)
summary["Avg Runs/Wicket"] = summary["Runs"] / summary["Wickets"]
summary["Avg Runs/Wicket"].replace([float("inf"), float("nan")], 0, inplace=True)

# --------------------------------------------------
# 6. PLOT HEATMAP
# --------------------------------------------------
norm = mcolors.Normalize(vmin=summary["Avg Runs/Wicket"].min(),
                         vmax=summary["Avg Runs/Wicket"].max())
cmap = cm.get_cmap("RdYlGn")

fig, ax = plt.subplots(figsize=(10, 10))

for zone, (x1, y1, x2, y2) in zones_layout.items():
    w, h = x2 - x1, y2 - y1
    avg  = summary.loc[zone, "Avg Runs/Wicket"]
    color = cmap(norm(avg))

    ax.add_patch(
        patches.Rectangle((x1, y1), w, h,
                          edgecolor="black",
                          facecolor=color,
                          linewidth=2)
    )

    runs = int(summary.loc[zone, "Runs"])
    wkts = int(summary.loc[zone, "Wickets"])

    ax.text(
        x1 + w / 2, y1 + h / 2,
        f"{zone}\nRuns: {runs}\nWkts: {wkts}\nAvg: {avg:.1f}",
        ha="center", va="center",
        fontsize=8, weight="bold",
        color="black" if norm(avg) < 0.6 else "white"
    )

ax.set_xlim(-0.75, 0.75)
ax.set_ylim(0, 2)
ax.set_xlabel("CreaseY (m)")
ax.set_ylabel("CreaseZ (m)")
ax.set_title("Zone‑wise Heatmap: Avg Runs/Wicket")
ax.grid(True)

sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
cbar.set_label("Avg Runs/Wicket")

st.pyplot(fig)
