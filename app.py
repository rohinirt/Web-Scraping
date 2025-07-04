import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Load your data
df = pd.read_csv("test data.csv")

# Sidebar filters
st.sidebar.header("Filters")
batsman = st.sidebar.selectbox("Select Batsman", ["All"] + sorted(df["BatsmanName"].unique()))
bowler = st.sidebar.selectbox("Select Bowler", ["All"] + sorted(df["BowlerName"].unique()))
bat_team = st.sidebar.selectbox("Select Batting Team", ["All"] + sorted(df["BattingTeam"].unique()))
bowl_team = st.sidebar.selectbox("Select Bowling Team", ["All"] + sorted(df["BowlingTeam"].unique()))

# Apply filters
filtered = df.copy()
if batsman != "All":
    filtered = filtered[filtered["BatsmanName"] == batsman]
if bowler != "All":
    filtered = filtered[filtered["BowlerName"] == bowler]
if bat_team != "All":
    filtered = filtered[filtered["BattingTeam"] == bat_team]
if bowl_team != "All":
    filtered = filtered[filtered["BowlingTeam"] == bowl_team]

# Define zones layout: (x1, y1, x2, y2)
zones_layout = {
    "Zone 1": (-0.72, 0, -0.45, 1.91),
    "Zone 2": (-0.45, 0, -0.18, 0.71),
    "Zone 3": (-0.18, 0, 0.18, 0.71),
    "Zone 4": (-0.45, 0.71, -0.18, 1.31),
    "Zone 5": (-0.18, 0.71, 0.18, 1.31),
    "Zone 6": (-0.45, 1.31, 0.18, 1.91),
}

# Assign zones
def assign_zone(row):
    x, y = row["CreaseY"], row["CreaseZ"]
    for zone, (x1, y1, x2, y2) in zones_layout.items():
        if x1 <= x <= x2 and y1 <= y <= y2:
            return zone
    return "Other"

filtered["Zone"] = filtered.apply(assign_zone, axis=1)
filtered = filtered[filtered["Zone"] != "Other"]

# Calculate runs, wickets, avg
summary = (
    filtered.groupby("Zone")
    .agg(
        Runs=("Runs", "sum"),
        Wickets=("Wicket", lambda x: (x == True).sum())
    )
    .reindex(["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Zone 6"])
    .fillna(0)
)
summary["Avg Runs/Wicket"] = summary["Runs"] / summary["Wickets"]
summary["Avg Runs/Wicket"] = summary["Avg Runs/Wicket"].replace([float("inf"), float("nan")], 0)

# Plot zones
colors = ['#FFCCCC', '#CCFFCC', '#CCCCFF', '#FFFFCC', '#FFCCFF', '#CCE5FF']
fig, ax = plt.subplots(figsize=(7, 10))

for (zone, (x1, y1, x2, y2)), color in zip(zones_layout.items(), colors):
    w, h = x2 - x1, y2 - y1
    ax.add_patch(
        patches.Rectangle((x1, y1), w, h, edgecolor="black", facecolor=color, linewidth=2)
    )

    runs = int(summary.loc[zone, "Runs"])
    wkts = int(summary.loc[zone, "Wickets"])
    avg = summary.loc[zone, "Avg Runs/Wicket"]

    ax.text(
        x1 + w / 2,
        y1 + h / 2,
        f"{zone}\nRuns: {runs}\nWkts: {wkts}\nAvg: {avg:.1f}",
        ha="center",
        va="center",
        weight="bold",
        fontsize=9
    )

ax.set_xlim(-0.75, 0.25)
ax.set_ylim(0, 2)
ax.set_xlabel("CreaseY (Width in meters)")
ax.set_ylabel("CreaseZ (Length in meters)")
ax.set_title("Zone‑wise Runs, Wickets, and Avg Runs/Wicket")
ax.grid(True)

st.pyplot(fig)
