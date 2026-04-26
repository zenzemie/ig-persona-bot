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
            raise ValueError("IG_USERNAME or IG_PASSWORD not found in environment variables")
        self.session_file = "session.json"

    def _load_persona(self):
        if os.path.exists("persona.json"):
            with open("persona.json", "r") as f:
                return json.load(f)
        return {
            "tone": "friendly and helpful",
            "vocabulary": [],
            "rules": [],
            "summary": "A helpful assistant."
        }

    def login(self):
        if os.path.exists(self.session_file):
            try:
                self.cl.load_settings(self.session_file)
                print("Loaded session from file.")
            except Exception as e:
                print(f"Could not load session: {e}")

        try:
            # Check if we are already logged in
            if not self.cl.user_id:
                print("Attempting login...")
                self.cl.login(self.username, self.password)
            else:
                # Test the session
                self.cl.get_timeline_feed()
                print("Session is still valid.")
        except Exception as e:
            print(f"Login failed or session expired: {e}. Attempting fresh login.")
            self.cl.login(self.username, self.password)
        
        self.cl.dump_settings(self.session_file)
        self.my_id = self.cl.user_id
        print(f"Logged in as user ID: {self.my_id}")

    def get_response(self, thread_id, user_text):
        history = self.memory.get_history(thread_id)
        
        system_prompt = f"""
        You are an AI version of this persona:
        {json.dumps(self.persona, indent=2)}
        
        Respond to the user's message in a way that perfectly mirrors this persona.
        Keep it natural for Instagram DMs.
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        
        return response.choices[0].message.content

    def run(self):
        print("Agent started. Polling for messages...")
        while True:
            try:
                threads = self.cl.direct_threads(selected_filter='unread')
                for thread in threads:
                    messages = self.cl.direct_messages(thread.id, amount=1)
                    if not messages:
                        continue
                    
                    last_msg = messages[0]
                    if str(last_msg.user_id) == str(self.my_id) or not last_msg.text:
                        continue
                    
                    print(f"New message from {last_msg.user_id}: {last_msg.text}")
                    
                    # Store user message
                    self.memory.add_message(thread.id, last_msg.user_id, last_msg.text)
                    
                    # Check if we should reply (avoid duplicate replies if polling is fast)
                    if not self.memory.is_last_message_from_me(thread.id):
                        response_text = self.get_response(thread.id, last_msg.text)
                        
                        # Simulate typing delay
                        typing_time = len(response_text) * 0.05 + random.uniform(1, 3)
                        print(f"Simulating typing for {typing_time:.2f}s...")
                        time.sleep(min(typing_time, 10))
                        
                        self.cl.direct_send(response_text, thread_ids=[thread.id])
                        print(f"Sent response: {response_text}")
                        
                        # Store my message
                        self.memory.add_message(thread.id, "me", response_text)
                        
                    # Mark as read
                    self.cl.direct_send_seen(thread.id)

                # Random sleep to avoid rate limiting
                sleep_time = random.randint(60, 120)
                print(f"Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    agent = InstagramAgent()
    agent.login()
    agent.run()
