import sys
import io
import os
import json
import ast
from datetime import datetime
from game_engine.adventure_engine import AdventureEngine

class SystemIntegrator:

    """
    The SystemIntegrator acts as the bridge between the Frontend  
    and the Backend. It handles code execution, 
    I/O redirection, and state management.
    """

    def __init__(self):
        self.engine = AdventureEngine()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.drafts_file = os.path.join(self.base_dir, "user_drafts.json")
        self.progress_file = os.path.join(self.base_dir, "user_progress.json")

    # --- CONTENT MANAGEMENT ---
    def load_content(self, mode, key):
        """Pass-through to engine to set state and retrieve content."""
        self.engine.set_mode(mode, key)
        return self.engine.get_current_content()

    def get_next_lesson_key(self):
        """Calculates the next lesson key based on current progress."""
        if self.engine.mode != "lesson": 
            return None
        
        all_keys = list(self.engine.lessons.keys())
        try:
            current_index = all_keys.index(self.engine.current_key)
            if current_index + 1 < len(all_keys):
                return all_keys[current_index + 1]
        except ValueError:
            pass
        return None

    # --- CODE EXECUTION SANDBOX ---

    def execute_code(self, user_code):
        """
        Captures the stdout of the user's code, runs it safely, 
        and validates it against the engine's requirements.
        """
        # Capture Standard Output 
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        runtime_error = None

        # Execute Code
        try:
            safe_globals = {
                        '__builtins__': {
                            'print': print,
                            'len': len,
                            'range': range,
                            'int': int,
                            'str': str,
                            'float': float,
                            'bool': bool,
                            'list': list,
                            'dict': dict,
                            'tuple': tuple,
                            'set': set,
                            'abs': abs,
                            'min': min,
                            'max': max,
                            'sum': sum,
                            'round': round,
                            'type': type,
                            'isinstance': isinstance,
                            'True': True,
                            'False': False,
                            'None': None,
                        },
                        # This allows f-strings to work
                        '__name__': '__main__',
                        '__doc__': None,
                    }
            safe_locals = {}
            exec(user_code, safe_globals, safe_locals)
        except Exception as e:
            runtime_error = str(e)
        
        # Restore Standard Output
        sys.stdout = old_stdout
        captured_output = redirected_output.getvalue()

        # Handle Results
        if runtime_error:
            return f"Runtime Error:\n{runtime_error}", False, "Code Crashed"
        
        actual_output = captured_output.strip()
        
        # Check against Engine Logic
        is_correct, message = self.engine.check_answer(actual_output)
        
        # Auto-Save Progress if successful
        if is_correct and self.engine.mode == "lesson":
            self._mark_lesson_complete(self.engine.current_key)

        return actual_output, is_correct, message
    

    # --- DEBUGGER ---
    def scan_syntax(self, code_text):
        
        """
        Static analysis of code to find syntax errors before running.
        """
        try:
            ast.parse(code_text)
            return True, "✅ No Syntax Errors Found. Logic looks valid."
        except SyntaxError as e:
            error_msg = f"❌ Syntax Error on Line {e.lineno}:\n{e.msg}"
            if "expected ':'" in e.msg:
                error_msg += "\n(Hint: Missing colon after if/def/while?)"
            return False, error_msg
        except Exception as e:
            return False, f"Debugger Error: {str(e)}"

    # --- SAVE/LOAD ---
    def save_user_draft(self, code_content):
        """Saves current code to the drafts JSON file."""
        if not code_content.strip():
            return False, "Empty code."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = self.engine.get_current_content()
        title = content.get("title", "Free Code")
        
        new_draft = {
            "timestamp": timestamp, 
            "lesson": title, 
            "code": code_content
        }
        
        drafts = self._load_json_file(self.drafts_file)
        drafts.insert(0, new_draft) # Add to top
        
        try:
            with open(self.drafts_file, "w") as f:
                json.dump(drafts, f, indent=4)
            return True, f"Saved Draft: {timestamp}"
        except Exception as e:
            return False, f"Save Failed: {str(e)}"

    def get_user_progress(self):
        """Returns list of completed lesson keys."""
        data = self._load_json_file(self.progress_file)
        return data.get("completed", [])

    def reset_progress(self):
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)

    # --- INTERNAL HELPERS ---
    def _mark_lesson_complete(self, lesson_key):
        data = self._load_json_file(self.progress_file)
        completed = data.get("completed", [])
        if lesson_key not in completed:
            completed.append(lesson_key)
            with open(self.progress_file, "w") as f:
                json.dump({"completed": completed}, f)

    def _load_json_file(self, filepath):
        if not os.path.exists(filepath):
            return [] if "drafts" in filepath else {}
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except:
            return [] if "drafts" in filepath else {}