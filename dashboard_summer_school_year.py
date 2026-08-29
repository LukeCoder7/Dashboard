#imports
import tkinter as tk
from tkinter import ttk
import calendar
from datetime import date, datetime, timedelta
import requests
import json
import os

SAVE_FILE = "json/dashboard_save_school_year.json"

calendar.setfirstweekday(calendar.SUNDAY)

# =========================================================================
# PERIOD CONFIGURATION (centralized — change dates here, nowhere else)
# =========================================================================
# The dashboard supports two independent periods: Summer and School Year.
# Each period keeps its own goals, progress, daily focus, and events.
# Update these dates each year instead of hunting through the code.

PERIOD_SUMMER = "summer"
PERIOD_SCHOOL_YEAR = "school_year"

SCHOOL_YEAR_START = date(2026, 8, 10)
SCHOOL_YEAR_END = date(2027, 5, 21)

# "Equivalent configuration" for Summer, per the same pattern.
SUMMER_START = date(2026, 5, 25)   # approx end of May
SUMMER_END = date(2026, 8, 9)      # day before school starts

PERIOD_LABELS = {
    PERIOD_SUMMER: "Summer",
    PERIOD_SCHOOL_YEAR: "School Year",
}

# How many years before/after "now" the calendar can navigate to.
CALENDAR_YEAR_SPAN = 2
CURRENT_YEAR = datetime.now().year
MIN_YEAR = CURRENT_YEAR - CALENDAR_YEAR_SPAN
MAX_YEAR = CURRENT_YEAR + CALENDAR_YEAR_SPAN

# Colors used to tell the two periods apart on the calendar.
ACTIVE_EVENT_COLOR = "#3A6EA5"      # active-period event (existing color)
OTHER_EVENT_COLOR = "#6a4c93"       # other-period event shown for context
TODAY_COLOR = "#4CAF50"

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
root.title("Summer / School Year Dashboard")
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

# =========================================================================
# DEFAULT CONTENT PER PERIOD
# =========================================================================
# Goal / daily-focus text and progress labels live in code (same convention
# the original dashboard used); only their *state* (done/current/goal) is
# saved. Events are fully user-editable, so they are stored in full.

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
    PERIOD_SUMMER: [
        "Arduino lesson(s)",
        "Work on coding",
        "Watched a marvel movie?",
    ],
    PERIOD_SCHOOL_YEAR: [
        "Homework done",
        "Robotics practice",
        "Coding practice",
    ],
}

# label -> (default current, default goal)
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

# Default events, carried over from the original hardcoded summer list.
# Each event now stores real ISO dates and which period it belongs to,
# which is what lets the calendar tell periods apart.
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


# =========================================================================
# PERIOD HELPERS
# =========================================================================

def is_school_year(d):
    return SCHOOL_YEAR_START <= d <= SCHOOL_YEAR_END


def detect_current_period():
    """Auto-detect which period today's date falls into."""
    return PERIOD_SCHOOL_YEAR if is_school_year(date.today()) else PERIOD_SUMMER


def other_period(period=None):
    period = period or current_period
    return PERIOD_SCHOOL_YEAR if period == PERIOD_SUMMER else PERIOD_SUMMER


def get_current_period():
    return current_period


def get_period_data(period=None):
    """The active (or given) period's goals/progress/events/daily-focus."""
    return app_data[period or current_period]


def get_period_target_date():
    """The date progress/countdowns for the active period are paced toward."""
    if current_period == PERIOD_SUMMER:
        return SCHOOL_YEAR_START
    return SCHOOL_YEAR_END


#load data
def build_default_period_data(period):
    return {
        "goals": [False] * len(DEFAULT_GOALS[period]),
        "daily_focus": [False] * len(DEFAULT_DAILY_FOCUS[period]),
        "progress": [[str(c), str(g)] for c, g in DEFAULT_PROGRESS[period].values()],
        "events": [dict(e) for e in DEFAULT_EVENTS[period]],
    }


def load_all_data():
    """Load saved data, migrating old single-period save files safely.

    Never loses existing data: if the save file predates the period system
    (flat goals/daily/progress, no "summer"/"school_year" keys), its values
    become the Summer period's data and School Year starts from defaults.
    """
    if not os.path.exists(SAVE_FILE):
        return (
            {
                PERIOD_SUMMER: build_default_period_data(PERIOD_SUMMER),
                PERIOD_SCHOOL_YEAR: build_default_period_data(PERIOD_SCHOOL_YEAR),
            },
            detect_current_period(),
        )

    try:
        with open(SAVE_FILE, "r") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        raw = {}

    # Legacy flat save (pre-period system) -- migrate without losing data.
    if PERIOD_SUMMER not in raw and PERIOD_SCHOOL_YEAR not in raw:
        summer = build_default_period_data(PERIOD_SUMMER)
        summer["goals"] = raw.get("goals", summer["goals"])
        summer["daily_focus"] = raw.get("daily", summer["daily_focus"])
        summer["progress"] = raw.get("progress", summer["progress"])
        return (
            {
                PERIOD_SUMMER: summer,
                PERIOD_SCHOOL_YEAR: build_default_period_data(PERIOD_SCHOOL_YEAR),
            },
            detect_current_period(),
        )

    # New-format save -- merge over defaults so a missing/partial period
    # (e.g. an older new-format save made before School Year existed)
    # can't crash the app.
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
    """Sync the active period's live widgets into app_data, then persist
    both periods. Only the active period's widgets are read, so the other
    period's stored data is never touched by this call."""
    active = get_period_data()
    active["goals"] = [var.get() for var in goal_vars]
    active["daily_focus"] = [var.get() for var in daily_vars]
    active["progress"] = [[e[0].get(), e[1].get()] for e in progress_entries]
    # events are mutated in place by add_event(), nothing to sync here.

    payload = dict(app_data)
    payload["current_period"] = current_period

    with open(SAVE_FILE, "w") as f:
        json.dump(payload, f)


def redraw_calendar():

    # update title
    monthstr = calendar.month_name[display_month].upper()

    calendar_title.config(
        text=monthstr + " " + str(display_year)
    )

    calendar_legend_label.config(
        text=(
            f"■ {PERIOD_LABELS[current_period]} event    "
            f"■ {PERIOD_LABELS[other_period()]} event (context only)"
        )
    )

    # disable navigation at the edges of the allowed range instead of
    # letting it silently do nothing (or breaking)
    prev_button.config(state="disabled" if (display_month == 1 and display_year <= MIN_YEAR) else "normal")
    next_button.config(state="disabled" if (display_month == 12 and display_year >= MAX_YEAR) else "normal")
    prev_year_button.config(state="disabled" if display_year <= MIN_YEAR else "normal")
    next_year_button.config(state="disabled" if display_year >= MAX_YEAR else "normal")

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

#write title (updates with period)
title = tk.Label(
    root,
    text="",
    font=("Arial", int(30 * scale), "bold")
)
title.pack(pady=10)


def update_title():
    if current_period == PERIOD_SUMMER:
        title.config(text=f"SUMMER {SUMMER_START.year}")
    else:
        title.config(text=f"SCHOOL YEAR {SCHOOL_YEAR_START.year}-{SCHOOL_YEAR_END.year}")


#current view + switch control
view_frame = tk.Frame(root, bg="#111111")
view_frame.pack(pady=(0, 10))

view_label = tk.Label(
    view_frame,
    text="",
    bg="#111111",
    fg="white",
    font=("Arial", int(16 * scale), "bold")
)
view_label.pack(side="left", padx=(0, 15))


def switch_period(new_period):
    """Switch the active view. Data for the period being left is synced
    and saved first; the other period's stored data is left untouched."""
    global current_period
    if new_period == current_period:
        return
    save_data()
    current_period = new_period
    rebuild_period_ui()


switch_button = tk.Button(
    view_frame,
    text="",
    command=lambda: switch_period(other_period())
)
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

#display (text/value refreshed by update_days_left)
days_label = tk.Label(
    days_card,
    text="",
    bg="#2b2b2b",
    fg="#4CAF50",
    font=("Arial", int(24 * scale), "bold")
)
days_label.pack(pady=10)


def update_days_left():
    days_left = (get_period_target_date() - date.today()).days
    if current_period == PERIOD_SUMMER:
        label = "days until school"
    else:
        label = "days until summer"
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
    """(Re)build the daily-focus checkboxes for the active period."""
    global daily_vars

    for widget in focus_card.winfo_children()[1:]:
        widget.destroy()

    daily_vars = []
    saved_daily = get_period_data()["daily_focus"]

    for i, goal in enumerate(DEFAULT_DAILY_FOCUS[current_period]):
        var = tk.BooleanVar(value=saved_daily[i] if i < len(saved_daily) else False)
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
    value=0
)
total_bar.pack(pady=15)

#add percentage
percent_label = tk.Label(
    progress_card,
    text="0%",
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
    """(Re)build the goal checkboxes for the active period."""
    global goal_vars

    for widget in goal_card.winfo_children()[1:]:
        widget.destroy()

    goal_vars = []
    saved_goals = get_period_data()["goals"]

    for i, goal in enumerate(DEFAULT_GOALS[current_period]):
        var = tk.BooleanVar(value=saved_goals[i] if i < len(saved_goals) else False)
        check = tk.Checkbutton(
            goal_card,
            text=goal,
            variable=var,
            command=update_total_progress,
            bg="#2b2b2b",
            fg="white",
            font=("Arial", int(20 * scale))
        )
        check.pack(anchor="w")
        goal_vars.append(var)


#create card
mini_progress_card = create_card(center_frame)

#write progress title
mini_progress_title = tk.Label(
    mini_progress_card,
    text="PROGRESS",
    bg ="#2b2b2b",
    fg ="white",
    font=("Arial", int(22 * scale), "bold")
)
mini_progress_title.pack(pady= 15)

progress_entries = []
progress_bars = []


def build_progress_section():
    """(Re)build the mini progress bars/entries for the active period."""
    global progress_entries, progress_bars

    for widget in mini_progress_card.winfo_children()[1:]:
        widget.destroy()

    progress_entries = []
    progress_bars = []

    labels = list(DEFAULT_PROGRESS[current_period].keys())
    saved_progress = get_period_data()["progress"]

    for i, habit in enumerate(labels):
        default_current, default_goal = DEFAULT_PROGRESS[current_period][habit]
        if i < len(saved_progress):
            current, goal = saved_progress[i]
        else:
            current, goal = default_current, default_goal

        frame = tk.Frame(mini_progress_card, bg ="#2b2b2b")
        frame.pack(fill="x",padx =20, pady=10)

        #write
        label = tk.Label(
            frame,
            text=habit,
            bg ="#2b2b2b",
            fg ="white",
            width =26,
            font=("Arial", int(16 * scale), "bold"),
            anchor="w"
        )
        label.pack(anchor="w")

        #allow bar to go under
        bottom_frame = tk.Frame(
            frame,
            bg="#2b2b2b"
        )
        bottom_frame.pack(fill="x")

        #make bar
        try:
            bar_max = int(goal)
            bar_val = int(current)
        except ValueError:
            bar_max, bar_val = default_goal, default_current

        bar = ttk.Progressbar(
            bottom_frame,
            style="Custom.Horizontal.TProgressbar",
            length=300,
            maximum=bar_max,
            value=bar_val
        )
        bar.pack(side="left", padx=10)

        #display editable fractions
        current_entry = tk.Entry(
            frame,
            width=4,
            font=("Arial", int(12 * scale)),
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
        )
        goal_entry.insert(0, str(goal))
        goal_entry.pack(side="left", padx=5)

        progress_entries.append((current_entry, goal_entry))
        progress_bars.append(bar)


#allow switchable months/years, clamped to the allowed calendar range
def previous_month():
    global display_month, display_year

    if display_month == 1 and display_year <= MIN_YEAR:
        return  # already at the earliest allowed month

    display_month -= 1
    if display_month < 1:
        display_month = 12
        display_year -= 1

    redraw_calendar()


def next_month():
    global display_month, display_year

    if display_month == 12 and display_year >= MAX_YEAR:
        return  # already at the latest allowed month

    display_month += 1
    if display_month > 12:
        display_month = 1
        display_year += 1

    redraw_calendar()


def previous_year():
    global display_year
    if display_year > MIN_YEAR:
        display_year -= 1
    redraw_calendar()


def next_year():
    global display_year
    if display_year < MAX_YEAR:
        display_year += 1
    redraw_calendar()


#create card
calendar_card = create_card(right_frame)

#month/year buttons
button_frame = tk.Frame(
    calendar_card,
    bg="#2b2b2b"
)

prev_year_button = tk.Button(button_frame, text="«", command=previous_year)
prev_year_button.pack(side="left")

prev_button = tk.Button(
    button_frame,
    text="<",
    command=previous_month,
)
prev_button.pack(side="left")

next_button = tk.Button(
    button_frame,
    text=">",
    command=next_month,
)
next_button.pack(side="left")

next_year_button = tk.Button(button_frame, text="»", command=next_year)
next_year_button.pack(side="left")

button_frame.pack()
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

#legend explaining event colors (active vs. other-period context)
calendar_legend_label = tk.Label(
    calendar_card,
    text="",
    bg="#2b2b2b",
    fg="#aaaaaa",
    font=("Arial", int(11 * scale))
)
calendar_legend_label.pack(pady=(0, 10))

#calendar grid
calendar_frame = tk.Frame(
    calendar_card,
    bg="#1e1e1e"
)
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
    """Events from BOTH periods that overlap any day in the given month,
    split into (active_period_events, other_period_events)."""
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    active_events = []
    other_events = []

    for period in (PERIOD_SUMMER, PERIOD_SCHOOL_YEAR):
        for event in app_data[period]["events"]:
            try:
                start = date.fromisoformat(event["start_date"])
                end = date.fromisoformat(event["end_date"])
            except (KeyError, ValueError):
                continue
            if start <= last_day and end >= first_day:
                if period == current_period:
                    active_events.append(event)
                else:
                    other_events.append(event)

    return active_events, other_events


def get_events_for_event_list():
    """Events belonging ONLY to the active period, hiding ones that have
    already fully ended (matches the dashboard's original behavior)."""
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

    #progress dots
    dot_dates = get_dot_dates()
    progress_labels = list(DEFAULT_PROGRESS[current_period].keys())

    #events visible on this month (active period + other period for context)
    active_events, other_events = get_events_for_calendar(display_year, display_month)

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

    today = date.today()

    for row_num, week in enumerate(cal):

        for col_num, day in enumerate(week):

            if day == 0:
                cell = tk.Frame(
                    calendar_frame,
                    bg="#1e1e1e",
                    width=int(80 * scale),
                    height=int(58 * scale)
                )
                cell.grid(row=row_num + 1, column=col_num, padx=4, pady=4)
                cell.pack_propagate(False)
                continue

            cell_date = date(display_year, display_month, day)

            day_active_events = [
                e for e in active_events
                if date.fromisoformat(e["start_date"]) <= cell_date <= date.fromisoformat(e["end_date"])
            ]
            day_other_events = [
                e for e in other_events
                if date.fromisoformat(e["start_date"]) <= cell_date <= date.fromisoformat(e["end_date"])
            ]

            is_today = cell_date == today

            if is_today:
                bg_color = TODAY_COLOR
            elif day_active_events:
                bg_color = ACTIVE_EVENT_COLOR
            elif day_other_events:
                bg_color = OTHER_EVENT_COLOR
            else:
                bg_color = "#2b2b2b"

            cell = tk.Frame(
                calendar_frame,
                bg=bg_color,
                #important/ change size of calendar
                width=int(80 * scale),
                height=int(58 * scale)
            )
            cell.grid(row=row_num + 1, column=col_num, padx=4, pady=4)
            cell.pack_propagate(False)

            day_label = tk.Label(
                cell,
                text=str(day),
                bg=bg_color,
                fg="white",
                font=("Arial", int(14 * scale), "bold"),
                justify="center"
            )
            day_label.pack()

            #active-period event name
            if day_active_events:
                tk.Label(
                    cell,
                    text=day_active_events[0]["name"],
                    bg=bg_color,
                    fg="white",
                    font=("Arial", int(9 * scale)),
                    justify="center",
                    wraplength=int(78 * scale)
                ).pack()

            #other-period event name (context only), visually distinguished
            if day_other_events:
                tk.Label(
                    cell,
                    text=f"{day_other_events[0]['name']} ({PERIOD_LABELS[other_period()]})",
                    bg=bg_color,
                    fg="#d8c5f0",
                    font=("Arial", int(8 * scale), "italic"),
                    justify="center",
                    wraplength=int(78 * scale)
                ).pack()

            dots_frame = tk.Frame(cell, bg=bg_color)
            dots_frame.pack()
            for j, label_text in enumerate(progress_labels):
                if cell_date in dot_dates.get(label_text, set()):
                    tk.Label(
                        dots_frame,
                        text="●",
                        bg=bg_color,
                        fg=dot_colors[j % len(dot_colors)],
                        font=("Arial", int(8 * scale))
                    ).pack(side="left")


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

legend_desc_labels = []

# add-event form fields (rebuilt with the rest of this section, but the
# widget references need to stay reachable by add_event())
event_name_entry = None
event_start_entry = None
event_end_entry = None
event_status_label = None


def add_event():
    """Add a new event to the ACTIVE period only. Does not touch the
    other period's events."""
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
        "name": name,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "period": current_period,
    })

    save_data()
    build_events_section()
    redraw_calendar()


def build_events_section():
    """(Re)build the progress legend, the active-period event list, and
    the add-event form. Only events belonging to the active period are
    listed here (calendar context events from the other period are handled
    separately in draw_calendar)."""
    global legend_desc_labels, event_name_entry, event_start_entry, event_end_entry, event_status_label

    for widget in events_frame.winfo_children()[1:]:
        widget.destroy()

    #progress dot legend
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
            if interval < 1:
                rate = round(1 / interval)
                desc = f"{rate} per day"
            else:
                desc = f"every {round(interval)} days"
        else:
            desc = "complete"

        row = tk.Frame(legend_frame, bg="#2b2b2b")
        row.pack(anchor="w", pady=3)

        tk.Label(
            row,
            text="●",
            bg="#2b2b2b",
            fg=dot_colors[i % len(dot_colors)],
            font=("Arial", int(14 * scale))
        ).pack(side="left", padx=(0, 6))

        desc_label = tk.Label(
            row,
            text=f"{label_text} — {desc}",
            bg="#2b2b2b",
            fg="white",
            font=("Arial", int(13 * scale))
        )
        desc_label.pack(side="left")
        legend_desc_labels.append(desc_label)

    #active-period event list only (other period is calendar-only context)
    visible_events = get_events_for_event_list()

    for event in visible_events:
        start = date.fromisoformat(event["start_date"])
        end = date.fromisoformat(event["end_date"])

        if start == end:
            date_text = start.strftime("%B %-d") if os.name != "nt" else start.strftime("%B %d").lstrip("0")
        else:
            if start.month == end.month:
                date_text = f"{start.strftime('%B')} {start.day}-{end.day}"
            else:
                date_text = f"{start.strftime('%B %-d') if os.name != 'nt' else start.strftime('%B %d')} - {end.strftime('%B %-d') if os.name != 'nt' else end.strftime('%B %d')}"

        event_label = tk.Label(
            events_frame,
            text=f"{date_text} • {event['name']}",
            bg="#2b2b2b",
            fg="white",
            font=("Arial", int(14 * scale)),
            padx=10,
            pady=6,
            anchor="w"
        )

        event_label.pack(
            fill="x",
            pady=6 / len(visible_events) if visible_events else 0
        )

    #add-event form
    add_frame = tk.Frame(events_frame, bg="#2b2b2b")
    add_frame.pack(fill="x", pady=(15, 0))

    tk.Label(
        add_frame,
        text=f"Add {PERIOD_LABELS[current_period]} event",
        bg="#2b2b2b",
        fg="white",
        font=("Arial", int(13 * scale), "bold")
    ).pack(anchor="w")

    name_row = tk.Frame(add_frame, bg="#2b2b2b")
    name_row.pack(fill="x", pady=3)
    tk.Label(name_row, text="Name:", bg="#2b2b2b", fg="white", width=6, anchor="w").pack(side="left")
    event_name_entry = tk.Entry(name_row)
    event_name_entry.pack(side="left", fill="x", expand=True)

    date_row = tk.Frame(add_frame, bg="#2b2b2b")
    date_row.pack(fill="x", pady=3)
    tk.Label(date_row, text="Start (YYYY-MM-DD):", bg="#2b2b2b", fg="white").pack(side="left")
    event_start_entry = tk.Entry(date_row, width=12)
    event_start_entry.pack(side="left", padx=(4, 10))
    tk.Label(date_row, text="End (optional):", bg="#2b2b2b", fg="white").pack(side="left")
    event_end_entry = tk.Entry(date_row, width=12)
    event_end_entry.pack(side="left", padx=(4, 0))

    tk.Button(add_frame, text="Add Event", command=add_event).pack(anchor="w", pady=(6, 0))

    event_status_label = tk.Label(add_frame, text="", bg="#2b2b2b", font=("Arial", int(11 * scale)))
    event_status_label.pack(anchor="w", pady=(4, 0))


def rebuild_period_ui():
    """Rebuild every part of the dashboard that depends on which period
    is active. Called on startup and whenever the view is switched."""
    build_goal_section()
    build_daily_focus_section()
    build_progress_section()
    build_events_section()

    update_title()
    update_days_left()
    view_label.config(text=f"Current View: {PERIOD_LABELS[current_period]}")
    switch_button.config(text=f"Switch to {PERIOD_LABELS[other_period()]}")

    update_total_progress()  # recomputes bars/legend and redraws the calendar


#build everything for the period detected/loaded at startup
rebuild_period_ui()

refresh_weather()

if __name__ == "__main__":
    root.mainloop()
