import customtkinter as ctk

class Attendance(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="📅 Attendance Tracker", font=("Arial", 20, "bold")).pack(pady=10)
        self.total = ctk.CTkEntry(self, placeholder_text="Total Classes")
        self.total.pack(pady=5)
        self.attended = ctk.CTkEntry(self, placeholder_text="Attended Classes")
        self.attended.pack(pady=5)
        ctk.CTkButton(self, text="Calculate Attendance", command=self.calculate).pack(pady=10)
        self.result = ctk.CTkLabel(self, text="")
        self.result.pack()

    def calculate(self):
        try:
            t = int(self.total.get())
            a = int(self.attended.get())
            percent = (a/t)*100
            self.result.configure(text=f"Attendance: {percent:.2f}%")
        except:
            self.result.configure(text="⚠️ Please enter valid numbers")