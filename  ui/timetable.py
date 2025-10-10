import customtkinter as ctk

class Timetable(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="🕒 Weekly Timetable", font=("Arial", 20, "bold")).pack(pady=10)

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for d in days:
            ctk.CTkLabel(self, text=f"{d}: Class @ 10 AM", font=("Arial", 14)).pack(pady=5)