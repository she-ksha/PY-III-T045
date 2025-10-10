import customtkinter as ctk

class GPACalculator(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="🎓 GPA / CGPA Calculator", font=("Arial", 20, "bold")).pack(pady=10)
        self.entry = ctk.CTkEntry(self, placeholder_text="Enter grades (e.g. 8,9,7)")
        self.entry.pack(pady=5)
        ctk.CTkButton(self, text="Calculate", command=self.calc).pack(pady=10)
        self.result = ctk.CTkLabel(self, text="")
        self.result.pack()

    def calc(self):
        try:
            vals = list(map(float, self.entry.get().split(',')))
            gpa = sum(vals)/len(vals)
            self.result.configure(text=f"Your GPA: {gpa:.2f}")
        except:
            self.result.configure(text="⚠️ Enter grades separated by commas")