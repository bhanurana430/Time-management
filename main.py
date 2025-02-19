import time
import streamlit as st
import sqlite3
import datetime
import pandas as pd

# Database setup
conn = sqlite3.connect("time_manager.db", check_same_thread=False)
c = conn.cursor()

# Create tables for logs and goals
c.execute("""
CREATE TABLE IF NOT EXISTS hourly_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hour TEXT,
    log TEXT
)
""")

c.execute("""
          
CREATE TABLE IF NOT EXISTS daily_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    goal TEXT,
    hours INTEGER,
    start_time TEXT,
    completed BOOLEAN DEFAULT 0
)
""")
conn.commit()

# Streamlit UI
st.title("⏳ Time Management App")

# Sidebar Navigation
menu = st.sidebar.radio("Menu", ["Progress Tracker", "Hourly Log", "Daily Goals", "Pomodoro Timer"])

def progress_tracker():
    st.header("📊 Progress Tracker")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    total_goals = c.execute("SELECT COUNT(*) FROM daily_goals WHERE date = ?", (today,)).fetchone()[0]
    completed_goals = c.execute("SELECT COUNT(*) FROM daily_goals WHERE date = ? AND completed = 1", (today,)).fetchone()[0]
    
    st.metric("Goals Completed", completed_goals, f"Out of {total_goals}")
    logs_today = c.execute("SELECT COUNT(*) FROM hourly_logs WHERE hour LIKE ?", (f"{today}%",)).fetchone()[0]
    st.metric("Hours Logged", logs_today)

def hourly_log():
    st.header("📖 Hourly Log")
    hour = st.selectbox("Select Hour", [f"{i}:00" for i in range(24)])
    log_text = st.text_area("What did you do this hour?")
    if st.button("Save Log"):
        c.execute("INSERT INTO hourly_logs (hour, log) VALUES (?, ?)", (hour, log_text))
        conn.commit()
        st.success("Log saved!")
    
    st.subheader("Past Hourly Logs")
    logs = pd.read_sql("SELECT hour, log FROM hourly_logs", conn)
    st.table(logs)

def daily_goals():
    st.header("🎯 Daily Goals")

    # Section for adding new goals
    goal_text = st.text_input("Set your goal for today:")
    hours = st.number_input("Hours to dedicate", min_value=1, max_value=24, step=1)
    start_time = st.time_input("Start time")
    if st.button("Add Goal"):
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO daily_goals (date, goal, hours, start_time) VALUES (?, ?, ?, ?)", 
                  (date, goal_text, hours, start_time.strftime("%H:%M")))
        conn.commit()
        st.success("Goal added!")
    
    goal_text = ""  # Clear the goal text input
    hours = 1      # Reset hours to 1
    start_time = datetime.time(9, 0) 

    st.subheader("Today's Goals")
    goals = pd.read_sql("SELECT * FROM daily_goals WHERE date = ?", conn, params=(datetime.datetime.now().strftime("%Y-%m-%d"),))
    goal_ids = goals['id'].tolist()

    for index, row in goals.iterrows():
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

        with col1:
            # Checkbox for marking goal as completed
            completed = st.checkbox("Completed", value=row['completed'], key=row['id'])
            if completed != row['completed']:
                # Update completion status in the database
                c.execute("UPDATE daily_goals SET completed = ? WHERE id = ?", (completed, row['id']))
                conn.commit()

        with col2:
            # Display the goal text
            st.write(row['goal'])

        with col3:
            # Display hours and start time
            st.write(f"Hours: {row['hours']}")

        with col4:
            # Button to delete the goal
            if st.button("Delete", key=f"delete_{row['id']}"):
                c.execute("DELETE FROM daily_goals WHERE id = ?", (row['id'],))
                conn.commit()
                st.success("Goal deleted!")

def pomodoro_timer():
    st.header("⏲️ Pomodoro Timer")
    pomodoro_type = st.radio("Choose Timer:", ["25-5 min", "50-10 min"])
    focus_time, break_time = (25, 5) if pomodoro_type == "25-5 min" else (50, 10)
    
    if st.button("Focus"):
        start_time = time.time()
        progress_bar = st.progress(0)
        time_left_text = st.empty()
        
        for i in range(focus_time * 60, 0, -1):
            time_elapsed = time.time() - start_time
            time_remaining = focus_time * 60 - time_elapsed
            progress_bar.progress((focus_time * 60 - i) / (focus_time * 60))
            time_left_text.text(f"Time Left: {int(time_remaining // 60)} min {int(time_remaining % 60)} sec")
            time.sleep(1)
        
        st.success("Focus session complete! Take a break.")

if menu == "Progress Tracker":
    progress_tracker()
elif menu == "Hourly Log":
    hourly_log()
elif menu == "Daily Goals":
    daily_goals()
elif menu == "Pomodoro Timer":
    pomodoro_timer()