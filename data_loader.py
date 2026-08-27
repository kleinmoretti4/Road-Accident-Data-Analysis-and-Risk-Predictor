import pandas as pd 
import numpy as np 
import sys
import os

#dictionary to map the weather codes used in the DfT CSV to human understandable labels
WEATHER_CONDITION_DD = {
    1: "Fine no high winds",
    2:"Raining no high winds",
    3:"Snowing no high winds",
    4:"Fine + high winds",
    5:"Raining + high winds",
    6:"Snowing + high winds",
    7:"Fog or mist",
    8:"Other",
}

#dictionary to map the road type codes used in the DfT CSV to human understandable labels
ROAD_TYPE_DD = {
    1: "Roundabout",
    2:"One way street",
    3: "Dual carriageway",
    6:"Single carriageway",
    7:"Slip road",
    12:"One way street / Slip road",
}

#dictionary to map the light condition codes used in the DfT CSV to human understandable labels
LIGHT_CONDITIONS_DD = {
    1:"Daylight",
    4:"Darkness - lights lit",
    5:"Darkness - lights unlit",
    6: "Darkness - no lighting",
    7:"Darkness - lighting unknown",
}

#dictionary to map the days of the week codes used in the DfT CSV to human understandable labels
DAY_OF_WEEK_DD = {
    1:"Sunday",
    2:"Monday",
    3:"Tuesday",
    4:"Wednesday",
    5:"Thursday",
    6:"Friday",
    7:"Saturday",
}

#month names being mapped to numbers which i will later use the date column to derive month from,
#Additionally, I will use it for the month dropdown in UI
MONTH_DD = {
  1:"January",  
  2:"February", 
  3:"March",    
  4:"April",
  5:"May",      
  6:"June",     
  7:"July",      
  8:"August",
  9:"September",
  10:"October", 
  11:"November", 
  12:"December",
}

#seasons which are being mapped to month numbers 
#To be directly derived from them therfore indirectly being derived from date
SEASON_DD = {
  "Spring":[3, 4, 5],
"Summer":[6, 7, 8],
  "Autumn":[9, 10, 11],
  "Winter":[12, 1, 2],
}

#maps each month number to its allocated season name using a reverse lookup dictionary
MONTH_TO_SEASON = {
  month: season
  for season, months in SEASON_DD.items()
  for month in months
}

#maps each integer month number to their allocated season name string to be
#used as a filter variable
def allocate_season(month_series):
  return month_series.map(MONTH_TO_SEASON)

#function to load, validate and clean the collision CSV data
def load_dataset(filepath):

  #list of all the necessary colums the risk engine needs to work.
  IND_COLUMNS = [
    "date",
    "weather_conditions",
    "road_type",
    "light_conditions",
    "day_of_week",
    ]
  
  #
  try:
    df = pd.read_csv(
      filepath,
      low_memory=False,
      parse_dates=["date"], #parses the date strings to date time
      dayfirst=True, #validates that the DfT dates are in DD/MM/YYY
    )

    #verifies all needed columns needed for the risk engine to work is present in the data set
    missing = [col for col in IND_COLUMNS if col not in df.columns]
    if missing:
      print(
      #if a needed column is missing it prints out the name of the missing colums so the user knows what's wrong
        f"ERROR: The dataset is missing a required independent column ({missing}). \n"
        f"Double-check you are using the correct DfT collisison dataset CSV.")
      sys.exit(1)

  #removes all rows where all the filter colums are null
    filter_cols = [
      "weather_conditions",
      "road_type",
      "light_conditions",
      "day_of_week",
      ]
    df.dropna(subset=filter_cols, how="all", inplace=True)
  
  #the DfT dataset uses -1 to represent missing or out of range data 
  #and 9 to represent unknow data, neither of which are usefull for my risk calculation
  #they are converted to NaN so that they are removed from calculation in the risk engine
    bad_num = [-1, 9]
    for col in filter_cols:
      df[col] = pd.to_numeric(df[col], errors="coerce")
      df[col] = df[col].replace(bad_num, np.nan)

  #extracts month numbers from the now parsed dates 
  #and derives the allocated season for each row
    df["month"] = df["date"].dt.month
    df["season"] = allocate_season(df["month"])

    return df #returns the cleaned data set
  
  #error handling for if the file isn't found
  except FileNotFoundError:
    print(f"ERROR: Data file not found at: '{filepath}'. \n"
          f"please ensure the CSV dataset file is in the same folder as the other programs."
         )

  #error handling for if the dataset can't be parsed by pandas 
  except pd.errors.ParserError:
    print(
      f"ERROR: The data file could not be read. \n"
      f"It may be corrupted. Try redownloading the file from the DfT's official website."   
        )

  #error handling for unexpected errors  
  except Exception as error:
    print(
      f"ERROR: An unexpected error occured while loading the data. \n"
      f"Type: {type(error).__name__}\n"
      f"Details: {error}\n"
      f"Please try loading up the program again."
    )
    sys.exit(1)

#function for building the filter options for the UI component
def get_dd_options(column):
   
   #maps eac hfilter to its appropriate static dictionary
   base = {
        "weather_conditions": WEATHER_CONDITION_DD,
        "road_type":          ROAD_TYPE_DD,
        "light_conditions":   LIGHT_CONDITIONS_DD,
        "day_of_week":        DAY_OF_WEEK_DD,
        "month":              MONTH_DD,
    }
   
   #seasons are strings so they are returned as both display text and filter value
   if column == "season":
     options = {"Any": None}
     for season in SEASON_DD:
       options[season] = season
     return options
   
   #starts with "any" as a placeholder then reverses the code to human readabel label
   #so the UI submits understandable names and the backend filters by integers   
   lookup = base.get(column, {})
   options = {"Any": None}
   for code, label in lookup.items():
     options[label] = code
   return options