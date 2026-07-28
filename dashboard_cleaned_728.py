#imports
import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime
import requests
import json
import os

SAVE_FILE = "dashboard_save.json"

calendar.setfirstweekday(calendar.SUNDAY)

#setup
root = tk.Tk()
style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Custom.Horizontal.TProgressbar",
    troughcolor="#1e1e1e",
    background="#4CAF50"
)

#tab title
root.title("Summer Dashboard")
#scale
#root.geometry("1400x1000")
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.geometry(f"{screen_w}x{screen_h}")
root.configure(bg= "#111111")

scale = min(screen_w / 1400, screen_h / 1000)

main_frame = tk.Frame(root, bg ="#111111")
main_frame.pack(fill ="both", expand =True, padx=20, pady =20)

now = datetime.now()
today= now.day
display_month = now.month
display_year = now.year

#load data
def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {}

#Save data
def save_data():
    data = {}
    data["goals"] = [var.get() for var in goal_vars]
    data["daily"] = [var.get() for var in daily_vars]
    data["progress"] = [
        (e[0].get(), e[1].get()) for e in progress_entries
    ]
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def redraw_calendar():

    # update title
    monthstr = calendar.month_name[display_month].upper()

    calendar_title.config(
        text=monthstr + " " + str(display_year)
    )

    # remove old calendar cells
    for widget in calendar_frame.winfo_children():
        widget.destroy()

    # redraw calendar
    draw_calendar()

def create_card(parent):

    card = tk.Frame(
        parent,
        bg="#2b2b2b",
        padx=15,
        pady=15
    )

    card.pack(
        fill="x",
        padx=15,
        pady=10
    )
    return card

#update progress
def update_total_progress():

    completed_goals = 0

    for var in goal_vars:
        if var.get():
            completed_goals += 1

    goal_percent = (
        completed_goals / len(goal_vars)
    ) * 100

    current_total = 0
    goal_total = 0

    for i, (current_entry, goal_entry) in enumerate(progress_entries):
        try:
            current = int(current_entry.get())
            goal = int(goal_entry.get())
            current_total += current
            goal_total += goal
            progress_bars[i]["maximum"] = goal
            progress_bars[i]["value"] = current
        except ValueError:
            pass
    
    
    habit_percent = (
        current_total / goal_total
    ) * 100

    progress_percent = int(
        (goal_percent + habit_percent) / 2
    )

    total_bar["value"] = progress_percent

    percent_label.config(
        text=f"{progress_percent}%"
    )
    save_data()
    
#positioning and making sections
left_frame = tk.Frame(
    main_frame,
    bg="#1e1e1e",
    width=300
)
center_frame = tk.Frame(
    main_frame,
    bg="#1e1e1e",
    width=350
)
right_frame = tk.Frame(
    main_frame,
    bg="#1e1e1e",
    #width=400
)

left_frame.pack(
    side="left",
    fill="y",
    padx=(0, 15)
)
center_frame.pack(
    side="left",
    fill="y",
    padx=(0, 15)
)
right_frame.pack(
    side="right",
    fill="both",
    expand=True
    #padx =(0, 15)
)

#write title summer
title = tk.Label(
    root,
    text="SUMMER 2026",
    font=("Arial", int(30 * scale), "bold")
)
title.pack(pady=10)

#create card
days_card = create_card(left_frame)

#add title
days_title = tk.Label(
    days_card,
    text="DAYS LEFT",
    bg="#2b2b2b",
    fg="white",
    font=("Arial", int(18 * scale), "bold")
)
days_title.pack(anchor="w")

#calculate days
today_date = datetime.now()

school_start = datetime(2026, 8, 10)

days_left = (school_start - today_date).days

#display
days_label = tk.Label(
    days_card,
    text=f"{days_left} days until school",
    bg="#2b2b2b",
    fg="#4CAF50",
    font=("Arial", int(24 * scale), "bold")
)
days_label.pack(pady=10)


#create card
focus_card = create_card(left_frame)

focus_title = tk.Label(
    focus_card,
    text="DAILY FOCUS",
    bg="#2b2b2b",
    fg="white",
    font=("Arial", int(18 * scale), "bold")
)
focus_title.pack(anchor="w")

daily_goals = [
    "Arduino lesson(s)",
    "Work on coding",
    "Watched a marvel movie?"
]

daily_vars = []

for goal in daily_goals:
    var = tk.BooleanVar()
    check = tk.Checkbutton(
        focus_card,
        text=goal,
        variable=var,
        bg="#2b2b2b",
        fg="white",
        font=("Arial", int(16 * scale)),
        selectcolor="#2b2b2b"
    )
    check.pack(anchor="w", pady=2)
    daily_vars.append(var)

#create card
weather_card = create_card(left_frame)

#write title
weather_title = tk.Label(
    weather_card,
    text="WEATHER",
    bg="#2b2b2b",
    fg="white",
    font=("Arial", int(18 * scale), "bold")
)
weather_title.pack(anchor="w")

#find real weather
def get_weather():

    latitude = 28.09
    longitude = -80.57

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&current=temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m"
        "&daily=temperature_2m_max,temperature_2m_min"
        "&temperature_unit=fahrenheit"
        "&wind_speed_unit=mph"
        "&forecast_days=1"
    )

    try:

        response = requests.get(url)
        data = response.json()

        temp = round(
            data["current"]["temperature_2m"]
        )

        code = data["current"]["weather_code"]
        
        humidity = data["current"]["relative_humidity_2m"]

        wind = round(
            data["current"]["wind_speed_10m"]
        )

        high = round(
            data["daily"]["temperature_2m_max"][0]
        )

        low = round(
            data["daily"]["temperature_2m_min"][0]
        )

        weather_codes = {

            0: ("☀", "Sunny"),

            1: ("🌤", "Mostly Clear"),
            2: ("⛅", "Partly Cloudy"),
            3: ("☁", "Cloudy"),

            45: ("🌫", "Fog"),
            48: ("🌫", "Fog"),

            51: ("🌦", "Light Drizzle"),
            53: ("🌦", "Drizzle"),
            55: ("🌦", "Heavy Drizzle"),

            61: ("🌧", "Light Rain"),
            63: ("🌧", "Rain"),
            65: ("🌧", "Heavy Rain"),

            71: ("❄", "Light Snow"),
            73: ("❄", "Snow"),
            75: ("❄", "Heavy Snow"),

            95: ("⛈", "Thunderstorm")
        }

        icon, description = weather_codes.get(
            code,
            ("❓", "Unknown")
        )

        return (
            f"{icon} {temp}°F\n\n"
            f"{description}\n"
            f"Humidity: {humidity}%\n"
            f"Wind: {wind} mph\n\n"
            f"H {high}°  L {low}°"
        )

    except Exception as e:
        
        print("Weather Error", e)

        return "❌\nWeather Error"

#update weather
def refresh_weather():

    weather_label.config(
        text=get_weather()
    )

    root.after(
        900000,
        refresh_weather
    )

#write info
weather_label = tk.Label(
    weather_card,
    text=get_weather(),
    bg="#2b2b2b",
    fg="white",
    font=("Arial", int(18 * scale))
)
weather_label.pack(pady=10)

#create progression tracking and calculating
goal_completion = [
    False,
    False,
    False,
    False,
    False
]

trip_completion = [
    False,
    True,
    False,
    False
]

completed = (
    sum(goal_completion)
    + sum(trip_completion)
)

total = (
    len(goal_completion)
    + len(trip_completion)
)

progress_percent = round(
    completed / total * 100
)

#create card
progress_card = create_card(left_frame)

#write title
progress_title = tk.Label(
    progress_card,
    text="TOTAL PROGRESS",
    bg ="#2b2b2b",
    fg="white",
    font=("Arial", int(18 * scale), "bold")
)
progress_title.pack(anchor="w")

#add bar
total_bar = ttk.Progressbar(
    progress_card,
    style="Custom.Horizontal.TProgressbar",
    length=220,
    maximum=100,
    value=progress_percent
)
total_bar.pack(pady=15)

#add percentage
percent_label = tk.Label(
    progress_card,
    text=f"{progress_percent}%",
    bg="#2b2b2b",
    fg="white",
    font=("Arial", int(20 * scale), "bold")
)
percent_label.pack()

#create progress button
update_button = tk.Button(
    progress_card,
    text="Update Progress",
    command=update_total_progress,
    #bg="#3A6EA5", 
    #fg="black",
    #activebackground="#4A7EB5",
    #activeforeground="white",
    #relief="flat",
    #borderwidth=0
)
update_button.pack(pady=10)

#create card
goal_card = create_card(center_frame)

#write title goals
goals_title = tk.Label(
    goal_card,
    text="GOALS",
    bg ="#2b2b2b",
    fg ="white",
    font=("Arial", int(22 * scale), "bold")
)
goals_title.pack()

#list goals
goals = [
    "Watch all marvel movies",
    "make a arduino or pi project",
    "Make money",
    "redesign upstairs",
    "Prepare nerdy docs for next year"
]

goal_vars = []

for goal in goals:

    var = tk.BooleanVar()

    check = tk.Checkbutton(
        goal_card,
        text=goal,
        variable=var,
        command=update_total_progress,
        bg="#2b2b2b",
        fg="white",
        #selectcolor="#2b2b2b",
        #activebackground="#2b2b2b",
        font=("Arial", int(20 * scale))
    )

    check.pack(anchor="w")

    goal_vars.append(var)

#create card
mini_progress_card = create_card(center_frame)

#write progress title
progress_title = tk.Label(
    mini_progress_card,
    text="PROGRESS",
    bg ="#2b2b2b",
    fg ="white",
    font=("Arial", int(22 * scale), "bold")
)
progress_title.pack(pady= 15)

#list of progession
progress = {
    "Coding course": (41, 134),
    "Arduino course": (27, 150),
    "Marvel movies": (5, 45)
    }

progress_entries = []
progress_bars = []

#writes out all progression
for habits, (current, goal) in progress.items():

    frame = tk.Frame(mini_progress_card, bg ="#2b2b2b")
    frame.pack(fill="x",padx =20, pady=10)
    
    #write
    label = tk.Label(
        frame,
        text=habits,
        bg ="#2b2b2b",
        fg ="white",
        width =26,
        font=("Arial", int(16 * scale), "bold"),
        anchor="w"
    )
    #label.pack(side = "left")
    label.pack(anchor="w")
    
    #allow bar to go under
    bottom_frame = tk.Frame(
        frame,
        bg="#2b2b2b"
    )
    bottom_frame.pack(fill="x")
    
    #make bar
    bar = ttk.Progressbar(
        bottom_frame,
        style="Custom.Horizontal.TProgressbar",
        length=300,
        maximum=goal,
        value=current
    )
    bar.pack(side="left", padx=10)
    
    #display editable fractions
    current_entry = tk.Entry(
        frame,
        width=4,
        font=("Arial", int(12 * scale)),
        #bg="#444444",
        #fg="white",
        #insertbackground="white",
        #relief="flat"
    )
    current_entry.insert(0, str(current))
    current_entry.pack(side="left", padx=5)
    
    slash = tk.Label(
    frame,
    text="/",
    bg="#2b2b2b",
    fg="white"
    )
    slash.pack(side="left")
    
    goal_entry = tk.Entry(
        frame,
        width=4,
        font=("Arial", int(12 * scale)),
        #bg="#444444",
        #fg="white",
        #insertbackground="white",
        #relief="flat"
    )
    goal_entry.insert(0, str(goal))
    goal_entry.pack(side="left", padx=5)
    
    progress_entries.append(
    (current_entry, goal_entry)
    )

    progress_bars.append(bar)

#allow switchable months
def previous_month():
    global display_month

    if display_month > 1: #5
        display_month -= 1

    redraw_calendar()


def next_month():
    global display_month

    if display_month < 12: #8
        display_month += 1

    redraw_calendar()


#create card
calendar_card = create_card(right_frame)

#month buttons
button_frame = tk.Frame(
    calendar_card,
    bg="#2b2b2b"
)
button_frame.pack()

prev_button = tk.Button(
    button_frame,
    text="<",
    command=previous_month,
    #bg="#3A6EA5",
    #fg="white",
    #activebackground="#4A7EB5",
    #activeforeground="white",
    #relief="flat",
    #borderwidth=0
)
prev_button.pack(side="left")

next_button = tk.Button(
    button_frame,
    text=">",
    command=next_month,
    #bg="#3A6EA5",
    #fg="white",
    #activebackground="#4A7EB5",
    #activeforeground="white",
    #relief="flat",
    #borderwidth=0
)
next_button.pack(side="left")

#change month string when switch
monthstr = calendar.month_name[display_month].upper()

#calendar title
calendar_title = tk.Label(
    calendar_card,
    text= monthstr + " " + str(display_year),
    bg="#2b2b2b",
    fg="white",
    font=("Arial", int(26 * scale), "bold")
)
calendar_title.pack(pady=15)

#calendar grid
calendar_frame = tk.Frame(
    calendar_card,
    bg="#1e1e1e"
)
calendar_frame.pack(pady=10)

#list events and start/end times
events = [
    {
        "name": "Cruise",
        "start_month": 5,
        "start_day": 31,
        "end_month": 6,
        "end_day": 6
    },
    
    {
        "name": "Banana Ball",
        "start_month": 5,
        "start_day": 29,
        "end_month": 5,
        "end_day": 29
    },
    
    {
        "name": "charleston",
        "start_month": 6,
        "start_day": 12,
        "end_month": 6,
        "end_day": 15
    },
    
    {
        "name": "Lake Norman",
        "start_month": 6,
        "start_day": 15,
        "end_month": 6,
        "end_day": 21
    }
]

def draw_calendar():

    #day headers
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    for col, day in enumerate(days):

        label = tk.Label(
            calendar_frame,
            text=day,
            bg="#1e1e1e",
            fg="#aaaaaa",
            font=("Arial", int(14 * scale), "bold"),
            width=6,
            height=2
        )

        label.grid(row=0, column=col)

    cal = calendar.monthcalendar(
        display_year,
        display_month
    )

    for row_num, week in enumerate(cal):

        for col_num, day in enumerate(week):

            event_name = None
            has_event = False

            if day != 0:
                for event in events:

                    if event["start_month"] == event["end_month"]:

                        if (
                            display_month == event["start_month"]
                            and event["start_day"] <= day <= event["end_day"]
                        ):
                            has_event = True
                            event_name = event["name"]
                            break

                    else:

                        if (
                            (display_month == event["start_month"] and day >= event["start_day"])
                            or
                            (display_month == event["end_month"] and day <= event["end_day"])
                        ):
                            has_event = True
                            event_name = event["name"]
                            break

            if day == 0:
                text = ""
                bg_color = "#1e1e1e"

            else:

                text = str(day)

                if has_event:
                    text += "\n" + event_name

                if (
                    day == today
                    and display_month == now.month
                ):
                    bg_color = "#4CAF50"

                elif has_event:
                    bg_color = "#3A6EA5"

                else:
                    bg_color = "#2b2b2b"

            label = tk.Label(
                calendar_frame,
                text=text,
                bg=bg_color,
                fg="white",
                width=6,
                height=3,
                font=("Arial", int(14 * scale)),
                wraplength= 50,
                justify="center"
            )

            label.grid(
                row=row_num + 1,
                column=col_num,
                padx=4,
                pady=4
            )

draw_calendar()

#create card
event_card = create_card(right_frame)

#create events
events_frame = tk.Frame(
    event_card,
    bg="#2b2b2b"
)

events_frame.pack(
    fill="x",
    padx=20,
    pady=20
)

events_title = tk.Label(
    events_frame,
    text="EVENTS",
    bg="#2b2b2b",
    fg="white",
    font=("Arial", int(20 * scale), "bold")
)
events_title.pack(anchor="w")

#make non accuring events visible
today_full = datetime.now().date()

visible_events = [
    e for e in events
    if datetime(2026, e["end_month"], e["end_day"]).date() >= today_full
]

#for date, event in events.items():
for event in visible_events:
    
    start = event["start_day"]
    end = event["end_day"]
    name = event["name"]

    event_month = event["start_month"]

    if event_month == 5:
        month_name = "May"
    elif event_month == 6:
        month_name = "June"
    elif event_month == 7:
        month_name = "July"
    elif event_month == 8:
        month_name = "August"

    if start == end:
        date_text = f"{month_name} {start}"

    else:
        date_text = f"{month_name} {start}-{end}"

    event_label = tk.Label(
        events_frame,
        text=f"{date_text} • {name}",
        bg="#2b2b2b",
        fg="white",
        font=("Arial", int(14 * scale)),
        padx=10,
        pady=6,
        anchor="w"
    )

    event_label.pack(
        fill="x",
        pady=6/len(visible_events) if visible_events else 0
    )

#load saved data
saved = load_data()

if "goals" in saved:
    for var, val in zip(goal_vars, saved["goals"]):
        var.set(val)

if "daily" in saved:
    for var, val in zip(daily_vars, saved["daily"]):
        var.set(val)

if "progress" in saved:
    for (current_entry, goal_entry), (cur_val, goal_val) in zip(progress_entries, saved["progress"]):
        current_entry.delete(0, tk.END)
        current_entry.insert(0, cur_val)
        goal_entry.delete(0, tk.END)
        goal_entry.insert(0, goal_val)

update_total_progress()

refresh_weather()

root.mainloop()