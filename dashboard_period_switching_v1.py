#imports
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
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

def get_progress_labels():
    return [item["label"] for item in get_period_data()["progress"]]

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
        "Finish raspberry pi case/setup",
        "Keep grades up",
        "finish arduino course project",
        "Make Money",
        "Make AI agent",
        "Complete and sell unfinished lego",
        "do something with guitar",
        "do something with duolingo",
        "Do something with stop motion"
    ],
}

DEFAULT_DAILY_FOCUS = {
    PERIOD_SUMMER: ["Arduino lesson(s)", "Work on coding", "Watched a marvel movie?"],
    PERIOD_SCHOOL_YEAR: ["Homework done", "Coding practice","Duolingo", "Read", "something else"],
}

DEFAULT_PROGRESS = {
    PERIOD_SUMMER: {
        "Coding course": (41, 134),
        "Arduino course": (27, 150),
        "Marvel movies": (5, 45),
    },
    PERIOD_SCHOOL_YEAR: {
        "Python Coding Camp": (0, 500),
        "Minecraft Modding course": (40, 130),
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

DEFAULT_STEPPED_GOALS = {
    PERIOD_SUMMER: [
        {
            "name": "Build a robotics project",
            "steps": ["Design the build", "Order parts", "Assemble", "Program it", "Test and refine"],
        },
    ],
    PERIOD_SCHOOL_YEAR: [
        {
            "name": "Finish the Raspberry Pi case",
            "steps": ["Measure and plan", "3D print or cut", "Assemble", "Mount the Pi", "Test fit and finish"],
        },
    ],
}

#activities
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

ACTIVITY_COLOR = "#2f8f7f"

# weekdays use Python's date.weekday(): Monday=0 ... Sunday=6
DEFAULT_ACTIVITIES = {
    PERIOD_SUMMER: [
        {"name": "Tennis", "weekdays": [0, 2], "start_time": "17:00", "end_time": "19:00", "skipped_dates": []},
    ],
    PERIOD_SCHOOL_YEAR: [
        {"name": "Robotics", "weekdays": [1, 3], "start_time": "16:00", "end_time": "18:00", "skipped_dates": []},
    ],
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
        "goals": [{"text": t, "done": False} for t in DEFAULT_GOALS[period]],
        "daily_focus": [{"text": t, "done": False} for t in DEFAULT_DAILY_FOCUS[period]],
        "progress": [
            {"label": label, "current": str(c), "goal": str(g)}
            for label, (c, g) in DEFAULT_PROGRESS[period].items()
        ],
        "events": [dict(e) for e in DEFAULT_EVENTS[period]],
        "stepped_goals": [
            {"name": g["name"], "steps": [{"text": s, "done": False} for s in g["steps"]]}
            for g in DEFAULT_STEPPED_GOALS[period]
        ],
        "activities": [
            {**a, "skipped_dates": list(a["skipped_dates"])}
            for a in DEFAULT_ACTIVITIES[period]
        ],
    }

def upgrade_checklist(items, texts, label):
    """Old saves stored a checklist as plain True/False (the text lived in the
    code). Returns the new [{"text", "done"}] form, or the items untouched if
    they're already in it."""
    if not items or isinstance(items[0], dict):
        return items
    return [
        {
            "text": texts[i] if i < len(texts) else f"{label} {i + 1}",
            "done": bool(items[i]) if i < len(items) else False,
        }
        for i in range(max(len(texts), len(items)))
    ]

def upgrade_progress(items, defaults):
    """Old saves stored progress as [current, goal] pairs, with the labels
    living in the code. Pair each with its label from DEFAULT_PROGRESS."""
    if not items or isinstance(items[0], dict):
        return items
    labels = list(defaults.keys())
    upgraded = []
    for i in range(max(len(labels), len(items))):
        label = labels[i] if i < len(labels) else f"Item {i + 1}"
        current, goal = items[i] if i < len(items) else defaults[label]
        upgraded.append({"label": label, "current": str(current), "goal": str(goal)})
    return upgraded

def upgrade_stepped_goals(items, defaults):
    """Old saves stored only True/False per step; the goal names and step text
    lived in the code. Pair them back up using DEFAULT_STEPPED_GOALS."""
    if not items or isinstance(items[0], dict):
        return items
    upgraded = []
    for i in range(max(len(defaults), len(items))):
        goal = defaults[i] if i < len(defaults) else {"name": f"Goal {i + 1}", "steps": []}
        states = items[i] if i < len(items) else []
        texts = goal["steps"]
        steps = [
            {
                "text": texts[j] if j < len(texts) else f"Step {j + 1}",
                "done": bool(states[j]) if j < len(states) else False,
            }
            for j in range(max(len(texts), len(states)))
        ]
        upgraded.append({"name": goal["name"], "steps": steps})
    return upgraded

def normalize_period_data(period, data):
    data["goals"] = upgrade_checklist(data.get("goals", []), DEFAULT_GOALS[period], "Goal")
    data["daily_focus"] = upgrade_checklist(data.get("daily_focus", []), DEFAULT_DAILY_FOCUS[period], "Task")
    data["progress"] = upgrade_progress(data.get("progress", []), DEFAULT_PROGRESS[period])
    data["stepped_goals"] = upgrade_stepped_goals(data.get("stepped_goals", []), DEFAULT_STEPPED_GOALS[period])
    return data

def load_all_data():
    if not os.path.exists(SAVE_FILE):
        return (
            {PERIOD_SUMMER: build_default_period_data(PERIOD_SUMMER),
             PERIOD_SCHOOL_YEAR: build_default_period_data(PERIOD_SCHOOL_YEAR)},
            detect_current_period(),
            [],
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
        summer = normalize_period_data(PERIOD_SUMMER, summer)
        return (
            {PERIOD_SUMMER: summer, PERIOD_SCHOOL_YEAR: build_default_period_data(PERIOD_SCHOOL_YEAR)},
            detect_current_period(),
            raw.get("ideas", []),
        )

    data = {}
    for period in (PERIOD_SUMMER, PERIOD_SCHOOL_YEAR):
        merged = build_default_period_data(period)
        merged.update(raw.get(period, {}))
        data[period] = normalize_period_data(period, merged)

    saved_period = raw.get("current_period")
    if saved_period not in (PERIOD_SUMMER, PERIOD_SCHOOL_YEAR):
        saved_period = detect_current_period()

    return data, saved_period, raw.get("ideas", [])

app_data, current_period, idea_list = load_all_data()
edit_mode = False

#Save data
def save_data():
    active = get_period_data()
    for goal, var in zip(active["goals"], goal_vars):
        goal["done"] = var.get()
    for task, var in zip(active["daily_focus"], daily_vars):
        task["done"] = var.get()
    for item, (current_entry, goal_entry) in zip(active["progress"], progress_entries):
        item["current"] = current_entry.get()
        item["goal"] = goal_entry.get()
    for goal, steps in zip(active["stepped_goals"], stepped_goal_vars):
        for step, var in zip(goal["steps"], steps):
            step["done"] = var.get()

    payload = dict(app_data)
    payload["current_period"] = current_period
    payload["ideas"] = idea_list

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

    completed_goals = sum(var.get() for var in goal_vars)
    total_goal_units = len(goal_vars)

    for steps in stepped_goal_vars:
        if steps:
            total_goal_units += 1
            completed_goals += sum(var.get() for var in steps) / len(steps)

    goal_percent = (completed_goals / total_goal_units) * 100 if total_goal_units else 0
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

    progress_labels = get_progress_labels()

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
    side="left",
    fill="both",
    expand=True
    #padx =(0, 15)
)
#switch to expand to position in middle and pad to fill specific space
#fill actuslly changes size. if y then only specific
#4th column
fourth_frame = tk.Frame(main_frame, bg="#1e1e1e")
fourth_frame.pack(side="left", fill="y")

idea_card = create_card(fourth_frame)

idea_title = tk.Label(
    idea_card, text="RANDOM IDEAS", bg="#2b2b2b", fg="white",
    font=("Arial", int(18 * scale), "bold")
)
idea_title.pack(anchor="w")

idea_add_row = tk.Frame(idea_card, bg="#2b2b2b")

idea_entry = tk.Entry(idea_add_row)
idea_entry.pack(side="left", fill="x", expand=True)


def add_idea():
    text = idea_entry.get().strip()
    if not text:
        return
    idea_list.append(text)
    idea_entry.delete(0, tk.END)
    save_data()
    build_ideas_section()


tk.Button(idea_add_row, text="Add", command=add_idea).pack(side="left", padx=(6, 0))

idea_list_frame = tk.Frame(idea_card, bg="#2b2b2b")
idea_list_frame.pack(fill="x", pady=(10, 0))


def remove_idea(i):
    del idea_list[i]
    save_data()
    build_ideas_section()

def build_ideas_section():
    for widget in idea_list_frame.winfo_children():
        widget.destroy()

    if edit_mode:
        # before= keeps the add box above the list instead of landing below it
        idea_add_row.pack(fill="x", pady=(10, 0), before=idea_list_frame)
    else:
        idea_add_row.pack_forget()

    for i, text in enumerate(idea_list):
        row = tk.Frame(idea_list_frame, bg="#2b2b2b")
        row.pack(fill="x", pady=2)

        tk.Label(
            row, text=text, bg="#2b2b2b", fg="white", font=("Arial", int(13 * scale)),
            anchor="w", wraplength=160, justify="left"
        ).pack(side="left", fill="x", expand=True)

        if edit_mode:
            tk.Button(row, text="×", command=lambda i=i: remove_idea(i)).pack(side="right")

build_ideas_section()

#write title summer
title = tk.Label(root, text="", font=("Arial", int(30 * scale), "bold"))
title.pack(pady=10) # before=main_frame


def update_title():
    if current_period == PERIOD_SUMMER:
        title.config(text=f"SUMMER {SUMMER_START.year}")
    else:
        title.config(text=f"SCHOOL YEAR {SCHOOL_YEAR_START.year}-{SCHOOL_YEAR_END.year}")


view_frame = tk.Frame(root, bg="#111111")
view_frame.pack(pady=(0, 10)) # before=main_frame

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


def toggle_edit_mode():
    global edit_mode
    save_data()  # capture anything typed or ticked before the screen gets rebuilt
    edit_mode = not edit_mode
    edit_button.config(text="✔ Done editing" if edit_mode else "✎ Edit mode")
    rebuild_period_ui()


edit_button = tk.Button(view_frame, text="✎ Edit mode", command=toggle_edit_mode)
edit_button.pack(side="left", padx=(10, 0))


#edit mode helpers
def ask_text(title, prompt, initial=""):
    """Pop up a small box asking for text. Returns the cleaned text, or
    None if you cancel or leave it blank."""
    value = simpledialog.askstring(title, prompt, initialvalue=initial, parent=root)
    if value is None:
        return None
    return value.strip() or None


def confirm_delete(name):
    return messagebox.askyesno("Delete", f'Delete "{name}"?', parent=root)


def add_edit_buttons(parent, on_rename, on_delete):
    """The small ✎ and × buttons that sit beside an item in edit mode."""
    tk.Button(parent, text="×", width=2, command=on_delete).pack(side="right")
    if on_rename:
        tk.Button(parent, text="✎", width=2, command=on_rename).pack(side="right")


def add_checklist_item(key, noun):
    text = ask_text(f"Add {noun}", f"New {noun}:")
    if text is None:
        return
    save_data()  # sync the checkboxes into the data first, so nothing is lost on rebuild
    get_period_data()[key].append({"text": text, "done": False})
    rebuild_period_ui()


def rename_checklist_item(key, i, noun):
    item = get_period_data()[key][i]
    text = ask_text(f"Rename {noun}", "New name:", item["text"])
    if text is None:
        return
    save_data()
    item["text"] = text
    rebuild_period_ui()


def delete_checklist_item(key, i):
    items = get_period_data()[key]
    if not confirm_delete(items[i]["text"]):
        return
    save_data()
    del items[i]
    rebuild_period_ui()


def add_progress_item():
    label = ask_text("Add progress tracker", "What are you tracking? (e.g. Reading pages)")
    if label is None:
        return
    goal = simpledialog.askinteger(
        "Add progress tracker", f'Goal for "{label}" (a whole number):', parent=root, minvalue=1
    )
    if goal is None:
        return
    save_data()
    get_period_data()["progress"].append({"label": label, "current": "0", "goal": str(goal)})
    rebuild_period_ui()


def rename_progress_item(i):
    item = get_period_data()["progress"][i]
    text = ask_text("Rename tracker", "New name:", item["label"])
    if text is None:
        return
    save_data()
    item["label"] = text
    rebuild_period_ui()


def delete_progress_item(i):
    items = get_period_data()["progress"]
    if not confirm_delete(items[i]["label"]):
        return
    save_data()
    del items[i]
    rebuild_period_ui()



def add_stepped_goal():
    name = ask_text("Add multistep goal", "Goal name:")
    if name is None:
        return
    save_data()
    get_period_data()["stepped_goals"].append({"name": name, "steps": []})
    rebuild_period_ui()


def rename_stepped_goal(i):
    goal = get_period_data()["stepped_goals"][i]
    name = ask_text("Rename goal", "New name:", goal["name"])
    if name is None:
        return
    save_data()
    goal["name"] = name
    rebuild_period_ui()


def delete_stepped_goal(i):
    goals = get_period_data()["stepped_goals"]
    if not confirm_delete(goals[i]["name"]):
        return
    save_data()
    del goals[i]
    rebuild_period_ui()


def add_step(i):
    text = ask_text("Add step", "Step:")
    if text is None:
        return
    save_data()
    get_period_data()["stepped_goals"][i]["steps"].append({"text": text, "done": False})
    rebuild_period_ui()


def rename_step(i, j):
    step = get_period_data()["stepped_goals"][i]["steps"][j]
    text = ask_text("Rename step", "New name:", step["text"])
    if text is None:
        return
    save_data()
    step["text"] = text
    rebuild_period_ui()


def delete_step(i, j):
    steps = get_period_data()["stepped_goals"][i]["steps"]
    if not confirm_delete(steps[j]["text"]):
        return
    save_data()
    del steps[j]
    rebuild_period_ui()


def delete_event(event):
    if not confirm_delete(event["name"]):
        return
    save_data()
    get_period_data()["events"].remove(event)
    rebuild_period_ui()

def delete_activity(activity):
    if not confirm_delete(activity["name"]):
        return
    save_data()
    get_period_data()["activities"].remove(activity)
    rebuild_period_ui()

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

    for i, task in enumerate(get_period_data()["daily_focus"]):
        row = tk.Frame(focus_card, bg="#2b2b2b")
        row.pack(fill="x")

        var = tk.BooleanVar(value=task["done"])
        check = tk.Checkbutton(
            row, text=task["text"], variable=var, bg="#2b2b2b", fg="white",
            font=("Arial", int(16 * scale)), selectcolor="#2b2b2b"
        )
        check.pack(side="left", pady=2)
        daily_vars.append(var)

        if edit_mode:
            add_edit_buttons(
                row,
                lambda i=i: rename_checklist_item("daily_focus", i, "task"),
                lambda i=i: delete_checklist_item("daily_focus", i),
            )

    if edit_mode:
        tk.Button(
            focus_card, text="+ Add task",
            command=lambda: add_checklist_item("daily_focus", "task")
        ).pack(anchor="w", pady=(6, 0))

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

#create AI card
ai_card = create_card(left_frame)

ai_title = tk.Label(
    ai_card,
    text="AI ASSISTANT",
    bg="#2b2b2b",
    fg="white",
    font=("Arial", int(18 * scale), "bold")
)
ai_title.pack(anchor="w")

ai_placeholder_label = tk.Label(
    ai_card,
    text="Reserved for a future AI integration (e.g. Protégé).\nNot wired up to anything yet.",
    bg="#2b2b2b",
    fg="#9a9fab",
    font=("Arial", int(13 * scale), "italic"),
    justify="left"
)
ai_placeholder_label.pack(anchor="w", pady=(8, 0))

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

    for i, goal in enumerate(get_period_data()["goals"]):
        row = tk.Frame(goal_card, bg="#2b2b2b")
        row.pack(fill="x")

        var = tk.BooleanVar(value=goal["done"])
        check = tk.Checkbutton(
            row, text=goal["text"], variable=var, command=update_total_progress,
            bg="#2b2b2b", fg="white", font=("Arial", int(20 * scale))
        )
        check.pack(side="left")
        goal_vars.append(var)

        if edit_mode:
            add_edit_buttons(
                row,
                lambda i=i: rename_checklist_item("goals", i, "goal"),
                lambda i=i: delete_checklist_item("goals", i),
            )

    if edit_mode:
        tk.Button(
            goal_card, text="+ Add goal",
            command=lambda: add_checklist_item("goals", "goal")
        ).pack(anchor="w", pady=(8, 0))

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

    for i, item in enumerate(get_period_data()["progress"]):
        habit, current, goal = item["label"], item["current"], item["goal"]

        frame = tk.Frame(mini_progress_card, bg="#2b2b2b")
        frame.pack(fill="x", padx=20, pady=10)

        title_row = tk.Frame(frame, bg="#2b2b2b")
        title_row.pack(fill="x")

        tk.Label(title_row, text=habit, bg="#2b2b2b", fg="white", width=20 if edit_mode else 26,
                 font=("Arial", int(16 * scale), "bold"), anchor="w").pack(side="left")

        if edit_mode:
            add_edit_buttons(
                title_row,
                lambda i=i: rename_progress_item(i),
                lambda i=i: delete_progress_item(i),
            )

        bottom_frame = tk.Frame(frame, bg="#2b2b2b")
        bottom_frame.pack(fill="x")

        try:
            bar_max, bar_val = int(goal), int(current)
        except ValueError:
            bar_max, bar_val = 1, 0

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

    if edit_mode:
        tk.Button(
            mini_progress_card, text="+ Add tracker", command=add_progress_item
        ).pack(anchor="w", pady=(4, 0))

#all has to do with stepped goals

#create card
stepped_goal_card = create_card(center_frame)

stepped_goal_title = tk.Label(
    stepped_goal_card, text="MULTISTEP GOALS", bg="#2b2b2b", fg="white",
    font=("Arial", int(20 * scale), "bold")
)
stepped_goal_title.pack(pady=(0, 5))

stepped_goal_vars = []
stepped_step_frames = []
stepped_expanded = []
stepped_fraction_labels = []
stepped_toggle_buttons = []


def toggle_stepped_goal(i):
    stepped_expanded[i] = not stepped_expanded[i]
    if stepped_expanded[i]:
        stepped_step_frames[i].pack(fill="x", padx=(30, 0), pady=(2, 6))
        stepped_toggle_buttons[i].config(text="▼")
    else:
        stepped_step_frames[i].pack_forget()
        stepped_toggle_buttons[i].config(text="▶")


def refresh_stepped_goal_label(i):
    done = sum(var.get() for var in stepped_goal_vars[i])
    total = len(stepped_goal_vars[i])
    stepped_fraction_labels[i].config(text=f"{done}/{total}")


def on_stepped_step_toggled(i):
    refresh_stepped_goal_label(i)
    update_total_progress()


def build_stepped_goals_section():
    global stepped_goal_vars, stepped_step_frames, stepped_expanded
    global stepped_fraction_labels, stepped_toggle_buttons

    for widget in stepped_goal_card.winfo_children()[1:]:
        widget.destroy()

    stepped_goal_vars = []
    stepped_step_frames = []
    stepped_expanded = []
    stepped_fraction_labels = []
    stepped_toggle_buttons = []

    for i, goal in enumerate(get_period_data()["stepped_goals"]):
        header = tk.Frame(stepped_goal_card, bg="#2b2b2b")
        header.pack(fill="x", pady=(10, 0))

        toggle_button = tk.Button(
            header, text="▼" if edit_mode else "▶", width=2,
            command=lambda i=i: toggle_stepped_goal(i)
        )
        toggle_button.pack(side="left")
        stepped_toggle_buttons.append(toggle_button)

        tk.Label(header, text=goal["name"], bg="#2b2b2b", fg="white",
                 font=("Arial", int(15 * scale), "bold")).pack(side="left", padx=(6, 6))

        fraction_label = tk.Label(header, text="", bg="#2b2b2b", fg="#9a9fab", font=("Arial", int(12 * scale)))
        fraction_label.pack(side="left")
        stepped_fraction_labels.append(fraction_label)

        if edit_mode:
            add_edit_buttons(
                header,
                lambda i=i: rename_stepped_goal(i),
                lambda i=i: delete_stepped_goal(i),
            )

        steps_frame = tk.Frame(stepped_goal_card, bg="#2b2b2b")
        if edit_mode:
            # opened up automatically while editing; otherwise stays collapsed
            # until toggle_stepped_goal() packs it
            steps_frame.pack(fill="x", padx=(30, 0), pady=(2, 6))

        goal_step_vars = []
        for j, step in enumerate(goal["steps"]):
            step_row = tk.Frame(steps_frame, bg="#2b2b2b")
            step_row.pack(fill="x")

            var = tk.BooleanVar(value=step["done"])
            check = tk.Checkbutton(
                step_row, text=step["text"], variable=var,
                command=lambda i=i: on_stepped_step_toggled(i),
                bg="#2b2b2b", fg="white", selectcolor="#2b2b2b", font=("Arial", int(13 * scale))
            )
            check.pack(side="left")
            goal_step_vars.append(var)

            if edit_mode:
                add_edit_buttons(
                    step_row,
                    lambda i=i, j=j: rename_step(i, j),
                    lambda i=i, j=j: delete_step(i, j),
                )

        if edit_mode:
            tk.Button(
                steps_frame, text="+ Add step", command=lambda i=i: add_step(i)
            ).pack(anchor="w", pady=(4, 0))

        stepped_goal_vars.append(goal_step_vars)
        stepped_step_frames.append(steps_frame)
        stepped_expanded.append(edit_mode)

        refresh_stepped_goal_label(i)

    if edit_mode:
        tk.Button(
            stepped_goal_card, text="+ Add multistep goal", command=add_stepped_goal
        ).pack(anchor="w", pady=(10, 0))

#end of stepped goals

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

    for i, item in enumerate(get_period_data()["progress"]):
        try:
            current = int(progress_entries[i][0].get())
            goal = int(progress_entries[i][1].get())
        except (ValueError, IndexError):
            try:
                current, goal = int(item["current"]), int(item["goal"])
            except ValueError:
                dot_dates[i] = set()
                continue

        remaining = goal - current
        if remaining <= 0 or days_left <= 0:
            dot_dates[i] = set()
            continue

        interval = days_left / remaining
        dates = set()
        for j in range(remaining):
            offset = round(j * interval)
            dates.add(today + timedelta(days=offset))
        dot_dates[i] = dates

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
    progress_labels = get_progress_labels()
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
                cell = tk.Frame(calendar_frame, bg="#1e1e1e", width=int(80 * scale), height=int(70 * scale))
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

            cell = tk.Frame(calendar_frame, bg=bg_color, width=int(80 * scale), height=int(70 * scale))  # was 58
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
                if cell_date in dot_dates.get(j, set()):
                    tk.Label(dots_frame, text="●", bg=bg_color,
                             fg=dot_colors[j % len(dot_colors)], font=("Arial", int(8 * scale))).pack(side="left")

draw_calendar()

#activity functions
def format_time_12h(time_str):
    hour, minute = map(int, time_str.split(":"))
    suffix = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    return f"{hour12}:{minute:02d} {suffix}"


def get_next_occurrence(activity, from_date=None):
    """The next upcoming date this activity falls on, skipped or not."""
    d = from_date or date.today()
    for _ in range(14):
        if d.weekday() in activity["weekdays"]:
            return d
        d += timedelta(days=1)
    return None


def is_valid_time(text):
    try:
        hour, minute = text.split(":")
        return 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59
    except ValueError:
        return False


def toggle_skip_next(activity):
    """Skip (or un-skip) this activity's very next upcoming date."""
    next_date = get_next_occurrence(activity)
    if not next_date:
        return
    iso = next_date.isoformat()
    if iso in activity["skipped_dates"]:
        activity["skipped_dates"].remove(iso)
    else:
        activity["skipped_dates"].append(iso)
    save_data()
    build_activities_panel()

#create card
event_card = create_card(right_frame)

event_body = tk.Frame(event_card, bg="#2b2b2b")
event_body.pack(fill="both", expand=True)

#weekly activities panel — packed first (side="right") so it keeps its
#natural width; events_frame packed after with expand=True takes the rest
activities_frame = tk.Frame(event_body, bg="#2b2b2b")
activities_frame.pack(side="right", fill="y", padx=(0, 20), pady=20)

activities_title = tk.Label(
    activities_frame,
    text="WEEKLY SCHEDULE",
    bg="#2b2b2b",
    fg="white",
    font=("Arial", int(16 * scale), "bold")
)
activities_title.pack(anchor="w")


def build_activities_panel():
    for widget in activities_frame.winfo_children()[1:]:
        widget.destroy()

    for activity in get_period_data()["activities"]:
        day_names = ", ".join(WEEKDAY_NAMES[d][:3] for d in sorted(activity["weekdays"]))
        time_text = f"{format_time_12h(activity['start_time'])}\u2013{format_time_12h(activity['end_time'])}"

        row = tk.Frame(activities_frame, bg="#2b2b2b")
        row.pack(anchor="w", pady=(10, 0), fill="x")

        name_row = tk.Frame(row, bg="#2b2b2b")
        name_row.pack(fill="x")

        tk.Label(name_row, text=activity["name"], bg="#2b2b2b", fg=ACTIVITY_COLOR,
                 font=("Arial", int(13 * scale), "bold")).pack(side="left")

        if edit_mode:
            add_edit_buttons(name_row, None, lambda a=activity: delete_activity(a))

        tk.Label(row, text=f"{day_names} \u00b7 {time_text}", bg="#2b2b2b", fg="white",
                 font=("Arial", int(11 * scale)), wraplength=140, justify="left").pack(anchor="w")

        next_date = get_next_occurrence(activity)
        if next_date:
            skipped = next_date.isoformat() in activity["skipped_dates"]
            status_text = f"Next: {next_date.strftime('%b')} {next_date.day}"
            if skipped:
                status_text += " (skipped)"

            status_row = tk.Frame(row, bg="#2b2b2b")
            status_row.pack(anchor="w", pady=(2, 0))

            tk.Label(status_row, text=status_text, bg="#2b2b2b",
                     fg="#7a7f8c" if skipped else "#9a9fab",
                     font=("Arial", int(10 * scale), "italic")).pack(side="left")

            if edit_mode:
                tk.Button(
                    status_row, text="Unskip" if skipped else "Skip next",
                    command=lambda a=activity: toggle_skip_next(a)
                ).pack(side="left", padx=(8, 0))


#create events
events_frame = tk.Frame(
    event_body,
    bg="#2b2b2b"
)

events_frame.pack(
    side="left",
    fill="both",
    expand=True,
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

repeats_weekly_var = None
event_type_frame = None
weekly_day_vars = []
weekly_start_entry = None
weekly_end_entry = None


def format_date_range(start, end):
    if start.month == end.month and start.day == end.day:
        return f"{start.strftime('%B')} {start.day}"
    if start.month == end.month:
        return f"{start.strftime('%B')} {start.day}-{end.day}"
    return f"{start.strftime('%B')} {start.day} - {end.strftime('%B')} {end.day}"

def add_event(name):
    start_text = event_start_entry.get().strip()
    end_text = event_end_entry.get().strip() or start_text

    if not start_text:
        event_status_label.config(text="Enter a start date (YYYY-MM-DD).", fg="#E53935")
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


def add_activity(name):
    selected_days = [i for i, var in enumerate(weekly_day_vars) if var.get()]
    start_time = weekly_start_entry.get().strip()
    end_time = weekly_end_entry.get().strip()

    if not selected_days:
        event_status_label.config(text="Pick at least one day of the week.", fg="#E53935")
        return
    if not is_valid_time(start_time) or not is_valid_time(end_time):
        event_status_label.config(text="Times must look like 17:00 (24-hour).", fg="#E53935")
        return

    get_period_data()["activities"].append({
        "name": name,
        "weekdays": selected_days,
        "start_time": start_time,
        "end_time": end_time,
        "skipped_dates": [],
    })
    save_data()
    build_events_section()
    build_activities_panel()


def render_event_type_fields():
    global event_start_entry, event_end_entry, weekly_day_vars, weekly_start_entry, weekly_end_entry

    for widget in event_type_frame.winfo_children():
        widget.destroy()

    if repeats_weekly_var.get():
        weekly_day_vars = []
        days_row = tk.Frame(event_type_frame, bg="#2b2b2b")
        days_row.pack(fill="x")
        for label in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            var = tk.BooleanVar()
            tk.Checkbutton(days_row, text=label, variable=var, bg="#2b2b2b", fg="white",
                           selectcolor="#2b2b2b", font=("Arial", int(10 * scale))).pack(side="left")
            weekly_day_vars.append(var)

        time_row = tk.Frame(event_type_frame, bg="#2b2b2b")
        time_row.pack(fill="x", pady=3)
        tk.Label(time_row, text="Start (HH:MM):", bg="#2b2b2b", fg="white").pack(side="left")
        weekly_start_entry = tk.Entry(time_row, width=8)
        weekly_start_entry.pack(side="left", padx=(4, 10))
        tk.Label(time_row, text="End (HH:MM):", bg="#2b2b2b", fg="white").pack(side="left")
        weekly_end_entry = tk.Entry(time_row, width=8)
        weekly_end_entry.pack(side="left", padx=(4, 0))
    else:
        date_row = tk.Frame(event_type_frame, bg="#2b2b2b")
        date_row.pack(fill="x")
        tk.Label(date_row, text="Start (YYYY-MM-DD):", bg="#2b2b2b", fg="white").pack(side="left")
        event_start_entry = tk.Entry(date_row, width=12)
        event_start_entry.pack(side="left", padx=(4, 10))
        tk.Label(date_row, text="End (optional):", bg="#2b2b2b", fg="white").pack(side="left")
        event_end_entry = tk.Entry(date_row, width=12)
        event_end_entry.pack(side="left", padx=(4, 0))


def submit_event_form():
    name = event_name_entry.get().strip()
    if not name:
        event_status_label.config(text="Enter a name.", fg="#E53935")
        return

    if repeats_weekly_var.get():
        add_activity(name)
    else:
        add_event(name)


def build_events_section():
    global legend_desc_labels, event_name_entry, event_start_entry
    global event_end_entry, event_status_label, add_event_form
    global repeats_weekly_var, event_type_frame, weekly_day_vars, weekly_start_entry, weekly_end_entry

    for widget in events_frame.winfo_children()[1:]:
        widget.destroy()

    legend_frame = tk.Frame(events_frame, bg="#2b2b2b")
    legend_frame.pack(anchor="w", pady=(10, 0))

    legend_desc_labels = []
    progress_labels = get_progress_labels()

    for i, label_text in enumerate(progress_labels):
        try:
            current = int(progress_entries[i][0].get())
            goal = int(progress_entries[i][1].get())
        except (ValueError, IndexError):
            current, goal = 0, 0

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

        event_row = tk.Frame(events_frame, bg="#2b2b2b")
        event_row.pack(fill="x", pady=6 / len(visible_events) if visible_events else 0)

        tk.Label(event_row, text=f"{date_text} • {event['name']}", bg="#2b2b2b", fg="white",
                 font=("Arial", int(14 * scale)), padx=10, pady=6, anchor="w"
                 ).pack(side="left", fill="x", expand=True)

        if edit_mode:
            add_edit_buttons(event_row, None, lambda e=event: delete_event(e))

    add_event_form = tk.Frame(events_frame, bg="#2b2b2b")

    tk.Label(add_event_form, text=f"Add to {PERIOD_LABELS[current_period]}", bg="#2b2b2b", fg="white",
             font=("Arial", int(13 * scale), "bold")).pack(anchor="w", pady=(10, 0))

    name_row = tk.Frame(add_event_form, bg="#2b2b2b")
    name_row.pack(fill="x", pady=3)
    tk.Label(name_row, text="Name:", bg="#2b2b2b", fg="white", width=6, anchor="w").pack(side="left")
    event_name_entry = tk.Entry(name_row)
    event_name_entry.pack(side="left", fill="x", expand=True)

    repeats_weekly_var = tk.BooleanVar(value=False)
    tk.Checkbutton(
        add_event_form, text="Repeats weekly (adds to Weekly Schedule instead)",
        variable=repeats_weekly_var, command=render_event_type_fields,
        bg="#2b2b2b", fg="white", selectcolor="#2b2b2b", font=("Arial", int(11 * scale))
    ).pack(anchor="w", pady=(3, 0))

    event_type_frame = tk.Frame(add_event_form, bg="#2b2b2b")
    event_type_frame.pack(fill="x", pady=3)
    render_event_type_fields()

    tk.Button(add_event_form, text="Add", command=submit_event_form).pack(anchor="w", pady=(6, 0))

    event_status_label = tk.Label(add_event_form, text="", bg="#2b2b2b", font=("Arial", int(11 * scale)))
    event_status_label.pack(anchor="w", pady=(4, 0))

    if edit_mode:
        add_event_form.pack(fill="x", pady=(15, 0))

#click anywhere else to leave a text box
def release_text_focus(event):
    widget = event.widget
    if not isinstance(widget, tk.Misc):
        return
    if widget.winfo_toplevel() is not root:
        return  # leave pop-up dialogs and the year dropdown's list alone
    if isinstance(widget, (tk.Entry, ttk.Entry, tk.Text)):
        return  # clicking a text box should go INTO it, not out of it
    root.focus_set()


def leave_text_box(event):
    """Escape does the same thing from the keyboard."""
    widget = event.widget
    if isinstance(widget, tk.Misc) and widget.winfo_toplevel() is root:
        root.focus_set()

root.bind_all("<Button-1>", release_text_focus, add="+")
root.bind_all("<Escape>", leave_text_box, add="+")


#rebuild ui
def rebuild_period_ui():
    build_goal_section()
    build_daily_focus_section()
    build_progress_section()
    build_events_section()
    build_stepped_goals_section()
    build_activities_panel()
    build_ideas_section()

    update_title()
    update_days_left()
    view_label.config(
        text=f"Current View: {PERIOD_LABELS[current_period]}" + ("   ✎ EDITING" if edit_mode else "")
    )
    switch_button.config(text=f"Switch to {PERIOD_LABELS[other_period()]}")

    update_total_progress()


rebuild_period_ui()

refresh_weather()

if __name__ == "__main__":
    root.mainloop()