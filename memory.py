chat_memory = {}

def get_history(session_id):
    return chat_memory.get(session_id, [])

def save_message(session_id, role, text):
    if session_id not in chat_memory:
        chat_memory[session_id] = []
    chat_memory[session_id].append({"role": role, "content": text})
    print(f"Message saved for session {session_id}: {role} - {text}")