# MIT License
#
# Copyright (c) [year] [Your Name]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import numpy as np
import hashlib
import sqlite3
import random
import matplotlib.pyplot as plt
from tkinter import Tk, Label, Button, Entry, messagebox, StringVar

# Izveido SQLite datubāzi
DB_NAME = "game.db"

def connect_db():
    return sqlite3.connect(DB_NAME)

def setup_db():
    db = connect_db()
    cursor = db.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        correct_answers INTEGER NOT NULL,
                        wrong_answers INTEGER NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    db.commit()
    db.close()

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user():
    username = username_entry.get()
    password = password_entry.get()

    if not username or not password:
        messagebox.showerror("Kļūda", "Ievadiet lietotājvārdu un paroli!")
        return

    db = connect_db()
    cursor = db.cursor()
    hashed_password = hash_password(password)
    
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        db.commit()
        messagebox.showinfo("Reģistrācija", "Reģistrācija veiksmīga!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Kļūda", "Lietotājvārds jau eksistē!")
    finally:
        db.close()

def authenticate_user():
    username = username_entry.get()
    password = password_entry.get()

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    db.close()
    
    if user and user[1] == hash_password(password):
        return user[0]
    return None

def save_result(user_id, correct, wrong):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO results (user_id, correct_answers, wrong_answers) VALUES (?, ?, ?)", (user_id, correct, wrong))
    db.commit()
    db.close()

def show_statistics():
    # Temporarily show login UI elements to get the username and password
    login_label.pack()
    username_entry.pack()
    password_entry.pack()

    def on_statistics_submit():
        username = username_entry.get()
        password = password_entry.get()

        user_id = authenticate_user()
        if not user_id:
            messagebox.showerror("Kļūda", "Nepareizs lietotājvārds vai parole!")
            return

        # Hide login widgets after authentication
        login_label.pack_forget()
        username_entry.pack_forget()
        password_entry.pack_forget()

        db = connect_db()
        cursor = db.cursor()

        # Get the last 10 game results
        cursor.execute("""
            SELECT correct_answers, wrong_answers 
            FROM results 
            WHERE user_id = ? 
            ORDER BY id DESC 
            LIMIT 10
        """, (user_id,))
        data = cursor.fetchall()

        # Get the personal best (highest correct answers)
        cursor.execute("""
            SELECT correct_answers, wrong_answers 
            FROM results 
            WHERE user_id = ? 
            ORDER BY correct_answers DESC 
            LIMIT 1
        """, (user_id,))
        best_result = cursor.fetchone()

        db.close()

        if not data:
            messagebox.showinfo("Nav datu", "Nav pieejami spēles rezultāti!")
            return

        correct = [x[0] for x in data]
        wrong = [x[1] for x in data]
        games = np.arange(len(correct))  # X-axis positions

        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Plot for last 10 games in the first subplot (ax1)
        bar_width = 0.4  # Bar width

        ax1.bar(games - bar_width/2, correct, bar_width, label="Pareizās atbildes", color='green', alpha=0.7)
        ax1.bar(games + bar_width/2, wrong, bar_width, label="Nepareizās atbildes", color='red', alpha=0.7)

        # Add labels on top of bars
        for i in range(len(correct)):
            ax1.text(i - bar_width/2, correct[i] + 0.2, str(correct[i]), ha='center', fontsize=10, fontweight='bold')
            ax1.text(i + bar_width/2, wrong[i] + 0.2, str(wrong[i]), ha='center', fontsize=10, fontweight='bold')

        ax1.set_xlabel("Spēles numurs", fontsize=12)
        ax1.set_ylabel("Atbilžu skaits", fontsize=12)
        ax1.set_title("Pēdējās 10 spēles", fontsize=14, fontweight='bold')
        ax1.grid(axis='y', linestyle="--", alpha=0.6)  # Horizontal grid lines
        ax1.legend()

        # Plot for personal best in the second subplot (ax2)
        if best_result:
            best_correct, best_wrong = best_result
            ax2.bar(0 - bar_width/2, best_correct, bar_width, label="Labākais rezultāts", color='blue', alpha=0.7)
            ax2.bar(0 + bar_width/2, best_wrong, bar_width, color='gray', alpha=0.7)
            ax2.text(0 - bar_width/2, best_correct + 0.2, str(best_correct), ha='center', fontsize=10, fontweight='bold')
            ax2.text(0 + bar_width/2, best_wrong + 0.2, str(best_wrong), ha='center', fontsize=10, fontweight='bold')
            ax2.set_xticks([0])
            ax2.set_xticklabels(["PB"])  # Label "PB" for best
        else:
            ax2.bar(0, 0, bar_width, label="Nav rezultāta", color='gray', alpha=0.7)

        ax2.set_title("Labākais rezultāts", fontsize=14, fontweight='bold')
        ax2.grid(axis='y', linestyle="--", alpha=0.6)  # Horizontal grid lines
        ax2.legend()

        # Adjust the layout so everything fits
        plt.tight_layout()
        plt.show()

    # Add the submit button for statistics
    statistics_submit_button = Button(root, text="Apstiprināt", command=on_statistics_submit)
    statistics_submit_button.pack()

def start_game():
    global current_question_index, correct_answers, wrong_answers, user_id, questions
    
    # Ensure the user is authenticated
    user_id = authenticate_user()
    if not user_id:
        messagebox.showerror("Kļūda", "Nepareizs lietotājvārds vai parole!")
        return

    # Clear input fields for new game (reset the entry widgets)
    username_entry.delete(0, 'end')
    password_entry.delete(0, 'end')

    # Prepare questions for the game
    questions = [
        ("Cik ir 5 + 3?", "8"),
        ("Kas ir Latvijas galvaspilsēta?", "Rīga"),
        ("Kāds ir 2 * 6?", "12"),
        ("Kurš ir lielākais planētas okeāns?", "Klusais"),
        ("Cik ir 10 / 2?", "5")
    ]
    
    random.shuffle(questions)

    correct_answers = 0
    wrong_answers = 0
    current_question_index = 0

    # Hide the login UI elements only for the game
    login_label.pack_forget()
    username_entry.pack_forget()
    password_entry.pack_forget()
    register_button.pack_forget()
    login_button.pack_forget()
    statistics_button.pack_forget()

    # Show the game interface
    question_label.pack()
    answer_entry.pack()
    submit_answer_button.pack()

    show_next_question()

def show_next_question():
    global current_question_index
    
    if current_question_index < len(questions):
        question_label.config(text=questions[current_question_index][0])
        answer_entry_var.set("")
    else:
        end_game(user_id, correct_answers, wrong_answers)

def check_answer():
    global current_question_index, correct_answers, wrong_answers
    
    user_answer = answer_entry_var.get().strip()
    correct_answer = questions[current_question_index][1]

    if user_answer.lower() == correct_answer.lower():
        correct_answers += 1
    else:
        wrong_answers += 1

    current_question_index += 1
    show_next_question()

def end_game(user_id, correct, wrong):
    # Clear the window
    for widget in root.winfo_children():
        widget.pack_forget()

    # Display "Spēle beigusies" message
    Label(root, text="Spēle beigusies!", font=("Arial", 16, "bold")).pack(pady=10)
    Label(root, text=f"Pareizās atbildes: {correct}", font=("Arial", 14)).pack()
    Label(root, text=f"Nepareizās atbildes: {wrong}", font=("Arial", 14)).pack()

    # Save the game result
    save_result(user_id, correct, wrong)

    # Buttons to either play again, see statistics, or exit
    Button(root, text="Spēlēt vēlreiz", command=start_game, font=("Arial", 12), width=15).pack(pady=5)
    Button(root, text="Rādīt statistiku", command=show_statistics, font=("Arial", 12), width=15).pack(pady=5)
    Button(root, text="Iziet", command=root.quit, font=("Arial", 12), width=15, bg="red", fg="white").pack(pady=10)

# Tkinter UI
root = Tk()
root.title("Spēle: Matemātika un vispārīgās zināšanas")

# Pieteikšanās UI
login_label = Label(root, text="Lietotājvārds:")
login_label.pack()
username_entry = Entry(root)
username_entry.pack()

Label(root, text="Parole:").pack()
password_entry = Entry(root, show="*")
password_entry.pack()

register_button = Button(root, text="Reģistrēties", command=register_user)
register_button.pack()

login_button = Button(root, text="Pieslēgties un sākt spēli", command=start_game)
login_button.pack()

statistics_button = Button(root, text="Parādīt statistiku", command=show_statistics)
statistics_button.pack()

# Spēles UI (sākumā slēpts)
question_label = Label(root, text="", font=("Arial", 14))
answer_entry_var = StringVar()
answer_entry = Entry(root, textvariable=answer_entry_var)
submit_answer_button = Button(root, text="Iesniegt atbildi", command=check_answer)

# Izveido datubāzi, ja nepieciešams
setup_db()

# Palaiž Tkinter
root.mainloop()
