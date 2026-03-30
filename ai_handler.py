import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are CiscoChatBot — an expert and friendly Cisco IOS network configuration assistant for university students. 
You help students with Cisco IOS commands, IP addressing, subnetting, troubleshooting, and configuration review.
You explain WHY certain commands are used and provide clear, step-by-step guidance. You handle typos naturally and provide helpful suggestions. Use code blocks for commands.


Lab devices:
- R1: GigabitEthernet0/0 = 192.168.10.1/24, Serial0/3/0 = 10.10.10.1/30
- R2: Serial0/2/0 = 10.10.10.2/30, GigabitEthernet0/0 = 192.168.20.1/24
- S1, S2: switches with FastEthernet access ports

Help with: Cisco IOS commands, IP validation, subnetting, troubleshooting, config review.
Be friendly, explain WHY commands are used, handle typos naturally, use code blocks for commands."""


def ask_groq(user_message, chat_history=None, file_content=None, image_data=None, image_type="image/jpeg"):
    try:
        messages = []

        if chat_history:
            for msg in chat_history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        full_message = user_message
        if file_content:
            full_message = f"FILE CONTENT:\n{file_content}\n\nUSER QUESTION:\n{user_message}"

        messages.append({"role": "user", "content": full_message})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            max_tokens=1000,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        error = str(e)
        if "rate_limit" in error.lower():
            return "⚠️ Too many requests. Please wait 30 seconds and try again."
        elif "invalid_api_key" in error.lower():
            return "❌ Invalid API key. Please check your .env file."
        else:
            return f"❌ Error: {error}"