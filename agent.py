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
            try:
                with open("persona.json", "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading persona.json: {e}")
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
            if not self.cl.user_id:
                print("Attempting login...")
                self.cl.login(self.username, self.password)
            else:
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
        Keep it natural for Instagram DMs. Do not mention you are an AI.
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        # The user_text is already added to memory before calling this, but for the very first message 
        # or if we want to be explicit, we can ensure the history includes the latest message.
        # In our run() loop, we add to memory first. So history already has it.
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        
        return response.choices[0].message.content

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
                            # Record my own messages if they aren't in memory
                            if not self.memory.message_exists(msg.id):
                                self.memory.add_message(thread.id, "me", msg.text, msg.id)

                    if new_messages_from_user:
                        # We have new messages to respond to
                        # If there were multiple messages, we combine them or just respond to the last one
                        # Here we use the whole history which now includes all of them
                        last_text = new_messages_from_user[-1]
                        
                        # Random delay before starting to "type" (human-like hesitation)
                        time.sleep(random.uniform(2, 5))
                        
                        response_text = self.get_response(thread.id, last_text)
                        
                        # Simulate typing delay based on response length
                        # Average typing speed is ~40-60 wpm, roughly 3-5 characters per second
                        typing_speed = random.uniform(0.1, 0.2) 
                        typing_time = len(response_text) * typing_speed + random.uniform(1, 3)
                        print(f"Simulating typing for {typing_time:.2f}s...")
                        time.sleep(min(typing_time, 15)) # Cap typing delay
                        
                        sent_msg = self.cl.direct_send(response_text, thread_ids=[thread.id])
                        print(f"Sent response: {response_text}")
                        
                        # Store my response in memory
                        # sent_msg is a DirectMessage object
                        self.memory.add_message(thread.id, "me", response_text, sent_msg.id)
                        
                        # Mark as read
                        self.cl.direct_send_seen(thread.id)

                # Random sleep to avoid rate limiting and look human
                # Vary between short checks and longer breaks
                if random.random() < 0.1: # 10% chance of a longer break
                    sleep_time = random.randint(300, 600)
                else:
                    sleep_time = random.randint(60, 180)
                    
                print(f"Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    agent = InstagramAgent()
    agent.login()
    agent.run()
