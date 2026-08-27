<img width="597" height="984" alt="image of the full ui" src="https://github.com/user-attachments/assets/b422be78-30c2-4c87-9ff5-0541e476d533" />

## About
This is my AQA A-level computer science NEA that got me 71/75 (A*). It is a python app that estimates accident risk by using a weighted mathematical model and historical data from England's Department of Transport to output a percentage risk estimate based on user inputs like weather, road type, e.t.c. Lined in this repo is the NEA documentation, the python code and the accident dataset.

## Software requirements
- python 3.9 or higher can be downloaded at: ([Download Python](https://www.python.org/downloads/))
- pip (Python package installer - included with modern Python installations)

## Hardware Requirements
- Minimum 4 GB RAM (8 GB recommended for smoother performance with large datasets)
- 200 MB free disk space (for Python, dependencies, and the dataset)

## Dataset
- `dft-road-casualty-statistics-collision-2024.csv` can be download from the official dataset from the [UK Department for Transport Open Data Portal](https://data.gov.uk/dataset/cb7ae6f0-4be6-4935-9277-47e5ce24a11f/road-safety-data).

- Place the CSV file in the same directory as the 4 other python modules Python scripts before running the application.

## How to run
- Step one: Ensure all the python modules and data set are in the same folder
- Step two: Run "pip install -r requirements.txt" in the command line to install all the needed python libraries
- Step three: Open then run main.py

## Troubleshooting
- ModuleNotfoundError: No module named "pandas": Try re-running "pip install -r requirements.txt" in command line and if that doesn't work try installing it separately by running "pip install pandas" in command line.
- ModuleNotfoundError: No module named "matplotlib": Try re-running "pip install -r requirements.txt" in command line and if that doesn't work try installing it separately by running "pip install matplotlib" in command line.
- ModuleNotfoundError: No module named "numpy": Try re-running "pip install -r requirements.txt" in command line and if that doesn't work try installing it separately by running "pip install numpy" in command line.
- FileNotFoundError: Ensure that the CSV dataset is in the same folder as all the python modules.
