import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)
import tkinter as tk
from tkinter import ttk, font as tkfont
import os
import sys



#imorting class and functions from the other 3 modules that handle data, risk calculation and chart visualisation
from data_loader import load_dataset, get_dd_options
from risk_engine  import calc_risk, COL_DIS_NAME, DIS_TO_COL
from chart_engine import build_chart, clear_chart


DATASET = "dft-road-casualty-statistics-collision-2024.csv"
DATASET_PTH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATASET)

#constant for the names of the colours stored as hex codes
C_BG = "#0a1628"
C_CARD= "#0d1e35"
C_CARD2= "#0f2540"
C_ACCENT = "#00b899"
C_ACCENT_DARK = "#008a72" 
C_TEXT = "#e0e8f0"
C_SUBTEXT = "#8a9bb0"
C_RED = "#ff6b6b"
C_WHITE = "#ffffff"
C_BORDER = "#1a3050"

#constant for the fontsize so it's easy to adjust the UI scaling
F_TITLE = 14
F_SEC = 11
F_LAB = 9
F_SMALL= 8
F_PER = 18

#class for the main road risk applications, responsible for the ui creation and everything else
class RoadRiskApp(tk.Tk):
  def __init__(self):
    super().__init__() #initialises an os window
    self.tk.call('tk', 'scaling', 1.25)

    #os window configuration
    self.title("Road Accident Risk Predictor")
    self.configure(bg=C_BG)
    self.resizable(True, True)
    self.geometry("620x980")
    self.minsize(520, 800)

    #Loads the dataset into a pandas DataFrame on startup
    self.df = load_dataset(DATASET_PTH)

    #controls the visualisations section buttons
    self.filter_vars={}
    self.viz_column_var = tk.StringVar(value="Light Condition")
    self.chart_type_var = tk.StringVar(value="bar")

    #Ui builder, calling each section in order of apperance
    self._scroll_cont()
    self._head()
    self._filters()
    self._risk_output()
    self._visualisation()
    self._about()
    self._analyse()

  #funtion to creade a scrollabe conintainer becasue tkinter doesn't nativly support scrollling frames 
  def _scroll_cont(self):
    #outer frame fills the whole windows and holds the canvas and scrolbar together, side to side
    outer = tk.Frame(self, bg=C_BG)
    outer.pack(fill="both", expand=True)

    #highlightness=0 removes the unastetic looking white border
    self.canvas_scroll = tk.Canvas(outer, bg=C_BG, highlightthickness=0)
    
    #linked the canvas and the scrollbar together using the y scroll comman
    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self.canvas_scroll.yview)
    self.canvas_scroll.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    self.canvas_scroll.pack(side="left", fill="both", expand=True)

    #frame to holds all visible UI sections
    self.content = tk.Frame(self.canvas_scroll, bg=C_BG )
    self.canvas_scroll.create_window((0, 0),window=self.content,  anchor="nw")

    #updates the canvas's scroll region so the scroll bar knows the new height when resizing
    self.content.bind("<Configure>", lambda e: self.canvas_scroll.configure
                      (scrollregion=self.canvas_scroll.bbox("all"))
                     )

    #mousewheel scrolling for macOS, Linux and windows 
    self.canvas_scroll.bind_all("<MouseWheel>",
          lambda e: self.canvas_scroll.yview_scroll(-1 * (e.delta // 120), "units"))
    self.canvas_scroll.bind_all("<Button-4>",
          lambda e: self.canvas_scroll.yview_scroll(-1, "units"))
    self.canvas_scroll.bind_all("<Button-5>",
          lambda e: self.canvas_scroll.yview_scroll(1, "units"))
  
  #function for the header, to display the app name and a disclaimer
  def _head(self):
    head_f = tk.Frame(self.content, bg=C_CARD, pady=12, padx=16)
    head_f.pack(fill="x", pady=(0,2))

    #main app name label
    tk.Label(
      head_f, text="Road Accident Risk Predictor",
      bg=C_CARD, fg=C_WHITE, font=("Helvetica", F_TITLE, "bold"),
      anchor="w").pack(anchor="w")

    #disclaimer label 
    tk.Label(
      head_f, text="This tool makes estimations based on historical data."
      "It doesn't make individual predictions.",
      bg=C_CARD, fg=C_RED, font=("Helvetica", F_SMALL, "italic"), anchor="w",
      wraplength=560, justify="left",).pack(anchor="w", pady=(4, 0))
    
  #function for creating the six dropdown menues for users to select their filters
  def _filters(self):
        section = self._make_sec(self.content, "FILTERS")
        #each tuple is label shown in the UI, then the column name in the dataset
        FILTER_DEFS = [
            ("WEATHER","weather_conditions"),
            ("ROAD TYPE","road_type"),
            ("SEASON","season"),
            ("DAY OF THE WEEK","day_of_week"),
            ("LIGHT CONDITION","light_conditions"),
            ("MONTH","month"),
        ]

        #Tkinter grid geometry manager to arrange the dowpdowns in equal width columns 
        grid_frame = tk.Frame(section, bg=C_CARD)
        grid_frame.pack(fill="x", padx=14, pady=(0, 10))
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        for idx, (display_label, col_name) in enumerate(FILTER_DEFS):
            #formular for getting the row and column values
            row_idx = idx // 2
            col_idx = idx  % 2

            #uses a dictionary for the dropdown from the data_loader module I previously made 
            options_dict = get_dd_options(col_name)
            option_labels = list(options_dict.keys())

            #default value is any when no filter has been selected
            var = tk.StringVar(value="Any") 
            self.filter_vars[col_name] = var

            #stores the options dictionary as a StringVar so _analyse can retrieve it and the selected label without needing a seperate data structure
            var._options = options_dict 

            #using a cell frame as a cointainer for the label and dropdown to give every filter its padded regiomn within the grid
            cell = tk.Frame(grid_frame,bg=C_CARD,pady=4, padx=6)
            cell.grid(row=row_idx, column=col_idx , sticky="ew", padx=4, pady=4)

            #this displays the filter label above the dropdown
            tk.Label(cell, text=display_label, bg=C_CARD, fg=C_SUBTEXT,font=(
               "Helvetica", F_SMALL, "bold"
               ),anchor="w",).pack(fill="x")

            #creates a dropdown widget
            menu = tk.OptionMenu(cell, var, *option_labels)
            #apply dark styling
            self._style_menu(menu)
            menu.pack(fill="x")

        #action buttons
        btn_frame = tk.Frame(section, bg=C_CARD)
        btn_frame.pack(fill="x", padx=14, pady=(4, 14))

        #buttons to start the risk analysis and chart updates
        tk.Button(
            btn_frame,
            text="▶  ANALYSE RISK",
            command=self._analyse,
            bg=C_ACCENT, fg=C_WHITE, activebackground=C_ACCENT_DARK,
            font=("Helvetica", F_LAB, "bold"),
            relief="flat", cursor="hand2",
            padx=18, pady=8,
        ).pack(side="left", padx=(0, 10))

        #button to reser all the dropdown menus to the default "Any" state
        tk.Button(
            btn_frame,text="⟳  RESET FILTERS",command=self._reset,bg=C_ACCENT,
            fg=C_WHITE, activebackground=C_ACCENT_DARK,font=(
            "Helvetica", F_LAB, "bold"
            ),relief="flat", cursor="hand2",padx=18, pady=8,).pack(side="left") 

  
  #function to display the result of the calculated risk prediction
  def _risk_output(self):
        sct = self._make_sec(self.content, "RISK OUTPUT")
        inr = tk.Frame(sct, bg=C_CARD, padx=14, pady=0)
        inr.pack(fill="x")

        #displays the risk bar row
        bar_row = tk.Frame(inr, bg=C_CARD)
        bar_row.pack(fill="x", pady=(0, 10))

        #draws the risk bar using different coloured rectangles to form a gradient
        self.risk_bar_canvas = tk.Canvas(bar_row, height=30, bg=C_CARD,highlightthickness=0,)
        self.risk_bar_canvas.pack(side="left", fill="x", expand=True)

        self.risk_label_var = tk.StringVar(value="- %")
        self.risk_label_widget = tk.Label(bar_row,textvariable=self.risk_label_var,
            bg=C_CARD, fg=C_RED,font=("Helvetica", F_PER, "bold"),width=14,
            anchor="e",)
        self.risk_label_widget.pack(side="right")

        #displays the contribuiting factors and precautions
        dtl_pnl = tk.Frame(inr, bg=C_CARD2, padx=12,pady=10)
        dtl_pnl.pack( fill="x", pady=(0, 14) )

        tk.Label(dtl_pnl, text="Contributing Factors:", bg=C_CARD2, fg=C_WHITE,
            font=("Helvetica", F_LAB, "bold italic"),anchor="w",).pack(anchor="w")

        #fills the factor lables with the appropriate factors after each analysis
        self.fact_frm = tk.Frame(dtl_pnl, bg=C_CARD2)
        self.fact_frm.pack(fill="x", padx=8)

        tk.Label(
            dtl_pnl, text="Precautions:", bg=C_CARD2, fg=C_WHITE,
          font=("Helvetica", F_LAB, "bold italic"), anchor="w",).pack(anchor="w", pady=(8, 0))

        #fills the precaution lables with the appropriate precautions after each analysis
        self.pre_frm = tk.Frame(dtl_pnl, bg=C_CARD2)
        self.pre_frm.pack(fill="x", padx=8)
 
 #function to display the matplotlib chart from the chart_engine section
  def _visualisation(self):
        sct = self._make_sec(self.content, "RISK VISUALISATION")
        inr = tk.Frame(sct, bg=C_CARD,padx=14, pady=6)
        inr.pack(fill="x")

        #matplotlib embedds the chart into this region of the tkinter layout
        self.chart_frame = tk.Frame(inr, bg=C_CARD)
        self.chart_frame.pack(side="left", fill="both", expand=True)

        cont = tk.Frame(inr, bg=C_CARD, padx=10)
        cont.pack(side="right", anchor="n")
       
        #ensures the buttons match the visualisation options
        viz_options = list(COL_DIS_NAME.values())

        for option in viz_options:
            rb = tk.Radiobutton(cont, text=option,variable=self.viz_column_var, #all buttons share one String var
                value=option, command=self._update_chart # redraws the charts when a button is clicked
                , bg=C_CARD, fg=C_TEXT,
                selectcolor=C_ACCENT, activebackground=C_CARD,
                font=("Helvetica", F_SMALL),anchor="w",)
            rb.pack(anchor="w", pady=2)

        #allows the user to switch between a bar chart or a line graph
        type_row = tk.Frame(sct, bg=C_CARD)
        type_row.pack(fill="x", padx=14, pady=(4, 12))

        for label, val in [("☰ BAR CHART", "bar"), ("⏦ LINE GRAPH", "line")]:
            tk.Radiobutton(type_row, text=label, variable=self.chart_type_var,
                value=val, command=self._update_chart, bg=C_CARD, fg=C_TEXT,
                selectcolor=C_ACCENT, activebackground=C_CARD,
                font=("Helvetica", F_SMALL, "bold"),).pack(side="left", padx=(0, 20))

  #function to display the about section(ethics, legality and how risk is calculated)
  def _about(self):
        sct= self._make_sec(self.content, "ABOUT AND ETHICS")
        inr =tk.Frame(sct, bg=C_CARD, padx=16, pady=10)
        inr.pack(fill="x")

        #displays an explanation of how the risk is calculated
        tk.Label(inr, text="How the risk prediction is calculated:",bg=C_CARD,
                 fg=C_WHITE, font=("Helvetica", F_LAB, "bold italic"),anchor="w",
        ).pack(anchor="w")

        #text explanation of how risk is calculated
        mtd_txt = (
            "For each condiction selected (e.g. 'Raining'), the tool calculates "
            "the proportion of all 2024 UK collisions that occurred under that "
            "condition. This is then compared to the expected baseline proportion "
            "(equal distribution across all categories) to produce a risk "
            "multiplier. The multipliers from all the selected conditions are then combined "
            "using a weighted geometric mean and normalised to a 0-100% scale. "
            "A score of 50% represents average baseline risk."
        )
        tk.Label(inr,text=mtd_txt,bg=C_CARD, fg=C_RED,font=(
            "Helvetica", F_SMALL, "italic"
            ), anchor="w", wraplength=560, justify="left",).pack(
                anchor="w", pady=(4, 10))

        #displays the data and privacy information
        tk.Label(inr, text="Data and privacy", bg=C_CARD, fg=C_WHITE,
            font=("Helvetica", F_LAB, "bold"), anchor="w",).pack(anchor="w")

        #list of data and privacy information
        pvcy_pnts = [
            "Accident data used in this software is from the UK Department "
            "for Transport (DfT) Road Safety Data.",
            "All data processing is done locally on your device.",
            "No personal information is collected or stored at any point.",
        ]
        for point in pvcy_pnts:
            tk.Label(inr, text=f"  •  {point}", bg=C_CARD, fg=C_TEXT,
                font=("Helvetica", F_SMALL), anchor="w",wraplength=560,
                justify="left",).pack(anchor="w")

        #explains the ethics and limitations of the risk generated
        tk.Label(
            inr, text="Ethics and Limitations",
            bg=C_CARD, fg=C_WHITE,
            font=("Helvetica", F_LAB, "bold"), anchor="w",
        ).pack(anchor="w", pady=(8, 0))

        #list of ethics and limitations of the risk generted
        eth_pnts = [
            "Risk estimates are advisory, they are to aid your judgement"
            "as a driver, not replace it.",
            "Risk estimates are calculated using historical data, so they may "
            "not reflect the latest changes in road conditions or legislation.",
            "Data bias: accident reports may over or under represent certain "
            "areas. The tool does not rank or stigmatise any location.",
            "Data source: UK Department for Transport - Road Safety Open "
            "Dataset 2024. Licensed under the Open Government Licence v3.0.",
        ]
        for point in eth_pnts:
            tk.Label( inr, text=f"  •  {point}", bg=C_CARD, fg=C_TEXT,
                font=("Helvetica", F_SMALL), anchor="w",
                wraplength=560, justify="left",).pack(anchor="w")
        tk.Frame(inr, bg=C_CARD, height=10).pack()      

  #function for analysing the current input in the filter dropdown and passing it to the risk_engine module to calculate the risk and update the charts and risk bar display
  def _analyse(self):
        rsd_filters = {}
        for col_name, str_var in self.filter_vars.items():
            selected_lab = str_var.get()
            options_dict = str_var._options
            code = options_dict.get(selected_lab)
            rsd_filters[col_name] = code
        
        #returns an object with with all the data needed to output a risk level from th risk_engine module
        result = calc_risk(self.df, rsd_filters)
        self._update_risk_display(result)
        self._update_chart()

  #funtion for reseting all the filters to any when the reset button is clicked
  def _reset(self):
        for str_var in self.filter_vars.values():
            str_var.set("Any")
        self._analyse()

  #function for updating the risk output bar, percentage, contribuiting factors and precautions when an analysis is rerun
  def _update_risk_display(self, result):
        self.risk_bar_canvas.update_idletasks()
        w = self.risk_bar_canvas.winfo_width() or 350
        h = 30

        self.risk_bar_canvas.delete("all") #clears the previous bar drawing

        #draws the colour gradient bar using 100 small rectangules of different interpolating colours 
        STEPS = 100
        step_w = w / STEPS
        for i in range(STEPS):
            t = i / STEPS #position of the percentage on the bar normalised

            #colour interpolation of green to amber and then amber to red
            if t < 0.5:
                t2 = t * 2
                r = int(0 + t2 * 220)
                g = int(200 + t2 * (200 - 200))
                b = int(80 - t2 * 80)
            else:
                t2 = (t - 0.5) * 2
                r = int(220)
                g = int(200 - t2 * 150)
                b = int(0)
            colour = f"#{r:02x}{g:02x}{b:02x}"
            x0 = i * step_w
            #removes any little gaps between the tiny 100 rectangles
            self.risk_bar_canvas.create_rectangle(x0, 0, x0 + step_w + 1, h,
                fill=colour, outline="",)

        #draws a tick mark at the end of the risk calculation
        tick_x = int(result.percentage/100 * w)
        self.risk_bar_canvas.create_rectangle(tick_x - 2, 0, tick_x + 2, h,
            fill=C_WHITE, outline="",)

        #updates the text percentage 
        lev_clr = {"Low": "#00c87a", "Medium": "#f0a000", "High": C_RED} #colour codes the percentage to match the risk level
        colour = lev_clr.get(result.level,C_WHITE)
        self.risk_label_widget.configure(fg=colour)
        self.risk_label_var.set(f"{result.percentage}% ({result.level.upper()})")

        #destroys all current child widgets to display a new child widget containing a new analysis
        for widget in self.fact_frm.winfo_children():
            widget.destroy()

        if result.factors:
            for factor in result.factors:
                mult = factor["multiplier"]

                #colour codes the multipliers if they are above or below the baseline
                if mult >= 1.2:
                    mult_clr = C_RED
                elif mult <= 0.8:
                    mult_clr = "#00c87a"
                else:
                    mult_clr = C_TEXT

                line_text = f"• {factor['label']}: {mult} x baseline risk"
                tk.Label(self.fact_frm,text=line_text,bg=C_CARD2, fg=mult_clr,
                         font=("Helvetica", F_SMALL, "italic"),anchor="w",).pack(anchor="w")
        else:
            #displays a message to the user when they havae no risk selected
            tk.Label(self.fact_frm,text="• No conditions selected: Showing baseline.",
                bg=C_CARD2, fg=C_SUBTEXT, font=("Helvetica", F_SMALL, "italic"),
                anchor="w",).pack(anchor="w")
        
        #rebuilds the list of precautions 
        for widget in self.pre_frm.winfo_children():
            widget.destroy()

        for prec in result.precautions:
            tk.Label(self.pre_frm, text=f"• {prec}", bg=C_CARD2, fg=C_TEXT,
                font=("Helvetica", F_SMALL, "italic"),anchor="w", 
                wraplength=430, justify="left",).pack(anchor="w") 
  
  #funtion to redraw the matplotlib chart embedded into tkinter
  def _update_chart(self):
        #fetches the display name of a column and converts it to the column name using another function from the risk_engine module
        display_name = self.viz_column_var.get()
        column = DIS_TO_COL.get(display_name, "light_conditions")
        chart_type = self.chart_type_var.get()

        #checks if the the current charted column has a user selected filter applied then applies a filter if so
        highlight_val = None
        if column in self.filter_vars:
            str_var = self.filter_vars[column]
            selected_lbl = str_var.get()
            options = str_var._options
            highlight_val = options.get(selected_lbl)
       
        #removes the former matplotlib chart from the char_frame
        clear_chart(self.chart_frame)

        canvas = build_chart(par_frame = self.chart_frame,df = self.df,
            brk_column = column, chart_type = chart_type,highlight_value = highlight_val,)
        canvas.get_tk_widget().pack(fill="both", expand=True)
  
  #function to make a reusable section
  def _make_sec(self, parent,title):
        card = tk.Frame(parent, bg=C_CARD, pady=0)
        card.pack(fill="x", padx=10, pady=6)

        title_bar = tk.Frame(card, bg=C_CARD)
        title_bar.pack(fill="x", padx=14, pady=(10, 6))

        #for labeling section headings
        tk.Label(title_bar,text=title,bg=C_CARD, fg=C_WHITE,font=("Helvetica", F_SEC, "bold"),
            anchor="w",).pack(side="left")
        
        #displays an underline under the headings 
        tk.Frame(card, bg=C_ACCENT, height=2).pack(fill="x", padx=14)
        return card
  
  #function for applying styling to the dropdown menues
  def _style_menu(self,menu):
        #styles the dropdown button
        menu.configure( bg=C_CARD2, fg=C_TEXT, activebackground=C_ACCENT,
            activeforeground=C_WHITE, relief="flat",highlightthickness=1, 
            highlightbackground=C_BORDER, font=("Helvetica", F_LAB), anchor="w",
            indicatoron=True, bd=0,)
        
        #styles the dropdown menue that appears then the button is clicked
        menu["menu"].configure(bg=C_CARD2, fg=C_TEXT,activebackground=C_ACCENT,
                               activeforeground=C_WHITE,font=("Helvetica", F_LAB),
            relief="flat",)
#runs the application
app = RoadRiskApp()
app.mainloop() #starts the tkinter event loop until the os window is closed