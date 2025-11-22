import google.generativeai as genai
from datetime import datetime
import os
from database import get_db_conn

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# ------------------ Context Agent ------------------
class ContextManagerAgent:
    def __init__(self, model="gemini-2.0-flash"):
        self.model = genai.GenerativeModel(model)

    def build_context(self, history):
        text = "\n".join([f"{h['sender']}: {h['message']}" for h in history])

        prompt = f"""
        Summarize this chat conversation in 3–4 sentences.
        Do NOT invent facts.

        Conversation:
        {text}
        """
        res = self.model.generate_content(prompt)
        return res.text.strip()


# ------------------ Character Agent ------------------
class CharacterAgent:
    def __init__(self, character_name, tone="friendly", model="gemini-2.0-flash"):
        self.character_name = character_name
        self.tone = tone
        self.model = genai.GenerativeModel(model)

    def reply(self, context_summary, user_msg):
        prompt = f"""
        You are {self.character_name}.
        Tone: {self.tone}.

        Stay completely in character.
        No breaking the fourth wall.

        Context Summary:
        {context_summary}

        User: {user_msg}

        Reply as {self.character_name}.
        """
        res = self.model.generate_content(prompt)
        return res.text.strip()


# ------------------ Moderator Agent ------------------
class ModeratorAgent:
    def __init__(self, model="gemini-2.0-flash"):
        self.model = genai.GenerativeModel(model)

    def check(self, reply):
        prompt = f"""
        Clean this reply:
        - No hallucinations
        - Keep same tone & personality
        - Remove unsafe content

        {reply}
        """
        res = self.model.generate_content(prompt)
        return res.text.strip()


# ------------------ Helpers ------------------
def fetch_last_messages_api(persona_id, limit=10):
    limit = max(3, min(limit, 30))  # safety

    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT sender, message FROM persona_messages
        WHERE persona_id=%s ORDER BY id DESC LIMIT %s
    """, (persona_id, limit))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return list(reversed(rows))


def save_message_api(persona_id, sender, message):
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO persona_messages (persona_id, sender, message, created_at)
        VALUES (%s, %s, %s, NOW())
    """, (persona_id, sender, message))

    conn.commit()
    cursor.close()
    conn.close()


class MultiAgentPipeline:
    def __init__(self, character_name, tone):
        self.ctx = ContextManagerAgent()
        self.char = CharacterAgent(character_name, tone)
        self.mod = ModeratorAgent()

    def run(self, persona_id, user_msg):
        history = fetch_last_messages_api(persona_id)
        ctx = self.ctx.build_context(history)
        raw = self.char.reply(ctx, user_msg)
        return self.mod.check(raw)
