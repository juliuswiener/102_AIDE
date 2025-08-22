#!/usr/bin/env python3
import subprocess
import threading
import time
import os
import sys

class InteractiveRunner:
    def __init__(self, command):
        self.command = command
        self.session_log = "ai_complete_session.log"
        self.ai_response_file = "ai_response.txt"
        self.process = None
        
    def run(self):
        # Clear previous session
        open(self.session_log, 'w').close()
        
        print("🚀 Starting AI-monitored program...")
        print(f"📄 AI can monitor: {self.session_log}")
        print(f"📝 AI should respond in: {self.ai_response_file}")
        
        # Start the subprocess
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Thread 1: Capture ALL output for AI
        def log_everything():
            with open(self.session_log, 'w') as log:
                for line in self.process.stdout:
                    # Show to human too
                    print(line, end='')
                    # Log for AI
                    log.write(line)
                    log.flush()
        
        # Thread 2: Watch for AI responses and feed them back
        def handle_ai_input():
            while self.process.poll() is None:
                if os.path.exists(self.ai_response_file):
                    try:
                        with open(self.ai_response_file, 'r') as f:
                            response = f.read().strip()
                        
                        if response:
                            print(f"🤖 AI responds: {response}")
                            # Feed to program
                            self.process.stdin.write(response + '\n')
                            self.process.stdin.flush()
                            
                            # Log AI's response too
                            with open(self.session_log, 'a') as log:
                                log.write(f"[AI INPUT]: {response}\n")
                                log.flush()
                            
                            # Remove response file
                            os.remove(self.ai_response_file)
                    
                    except Exception as e:
                        print(f"Error reading AI response: {e}")
                
                time.sleep(0.2)  # Check every 200ms
        
        # Start both threads
        output_thread = threading.Thread(target=log_everything, daemon=True)
        input_thread = threading.Thread(target=handle_ai_input, daemon=True)
        
        output_thread.start()
        input_thread.start()
        
        # Wait for program to finish
        self.process.wait()
        print("\n✅ Program finished")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python interactive_runner.py your_program [args...]")
        sys.exit(1)
    
    # Add the project root to the PYTHONPATH
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    command = ["python", "-m", "aide.src.aide.app"] + sys.argv[1:]
    runner = InteractiveRunner(command)
    runner.run()
