#imports
import tkinter as tk
from tkinter import ttk
import calendar
from datetime import date, datetime, timedelta
import requests
import json
import os

SAVE_FILE = "json/dashboard_save_periods.json"

calendar.setfirstweekday(calendar.SUNDAY)

#extra variables
PERIOD_SUMMER = "summer"
PERIOD_SCHOOL_YEAR = "school_year"

SCHOOL_YEAR_START = date(2026, 8, 10)
SCHOOL_YEAR_END = date(2027, 5, 21)

SUMMER_START = date(2026, 5, 25)
SUMMER_END = date(2026, 8, 9)

PERIOD_LABELS = {PERIOD_SUMMER: "Summer", PERIOD_SCHOOL_YEAR: "School Year"}

CALENDAR_YEAR_SPAN = 2
CURRENT_YEAR = datetime.now().year
MIN_YEAR = CURRENT_YEAR - CALENDAR_YEAR_SPAN
MAX_YEAR = CURRENT_YEAR + CALENDAR_YEAR_SPAN

ACTIVE_EVENT_COLOR = "#3A6EA5"
OTHER_EVENT_COLOR = "#6a4c93"
TODAY_COLOR = "#4CAF50"


def is_school_year(d):
    return SCHOOL_YEAR_START <= d <= SCHOOL_YEAR_END


def detect_current_period():
    return PERIOD_SCHOOL_YEAR if is_school_year(date.today()) else PERIOD_SUMMER


def other_period(period=None):
    period = period or current_period
    return PERIOD_SCHOOL_YEAR if period == PERIOD_SUMMER else PERIOD_SUMMER


def get_current_period():
    return current_period


def get_period_data(period=None):
    return app_data[period or current_period]


def get_period_target_date():
    if current_period == PERIOD_SUMMER:
        return SCHOOL_YEAR_START
    return SCHOOL_YEAR_END

#period defaults
DEFAULT_GOALS = {
    PERIOD_SUMMER: [
        "Watch all marvel movies",
        "make a arduino or pi project",
        "Make money",
        "redesign upstairs",
        "Prepare nerdy docs for next year",
    ],
    PERIOD_SCHOOL_YEAR: [
        "Finish robotics season strong",
        "Keep grades up",
        "Learn a new coding skill",
        "Stay active in a club/sport",
        "Plan next summer's projects",
    ],
}

DEFAULT_DAILY_FOCUS = {
    PERIOD_SUMMER: ["Arduino lesson(s)", "Work on coding", "Watched a marvel movie?"],
    PERIOD_SCHOOL_YEAR: ["Homework done", "Robotics practice", "Coding practice"],
}

DEFAULT_PROGRESS = {
    PERIOD_SUMMER: {
        "Coding course": (41, 134),
        "Arduino course": (27, 150),
        "Marvel movies": (5, 45),
    },
    PERIOD_SCHOOL_YEAR: {
        "Robotics hours": (0, 120),
        "Reading pages": (0, 600),
        "Coding course": (0, 100),
    },
}

dot_colors = ["#3A6EA5", "#FF8C00", "#E53935"]

DEFAULT_EVENTS = {
    PERIOD_SUMMER: [
        {"name": "Banana Ball", "start_date": "2026-05-29", "end_date": "2026-05-29", "period": PERIOD_SUMMER},
        {"name": "Cruise", "start_date": "2026-05-31", "end_date": "2026-06-06", "period": PERIOD_SUMMER},
        {"name": "charleston", "start_date": "2026-06-12", "end_date": "2026-06-15", "period": PERIOD_SUMMER},
        {"name": "Lake Norman", "start_date": "2026-06-15", "end_date": "2026-06-21", "period": PERIOD_SUMMER},
        {"name": "wedding trip", "start_date": "2026-07-03", "end_date": "2026-07-19", "period": PERIOD_SUMMER},
    ],
    PERIOD_SCHOOL_YEAR: [],
}

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
display_month = now.month
display_year = now.year

#load data
def build_default_period_data(period):
    return {
        "goals": [False] * len(DEFAULT_GOALS[period]),
        "daily_focus": [False] * len(DEFAULT_DAILY_FOCUS[period]),
        "progress": [[str(c), str(g)] for c, g in DEFAULT_PROGRESS[period].values()],
        "events": [dict(e) for e in DEFAULT_EVENTS[period]],
    }


def load_all_data():
    if not os.path.exists(SAVE_FILE):
        return (
            {PERIOD_SUMMER: build_default_period_data(PERIOD_SUMMER),
             PERIOD_SCHOOL_YEAR: build_default_period_data(PERIOD_SCHOOL_YEAR)},
            detect_current_period(),
        )

    try:
        with open(SAVE_FILE, "r") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        raw = {}

    if PERIOD_SUMMER not in raw and PERIOD_SCHOOL_YEAR not in raw:
        summer = build_default_period_data(PERIOD_SUMMER)
        summer["goals"] = raw.get("goals", summer["goals"])
        summer["daily_focus"] = raw.get("daily", summer["daily_focus"])
        summer["progress"] = raw.get("progress", summer["progress"])
        return (
            {PERIOD_SUMMER: summer, PERIOD_SCHOOL_YEAR: build_default_period_data(PERIOD_SCHOOL_YEAR)},
            detect_current_period(),
        )

    data = {}
    for period in (PERIOD_SUMMER, PERIOD_SCHOOL_YEAR):
        merged = build_default_period_data(period)
        merged.update(raw.get(period, {}))
        data[period] = merged

    saved_period = raw.get("current_period")
    if saved_period not in (PERIOD_SUMMER, PERIOD_SCHOOL_YEAR):
        saved_period = detect_current_period()

    return data, saved_period


app_data, current_period = load_all_data()

#Save data
def save_data():
    active = get_period_data()
    active["goals"] = [var.get() for var in goal_vars]
    active["daily_focus"] = [var.get() for var in daily_vars]
    active["progress"] = [[e[0].get(), e[1].get()] for e in progress_entries]

    payload = dict(app_data)
    payload["current_period"] = current_period

    with open(SAVE_FILE, "w") as f:
        json.dump(payload, f)

def redraw_calendar():
    calendar_title.config(text=calendar.month_name[display_month].upper())
    year_var.set(str(display_year))

    calendar_legend_label.config(
        text=f"■ {PERIOD_LABELS[current_period]} event    ■ {PERIOD_LABELS[other_period()]} event (context only)"
    )

    prev_button.config(state="disabled" if (display_month == 1 and display_year <= MIN_YEAR) else "normal")
    next_button.config(state="disabled" if (display_month == 12 and display_year >= MAX_YEAR) else "normal")

    for widget in calendar_frame.winfo_children():
        widget.destroy()

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
    (current_total / goal_total) * 100
    if goal_total else 0
    )

    progress_percent = int(
        (goal_percent + habit_percent) / 2
    )

    total_bar["value"] = progress_percent

    percent_label.config(
        text=f"{progress_percent}%"
    )
    save_data()
    redraw_calendar()

    progress_labels = list(DEFAULT_PROGRESS[current_period].keys())

    for i, label_text in enumerate(progress_labels):
        try:
            current = int(progress_entries[i][0].get())
            goal = int(progress_entries[i][1].get())
        except ValueError:
            continue

        remaining = goal - current
        days_left_now = (get_period_target_date() - date.today()).days

        if days_left_now > 0 and remaining > 0:
            interval = days_left_now / remaining
            if interval < 1:
                rate = round(1 / interval)
                desc = f"{rate} per day"
            else:
                desc = f"every {round(interval)} days"
        else:
            desc = "complete"

        legend_desc_labels[i].config(text=f"{label_text} — {desc}")

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
title = tk.Label(root, text="", font=("Arial", int(30 * scale), "bold"))
title.pack(pady=10)


def update_title():
    if current_period == PERIOD_SUMMER:
        title.config(text=f"SUMMER {SUMMER_START.year}")
    else:
        title.config(text=f"SCHOOL YEAR {SCHOOL_YEAR_START.year}-{SCHOOL_YEAR_END.year}")


view_frame = tk.Frame(root, bg="#111111")
view_frame.pack(pady=(0, 10))

view_label = tk.Label(view_frame, text="", bg="#111111", fg="white", font=("Arial", int(16 * scale), "bold"))
view_label.pack(side="left", padx=(0, 15))


def switch_period(new_period):
    global current_period
    if new_period == current_period:
        return
    save_data()
    current_period = new_period
    rebuild_period_ui()


switch_button = tk.Button(view_frame, text="", command=lambda: switch_period(other_period()))
switch_button.pack(side="left")

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
days_label = tk.Label(days_card, text="", bg="#2b2b2b", fg="#4CAF50", font=("Arial", int(24 * scale), "bold"))
days_label.pack(pady=10)


def update_days_left():
    days_left = (get_period_target_date() - date.today()).days
    label = "days until school" if current_period == PERIOD_SUMMER else "days until summer"
    days_label.config(text=f"{days_left} {label}")

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

daily_vars = []


def build_daily_focus_section():
    global daily_vars
    for widget in focus_card.winfo_children()[1:]:
        widget.destroy()

    daily_vars = []
    saved_daily = get_period_data()["daily_focus"]

    for i, goal in enumerate(DEFAULT_DAILY_FOCUS[current_period]):
        var = tk.BooleanVar(value=saved_daily[i] if i < len(saved_daily) else False)
        check = tk.Checkbutton(
            focus_card, text=goal, variable=var, bg="#2b2b2b", fg="white",
            font=("Arial", int(16 * scale)), selectcolor="#2b2b2b"
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

goal_vars = []

def build_goal_section():
    global goal_vars
    for widget in goal_card.winfo_children()[1:]:
        widget.destroy()

    goal_vars = []
    saved_goals = get_period_data()["goals"]

    for i, goal in enumerate(DEFAULT_GOALS[current_period]):
        var = tk.BooleanVar(value=saved_goals[i] if i < len(saved_goals) else False)
        check = tk.Checkbutton(
            goal_card, text=goal, variable=var, command=update_total_progress,
            bg="#2b2b2b", fg="white", font=("Arial", int(20 * scale))
        )
        check.pack(anchor="w")
        goal_vars.append(var)

#create card
mini_progress_card = create_card(center_frame)

#write progress title
mini_progress_title = tk.Label(
    mini_progress_card, text="PROGRESS", bg="#2b2b2b", fg="white",
    font=("Arial", int(22 * scale), "bold")
)
mini_progress_title.pack(pady=15)

progress_entries = []
progress_bars = []


def build_progress_section():
    global progress_entries, progress_bars
    for widget in mini_progress_card.winfo_children()[1:]:
        widget.destroy()

    progress_entries = []
    progress_bars = []

    labels = list(DEFAULT_PROGRESS[current_period].keys())
    saved_progress = get_period_data()["progress"]

    for i, habit in enumerate(labels):
        default_current, default_goal = DEFAULT_PROGRESS[current_period][habit]
        current, goal = saved_progress[i] if i < len(saved_progress) else (default_current, default_goal)

        frame = tk.Frame(mini_progress_card, bg="#2b2b2b")
        frame.pack(fill="x", padx=20, pady=10)

        tk.Label(frame, text=habit, bg="#2b2b2b", fg="white", width=26,
                 font=("Arial", int(16 * scale), "bold"), anchor="w").pack(anchor="w")

        bottom_frame = tk.Frame(frame, bg="#2b2b2b")
        bottom_frame.pack(fill="x")

        try:
            bar_max, bar_val = int(goal), int(current)
        except ValueError:
            bar_max, bar_val = default_goal, default_current

        bar = ttk.Progressbar(bottom_frame, style="Custom.Horizontal.TProgressbar",
                               length=300, maximum=bar_max, value=bar_val)
        bar.pack(side="left", padx=10)

        current_entry = tk.Entry(frame, width=4, font=("Arial", int(12 * scale)))
        current_entry.insert(0, str(current))
        current_entry.pack(side="left", padx=5)

        tk.Label(frame, text="/", bg="#2b2b2b", fg="white").pack(side="left")

        goal_entry = tk.Entry(frame, width=4, font=("Arial", int(12 * scale)))
        goal_entry.insert(0, str(goal))
        goal_entry.pack(side="left", padx=5)

        progress_entries.append((current_entry, goal_entry))
        progress_bars.append(bar)
        
#allow switchable months
def previous_month():
    global display_month, display_year
    if display_month == 1 and display_year <= MIN_YEAR:
        return
    display_month -= 1
    if display_month < 1:
        display_month = 12
        display_year -= 1
    redraw_calendar()


def next_month():
    global display_month, display_year
    if display_month == 12 and display_year >= MAX_YEAR:
        return
    display_month += 1
    if display_month > 12:
        display_month = 1
        display_year += 1
    redraw_calendar()


#create card
calendar_card = create_card(right_frame)

#month buttons
button_frame = tk.Frame(
    calendar_card,
    bg="#2b2b2b"
)

prev_button = tk.Button(
    button_frame,
    text="<",
    command=previous_month,
    # bg="#3A6EA5",
    # fg="black",
    # activebackground="#4A7EB5",
    # activeforeground="white",
    # relief="flat",
    # borderwidth=0
)
prev_button.pack(side="left")

next_button = tk.Button(
    button_frame,
    text=">",
    command=next_month,
    # bg="#3A6EA5",
    # fg="black",
    # activebackground="#4A7EB5",
    # activeforeground="black",
    # relief="flat",
    # borderwidth=0
)
next_button.pack(side="left")

button_frame.pack()
#change month when switch
header_row = tk.Frame(calendar_card, bg="#2b2b2b")
header_row.pack(pady=15)

calendar_title = tk.Label(
    header_row, text=calendar.month_name[display_month].upper(),
    bg="#2b2b2b", fg="white", font=("Arial", int(26 * scale), "bold")
)
calendar_title.pack(side="left")

year_var = tk.StringVar(value=str(display_year))


def on_year_selected(event=None):
    global display_year
    display_year = int(year_var.get())
    redraw_calendar()


year_dropdown = ttk.Combobox(
    header_row, textvariable=year_var,
    values=[str(y) for y in range(MIN_YEAR, MAX_YEAR + 1)],
    width=6, state="readonly", font=("Arial", int(16 * scale))
)
year_dropdown.pack(side="left", padx=(10, 0))
year_dropdown.bind("<<ComboboxSelected>>", on_year_selected)

calendar_legend_label = tk.Label(calendar_card, text="", bg="#2b2b2b", fg="#aaaaaa", font=("Arial", int(11 * scale)))
calendar_legend_label.pack(pady=(0, 10))

calendar_frame = tk.Frame(calendar_card, bg="#1e1e1e")
calendar_frame.pack(pady=10)

#function that does math to get dates for progress
def get_dot_dates():
    today = date.today()
    target = get_period_target_date()
    days_left = (target - today).days
    dot_dates = {}

    labels = list(DEFAULT_PROGRESS[current_period].keys())

    for i, label_text in enumerate(labels):
        default_current, default_goal = DEFAULT_PROGRESS[current_period][label_text]
        try:
            current = int(progress_entries[i][0].get())
            goal = int(progress_entries[i][1].get())
        except (ValueError, IndexError):
            current, goal = default_current, default_goal

        remaining = goal - current
        if remaining <= 0 or days_left <= 0:
            dot_dates[label_text] = set()
            continue

        interval = days_left / remaining
        dates = set()
        for j in range(remaining):
            offset = round(j * interval)
            dates.add(today + timedelta(days=offset))
        dot_dates[label_text] = dates

    return dot_dates


def get_events_for_calendar(year, month):
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    active_events, other_events = [], []

    for period in (PERIOD_SUMMER, PERIOD_SCHOOL_YEAR):
        for event in app_data[period]["events"]:
            try:
                start = date.fromisoformat(event["start_date"])
                end = date.fromisoformat(event["end_date"])
            except (KeyError, ValueError):
                continue
            if start <= last_day and end >= first_day:
                (active_events if period == current_period else other_events).append(event)

    return active_events, other_events


def get_events_for_event_list():
    today = date.today()
    visible = []
    for event in get_period_data()["events"]:
        try:
            end = date.fromisoformat(event["end_date"])
        except (KeyError, ValueError):
            continue
        if end >= today:
            visible.append(event)
    visible.sort(key=lambda e: e["start_date"])
    return visible

def draw_calendar():
    dot_dates = get_dot_dates()
    progress_labels = list(DEFAULT_PROGRESS[current_period].keys())
    active_events, other_events = get_events_for_calendar(display_year, display_month)

    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for col, day in enumerate(days):
        tk.Label(calendar_frame, text=day, bg="#1e1e1e", fg="#aaaaaa",
                 font=("Arial", int(14 * scale), "bold"), width=6, height=2).grid(row=0, column=col)

    cal = calendar.monthcalendar(display_year, display_month)
    today = date.today()

    for row_num, week in enumerate(cal):
        for col_num, day in enumerate(week):

            if day == 0:
                cell = tk.Frame(calendar_frame, bg="#1e1e1e", width=int(80 * scale), height=int(58 * scale))
                cell.grid(row=row_num + 1, column=col_num, padx=4, pady=4)
                cell.pack_propagate(False)
                continue

            cell_date = date(display_year, display_month, day)
            day_active = [e for e in active_events
                          if date.fromisoformat(e["start_date"]) <= cell_date <= date.fromisoformat(e["end_date"])]
            day_other = [e for e in other_events
                         if date.fromisoformat(e["start_date"]) <= cell_date <= date.fromisoformat(e["end_date"])]

            if cell_date == today:
                bg_color = TODAY_COLOR
            elif day_active:
                bg_color = ACTIVE_EVENT_COLOR
            elif day_other:
                bg_color = OTHER_EVENT_COLOR
            else:
                bg_color = "#2b2b2b"

            cell = tk.Frame(calendar_frame, bg=bg_color, width=int(80 * scale), height=int(58 * scale))
            cell.grid(row=row_num + 1, column=col_num, padx=4, pady=4)
            cell.pack_propagate(False)

            tk.Label(cell, text=str(day), bg=bg_color, fg="white",
                     font=("Arial", int(14 * scale), "bold"), justify="center").pack()

            if day_active:
                tk.Label(cell, text=day_active[0]["name"], bg=bg_color, fg="white",
                         font=("Arial", int(9 * scale)), justify="center", wraplength=int(78 * scale)).pack()

            if day_other:
                tk.Label(cell, text=f"{day_other[0]['name']} ({PERIOD_LABELS[other_period()]})",
                         bg=bg_color, fg="#d8c5f0", font=("Arial", int(8 * scale), "italic"),
                         justify="center", wraplength=int(78 * scale)).pack()

            dots_frame = tk.Frame(cell, bg=bg_color)
            dots_frame.pack()
            for j, label_text in enumerate(progress_labels):
                if cell_date in dot_dates.get(label_text, set()):
                    tk.Label(dots_frame, text="●", bg=bg_color,
                             fg=dot_colors[j % len(dot_colors)], font=("Arial", int(8 * scale))).pack(side="left")

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

#progress dot legend
legend_desc_labels = []

event_name_entry = None
event_start_entry = None
event_end_entry = None
event_status_label = None
add_event_form = None
toggle_event_form_button = None
add_event_form_open = False


def format_date_range(start, end):
    if start.month == end.month and start.day == end.day:
        return f"{start.strftime('%B')} {start.day}"
    if start.month == end.month:
        return f"{start.strftime('%B')} {start.day}-{end.day}"
    return f"{start.strftime('%B')} {start.day} - {end.strftime('%B')} {end.day}"


def toggle_add_event_form():
    global add_event_form_open
    add_event_form_open = not add_event_form_open
    if add_event_form_open:
        add_event_form.pack(fill="x", pady=(10, 0))
        toggle_event_form_button.config(text="− Hide Add Event Form")
    else:
        add_event_form.pack_forget()
        toggle_event_form_button.config(text="+ Add Event")


def add_event():
    global event_status_label
    name = event_name_entry.get().strip()
    start_text = event_start_entry.get().strip()
    end_text = event_end_entry.get().strip() or start_text

    if not name or not start_text:
        event_status_label.config(text="Enter a name and a start date (YYYY-MM-DD).", fg="#E53935")
        return
    try:
        start = date.fromisoformat(start_text)
        end = date.fromisoformat(end_text)
    except ValueError:
        event_status_label.config(text="Dates must look like 2026-08-15.", fg="#E53935")
        return
    if end < start:
        start, end = end, start

    get_period_data()["events"].append({
        "name": name, "start_date": start.isoformat(), "end_date": end.isoformat(), "period": current_period,
    })
    save_data()
    build_events_section()
    redraw_calendar()


def build_events_section():
    global legend_desc_labels, event_name_entry, event_start_entry
    global event_end_entry, event_status_label, add_event_form, toggle_event_form_button

    for widget in events_frame.winfo_children()[1:]:
        widget.destroy()

    legend_frame = tk.Frame(events_frame, bg="#2b2b2b")
    legend_frame.pack(anchor="w", pady=(10, 0))

    legend_desc_labels = []
    progress_labels = list(DEFAULT_PROGRESS[current_period].keys())

    for i, label_text in enumerate(progress_labels):
        try:
            current = int(progress_entries[i][0].get())
            goal = int(progress_entries[i][1].get())
        except (ValueError, IndexError):
            current, goal = list(DEFAULT_PROGRESS[current_period].values())[i]

        remaining = goal - current
        days_left_now = (get_period_target_date() - date.today()).days

        if days_left_now > 0 and remaining > 0:
            interval = days_left_now / remaining
            desc = f"{round(1 / interval)} per day" if interval < 1 else f"every {round(interval)} days"
        else:
            desc = "complete"

        row = tk.Frame(legend_frame, bg="#2b2b2b")
        row.pack(anchor="w", pady=3)

        tk.Label(row, text="●", bg="#2b2b2b", fg=dot_colors[i % len(dot_colors)],
                 font=("Arial", int(14 * scale))).pack(side="left", padx=(0, 6))

        desc_label = tk.Label(row, text=f"{label_text} — {desc}", bg="#2b2b2b", fg="white",
                               font=("Arial", int(13 * scale)))
        desc_label.pack(side="left")
        legend_desc_labels.append(desc_label)

    visible_events = get_events_for_event_list()
    for event in visible_events:
        start = date.fromisoformat(event["start_date"])
        end = date.fromisoformat(event["end_date"])
        date_text = format_date_range(start, end)

        event_label = tk.Label(events_frame, text=f"{date_text} • {event['name']}", bg="#2b2b2b", fg="white",
                                font=("Arial", int(14 * scale)), padx=10, pady=6, anchor="w")
        event_label.pack(fill="x", pady=6 / len(visible_events) if visible_events else 0)

    toggle_event_form_button = tk.Button(
        events_frame, text="− Hide Add Event Form" if add_event_form_open else "+ Add Event",
        command=toggle_add_event_form
    )
    toggle_event_form_button.pack(anchor="w", pady=(15, 0))

    add_event_form = tk.Frame(events_frame, bg="#2b2b2b")

    tk.Label(add_event_form, text=f"Add {PERIOD_LABELS[current_period]} event", bg="#2b2b2b", fg="white",
             font=("Arial", int(13 * scale), "bold")).pack(anchor="w", pady=(10, 0))

    name_row = tk.Frame(add_event_form, bg="#2b2b2b")
    name_row.pack(fill="x", pady=3)
    tk.Label(name_row, text="Name:", bg="#2b2b2b", fg="white", width=6, anchor="w").pack(side="left")
    event_name_entry = tk.Entry(name_row)
    event_name_entry.pack(side="left", fill="x", expand=True)

    date_row = tk.Frame(add_event_form, bg="#2b2b2b")
    date_row.pack(fill="x", pady=3)
    tk.Label(date_row, text="Start (YYYY-MM-DD):", bg="#2b2b2b", fg="white").pack(side="left")
    event_start_entry = tk.Entry(date_row, width=12)
    event_start_entry.pack(side="left", padx=(4, 10))
    tk.Label(date_row, text="End (optional):", bg="#2b2b2b", fg="white").pack(side="left")
    event_end_entry = tk.Entry(date_row, width=12)
    event_end_entry.pack(side="left", padx=(4, 0))

    tk.Button(add_event_form, text="Add Event", command=add_event).pack(anchor="w", pady=(6, 0))

    event_status_label = tk.Label(add_event_form, text="", bg="#2b2b2b", font=("Arial", int(11 * scale)))
    event_status_label.pack(anchor="w", pady=(4, 0))

    if add_event_form_open:
        add_event_form.pack(fill="x", pady=(10, 0))

#rebuild ui
def rebuild_period_ui():
    build_goal_section()
    build_daily_focus_section()
    build_progress_section()
    build_events_section()

    update_title()
    update_days_left()
    view_label.config(text=f"Current View: {PERIOD_LABELS[current_period]}")
    switch_button.config(text=f"Switch to {PERIOD_LABELS[other_period()]}")

    update_total_progress()


rebuild_period_ui()

refresh_weather()

if __name__ == "__main__":
    root.mainloop()