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
        cl.load_settings(session_file)
    
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    
    cl.login(username, password)
    cl.dump_settings(session_file)
    return cl

def fetch_my_messages(cl, limit=100):
    print("Fetching sent messages to build persona...")
    threads = cl.direct_threads(limit=50)
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
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""
    Analyze the following messages sent by a user on Instagram. 
    Extract their personality, tone, vocabulary, and style.
    Create a JSON object representing their 'persona' with the following fields:
    - tone: (e.g., casual, professional, witty, empathetic)
    - vocabulary: (notable words or phrases they use often)
    - rules: (any consistent behavior patterns like using emojis, length of responses)
    - summary: (a short paragraph describing who they are)

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
