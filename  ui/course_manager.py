import customtkinter as ctk
from utils.db_helper import insert_course, fetch_courses
from utils.helpers import show_info

class CourseManager(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="📚 Course Manager", font=("Arial", 20, "bold")).pack(pady=10)

        self.name = ctk.CTkEntry(self, placeholder_text="Course Name")
        self.name.pack(pady=5)
        self.code = ctk.CTkEntry(self, placeholder_text="Course Code")
        self.code.pack(pady=5)
        ctk.CTkButton(self, text="Add Course", command=self.add_course).pack(pady=10)

        self.listbox = ctk.CTkTextbox(self, height=250, width=400)
        self.listbox.pack(pady=10)
        self.refresh_list()

    def add_course(self):
        name = self.name.get().strip()
        code = self.code.get().strip()
        if name and code:
            insert_course(name, code)
            show_info("✅ Course added successfully!")
            self.name.delete(0, "end")
            self.code.delete(0, "end")
            self.refresh_list()
        else:
            show_info("Please enter both name and code")

    def refresh_list(self):
        self.listbox.delete("1.0", "end")
        for cid, name, code in fetch_courses():
            self.listbox.insert("end", f"ID:{cid} | {name} ({code})\n")
            