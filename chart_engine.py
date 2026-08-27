import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

#backend required for Matplotlib to properly render to a Tkinter canvas
matplotlib.use("Agg")

#constant variables to ensure that the charts colour scheme match my high-fidelity prototype
CHART_BG = "#0d1e35"
CHART_FG = "#e0e8f0"
CHART_GD = "#1a3050"
BAR_CLR = "#00b899"
LINE_CLR = "#00b899"
LINE_MKR = "#ffffff"
HLT_BAR = "#ff6b6b"
SPINE_CLR = "#1a3050"

#imports the label dictionary I made previously in the daya_loader.py module
from data_loader import (
  WEATHER_CONDITION_DD,
  ROAD_TYPE_DD,
  LIGHT_CONDITIONS_DD,
  DAY_OF_WEEK_DD,
  MONTH_DD,
)

#imports the column display names from the risk_engine module
from risk_engine import COL_DIS_NAME, DIS_TO_COL

#links breaksdown columns to their label dictionaries
MAPS_LABEL = {
  "weather_conditions": WEATHER_CONDITION_DD,
  "road_type": ROAD_TYPE_DD,
  "light_conditions": LIGHT_CONDITIONS_DD,
  "day_of_week": DAY_OF_WEEK_DD,
  "month": MONTH_DD,
}

#function to generate the axis labels 
def axis_lab(column,codes):
  lookup = MAPS_LABEL.get(column, {})#fetches the corresponding dictionary for the label
  labels = []
  for code in codes:
    if column in ("season", "month") and isinstance(code, str):
      label = code
    #maps the numeric code to label 
    else:
      label = lookup.get(int(code), str(code))
    
    #splits long labels at the midpoint
    if len(label) > 14:
      words = label.split()
      mid = len(words)//2
      label= " ".join(words[:mid]) + "\n" + " ".join(words[:mid])
    labels.append(label)
  return labels

#function for constructing and rendering the plots to Tkinter
def build_chart(par_frame, df, brk_column, chart_type, highlight_value):
  #removes rows with empty values in the selected breakdown column
  clean = df[df[brk_column].notna()]
  #groups the data by breakdown coulmn and collision count
  counts = (clean.groupby(brk_column)
            .size()
            .reset_index(name="collisions"))
  #arranges the days of the week and month in proper order for display
  ARNG_COLUMNS = {
    "day_of_week": [2, 3, 4, 5, 6, 7, 1],
    "month": list(range(1, 13)),
  }

  #categorically orders a column if it requires a speciefic sequence
  if brk_column in ARNG_COLUMNS:
    arng = ARNG_COLUMNS[brk_column]
    counts[brk_column] = pd.Categorical(counts[brk_column], categories=arng, ordered=True)
    counts = counts.sort_values(brk_column)
  #sorts by collision descending as a fallback
  else:
    counts = counts.sort_values("collisions", ascending=False)
  
  #extracts data to plot
  values = counts[brk_column].tolist()
  heights = counts["collisions"].tolist()
  x_labels = axis_lab(brk_column, values)

  #sets the dimensions and DPI for consistent scaling
  fig = Figure(figsize=(6.2, 3.6), dpi=96)
  fig.patch.set_facecolor(CHART_BG)
  ax = fig.add_subplot(111)
  ax.set_facecolor(CHART_BG)
  x_positions = range(len(values))

  #renders a bar or line chart
  if chart_type == "bar":
    colours = [] #determines the colours of the bar
    for V in values:
      if highlight_value is not None and V == highlight_value:
        colours.append(HLT_BAR)
      else:
        colours.append(BAR_CLR)
    #plot bars with the z order = 3 to enable rendering above line grids
    bars = ax.bar(x_positions, heights, color = colours, width =0.6, zorder = 3)

    #adds labels above each bar
    for bar, height, in zip(bars, heights):
      ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + max(heights) * 0.01,
            f"{height:,}",
            ha="center", va="bottom",
            fontsize=7, color=CHART_FG,
            )
  
  else:
    #linechart plots with a semi-transparent fill underneath a marker
    ax.plot(list(x_positions), heights,linewidth=2,color=LINE_CLR, marker="o",
            markersize=5, markerfacecolor=LINE_MKR, zorder=3,)
    ax.fill_between(list(x_positions), heights, alpha=0.15, color=LINE_CLR)
  
  
  ax.set_xticks(list(x_positions))
  ax.set_xticklabels(x_labels,rotation=25,ha="right",fontsize=7.5, color=CHART_FG)
  ax.tick_params(axis="y", color=CHART_FG, labelsize = 8)

  #Formarts the y axis with a comma for numbers with more that 4 values
  ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _:f"{int(val):,}"))

  #sets the graph titles and axis labels using the display names imported from the risk engine
  display_name = COL_DIS_NAME.get(brk_column, brk_column)
  ax.set_title(f"{display_name} vs. Collisions", color=CHART_FG, fontsize=10, fontweight="bold")
  ax.set_ylabel("Collisions", color=CHART_FG, fontsize=8)

  #adds a horizontal grid behind the plot elements
  ax.yaxis.grid(True, color=CHART_GD, linestyle="--", linewidth=0.6, zorder=0)
  ax.set_axisbelow(True)

  #it hides all other spines except for the bottom making the UI cleaner
  for spine_name, spine in ax.spines.items():
    if spine_name == "bottom":
      spine.set_color(SPINE_CLR)
    else:
      spine.set_visible(False)
  
  #padding to avoid the labels cutting off
  fig.tight_layout(pad=1.2)

  #converts the matplotlib figure to a Tkinter canvas widget
  canvas=FigureCanvasTkAgg(fig, master=par_frame)
  canvas.draw()
  return canvas

#removes current chart widged befor rendering a new one
def clear_chart(par_frame):
  for widget in par_frame.winfo_children():
    widget.destroy()