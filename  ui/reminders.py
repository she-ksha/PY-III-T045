import customtkinter as ctk

class Reminders(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="📝 Reminders", font=("Arial", 20, "bold")).pack(pady=10)
        ctk.CTkLabel(self, text="Set your assignments and exam reminders here.", font=("Arial", 14)).pack(pady=5)