import json
import os

class AdventureEngine: 
    
    def __init__(self, content_path='game_engine/adventure_content.json'):
        """initializing the engine and loading the story content from a JSON file."""
        self.content_path = content_path
        self.lessons = self.load_content()
        self.current_lesson_key = "Introduction to Python"

    def load_content(self):
        """reads the JSON file created"""
        try: 
            with open(self.content_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Error: adventure_content.json file not found.")
            return{}
        
    def get_current_lesson(self):
        """ retrieves the current lesson based on the current lesson key."""
        return self.lessons.get(self.current_lesson_key, {})
    
    def check_answer(self, user_output):
        """compares the user's output with the expected output for the current lesson."""
        lesson = self.get_current_lesson()
        expect_output = lesson.get("expected_output", "").strip()

        #.strip() is used to ignore accidental extra spaces or newlines
        if user_output.strip() == expect_output:
            return True, lesson.get("success_msg")    
        else:
            return False, lesson.get("error_hint")

    def move_to_next_lesson(self):
        """updates the progress tracker to the next lesson in the sequence."""
        lesson_keys = list(self.lessons.keys())
        current_index = lesson_keys.index(self.current_lesson_key)

        if current_index < len(lesson_keys) - 1:
            self.current_lesson_key = lesson_keys[current_index + 1]
            return True
        return False # No more lessons available
       

#logic for testing the engine
if __name__ == "__main__":
    engine = AdventureEngine()
    print(f"Current Floor: {engine.get_current_lesson().get('title')}")
    
    # Test a "Boss Gate" answer
    success, message = engine.check_answer("I accept the challenge")
    print(f"Success: {success} | Message: {message}")