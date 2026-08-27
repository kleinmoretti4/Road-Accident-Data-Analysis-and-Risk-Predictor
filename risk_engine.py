import pandas as pd
import numpy as np
from dataclasses import dataclass, field

#percentage threashold for categorising the risk levels into High, Medium and Low
LOW_RISK = 33
MID_RISK = 66

#these are the codes that represent fatal or serious collisions in the DfT daabase
FAT_CODES = [1,2] 

#these are the relative weights assigned to each condition to be used for risk calculation
VAR_WEIGHT = {
  "weather_conditions": 0.3,
  "light_conditions": 0.25,
  "road_type": 0.2,
  "season": 0.15,
  "day_of_week": 0.05,
  "month": 0.05,
}

#speciefic precutionary saftey advise assigned to individual condition labels
PRE_ADVISE = {
  "weather_conditions":{
    "Raining no high winds":"Increase following distance and reduce speed.",
    "Snowing no high winds":"Avoid driving if possible, but if driving use winter tyres.",
    "Fine + high winds":"pay attention to sudden wind, affecting highsided vehicles (such as lorries or coaches).",
    "Raining + high winds":"Increase following distance to allow for longer braking distance and reduce speed to avoid tyre slipping.",
    "Snowing + high winds":"Avoid driving whatsoever",
    "Fog or mist":"use fog lights and reduce speed",
  },
  "light_conditions":{
    "Daylight":"Good visibility, stay focused and abide to standard driving practices.",
    "Darkness - lights lit":"Check headlights are clean and working properly.",
    "Darkness - lights unlit": "Reduce speed and expect less visibility.",
    "Darkness - no lighting": "reduce speed, expect less visibility and be ready to  react to any sudden updates.",
    "Darkness - lighting unknown": "Drive with caution, reduce speed, expect less visibility and be ready to  react to any sudden updates.",
  },
  "road_type":{
    "Roundabout": "Pioritise cars already on the roundabout.",
    "Single carriageway": "Stay alert for oncoming traffic and avoid overtaking at bends.",
    "Slip road": "Match motoway speed befor merging",
    "Dual carriageway": "Abide to standard lane discipline and use mirrors before lane change",
    "One way street": "Check for pedestirians and cyclist before driving through one",
  },
  "season":{
    "Winter": "Road may look normal but be icy, so increase folllowing distance to allow for extra braking distance",
    "Autumn": "Watchout for wet leaves which can reduce tyre grip especially on bends",
    "Spring": "Be prepared for Varying weather conditions (random rain) because, they can cause varying road conditions",
    "summer": "Be prepared for an increase in cyclist and pedestrians becuase of good outside conditions",
  },
  "day_of_week":{
    "Friday":"Increased traffic and pedestrian activity in the evening, so plan journeys accordingly",
    "Saturday": "Increased cyclist, pedestrians and traffic, so plan journeys accordingly",
    "Sunday": "Increased rural traffic and slow moving-veichles, so plan journeys accordingly",
  },
  "month":{
    "December": "Short daylight hours so expect darkness (and to switch on your headlight) earlier than usual",
    "Saturday": "Typicaly icy roads so check weather forecasts before travelling",
    "November": "Heavy rain combined with early darkness, so expect less visibility and to switch on your headlights earlier than usual",
  },
}


#class to return the result of the risk analysis
@dataclass
class RiskResult:
  percentage: int
  level: str
  factors: list = field(default_factory=list)
  precautions: list = field(default_factory=list)
  explanation: str = " "
  active_count: int = 0

#makes the UI more clean and understandable by mapping the inernal datafrae colums to cleaner ones
COL_DIS_NAME = {
  "weather_conditions": "Weather",
  "road_type": "Road Type",
  "light_conditions": "Light Condition",
  "day_of_week": "Day of Week",
  "season": "Season",
  "month": "Month",
}

#reverse lookup for UI display name to internal dataframe colums
DIS_TO_COL = {v: k for k, v in COL_DIS_NAME.items()}

#imports the label dictionary I made previously in the daya_loader.py module
from data_loader import (
  WEATHER_CONDITION_DD,
  ROAD_TYPE_DD,
  LIGHT_CONDITIONS_DD,
  DAY_OF_WEEK_DD,
  MONTH_DD,
)

#Maps each data column to it's corresponding dictionary
LABEL_MAP = {
  "weather_conditions": WEATHER_CONDITION_DD,
  "road_type": ROAD_TYPE_DD,
  "light_conditions": LIGHT_CONDITIONS_DD,
  "day_of_week": DAY_OF_WEEK_DD,
  "month": MONTH_DD,
}

#function to inteprets the raw condition code into human understandable label
def dec_label(column,value):
  if column == "season":
    return str(value)
  lookup = LABEL_MAP.get(column, {})
  return lookup.get(int(value), str(value))

#function to calculates a wighted risk percentage  based on the selected user filters 
def calc_risk(df, filters):
  #removes unselected filters from processing
  atv_filters = {col:val for col, val in filters.items() if val is not None}

  #returns a base result if no filters are selected
  if not atv_filters:
    return RiskResult(
      percentage = 50,
      level = "medium",
      factors = [],
      precautions = ["select contition filters to see speciefic risk factors."],
      explanation = ("No condition has been selected; Showing the baseline average accident risk across all 100,927 UK collision records 2024.\n"
      "Use the dropdown menues to filter by conditions"),
      active_count = 0, 
    )
  weighted_log_mx = []
  total_weight = 0.0
  factors_list = []
  precaution_list = []

  #loops through each user selected filter to calculate it's individual risk impact
  for column, value in atv_filters.items():
    valid_mask = df[column].notna() & df["collision_severity"].notna()
    valid_rows = df[valid_mask]

    if len(valid_rows) == 0: 
      continue

    #calculates a baseline seious/fatal collision rate for the entire category
    col_base_rate = (valid_rows["collision_severity"].isin(FAT_CODES).mean())
    #ensures the row is mathcing the user selected value
    con_rows = valid_rows[valid_rows[column] ==value]
    con_count = len(con_rows)

    if con_count < 10: #ignores small samples that would be statistically insignificant
      continue
    
    #serious and fatal accident rate for the condition the user selected
    con_sf_rate = (con_rows["collision_severity"].isin(FAT_CODES).mean())

    if col_base_rate == 0:
      continue
    
    #calculates a relative risk multiplier for the user selected condition and then applies its assigned weight
    multiplier = con_sf_rate/col_base_rate
    weight = VAR_WEIGHT.get(column, 1.0/ len(atv_filters))
    weighted_log_mx.append(np.log(max(multiplier, 1e-6))*weight)
    total_weight += weight
    label = dec_label(column,value)

    #condition label, multipler, and sample count for the Tkinter UI display
    factors_list.append({
      "label": f"{COL_DIS_NAME.get(column,column)}: {label}",
      "multiplier": round(multiplier, 2),
      "count": con_count,
    })

    #appends user condition seciefic advice
    advise = PRE_ADVISE.get(column, {}).get(label)
    if advise:
      precaution_list.append(advise)

  #derives a geometric mean by combining all the weighted log multipliers
  if not weighted_log_mx or total_weight == 0:
    comb_mx = 1.0
  else:
    comb_log = sum(weighted_log_mx) / total_weight
    comb_mx = np.exp(comb_log)

  #converts the geometric mean into a 1-100 percentage score
  raw_percent = comb_mx*50
  percent = int(np.clip(raw_percent, 0, 100))

  #categorises the risk percentage into categorical levels
  if percent <= LOW_RISK:
    level = "Low"
  elif percent <= MID_RISK:
    level = "Medium"
  else:
    level = "High"

  #generate an explanation of how the risk is calculated 
  factors_list.sort(key=lambda f:f["multiplier"])
  explanation = (
    f"Accident risk is estimated from {len(atv_filters)} selected conditions\n"
    f"using {len(df):,} UK collision records (DfT, 2024).\n"
    "For each condition selected, the propotiono of serious or fatal collisions" \
    "within that condition is compared to the overall serious/fatal rate." \
    "A multiplier of 1.5x translates to a 50% more serious or fatal outcome than average\n" \
    "The multipliers are then combined using a weighted geometric mean and " \
    "normalised: 50%: average risk, 100% = double the average risk.\n" \
    "DISCLAIMER: Estimates are only advisory. They are derived from historical data" \
    "so reflect statistical patterns not individual outcomes." 
  )

  #ensures it still outputs a precaution even if there isn't one speciefic to the risk
  if not precaution_list:
    precaution_list = ["Always follow best driving practices"]

  #returns the result of the risk assesment
  return RiskResult(
    percentage= percent,
    level = level,
    factors = factors_list,
    precautions= precaution_list,
    explanation= explanation,
    active_count=len(atv_filters)
  )