import sys
import traceback
import os
import inspect
from datetime import datetime

# Import PyQt6 modules
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor

# Import Gemini API
import google.generativeai as genai

# --- 0. Configure Gemini API ---
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = "YOUR_GEMINI_API_KEY" # Placeholder
    if api_key == "YOUR_GEMINI_API_KEY" or not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set or placeholder used. Please configure your API key.")
    genai.configure(api_key=api_key)
    print("[INFO] Gemini API configured successfully.")
except Exception as e:
    print(f"FATAL ERROR: Gemini API key configuration failed. Error: {e}")
    sys.exit(1)

# --- A NEW, SIMPLE APPLICATION WITH AN INTENTIONAL ERROR ---

def divide_numbers(numerator, denominator):
    """
    Divides two numbers.
    """
    print(f"Attempting to divide {numerator} by {denominator}...")
    result = numerator / denominator
    return result

def process_data(data_list):
    """
    Processes a list of numbers by performing a division.
    """
    total_sum = 0
    for i, item in enumerate(data_list):
        try:
            value = divide_numbers(item, 2)
            total_sum += value
        except Exception as e:
            print(f"Error processing item {item}: {e}")
            raise # Re-raise to trigger the global error handler
    return total_sum

def my_application_main():
    """
    The main entry point for the demonstration application.
    """
    print("\n--- Running New Demonstration Application ---")
    
    # INTENTIONAL ERROR FOR DEMO: This will cause a ZeroDivisionError
    final_result = divide_numbers(10, 0) 

    # This will run if the error line above is commented out
    # data_points = [10, 20, 30, 40]
    # final_result = process_data(data_points)
    
    print(f"Application finished. Final result: {final_result}")


# --- ERROR FIXING SYSTEM COMPONENTS START HERE ---

# --- 2. Gemini Error Fixing Logic ---
def get_gemini_fix_suggestion(error_info, original_code_snippet):
    """
    Sends error information and original code to Gemini for a fix.
    """
    # *** IMPORTANT CHANGE HERE: Using the correct model name ***
    model = genai.GenerativeModel('models/gemini-2.5-pro') 
    
    prompt = f"""
    A Python application encountered an error. Please analyze the error information and provide a corrected version of the relevant code snippet.
    Provide ONLY the corrected code snippet, nothing else. If you cannot fix it, return "NO_FIX_AVAILABLE".

    Error Type: {error_info.get('type', 'Unknown')}
    Error Message: {error_info.get('message', 'No message')}
    Traceback:
    {error_info.get('traceback', 'No traceback')}

    Original Code Snippet (from the function that caused the error, if available/relevant):
    ```python
    {original_code_snippet}
    ```

    Corrected Code:
    """
    try:
        print("\n[Gemini] Sending prompt to Gemini API...")
        response = model.generate_content(prompt)
        fix_code = response.text.strip()

        if fix_code.startswith("```python"):
            fix_code = fix_code[len("```python"):].strip()
        if fix_code.endswith("```"):
            fix_code = fix_code[:-len("```")].strip()

        if not fix_code:
            return "NO_FIX_AVAILABLE"

        print("[Gemini] Fix received.")
        return fix_code
    except Exception as e:
        print(f"[Gemini] Error calling Gemini API: {e}")
        QMessageBox.critical(None, "Gemini API Error", f"Failed to get fix from Gemini: {e}")
        return "NO_FIX_AVAILABLE"

# --- 3. PyQt6 UI for Confirmation ---
class ErrorFixConfirmationUI(QWidget):
    def __init__(self, error_info, original_code, suggested_fix):
        super().__init__()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [UI] ErrorFixConfirmationUI __init__ started (PyQt).")
        self.error_info = error_info
        self.original_code = original_code
        self.suggested_fix = suggested_fix
        self.fix_accepted = False

        self.setWindowTitle("Application Error Detected! - Gemini Fix Suggestion")
        self.setGeometry(100, 100, 900, 700) # x, y, width, height

        self.setup_ui()
        self.show() # Show the window immediately
        self.raise_() # Bring to front
        self.activateWindow() # Activate the window

        # Store the application instance to manage its event loop later
        self.app_instance = QApplication.instance()
        
        # We need to run a local event loop for this modal dialog,
        # otherwise, it won't be interactive.
        self._loop = True
        while self._loop:
            self.app_instance.processEvents() # Process events in this window
            QApplication.processEvents() # Process any other pending events
            QTimer.singleShot(10, lambda: None) # Small delay to yield control (non-blocking)

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Set a monospaced font for code displays
        code_font = QFont("Consolas", 10)
        # Fallback fonts for other OS if Consolas isn't available
        if sys.platform == "darwin": # macOS
             code_font = QFont("Monaco", 10)
        elif sys.platform == "linux": # Linux
             code_font = QFont("DejaVu Sans Mono", 10)

        # Error Details
        main_layout.addWidget(QLabel("<b>Error Details:</b>"))
        error_text_edit = QTextEdit()
        error_text_edit.setReadOnly(True)
        error_text_edit.setText(
            f"Type: {self.error_info.get('type', 'N/A')}\n"
            f"Message: {self.error_info.get('message', 'N/A')}\n\n"
            f"Traceback:\n{self.error_info.get('traceback', 'N/A')}"
        )
        error_text_edit.setFont(code_font)
        error_text_edit.setFixedHeight(120) # Fixed height for error details
        main_layout.addWidget(error_text_edit)

        # Original Code
        main_layout.addWidget(QLabel("<b>Original Code Snippet (from the erroring function):</b>"))
        original_code_text_edit = QTextEdit()
        original_code_text_edit.setReadOnly(True)
        original_code_text_edit.setText(self.original_code)
        original_code_text_edit.setFont(code_font)
        original_code_text_edit.setFixedHeight(180) # Fixed height for original code
        main_layout.addWidget(original_code_text_edit)

        # Suggested Fix
        main_layout.addWidget(QLabel("<b>Gemini Suggested Fix:</b>"))
        self.suggested_fix_text_edit = QTextEdit()
        self.suggested_fix_text_edit.setReadOnly(True)
        self.suggested_fix_text_edit.setText(self.suggested_fix if self.suggested_fix != "NO_FIX_AVAILABLE" else "Gemini could not provide a fix for this error or the fix was empty.")
        self.suggested_fix_text_edit.setFont(code_font)
        self.suggested_fix_text_edit.setFixedHeight(180) # Fixed height for suggested fix
        main_layout.addWidget(self.suggested_fix_text_edit)

        # Buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        self.accept_button = QPushButton("Accept Fix and Save")
        self.accept_button.clicked.connect(self.accept_fix)
        button_layout.addWidget(self.accept_button)

        self.reject_button = QPushButton("Reject Fix (Continue with Error)")
        self.reject_button.clicked.connect(self.reject_fix)
        button_layout.addWidget(self.reject_button)

        if self.suggested_fix == "NO_FIX_AVAILABLE" or not self.suggested_fix.strip():
            self.accept_button.setEnabled(False)
            self.accept_button.setText("No Fix Available")

    def accept_fix(self):
        self.fix_accepted = True
        QMessageBox.information(self, "Fix Accepted", "The suggested fix has been accepted. Attempting to save to file.")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [UI] accept_fix called. Closing UI (PyQt).")
        self._loop = False # IMPORTANT: Exit the local event loop *before* closing the window
        self.close() # Close the PyQt window

    def reject_fix(self):
        self.fix_accepted = False
        QMessageBox.warning(self, "Fix Rejected", "The suggested fix has been rejected. The application will continue without applying the fix.")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [UI] reject_fix called. Closing UI (PyQt).")
        self._loop = False # IMPORTANT: Exit the local event loop *before* closing the window
        self.close() # Close the PyQt window

    def closeEvent(self, event):
        # This method is called when the window is closed (e.g., by clicking 'X' or self.close()).
        # We only set fix_accepted to False if it wasn't already set to True by an explicit 'Accept' click.
        if not self.fix_accepted: # If it's not already true, it implies the user closed it without accepting.
            self.fix_accepted = False
            # Only show warning if not already handled by accept/reject
            QMessageBox.warning(self, "Fix Not Applied", "Window closed without accepting fix. Fix not applied.")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [UI] closeEvent called. Fix was not accepted. Closing UI (PyQt).")
        else:
            # If fix_accepted is True, it means 'accept_fix' was called.
            # No need to show a warning or reset fix_accepted.
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [UI] closeEvent called. Fix was accepted. Closing UI (PyQt).")
        
        self._loop = False # Ensure the local event loop exits
        event.accept() # Accept the close event, allowing the window to close

    def get_user_decision(self):
        return self.fix_accepted

# --- 4. Code Patching Logic (DEMO-SPECIFIC) ---
def apply_function_code_fix(filepath, target_function_name, new_code_snippet):
    """
    !!! IMPORTANT: This function is highly simplified for demonstration purposes ONLY. !!!
    It attempts to replace the *entire content* of a specific function within the *current file*.
    """
    print(f"\n[Patcher] Applying fix to: {filepath} for function '{target_function_name}'")
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        new_lines = []
        in_target_function = False
        function_def_indent = 0
        found_target_function_def = False

        for i, line in enumerate(lines):
            stripped_line = line.lstrip()
            current_indent = len(line) - len(stripped_line)

            if not found_target_function_def and stripped_line.startswith(f"def {target_function_name}("):
                new_lines.append(line)
                found_target_function_def = True
                in_target_function = True
                function_def_indent = current_indent
                print(f"[Patcher] Found target function '{target_function_name}' at line {i+1} with indent {function_def_indent}.")

                body_indent_prefix = ' ' * (function_def_indent + 4)
                new_lines.append(f"{body_indent_prefix}\"\"\"\n")
                new_lines.append(f"{body_indent_prefix}Corrected by Gemini on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                new_lines.append(f"{body_indent_prefix}Original error type: {os.environ.get('LAST_ERROR_TYPE', 'Unknown')}\n")
                new_lines.append(f"{body_indent_prefix}Original error message: {os.environ.get('LAST_ERROR_MESSAGE', 'Unknown')}\n")
                new_lines.append(f"{body_indent_prefix}\"\"\"\n")

                for fix_line in new_code_snippet.splitlines():
                    if fix_line.strip() or fix_line.isspace(): # Also add blank lines if they are part of the fix
                        new_lines.append(f"{body_indent_prefix}{fix_line}\n")
                print(f"[Patcher] Replaced content for function '{target_function_name}'.")
                continue

            if in_target_function:
                # This logic assumes the function body is consistently indented more than the def line.
                # It stops when it hits a line with equal or less indentation that is not a comment.
                if stripped_line and current_indent <= function_def_indent and not stripped_line.startswith('#'):
                    in_target_function = False
                    new_lines.append(line) # Add the line that broke the function block
                    print(f"[Patcher] Exited function block at line {i+1}.")
                else:
                    # Skip lines that are part of the old function body
                    continue
            else:
                new_lines.append(line)

        if not found_target_function_def:
            print(f"[Patcher] Error: Could not find function definition for '{target_function_name}' in the file.")
            QMessageBox.critical(None, "Patching Error", f"Could not find function '{target_function_name}' to patch.")
            return False

        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        print(f"[Patcher] Code successfully written to {filepath}.")
        return True
    except Exception as e:
        print(f"[Patcher] Failed to apply fix to file: {e}")
        traceback.print_exc()
        QMessageBox.critical(None, "Patching Error", f"Failed to write fix to file: {e}")
        return False

# --- 5. Main Error Handling and UI Orchestration (Direct Call) ---
def handle_application_error(exc_type, exc_value, exc_traceback):
    # We no longer pass the Tkinter root, as PyQt has its own QApplication
    os.environ['LAST_ERROR_TYPE'] = exc_type.__name__
    os.environ['LAST_ERROR_MESSAGE'] = str(exc_value)

    error_info = {
        "type": exc_type.__name__,
        "message": str(exc_value),
        "traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    }
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] --- APPLICATION ERROR DETECTED ---")
    print(error_info)

    current_script_path = os.path.abspath(__file__)
    function_that_errored_name = "unknown_function"
    original_code_snippet = "Could not retrieve original code. Check traceback for file and line details."

    try:
        target_func_obj = None
        for frame_info in reversed(traceback.extract_tb(exc_traceback)):
            if os.path.abspath(frame_info.filename) == current_script_path:
                function_that_errored_name = frame_info.name
                target_func_obj = globals().get(function_that_errored_name)
                if target_func_obj and inspect.isfunction(target_func_obj):
                    break
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [Handler] Warning: Function '{function_that_errored_name}' found in traceback but not as a top-level function object.")
                    target_func_obj = None
        
        if target_func_obj:
            source_lines, start_line_num = inspect.getsourcelines(target_func_obj)
            original_code_snippet = "".join(source_lines)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [Handler] Original code snippet extracted for '{function_that_errored_name}'.")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [Handler] Could not reliably retrieve source object for function '{function_that_errored_name}'. Falling back to patching my_application_main.")
            original_code_snippet = "No specific function source retrieved. Attempting to get source for 'my_application_main'.\n\n"
            try:
                main_source_lines, _ = inspect.getsourcelines(my_application_main)
                original_code_snippet += "".join(main_source_lines)
            except Exception as src_err:
                original_code_snippet += f"(Error getting source for my_application_main: {src_err})\n\n" + "Defaulting to: " + original_code_snippet
            
            function_that_errored_name = "my_application_main"

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [Handler] Critical Warning: Error during source code retrieval for '{function_that_errored_name}'. Error: {e}")
        original_code_snippet = f"Error retrieving source code: {e}\n\n" + original_code_snippet
        function_that_errored_name = "my_application_main"

    try:
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f"[{current_time}] [Handler] Attempting to create ErrorFixConfirmationUI instance (PyQt)...")
        suggested_fix = get_gemini_fix_suggestion(error_info, original_code_snippet)
        print(f"[{current_time}] [Handler] Suggested fix generated/retrieved. Creating UI (PyQt)...")
        
        # Instantiate and show the PyQt window
        fix_ui = ErrorFixConfirmationUI(error_info, original_code_snippet, suggested_fix)
        
        print(f"[{current_time}] [Handler] ErrorFixConfirmationUI creation returned. Checking user decision (PyQt).")

    except Exception as ui_error:
        print(f"[{current_time}] [Handler] FATAL ERROR: Exception occurred during UI creation or display (PyQt): {ui_error}")
        traceback.print_exc()
        QMessageBox.critical(None, "UI Display Error",
                             "The error handling UI could not be displayed due to an internal error (PyQt). "
                             f"Please check console for details.\nError: {ui_error}")
        # Re-raise the *original* exception, not the UI error
        raise exc_value.with_traceback(exc_traceback)

    if fix_ui.get_user_decision() and suggested_fix != "NO_FIX_AVAILABLE":
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [Handler] User accepted the fix! Attempting to apply...")
        if apply_function_code_fix(current_script_path, function_that_errored_name, suggested_fix):
            QMessageBox.information(None, "Fix Applied", "Code file updated successfully. Please restart this script to run with the fix!")
            sys.exit(0) # Exit cleanly after applying fix
        else:
            QMessageBox.critical(None, "Fix Failed", "Could not apply fix to file. Manual intervention required. See console for details.")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [Handler] User rejected the fix or no fix was available.")
        QMessageBox.warning(None, "Fix Not Applied", "Fix not applied. The application may continue to encounter the error.")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] --- Error handler finished. Re-raising original exception ---")
    raise exc_value.with_traceback(exc_traceback) # Re-raise the original exception


# --- Main application entry point ---
if __name__ == "__main__":
    # Create the QApplication instance once at the start of the program
    app = QApplication(sys.argv)

    # --- Welcome Popup Test (PyQt6 version) ---
    welcome_box = QMessageBox()
    welcome_box.setIcon(QMessageBox.Icon.Information)
    welcome_box.setText("Welcome to the App!")
    welcome_box.setInformativeText("This is a test of your PyQt6 display capabilities. Click OK to proceed.")
    welcome_box.setWindowTitle("Welcome")
    welcome_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    welcome_box.exec()
    print("[INFO] Welcome popup displayed and closed.")
    # --- END NEW ---

    print("Application starting...")
    try:
        my_application_main() # This is where the intentional error occurs
        print("Application finished successfully without errors. Exiting.")
        sys.exit(0)
    except Exception as e:
        # Directly call our error handler with necessary info
        print(f"Application caught an error in main block: {e}. Calling custom error handler.")
        handle_application_error(type(e), e, e.__traceback__)
    
    print("Exiting main application loop.")
    sys.exit(app.exec()) # Ensure the PyQt application runs its event loop and exits cleanly