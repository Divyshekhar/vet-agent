import os
from google import genai
from dotenv import load_dotenv
from tools import book_appointment
from memory import get_history, save_message
from google.genai import types
from fastapi import HTTPException
load_dotenv()


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

book_appointment_tool = {
    "name": "book_appointment",
    "description": "Books a veterinary appointment for a pet",
    "parameters": {
        "type": "object",
        "properties": {
            "owner_name": {
                "type": "string",
                "description": "Name of the pet owner"
            },
            "pet_name": {
                "type": "string",
                "description": "Name of the pet"
            },
            "date": {
                "type": "string",
                "description": "Appointment date"
            },
            "time": {
                "type": "string",
                "description": "Appointment time"
            }
        },
        "required": ["owner_name", "pet_name", "date", "time"]
    }
}


SYSTEM_PROMPT ="""
You are a veterinary assistant.

You have access to a tool:
- book_appointment(owner_name, pet_name, date, time)

Your responsibilities:

1. Understand user intent:
   - If user wants to book / schedule / visit → start booking process
   - Otherwise answer normally

2. Information required for booking:
   - owner_name
   - pet_name
   - date
   - time

3. CRITICAL RULES:
   - NEVER ask for information that is already provided in conversation
   - ALWAYS extract information from previous messages
   - Be context-aware and remember details mentioned earlier

4. Conversation behavior:
   - Ask ONLY for missing fields
   - Ask ONE question at a time
   - Be short and direct

5. Tool usage (VERY IMPORTANT):
   - As soon as ALL required fields are available → CALL the tool immediately
   - DO NOT ask any extra questions after all data is available
   - DO NOT confirm again → just call the tool

6. If user provides multiple details in one message:
   - Extract ALL of them correctly

7. After tool execution:
   - Respond naturally with confirmation

8. Do NOT:
   - restart conversation
   - forget previously given info
   - ask same question again
   - hallucinate missing data

Be smart, concise, and context-aware.
"""


# 🔥 Simple in-memory state tracking (important)
booking_state = {}


# def extract_details(session_id, message):
#     """
#     Very basic extraction (can improve later)
#     """
#     state = booking_state.get(session_id, {
#         "owner_name": None,
#         "pet_name": None,
#         "date": None,
#         "time": None
#     })

#     msg = message.lower()

#     # naive extraction (improve later with NLP)
#     if not state["owner_name"]:
#         state["owner_name"] = message
#     elif not state["pet_name"]:
#         state["pet_name"] = message
#     elif not state["date"]:
#         state["date"] = message
#     elif not state["time"]:
#         state["time"] = message

#     booking_state[session_id] = state
#     return state

def run_agent(session_id, user_message):
    history = get_history(session_id)

    save_message(session_id, "user", user_message)

    # 🔹 Build conversation
    messages = SYSTEM_PROMPT + "\n\nConversation:\n"

    for msg in history:
        role = msg.get("role", "user")
        text = msg.get("content", "")
        messages += f"{role.upper()}: {text}\n"

    messages += f"USER: {user_message}\nASSISTANT:"

    print("\n--- PROMPT ---\n", messages)

    # 🔹 Attach tool
    tools = types.Tool(function_declarations=[book_appointment_tool])
    config = types.GenerateContentConfig(tools=[tools])

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=config
        )
    except Exception as e:
        error_str = str(e)

        if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                raise HTTPException(status_code=429, detail="⚠️ AI response delayed due to quota limits. Please try again later.")

        print("Error generating content:", e)
        raise HTTPException(status_code=500, detail="❌ Failed to generate AI response.")
    # 🔥 IMPORTANT: Check if tool call exists
    if response.candidates and response.candidates[0].content.parts:
        parts = response.candidates[0].content.parts[0]

        # ✅ TOOL CALL DETECTED
        if hasattr(parts, "function_call") and parts.function_call:
            func_call = parts.function_call

            tool_name = func_call.name
            args = dict(func_call.args)

            print("\n--- TOOL CALL ---\n", tool_name, args)

            # 🔹 Execute tool
            if tool_name == "book_appointment":
                result = book_appointment(**args)
            else:
                result = "Unknown tool"

            # 🔹 Send result back to LLM
            try:
                followup = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"Tool result: {result}"
                )
                final_text = followup.text

            except Exception as e:
                error_str = str(e)

                if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                    raise HTTPException(status_code=429, detail="⚠️ AI response delayed due to quota limits. Please try again later.")
                final_text = str(result)  # fallback to raw tool result
            

            final_text = followup.text

            save_message(session_id, "assistant", final_text)
            return final_text

    # 🔹 Normal response
    text = response.text

    print("\n--- RESPONSE ---\n", text)

    save_message(session_id, "assistant", text)

    return text