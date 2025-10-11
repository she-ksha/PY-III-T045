import customtkinter as ctk

class Dashboard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="Welcome to Campus Companion!", font=("Arial", 22, "bold")).pack(pady=30)
        ctk.CTkLabel(self, text="Your all-in-one student companion app", font=("Arial", 14)).pack()