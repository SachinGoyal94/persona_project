import google.generativeai as genai
from datetime import datetime
import os
from database import get_db_conn

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# ======================================================
# 📌 1. Context Manager Agent – HIGH QUALITY SUMMARY
# ======================================================

class ContextManagerAgent:
    def __init__(self, model="gemini-2.0-flash"):
        self.model = genai.GenerativeModel(model)

    def build_context(self, history):
        """Builds a structured concise context from last messages"""
        conv = ""
        for h in history:
            role = "User" if h["sender"] == "user" else "Character"
            conv += f"{role}: {h['message']}\n"

        prompt = f"""
        You are a high-accuracy conversation summarizer.

        Summarize the conversation in **3–5 bullet points**.

        Rules:
        - Keep only important context and key emotional cues.
        - Preserve character personality hints.
        - Do NOT invent new information.
        - MUST return ONLY bullet points.

        Conversation:
        {conv}
        """

        response = self.model.generate_content(prompt)
        return response.text.strip()


# ======================================================
# 📌 2. Character Agent – 100% IN-CHARACTER Replies
# ======================================================

class CharacterAgent:
    def __init__(self, character_name, tone="neutral", model="gemini-2.0-flash"):
        self.character_name = character_name
        self.tone = tone
        self.model = genai.GenerativeModel(model)

    def reply(self, context_summary, user_msg):
        prompt = f"""
        You are role-playing as **{self.character_name}**.

        STRICT RULES:
        - Stay 100% in character at all times.
        - Speak exactly how {self.character_name} would.
        - Maintain tone: **{self.tone}**.
        - No AI disclaimers. No "as an AI".
        - No breaking the fourth wall.
        - Use natural conversation style.

        CONTEXT SUMMARY:
        {context_summary}

        USER MESSAGE:
        "{user_msg}"

        Respond as {self.character_name}.
        """

        response = self.model.generate_content(prompt)
        return response.text.strip()


# ======================================================
# 📌 3. Moderator Agent – Clean, Safe, Polished Output
# ======================================================

class ModeratorAgent:
    def __init__(self, model="gemini-2.0-flash"):
        self.model = genai.GenerativeModel(model)

    def check(self, reply):
        prompt = f"""
        You are a refinement and safety agent.

        Improve this reply following these rules:
        - Remove hallucinations.
        - Remove unsafe, toxic, or irrelevant content.
        - Maintain emotional intent of the reply.
        - Keep the character's personality consistent.
        - Improve clarity & coherence.
        - Do NOT remove important information.

        ORIGINAL REPLY:
        {reply}

        Return the cleaned final reply only.
        """

        response = self.model.generate_content(prompt)
        return response.text.strip()


# ======================================================
# 📌 4. Database Helper Functions (MySQL)
# ======================================================

def fetch_last_messages_api(persona_id, limit=10):
    """Retrieve last N messages for a persona"""
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT sender, message
        FROM persona_messages
        WHERE persona_id = %s
        ORDER BY id DESC
            LIMIT %s
        """,
        (persona_id, limit),
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # Reverse so newest is last (natural flow)
    return list(reversed(rows))


def save_message_api(persona_id, sender, message):
    """Stores a message into persona_messages table"""
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO persona_messages (persona_id, sender, message, created_at)
        VALUES (%s, %s, %s, NOW())
        """,
        (persona_id, sender, message),
    )

    conn.commit()
    cursor.close()
    conn.close()


# ======================================================
# 📌 5. FINAL MULTI-AGENT PIPELINE
# ======================================================

class MultiAgentPipeline:
    def __init__(self, character_name, tone):
        self.ctx_agent = ContextManagerAgent()
        self.character_agent = CharacterAgent(character_name, tone)
        self.moderator_agent = ModeratorAgent()

    def run(self, persona_id, user_message):
        """
        Full pipeline:
        1. fetch chat history from DB
        2. summarize context
        3. generate character reply
        4. moderate & clean reply
        5. return final output
        """

        # Step 1: Get last 10 messages
        history = fetch_last_messages_api(persona_id)

        # Step 2: Build context
        context_summary = self.ctx_agent.build_context(history)

        # Step 3: Character speaks
        raw_reply = self.character_agent.reply(context_summary, user_message)

        # Step 4: Clean with moderator
        final_reply = self.moderator_agent.check(raw_reply)

        return final_reply
