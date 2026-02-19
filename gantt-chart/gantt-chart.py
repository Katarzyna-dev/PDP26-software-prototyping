import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle, Patch
import datetime as dt

# === 1. Read tasks and study periods ===
tasks = pd.read_csv("timeline.csv", sep=",")
tasks["start_date"] = pd.to_datetime(tasks["start_date"], dayfirst=True)
tasks["due_date"] = pd.to_datetime(tasks["due_date"], dayfirst=True)

periods = pd.read_csv("study_periods.csv")
periods["start_date"] = pd.to_datetime(periods["start_date"], dayfirst=True)
periods["due_date"] = pd.to_datetime(periods["due_date"], dayfirst=True)

# === Optional: add period descriptions ===
period_descriptions = {
    "Period 1": "Introduction",
    "Period 2": "Research",
    "Period 3": "Design & Planning",
    "Period 4": "Building & Design",
    "Period 5": "Final Gala Prep"
}

# === 2. Sort tasks by start date ascending (earliest at top) ===
tasks = tasks.sort_values(by="start_date", ascending=True).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(14, 8))
default_gray = "#D3D3D3"

# === 3. Draw period background blocks (semi-transparent) ===
y_bottom = -0.5
y_top = len(tasks) - 0.5
for _, row in periods.iterrows():
    start = mdates.date2num(row["start_date"])
    end = mdates.date2num(row["due_date"])
    ax.add_patch(
        Rectangle(
            (start, y_bottom),
            end - start,
            y_top - y_bottom,
            color=row["color"],
            alpha=0.15,
            zorder=0
        )
    )

# === 4. Functions to get task/milestone colors ===
def get_task_color(task_start, task_end):
    overlapping_periods = []
    for _, row in periods.iterrows():
        period_start = row["start_date"]
        period_end = row["due_date"]
        if task_end >= period_start and task_start <= period_end:
            overlapping_periods.append((max(task_start, period_start), min(task_end, period_end), row["color"]))
    if not overlapping_periods:
        return [(task_start, task_end, default_gray)]
    return overlapping_periods

def get_milestone_color(date):
    for _, row in periods.iterrows():
        if row["start_date"] <= date <= row["due_date"]:
            return row["color"]
    return default_gray

# === 5. Plot tasks and milestones ===
for i, row in tasks.iterrows():
    start = row["start_date"]
    end = row["due_date"]
    title = row["title"]

    if start == end:
        color = get_milestone_color(start)
        ax.scatter(mdates.date2num(start), i, marker="D", s=100, color=color, zorder=5)
        milestone_padding = 3.0
        ax.text(mdates.date2num(start) + milestone_padding, i, title, va='center', ha='left', fontsize=9)
    elif "holiday" in str(title).lower():
        rect = FancyBboxPatch(
            (mdates.date2num(start), i - 0.2),
            mdates.date2num(end) - mdates.date2num(start),
            0.4,
            boxstyle="round,pad=0.1",
            linewidth=0,
            color=default_gray
        )
        ax.add_patch(rect)
        ax.text(mdates.date2num(end) + 0.5, i, title, va='center', ha='left', fontsize=9)
    else:
        segments = get_task_color(start, end)
        for seg_start, seg_end, color in segments:
            width = mdates.date2num(seg_end) - mdates.date2num(seg_start)
            rect = FancyBboxPatch(
                (mdates.date2num(seg_start), i - 0.2), width, 0.4,
                boxstyle="round,pad=0.1", linewidth=0, color=color
            )
            ax.add_patch(rect)
        ax.text(mdates.date2num(end) + 0.5, i, title, va='center', ha='left', fontsize=9)

# === 6. Format chart ===
ax.set_xlabel("Timeline")
ax.set_yticks([])
ax.xaxis_date()
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
plt.xticks(rotation=45)
ax.grid(axis='x', linestyle='--', alpha=0.5)

today_num = mdates.date2num(dt.datetime.today())
ax.axvline(today_num, color="gray", linestyle="--", linewidth=1, label="Today")

for spine in ax.spines.values():
    spine.set_visible(False)

# === 7. Add legend for study periods ===
from matplotlib.patches import Patch

legend_elements = []
for _, row in periods.iterrows():
    desc = period_descriptions.get(row["period"], row["period"])
    legend_elements.append(Patch(facecolor=row["color"], edgecolor='none', label=desc))

ax.legend(handles=legend_elements, title="Study Periods", loc='best')

ax.set_title("Project Gantt Chart with Milestones Colored by Period", fontsize=12, weight="bold")
ax.invert_yaxis()  # earliest tasks at top, final tasks at bottom
plt.tight_layout()
plt.show()