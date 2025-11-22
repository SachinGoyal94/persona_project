from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from database import get_db_conn
from schemas import UserCreate, UserLogin, PersonaCreate, PersonaOut, MessageCreate
from utils import hash_password, verify_password
from agents import MultiAgentPipeline, save_message_api

app = FastAPI(title="Character AI – Simplest Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------
# REGISTER
# --------------------------------------------------------
@app.post("/register")
def register(user: UserCreate):
    conn = get_db_conn()
    cursor = conn.cursor()

    hashed = hash_password(user.password)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute("""
            INSERT INTO users (username, hashed_password, created_at)
            VALUES (%s, %s, %s)
        """, (user.username, hashed, now))

        conn.commit()
        return {"msg": "User created", "username": user.username}

    except:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")

    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------------
# LOGIN → Return ONLY user_id
# --------------------------------------------------------
@app.post("/login")
def login(data: UserLogin):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE username=%s", (data.username,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username/password")

    return {
        "msg": "Login successful",
        "user_id": user["id"],  # frontend will store this
        "username": user["username"]
    }


# --------------------------------------------------------
# CREATE PERSONA
# --------------------------------------------------------
@app.post("/personas", response_model=PersonaOut)
def create_persona(p: PersonaCreate):

    conn = get_db_conn()
    cursor = conn.cursor()

    if p.mode == "custom" and (not p.summary or not p.tone):
        raise HTTPException(400, "Custom mode needs tone + summary")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO persona_flow (user_id, character_name, mode, tone, summary, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (p.user_id, p.character_name, p.mode, p.tone, p.summary, now))

    conn.commit()
    persona_id = cursor.lastrowid

    cursor.execute("SELECT * FROM persona_flow WHERE id=%s", (persona_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return PersonaOut(
        id=row[0], user_id=row[1], character_name=row[2],
        mode=row[3], tone=row[4], summary=row[5], created_at=row[6]
    )


# --------------------------------------------------------
# CHAT WITH AGENT
# --------------------------------------------------------
@app.post("/agent/respond")
def agent_respond(
    user_id: int = Body(...),
    persona_id: int = Body(...),
    user_input: str = Body(...)
):

    # Check persona belongs to user
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM persona_flow WHERE id=%s AND user_id=%s",
                   (persona_id, user_id))
    persona = cursor.fetchone()

    if not persona:
        raise HTTPException(404, "Persona not found for this user")

    cursor.close()
    conn.close()

    pipeline = MultiAgentPipeline(persona["character_name"], persona["tone"])
    save_message_api(persona_id, "user", user_input)
    reply = pipeline.run(persona_id, user_input)
    save_message_api(persona_id, "agent", reply)

    return {"reply": reply}


# --------------------------------------------------------
# GET MESSAGES
# --------------------------------------------------------
@app.get("/messages/{persona_id}")
def get_messages(persona_id: int, user_id: int):

    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM persona_flow WHERE id=%s AND user_id=%s",
                   (persona_id, user_id))
    owner = cursor.fetchone()

    if not owner:
        raise HTTPException(403, "Access denied")

    cursor.execute("""
        SELECT * FROM persona_messages
        WHERE persona_id=%s ORDER BY id ASC
    """, (persona_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows
@app.delete("/personas/{persona_id}")
def delete_persona(persona_id: int, user_id: int):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    # Check ownership
    cursor.execute(
        "SELECT * FROM persona_flow WHERE id=%s AND user_id=%s",
        (persona_id, user_id)
    )
    persona = cursor.fetchone()

    if not persona:
        cursor.close()
        conn.close()
        raise HTTPException(403, "Persona not found or access denied")

    # Delete messages first
    cursor.execute(
        "DELETE FROM persona_messages WHERE persona_id=%s",
        (persona_id,)
    )

    # Delete persona
    cursor.execute(
        "DELETE FROM persona_flow WHERE id=%s",
        (persona_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "msg": "Persona deleted successfully",
        "deleted_persona_id": persona_id,
        "character_name": persona["character_name"]
    }
# 📌 GET ALL CHARACTERS OF A USER
@app.get("/personas/list/{user_id}")
def list_personas(user_id: int):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, user_id, character_name, mode, tone, summary, created_at
        FROM persona_flow
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))

    personas = cursor.fetchall()

    cursor.close()
    conn.close()

    return personas

# 📌 GET FULL CHAT HISTORY FOR A SPECIFIC CHARACTER
@app.get("/messages/full/{persona_id}")
def full_history(persona_id: int):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, persona_id, sender, message, created_at
        FROM persona_messages
        WHERE persona_id = %s
        ORDER BY created_at ASC
    """, (persona_id,))

    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    return messages
