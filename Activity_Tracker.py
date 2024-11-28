import tkinter as tk
from tkinter import messagebox, scrolledtext
import datetime
import pickle
import os
import calendar
import openai
from dotenv import load_dotenv  # Optional: For loading environment variables from a .env file

# Load environment variables from .env file (if using python-dotenv)
load_dotenv()

# Paths for saving data
ACTIVITIES_FILE = "activities_data.pkl"

# Set up OpenAI API key securely
openai.api_key = os.getenv('OPENAI_API_KEY')

if not openai.api_key:
    messagebox.showerror(
        "API Key Missing",
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )
    exit()

# Global data
activities = {}  # Activities stored with date keys

# Function to predict mood (stub function since we don't have a model)
def predict_mood(activity_name, time_spent):
    # Simple heuristic for mood prediction
    if "run" in activity_name.lower() or "exercise" in activity_name.lower():
        return "Energetic"
    elif "meditate" in activity_name.lower() or "yoga" in activity_name.lower():
        return "Relaxed"
    else:
        return "Neutral"

# Function to get dynamic activity suggestions using OpenAI API
def get_activity_suggestions():
    # Analyze past activities to suggest new ones
    all_activities = set()
    for date_activities in activities.values():
        for activity in date_activities:
            if activity['activity_name']:
                all_activities.add(activity['activity_name'].lower())

    # Generate suggestions using OpenAI's API
    try:
        prompt = (
            "Based on the following activities I've done: "
            f"{', '.join(all_activities)}. "
            "Suggest some new and different activities I can try today."
        )
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.7,
        )
        suggestions = response.choices[0].text.strip()
        return suggestions
    except Exception as e:
        print(f"Error: {e}")
        return "Unable to generate suggestions at this time."

# Global variable for the current displayed month
current_year = datetime.datetime.now().year
current_month = datetime.datetime.now().month

# Function to get the days of the month
def get_month_days(year, month):
    _, num_days = calendar.monthrange(year, month)
    return num_days

# Function to display the calendar for the current month
def display_calendar():
    # Clear current calendar view
    for widget in frame_calendar.winfo_children():
        widget.destroy()

    # Get the month name and days
    month_name = calendar.month_name[current_month]
    days_in_month = get_month_days(current_year, current_month)

    # Display the month name
    label_month.config(text=f"{month_name} {current_year}")

    # Display the days of the month
    for i in range(1, days_in_month + 1):
        day_button = tk.Button(
            frame_calendar,
            text=str(i),
            width=4,
            height=2,
            command=lambda day=i: show_day_activities(day),
        )
        day_button.grid(row=(i - 1) // 7, column=(i - 1) % 7, padx=5, pady=5)

# Function to change months
def change_month(direction):
    global current_month, current_year
    current_month += direction

    if current_month < 1:
        current_month = 12
        current_year -= 1
    elif current_month > 12:
        current_month = 1
        current_year += 1

    display_calendar()
    update_activity_log()

# Function to show activities for a selected day
def show_day_activities(day):
    selected_day.set(day)
    update_activity_log()

# Function to update the activity log for the selected day
def update_activity_log():
    # Clear the log
    for widget in frame_activity_log.winfo_children():
        widget.destroy()

    day = selected_day.get()
    selected_date = f"{current_year}-{current_month:02d}-{day:02d}"
    if selected_date in activities:
        for activity in activities[selected_date]:
            activity_label = tk.Label(
                frame_activity_log,
                text=f"{activity['time']} - {activity['activity_name']} ({activity['mood']})",
            )
            activity_label.pack()
    else:
        tk.Label(frame_activity_log, text="No activities for this day.").pack()

# Function to log activity
def log_activity():
    activity_name = entry_activity.get().strip()
    time_spent_str = entry_time_spent.get().strip()
    date_str = entry_date.get().strip()
    time_str = entry_time.get().strip()
    mood = mood_var.get()

    # Validate inputs
    if not activity_name or not time_spent_str or not date_str or not time_str or not mood:
        messagebox.showerror("Invalid Input", "Please fill out all fields.")
        return

    try:
        time_spent = int(time_spent_str)
    except ValueError:
        messagebox.showerror("Invalid Input", "Time spent must be a valid number.")
        return

    # Parse date
    try:
        activity_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        messagebox.showerror("Invalid Input", "Date must be in YYYY-MM-DD format.")
        return

    day = activity_date.day
    selected_day.set(day)
    selected_date = date_str

    # Predict mood (or use selected mood)
    if mood == "Predict":
        predicted_mood = predict_mood(activity_name, time_spent)
    else:
        predicted_mood = mood

    # Store activity
    if selected_date not in activities:
        activities[selected_date] = []

    activities[selected_date].append({
        "activity_name": activity_name,
        "time_spent": time_spent,
        "date": selected_date,
        "time": time_str,
        "mood": predicted_mood
    })

    # Clear input fields
    entry_activity.delete(0, tk.END)
    entry_time_spent.delete(0, tk.END)
    entry_date.delete(0, tk.END)
    entry_time.delete(0, tk.END)
    mood_var.set("Predict")

    update_activity_log()
    update_suggestions()

# Function to add scheduled activity
def add_scheduled_activity():
    schedule_name = entry_schedule_name.get().strip()
    dates_str = entry_schedule_dates.get().strip()
    schedule_time = entry_schedule_time.get().strip()

    if not schedule_name or not dates_str or not schedule_time:
        messagebox.showerror("Invalid Input", "Please fill out all fields.")
        return

    dates = dates_str.split(',')
    for date_str in dates:
        date_str = date_str.strip()
        try:
            activity_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror(
                "Invalid Input", f"Date {date_str} must be in YYYY-MM-DD format."
            )
            return

        selected_date = date_str
        if selected_date not in activities:
            activities[selected_date] = []

        activities[selected_date].append({
            "activity_name": schedule_name,
            "time_spent": None,
            "date": selected_date,
            "time": schedule_time,
            "mood": None  # Scheduled activity, mood not applicable yet
        })

    # Clear input fields
    entry_schedule_name.delete(0, tk.END)
    entry_schedule_dates.delete(0, tk.END)
    entry_schedule_time.delete(0, tk.END)

    update_activity_log()
    update_suggestions()

# Function to save activities to a file
def save_activities():
    with open(ACTIVITIES_FILE, "wb") as file:
        pickle.dump(activities, file)

# Function to load activities from a file
def load_activities():
    global activities
    if os.path.exists(ACTIVITIES_FILE):
        with open(ACTIVITIES_FILE, "rb") as file:
            activities = pickle.load(file)

# Function to handle application closing
def on_closing():
    save_activities()
    root.destroy()

# Initialize conversation history
conversation_history = [
    {"role": "system", "content": "You are ChatGPT, a helpful assistant that can answer any question."}
]

# Function to send message to chatbot
def send_message(event=None):
    user_message = entry_chat.get().strip()
    if not user_message:
        return

    # Display user's message
    chat_history.configure(state='normal')
    chat_history.insert(tk.END, f"You: {user_message}\n")
    chat_history.configure(state='disabled')

    # Get chatbot response
    bot_response = chatbot_response(user_message)

    # Display bot's response
    chat_history.configure(state='normal')
    chat_history.insert(tk.END, f"Bot: {bot_response}\n")
    chat_history.configure(state='disabled')

    chat_history.see(tk.END)
    entry_chat.delete(0, tk.END)

# Function to generate chatbot response using OpenAI API
def chatbot_response(message):
    global conversation_history

    # Append user's message to the conversation history
    conversation_history.append({"role": "user", "content": message})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=150,
            temperature=0.7,
        )

        # Extract assistant's reply
        reply = response.choices[0].message.content.strip()

        # Append assistant's reply to the conversation history
        conversation_history.append({"role": "assistant", "content": reply})

        return reply

    except openai.error.OpenAIError as e:
        print(f"OpenAI API Error: {e}")
        return "Sorry, I'm experiencing technical difficulties."

    except Exception as e:
        print(f"General Error: {e}")
        return "Sorry, I'm having trouble understanding. Please try again later."

# Function to update activity suggestions
def update_suggestions():
    # Clear previous suggestions
    for widget in frame_suggestions.winfo_children():
        widget.destroy()

    suggestions_text = get_activity_suggestions()

    label_summary = tk.Label(
        frame_suggestions, text="Activity Suggestions:", font=("Helvetica", 12, "bold")
    )
    label_summary.pack(anchor="w")

    suggestions_label = tk.Label(
        frame_suggestions, text=suggestions_text, wraplength=400, justify="left"
    )
    suggestions_label.pack(anchor="w")

# Create main window
root = tk.Tk()
root.title("Activity Tracker")
root.geometry("1200x700")  # Full-screen size (adjust as needed)

# Bind the closing event to save data
root.protocol("WM_DELETE_WINDOW", on_closing)

# Frames setup
frame_navigation = tk.Frame(root)
frame_navigation.grid(row=0, column=0, padx=10, pady=10, sticky="w")

frame_calendar = tk.Frame(root)
frame_calendar.grid(row=1, column=0, padx=10, pady=10, sticky="nw")

frame_activity_log = tk.LabelFrame(root, text="Activities for Selected Day")
frame_activity_log.grid(row=2, column=0, padx=10, pady=10, sticky="nw")

frame_input = tk.LabelFrame(root, text="Add Activity")
frame_input.grid(row=1, column=1, padx=10, pady=10, sticky="n")

frame_schedule = tk.LabelFrame(root, text="Schedule Activity")
frame_schedule.grid(row=2, column=1, padx=10, pady=10, sticky="n")

frame_chatbot = tk.LabelFrame(root, text="AI Chatbot")
frame_chatbot.grid(row=1, column=2, rowspan=2, padx=10, pady=10, sticky="n")

frame_suggestions = tk.LabelFrame(root, text="Activity Suggestions")
frame_suggestions.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="w")

# Navigation Controls
label_month = tk.Label(frame_navigation, text="", font=("Helvetica", 16))
label_month.grid(row=0, column=1, padx=10)

prev_button = tk.Button(
    frame_navigation, text="Previous", command=lambda: change_month(-1)
)
prev_button.grid(row=0, column=0, padx=10)

next_button = tk.Button(frame_navigation, text="Next", command=lambda: change_month(1))
next_button.grid(row=0, column=2, padx=10)

# Activity Input Fields
label_activity = tk.Label(frame_input, text="Activity Name:")
label_activity.grid(row=0, column=0, sticky="w")
entry_activity = tk.Entry(frame_input)
entry_activity.grid(row=0, column=1)

label_date = tk.Label(frame_input, text="Date (YYYY-MM-DD):")
label_date.grid(row=1, column=0, sticky="w")
entry_date = tk.Entry(frame_input)
entry_date.grid(row=1, column=1)

label_time = tk.Label(frame_input, text="Time (HH:MM):")
label_time.grid(row=2, column=0, sticky="w")
entry_time = tk.Entry(frame_input)
entry_time.grid(row=2, column=1)

label_time_spent = tk.Label(frame_input, text="Time Spent (minutes):")
label_time_spent.grid(row=3, column=0, sticky="w")
entry_time_spent = tk.Entry(frame_input)
entry_time_spent.grid(row=3, column=1)

label_mood = tk.Label(frame_input, text="Mood:")
label_mood.grid(row=4, column=0, sticky="w")
mood_var = tk.StringVar(value="Predict")
mood_options = ["Predict", "Happy", "Sad", "Energetic", "Relaxed", "Stressed", "Unknown"]
option_mood = tk.OptionMenu(frame_input, mood_var, *mood_options)
option_mood.grid(row=4, column=1)

log_button = tk.Button(frame_input, text="Log Activity", command=log_activity)
log_button.grid(row=5, column=0, columnspan=2, pady=10)

# Scheduled Activity Input Fields
label_schedule_name = tk.Label(frame_schedule, text="Schedule Name:")
label_schedule_name.grid(row=0, column=0, sticky="w")
entry_schedule_name = tk.Entry(frame_schedule)
entry_schedule_name.grid(row=0, column=1)

label_schedule_dates = tk.Label(
    frame_schedule, text="Dates (YYYY-MM-DD, comma-separated):"
)
label_schedule_dates.grid(row=1, column=0, sticky="w")
entry_schedule_dates = tk.Entry(frame_schedule)
entry_schedule_dates.grid(row=1, column=1)

label_schedule_time = tk.Label(frame_schedule, text="Time (HH:MM):")
label_schedule_time.grid(row=2, column=0, sticky="w")
entry_schedule_time = tk.Entry(frame_schedule)
entry_schedule_time.grid(row=2, column=1)

button_add_schedule = tk.Button(
    frame_schedule, text="Add Scheduled Activity", command=add_scheduled_activity
)
button_add_schedule.grid(row=3, column=0, columnspan=2, pady=10)

# Chatbot Interface
chat_history = scrolledtext.ScrolledText(
    frame_chatbot, state='disabled', width=40, height=20, wrap='word'
)
chat_history.pack(padx=5, pady=5)

entry_chat = tk.Entry(frame_chatbot, width=30)
entry_chat.pack(side=tk.LEFT, padx=5, pady=5)
entry_chat.bind("<Return>", send_message)

send_button = tk.Button(frame_chatbot, text="Send", command=send_message)
send_button.pack(side=tk.LEFT, padx=5)

# Variable to store selected day
selected_day = tk.IntVar(value=datetime.datetime.now().day)

# Load activities if any
load_activities()

# Start the application
display_calendar()
update_activity_log()
update_suggestions()
root.mainloop()
