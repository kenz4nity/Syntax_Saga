import customtkinter as ctk
import sys
import io
import re
import os
import json
import ast 
from datetime import datetime
from tkinter import filedialog
from game_engine.adventure_engine import AdventureEngine 

# --- CONFIG ---
COLOR_BG = "#050A30"        
COLOR_PANEL = "#84A9FF"     
COLOR_SIDEBAR = "#000C66"
COLOR_TEXT_BLACK = "#000000"
COLOR_EDITOR_BG = "#1A1A1A" 
COLOR_KEYWORD = "#FF7F50"   
COLOR_STRING = "#98FB98"    
COLOR_BUILTIN = "#FF00FF"
COLOR_CHALLENGE = "#FF4444" 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class SyntaxSagaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.engine = AdventureEngine()
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.drafts_file = os.path.join(base_dir, "user_drafts.json")
        self.progress_file = os.path.join(base_dir, "user_progress.json")

        self.title("Syntax Saga - Final Fixed")
        self.geometry("1200x800")
        self.configure(fg_color=COLOR_BG) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.setup_ui()
        
        # Start at Lessons Menu
        self.show_lessons()

    def setup_ui(self):
        # TOP BAR
        self.top_bar = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color=COLOR_BG)
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.btn_run = ctk.CTkButton(self.top_bar, text="RUN", width=60, fg_color="transparent", hover_color=COLOR_SIDEBAR, font=("Arial", 12, "bold"), command=self.run_code_logic)
        self.btn_run.pack(side="left", padx=10, pady=5)

        self.btn_open = ctk.CTkButton(self.top_bar, text="OPEN FILE", width=80, fg_color="transparent", hover_color=COLOR_SIDEBAR, font=("Arial", 12), command=self.open_file)
        self.btn_open.pack(side="left", padx=5, pady=5)
        
        self.btn_save = ctk.CTkButton(self.top_bar, text="SAVE DRAFT", width=80, fg_color="transparent", hover_color=COLOR_SIDEBAR, font=("Arial", 12), command=self.save_draft)
        self.btn_save.pack(side="left", padx=5, pady=5)
        
        self.btn_debug = ctk.CTkButton(self.top_bar, text="DEBUG", width=80, fg_color="transparent", hover_color=COLOR_SIDEBAR, font=("Arial", 12), command=self.run_debugger)
        self.btn_debug.pack(side="left", padx=5, pady=5)

        # NEXT BUTTON: Created but NOT packed. It only appears in Lessons.
        self.btn_next = ctk.CTkButton(self.top_bar, text="NEXT >", width=80, fg_color="transparent", hover_color=COLOR_SIDEBAR, font=("Arial", 12, "bold"), command=self.load_next_lesson)
        
        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1) 

        self.create_sidebar_btn("LESSONS", self.show_lessons)
        self.create_sidebar_btn("CHALLENGES", self.show_challenges)
        self.create_sidebar_btn("DRAFTS", self.show_drafts)
        self.create_sidebar_btn("PROGRESS", self.show_progress) 
        self.create_sidebar_btn("EDITOR / DEBUG", self.show_editor)

        # MAIN CONTENT
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        self.frame_lessons = self.build_lessons_view()
        self.frame_challenges = self.build_challenges_view()
        self.frame_drafts = self.build_drafts_view() 
        self.frame_progress = self.build_progress_view() 
        self.frame_editor = self.build_editor_view()

    # --- CORE LOGIC ---

    def load_content(self, mode, key):
        self.engine.set_mode(mode, key)
        self.show_editor() 
        # Note: show_editor() now calls update_editor_instructions() automatically

    def update_editor_instructions(self):
        content = self.engine.get_current_content()
        if not content:
            self.lbl_story.configure(text="ERROR: Content is empty.")
            return

        title = content.get('title', 'Unknown')
        story = content.get('reading') or content.get('description', '')
        mission = content.get('challenge_objective') or "Objective: Match the expected output."
        
        # --- DYNAMIC BUTTON LOGIC ---
        if self.engine.mode == "challenge":
            # Boss Mode: Hide Next Button
            self.btn_next.pack_forget()
            self.lbl_status.configure(text=f"⚔️ BOSS FIGHT: {title}", text_color=COLOR_CHALLENGE)
            self.input_box.configure(border_color=COLOR_CHALLENGE, border_width=2)
        else:
            # Lesson Mode: Show Next Button
            # We pack it ONLY if it's not already there
            if not self.btn_next.winfo_ismapped():
                self.btn_next.pack(side="right", padx=10, pady=5)
            
            self.lbl_status.configure(text=f"Current Objective: {title}", text_color="white")
            self.input_box.configure(border_color="black", border_width=2)

        full_text = f"--- BRIEFING ---\n{story}\n\n--- MISSION ---\n{mission}"
        self.lbl_story.configure(state="normal")
        self.lbl_story.delete("0.0", "end")
        self.lbl_story.insert("0.0", full_text)
        self.lbl_story.configure(state="disabled")

    def load_next_lesson(self):
        if self.engine.mode != "lesson": return
        completed = self.get_completed_lessons()
        if self.engine.current_key not in completed:
            self.lbl_status.configure(text="🔒 Locked! Complete this lesson first.", text_color="#FF5555")
            return

        all_keys = list(self.engine.lessons.keys())
        try:
            current_index = all_keys.index(self.engine.current_key)
            if current_index + 1 < len(all_keys):
                next_key = all_keys[current_index + 1]
                self.load_content("lesson", next_key)
            else:
                self.lbl_status.configure(text="You have completed all lessons!", text_color="gold")
        except: pass

    # --- VIEW NAVIGATION ---
    def hide_all(self): 
        # Always hide the NEXT button when switching views
        self.btn_next.pack_forget()
        for f in [self.frame_lessons, self.frame_challenges, self.frame_drafts, self.frame_editor, self.frame_progress]: 
            f.grid_forget()

    def show_editor(self): 
        self.hide_all()
        self.frame_editor.grid(row=0, column=0, sticky="nsew")
        # FIX: We MUST call this to restore the button if we are in Lesson Mode
        self.update_editor_instructions()

    def show_lessons(self): 
        self.hide_all()
        self.frame_lessons = self.build_lessons_view()
        self.frame_lessons.grid(row=0, column=0, sticky="nsew")

    def show_challenges(self): 
        self.hide_all()
        self.frame_challenges.grid(row=0, column=0, sticky="nsew")

    def show_drafts(self): 
        self.hide_all()
        self.frame_drafts = self.build_drafts_view()
        self.frame_drafts.grid(row=0, column=0, sticky="nsew")

    def show_progress(self): 
        self.hide_all()
        self.frame_progress = self.build_progress_view()
        self.frame_progress.grid(row=0, column=0, sticky="nsew")

    # --- DEBUGGER ---
    def run_debugger(self):
        self.show_editor()
        user_code = self.input_box.get("1.0", "end").strip()
        if not user_code:
            self.lbl_status.configure(text="⚠️ Editor is empty.", text_color="gold")
            return
        self.output_box.delete("1.0", "end")
        try:
            ast.parse(user_code)
            self.lbl_status.configure(text="✅ No Syntax Errors Found.", text_color="#00FF00")
            self.output_box.insert("end", "Debugger: The code structure looks valid.\nPress RUN to execute it.")
        except SyntaxError as e:
            self.lbl_status.configure(text=f"❌ Syntax Error on Line {e.lineno}", text_color="#FF5555")
            error_msg = f"Debugger Report:\n----------------\nError: {e.msg}\nLine:  {e.lineno}\n"
            if e.text: error_msg += f"Code:  {e.text.strip()}\n       {' ' * (e.offset - 1) if e.offset else ''}^\n"
            if "expected ':'" in e.msg: error_msg += "\nHint: Did you forget a colon at the end of your if/else/def line?"
            elif "unexpected indent" in e.msg: error_msg += "\nHint: Check your indentation. Blocks of code must line up perfectly."
            elif "was never closed" in e.msg: error_msg += "\nHint: You have an open ( or \" that was not closed."
            self.output_box.insert("end", error_msg)
        except Exception as e:
            self.output_box.insert("end", f"Debugger Error: {str(e)}")

    # --- RUN LOGIC ---
    def run_code_logic(self):
        self.show_editor()
        user_code = self.input_box.get("1.0", "end").strip()
        old_stdout = sys.stdout; redirected_output = io.StringIO(); sys.stdout = redirected_output; runtime_error = None
        try: exec(user_code, globals()) 
        except Exception as e: runtime_error = str(e)
        sys.stdout = old_stdout; captured_output = redirected_output.getvalue()

        self.output_box.delete("1.0", "end")
        if runtime_error:
            self.output_box.insert("end", f"Runtime Error:\n{runtime_error}")
            actual_result = "ERROR"
        else:
            self.output_box.insert("end", captured_output)
            actual_result = captured_output.strip()

        is_correct, message = self.engine.check_answer(actual_result)
        
        if is_correct:
            self.lbl_status.configure(text=f"✅ SUCCESS: {message}", text_color="#00FF00")
            if self.engine.mode == "lesson" and self.engine.current_key:
                self.mark_lesson_complete(self.engine.current_key)
        else:
            self.lbl_status.configure(text=f"❌ FAILED: {message}", text_color="#FF5555")

    # --- SAVE/LOAD ---
    def get_completed_lessons(self):
        if not os.path.exists(self.progress_file): return []
        try:
            with open(self.progress_file, "r") as f:
                return json.load(f).get("completed", [])
        except: return []

    def mark_lesson_complete(self, lesson_key):
        completed = self.get_completed_lessons()
        if lesson_key not in completed:
            completed.append(lesson_key)
            with open(self.progress_file, "w") as f:
                json.dump({"completed": completed}, f)

    def save_draft(self):
        code_content = self.input_box.get("1.0", "end").strip()
        if not code_content: return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = self.engine.get_current_content()
        title = content.get("title", "Free Code")
        new_draft = {"timestamp": timestamp, "lesson": title, "code": code_content}
        
        drafts = []
        if os.path.exists(self.drafts_file):
            try:
                with open(self.drafts_file, "r") as f:
                    drafts = json.load(f)
            except:
                drafts = []
        
        drafts.insert(0, new_draft)
        with open(self.drafts_file, "w") as f:
            json.dump(drafts, f, indent=4)
        
        self.lbl_status.configure(text=f"Saved Draft: {timestamp}", text_color="#4B7BE5")

    def load_draft_into_editor(self, draft_code):
        self.show_editor()
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", draft_code)
        self.highlight_syntax()
        self.lbl_status.configure(text="Draft Loaded", text_color="#4B7BE5")

    def open_file(self):
        self.show_editor()
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "r") as f:
                self.input_box.delete("1.0", "end")
                self.input_box.insert("1.0", f.read())
                self.highlight_syntax()

    # --- PHASE 9: DELETE LOGIC ---
    def delete_draft(self, index):
        if not os.path.exists(self.drafts_file): return
        try:
            with open(self.drafts_file, "r") as f:
                drafts = json.load(f)
            
            if 0 <= index < len(drafts):
                del drafts[index]
            
            with open(self.drafts_file, "w") as f:
                json.dump(drafts, f, indent=4)
            
            self.show_drafts()
        except: pass

    # --- UI HELPERS ---
    def on_key_release(self, event=None): self.highlight_syntax()
    def highlight_syntax(self):
        text_widget = self.input_box._textbox
        full_text = text_widget.get("1.0", "end")
        for tag in ["keyword", "string", "builtin"]: text_widget.tag_remove(tag, "1.0", "end")
        text_widget.tag_config("keyword", foreground=COLOR_KEYWORD)
        text_widget.tag_config("string", foreground=COLOR_STRING)
        text_widget.tag_config("builtin", foreground=COLOR_BUILTIN)
        self.apply_tag(text_widget, full_text, r"\b(def|class|if|else|elif|return|import|from|while|for)\b", "keyword")
        self.apply_tag(text_widget, full_text, r"\b(print|len|range|int|str|input)\b", "builtin")
        self.apply_tag(text_widget, full_text, r"(\".*?\"|'.*?')", "string")
    def apply_tag(self, widget, text, pattern, tag):
        for match in re.finditer(pattern, text):
            widget.tag_add(tag, f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

    def create_sidebar_btn(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, height=40, anchor="w", fg_color="transparent", hover_color="#4B7BE5", corner_radius=0, command=command)
        btn.pack(fill="x", pady=2)

    # --- VIEWS ---
    def build_lessons_view(self):
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent"); frame.grid_columnconfigure((0,1,2), weight=1)
        lessons_list = list(self.engine.lessons.items()); completed = self.get_completed_lessons()
        for i, (key, data) in enumerate(lessons_list):
            card = ctk.CTkFrame(frame, fg_color=COLOR_PANEL, height=150)
            card.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="nsew")
            title = data.get("title", key)
            is_unlocked = (i==0) or (lessons_list[i-1][0] in completed); is_completed = (key in completed)
            status, color, state = ("✅ COMPLETED", "#00AA00", "normal") if is_completed else ("READY", "#4B7BE5", "normal") if is_unlocked else ("LOCKED", "gray", "disabled")
            ctk.CTkLabel(card, text=title, font=("Arial", 12, "bold"), text_color="black", wraplength=180).pack(pady=(20, 5))
            ctk.CTkLabel(card, text=status, font=("Arial", 10), text_color="black").pack(pady=(0, 10))
            ctk.CTkButton(card, text="START", height=30, fg_color=color, state=state, command=lambda k=key: self.load_content("lesson", k)).pack(pady=10)
        return frame

    def build_challenges_view(self):
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent"); frame.grid_columnconfigure((0,1), weight=1)
        challenges = list(self.engine.challenges.items())
        if not challenges: ctk.CTkLabel(frame, text="No Challenges Loaded", font=("Arial", 20)).pack(pady=20); return frame
        for i, (key, data) in enumerate(challenges):
            card = ctk.CTkFrame(frame, fg_color="#440000", border_color=COLOR_CHALLENGE, border_width=2, height=100)
            card.grid(row=i, column=0, padx=20, pady=10, sticky="ew")
            ctk.CTkLabel(card, text=f"⚔️ {data.get('title', key)}", font=("Arial", 16, "bold"), text_color="white").pack(side="left", padx=20)
            ctk.CTkButton(card, text="ACCEPT CHALLENGE", fg_color=COLOR_CHALLENGE, hover_color="#CC0000", command=lambda k=key: self.load_content("challenge", k)).pack(side="right", padx=20)
        return frame

    def build_drafts_view(self):
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        drafts = []
        if os.path.exists(self.drafts_file):
            try:
                with open(self.drafts_file, "r") as f:
                    drafts = json.load(f)
            except:
                drafts = []
        
        if not drafts: 
            ctk.CTkLabel(frame, text="No Drafts Saved Yet", font=("Arial", 20)).pack(pady=20)
            return frame
        
        for i, draft in enumerate(drafts):
            row_frame = ctk.CTkFrame(frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=5, padx=20)
            btn_text = f"{draft['timestamp']} | {draft['lesson']}"
            ctk.CTkButton(row_frame, text=btn_text, fg_color=COLOR_PANEL, text_color=COLOR_TEXT_BLACK, height=50, corner_radius=10, anchor="w", hover_color="#4B7BE5",
                command=lambda c=draft['code']: self.load_draft_into_editor(c)).pack(side="left", fill="x", expand=True, padx=(0, 10))
            ctk.CTkButton(row_frame, text="DELETE", fg_color="#FF5555", width=80, height=50, corner_radius=10, hover_color="#CC0000",
                command=lambda idx=i: self.delete_draft(idx)).pack(side="right")
        return frame

    def build_progress_view(self):
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        completed = self.get_completed_lessons(); total = len(self.engine.lessons) or 1
        ctk.CTkLabel(frame, text=f"MASTERY: {int((len(completed)/total)*100)}%", font=("Arial", 40, "bold"), text_color="white").pack(pady=(40, 20))
        bar = ctk.CTkProgressBar(frame, width=400, height=20, progress_color="#00AA00"); bar.set(len(completed)/total); bar.pack(pady=20)
        ctk.CTkLabel(frame, text=f"Lessons: {len(completed)} / {total}", font=("Arial", 16)).pack(pady=10)
        ctk.CTkButton(frame, text="RESET PROGRESS", fg_color="#FF5555", command=lambda: [os.remove(self.progress_file) if os.path.exists(self.progress_file) else None, self.show_progress()]).pack(pady=40)
        return frame

    def build_editor_view(self):
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent"); frame.grid_columnconfigure((0,1), weight=1); frame.grid_rowconfigure(0, weight=3); frame.grid_rowconfigure(1, weight=1)
        self.input_box = ctk.CTkTextbox(frame, font=("Consolas", 14), fg_color=COLOR_EDITOR_BG, text_color="white", undo=True, border_color="black", border_width=2)
        self.input_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5); self.input_box._textbox.bind("<KeyRelease>", self.on_key_release)
        self.output_box = ctk.CTkTextbox(frame, font=("Consolas", 14), fg_color=COLOR_EDITOR_BG, text_color="white"); self.output_box.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        bottom_panel = ctk.CTkFrame(frame, fg_color="#334466"); bottom_panel.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)
        self.lbl_status = ctk.CTkLabel(bottom_panel, text="Ready", font=("Arial", 14, "bold"), anchor="w", text_color="white"); self.lbl_status.pack(fill="x", padx=10, pady=5)
        self.lbl_story = ctk.CTkTextbox(bottom_panel, fg_color="transparent", text_color="white", wrap="word", font=("Arial", 12)); self.lbl_story.pack(fill="both", expand=True, padx=10, pady=5)
        return frame

if __name__ == "__main__":
    app = SyntaxSagaApp()
    app.mainloop()