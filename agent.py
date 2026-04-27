import os
import time
import json
import random
from instagrapi import Client
from openai import OpenAI
from dotenv import load_dotenv
from memory import ChatMemory

load_dotenv()

class InstagramAgent:
    def __init__(self):
        self.cl = Client()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.openai_client = OpenAI(api_key=api_key)
        self.memory = ChatMemory()
        self.persona = self._load_persona()
        self.username = os.getenv("IG_USERNAME")
        self.password = os.getenv("IG_PASSWORD")
        if not self.username or not self.password:
            # For local dev, we might not have these yet
            print("Warning: IG_USERNAME or IG_PASSWORD not found in environment variables")
        self.session_file = "session.json"

    def _load_persona(self):
        if os.path.exists("persona.json"):
            try:
                with open("persona.json", "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading persona.json: {e}")
        return {
            "tone": "casual",
            "vocabulary": ["Ion", "frl", "odin din done"],
            "rules": ["always use lowercase", "no periods"],
            "summary": "a casual person"
        }

    def login(self):
        if not self.username or not self.password:
            print("Login failed: Missing credentials.")
            return False

        if os.path.exists(self.session_file):
            try:
                self.cl.load_settings(self.session_file)
                print("Loaded session from file.")
            except Exception as e:
                print(f"Could not load session: {e}")

        try:
            if not self.cl.user_id:
                print("Attempting login...")
                self.cl.login(self.username, self.password)
            else:
                # Test if session is still valid
                try:
                    self.cl.get_timeline_feed()
                    print("Session is still valid.")
                except:
                    print("Session expired. Re-logging in...")
                    self.cl.login(self.username, self.password)
        except Exception as e:
            print(f"Login failed: {e}")
            return False
        
        self.cl.dump_settings(self.session_file)
        self.my_id = self.cl.user_id
        print(f"Logged in as user ID: {self.my_id}")
        return True

    def get_response(self, thread_id, user_text):
        history = self.memory.get_history(thread_id)
        
        system_prompt = f"""
        You are an AI version of this persona:
        {json.dumps(self.persona, indent=2)}
        
        IMPORTANT RULES:
        1. ALWAYS use lowercase ONLY.
        2. NEVER use periods at the end of sentences.
        3. Split your thoughts into multiple short messages using newlines.
        4. Respond to the user's message in a way that perfectly mirrors this persona.
        5. Keep it natural for Instagram DMs. Do not mention you are an AI.
        6. Use slang like 'Ion', 'frl', and 'odin din done' naturally.
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            content = response.choices[0].message.content
            
            # Enforce lowercase and no periods programmatically
            content = content.lower().replace('.', '')
            return content
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return "my bad i can't think rn"

    def run(self):
        print("Agent started. Polling for messages...")
        while True:
            try:
                # Get recent threads
                threads = self.cl.direct_threads(amount=10)
                for thread in threads:
                    # Get recent messages in thread
                    messages = self.cl.direct_messages(thread.id, amount=5)
                    if not messages:
                        continue
                    
                    new_messages_from_user = []
                    for msg in reversed(messages): # Oldest to newest
                        if str(msg.user_id) != str(self.my_id) and msg.text:
                            if not self.memory.message_exists(msg.id):
                                print(f"New message from {msg.user_id} in thread {thread.id}: {msg.text}")
                                self.memory.add_message(thread.id, msg.user_id, msg.text, msg.id)
                                new_messages_from_user.append(msg.text)
                        elif str(msg.user_id) == str(self.my_id):
                            if not self.memory.message_exists(msg.id):
                                self.memory.add_message(thread.id, "me", msg.text, msg.id)

                    if new_messages_from_user:
                        last_text = new_messages_from_user[-1]
                        
                        # Initial hesitation delay
                        time.sleep(random.uniform(1, 3))
                        
                        full_response = self.get_response(thread.id, last_text)
                        
                        # Split response by newlines for "yapping style"
                        messages_to_send = [m.strip() for m in full_response.split('\n') if m.strip()]
                        
                        for part in messages_to_send:
                            # Simulate typing delay
                            typing_speed = random.uniform(0.04, 0.08) # Realistic typing speed
                            typing_time = len(part) * typing_speed + random.uniform(0.5, 1.5)
                            print(f"Simulating typing for {typing_time:.2f}s: {part}")
                            
                            time.sleep(min(typing_time, 10))
                            
                            try:
                                sent_msg = self.cl.direct_send(part, thread_ids=[thread.id])
                                if hasattr(sent_msg, 'id'):
                                    self.memory.add_message(thread.id, "me", part, sent_msg.id)
                                else:
                                    self.memory.add_message(thread.id, "me", part, f"sent_{int(time.time())}_{random.randint(0,1000)}")
                            except Exception as e:
                                print(f"Error sending message: {e}")
                            
                            # Small gap between messages
                            time.sleep(random.uniform(0.5, 2.0))
                        
                        # Mark thread as seen
                        self.cl.direct_send_seen(thread.id)

                # Human-like polling
                if random.random() < 0.05: # 5% chance of a long break
                    sleep_time = random.randint(600, 1500)
                else:
                    sleep_time = random.randint(45, 120)
                    
                print(f"Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"Error in main loop: {e}")
                if "429" in str(e):
                    time.sleep(900)
                else:
                    time.sleep(120)

if __name__ == "__main__":
    agent = InstagramAgent()
    if agent.login():
        agent.run()
    else:
        print("Initial login failed. Waiting 5 minutes before retry...")
        time.sleep(300)
        # In a real 24/7 environment, you might want a loop here or let the orchestrator restart the container
