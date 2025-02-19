import time
import streamlit as st
import sqlite3
import datetime
import pandas as pd
import matplotlib.pyplot as plt

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
    completed BOOLEAN DEFAULT 0,
    priority TEXT,
    recurrence TEXT
)
""")
conn.commit()

# Streamlit UI
st.title("⏳ Time Management App")

# Sidebar Navigation
menu = st.sidebar.radio("Menu", ["Progress Tracker", "Hourly Log", "Daily Goals", "Pomodoro Timer"])

def progress_tracker():
    st.divider()
    st.header("📊 Progress Tracker")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    total_goals = c.execute("SELECT COUNT(*) FROM daily_goals WHERE date = ?", (today,)).fetchone()[0]
    completed_goals = c.execute("SELECT COUNT(*) FROM daily_goals WHERE date = ? AND completed = 1", (today,)).fetchone()[0]
    
    st.metric("Goals Completed", completed_goals, f"Out of {total_goals}")
    logs_today = c.execute("SELECT COUNT(*) FROM hourly_logs WHERE hour LIKE ?", (f"{today}%",)).fetchone()[0]
    st.metric("Hours Logged", logs_today)

    # Progress Visualization
    progress_data = pd.read_sql("SELECT date, COUNT(*) as total_goals, SUM(completed) as completed_goals FROM daily_goals GROUP BY date", conn)
    st.line_chart(progress_data.set_index('date'))

def hourly_log():
    st.divider()
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
    st.divider()
    st.header("🎯 Daily Goals")
    goal_text = st.text_input("Set your goal for today:")

    c1,c2 = st.columns([1,1])

    with c1:
        hours = st.number_input("Hours to dedicate", min_value=1, max_value=24, step=1)
        start_time = st.time_input("Start time")

    with c2:
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        recurrence = st.selectbox("Recurrence", ["None", "Daily", "Weekly", "Monthly"])

    # Section for adding new goals
    
    
   

    if st.button("Add Goal"):
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO daily_goals (date, goal, hours, start_time, priority, recurrence) VALUES (?, ?, ?, ?, ?, ?)", 
                  (date, goal_text, hours, start_time.strftime("%H:%M"), priority, recurrence))
        conn.commit()
        st.success("Goal added!")

    st.subheader("Today's Goals")
    filter_option = st.selectbox("Filter Goals", ["All", "Completed", "Not Completed"])
    query = "SELECT * FROM daily_goals WHERE date = ?"
    params = (datetime.datetime.now().strftime("%Y-%m-%d"),)

    if filter_option == "Completed":
        query += " AND completed = 1"
    elif filter_option == "Not Completed":
        query += " AND completed = 0"

    goals = pd.read_sql(query, conn, params=params)
    
    goal_ids = goals['id'].tolist()

    for index, row in goals.iterrows():
        col1, col2, col3, col4, col5,col6 = st.columns([1, 2, 1, 1, 1,1])

        with col1:
            # Checkbox for marking goal as completed
            completed = st.checkbox("✅", value=row['completed'], key=row['id'])
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
            # Display priority
            st.write(f"{row['priority']}")

        with col5:
            # Button to edit the goal
            if st.button("Edit", key=f"edit_{row['id']}"):
                edit_goal(row)

        with col6:
            # Button to delete the goal
            if st.button("❌", key=f"delete_{row['id']}"):
                c.execute("DELETE FROM daily_goals WHERE id = ?", (row['id'],))
                conn.commit()
                st.success("Goal deleted!")

def edit_goal(row):
    new_goal_text = st.text_input("Edit your goal:", row['goal'])
    new_hours = st.number_input("Edit hours:", min_value=1, max_value=24, value=row['hours'])
    new_start_time = st.time_input("Edit start time:", value=datetime.datetime.strptime(row['start_time'], '%H:%M').time())
    new_priority = st.selectbox("Edit priority", ["High", "Medium", "Low"], index=["High", "Medium", "Low"].index(row['priority']))
    
    if st.button("Save Changes"):
        c.execute("UPDATE daily_goals SET goal = ?, hours = ?, start_time = ?, priority = ? WHERE id = ?", 
                  (new_goal_text, new_hours, new_start_time.strftime("%H:%M"), new_priority, row['id']))
        conn.commit()
        st.success("Goal updated!")

def pomodoro_timer():

    st.divider()
    st.header("⏲️ Pomodoro Timer")
    # Choose timer type
    

    a1,a2 = st.columns([1,1])

    with a1:

        pomodoro_type = st.radio("Choose Timer:", ["25-5 min", "50-10 min"])
         # Set focus and break times based on the selection
        if pomodoro_type == "25-5 min":
            focus_time, break_time = 25, 5
        else:
            focus_time, break_time = 50, 10

    with a2:
        if st.button("Start Timer"):
            # Timer for focus session

            focus_timer = st.empty()  # Placeholder for the focus timer
            for i in range(focus_time * 60, 0, -1):
                minutes, seconds = divmod(i, 60)
                focus_timer.text(f"Focus Time Left: {minutes:02d}:{seconds:02d}")
                time.sleep(1)

            st.success("Focus session complete! Take a break.")

            # Timer for break session
            st.write(f"Starting break session for {break_time} minutes.")
            break_timer = st.empty()  # Placeholder for the break timer
            for i in range(break_time * 60, 0, -1):
                minutes, seconds = divmod(i, 60)
                break_timer.text(f"Break Time Left: {minutes:02d}:{seconds:02d}")
                time.sleep(1)

            st.success("Break time is over! Ready for the next session.")

if menu == "Progress Tracker":
    progress_tracker()
elif menu == "Hourly Log":
    hourly_log()
elif menu == "Daily Goals":
    daily_goals()
elif menu == "Pomodoro Timer":
    pomodoro_timer()