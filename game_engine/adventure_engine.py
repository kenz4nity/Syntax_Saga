import json
import os

class AdventureEngine: 
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 1. Load BOTH files
        self.lessons = self.load_json('adventure_content.json')
        self.challenges = self.load_json('challenges.json')
        
        # 2. State Tracking
        self.mode = "lesson" # Can be "lesson" or "challenge"
        self.current_key = None
        
        # Set default start
        if self.lessons:
            self.current_key = list(self.lessons.keys())[0]

    def load_json(self, filename):
        path = os.path.join(self.base_dir, filename)
        if not os.path.exists(path):
            return {}
        try: 
            with open(path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except:
            return {}
        
    def set_mode(self, mode, key):
        """Switches between Story and Challenge mode"""
        self.mode = mode
        self.current_key = key
        print(f"ENGINE: Switched to {mode} -> {key}")

    def get_current_content(self):
        """Returns the data for the current lesson OR challenge"""
        if not self.current_key: return {}
        
        if self.mode == "lesson":
            return self.lessons.get(self.current_key, {})
        else:
            return self.challenges.get(self.current_key, {})
    
    def check_answer(self, user_output):
        content = self.get_current_content()
        if not content: return False, "No content loaded."

        expected = content.get("expected_output", "").strip()
        user_clean = str(user_output).strip()
        
        if user_clean == expected:
            return True, content.get("success_msg", "Correct!")    
        else:
            return False, content.get("error_hint", "Try again.")