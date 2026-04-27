import os
import json
from instagrapi import Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_ig_client():
    cl = Client()
    session_file = "session.json"
    if os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            print("Loaded session from file.")
        except Exception as e:
            print(f"Could not load session: {e}")
    
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    
    if not username or not password:
        raise ValueError("IG_USERNAME or IG_PASSWORD not found in environment variables")
    
    try:
        if not cl.user_id:
            print("Attempting login...")
            cl.login(username, password)
        else:
            # Test the session
            cl.get_timeline_feed()
            print("Session is still valid.")
    except Exception as e:
        print(f"Login failed or session expired: {e}. Attempting fresh login.")
        cl.login(username, password)

    cl.dump_settings(session_file)
    return cl

def fetch_my_messages(cl, limit=100):
    print("Fetching sent messages to build persona...")
    threads = cl.direct_threads(amount=50)
    my_messages = []
    my_id = cl.user_id
    
    for thread in threads:
        messages = cl.direct_messages(thread.id, amount=20)
        for msg in messages:
            if str(msg.user_id) == str(my_id) and msg.text:
                my_messages.append(msg.text)
                if len(my_messages) >= limit:
                    break
        if len(my_messages) >= limit:
            break
    return my_messages

def generate_persona(messages):
    print(f"Analyzing {len(messages)} messages with OpenAI...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    Analyze the following messages sent by a user on Instagram. 
    Extract their personality, tone, vocabulary, and style.
    Create a JSON object representing their 'persona' that will be used to guide an AI to respond exactly like them.
    The JSON should have the following fields:
    - tone: A description of their overall tone (e.g., casual, professional, witty, empathetic).
    - vocabulary: A list of notable words, phrases, or slang they use often.
    - rules: A list of consistent behavior patterns (e.g., "always uses lowercase", "uses lots of emojis", "keeps responses under 10 words", "never uses punctuation").
    - summary: A short paragraph describing who they are and how they interact with others.

    Messages:
    {chr(10).join(messages[:50])}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    
    return response.choices[0].message.content

def main():
    try:
        cl = get_ig_client()
        messages = fetch_my_messages(cl)
        if not messages:
            print("No messages found. Please make sure you have sent some DMs.")
            return
            
        persona_json = generate_persona(messages)
        with open("persona.json", "w") as f:
            f.write(persona_json)
        print("Persona generated and saved to persona.json")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
