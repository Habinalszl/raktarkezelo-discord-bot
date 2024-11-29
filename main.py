from typing import Final
import os
import sqlite3
from dotenv import load_dotenv
from discord import Intents, Client, Message

# STEP 0: LOAD OUR TOKEN FROM SOMEWHERE SAFE
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# STEP 1: BOT SETUP
intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

# STEP 2: DATABASE SETUP
def create_database():
    conn = sqlite3.connect('raktar.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raktar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nev TEXT NOT NULL,
        mennyiseg INTEGER NOT NULL
    )
    """)
    conn.commit()
    conn.close()

create_database()

# STEP 3: MESSAGE FUNCTIONALITY
async def send_message(message: Message, user_message: str) -> None:
    user_message = user_message.strip().lower()  # Normalize input
    try:
        response: str = handle_raktar_command(user_message)
        if response:
            await message.channel.send(response)
            await message.add_reaction("✅")  # Success reaction
    except Exception as e:
        await message.add_reaction("❌")  # Failure reaction
        print(e)

# STEP 4: HANDLING RAKTAR COMMANDS
def handle_raktar_command(command: str) -> str:
    conn = sqlite3.connect('raktar.db')
    cursor = conn.cursor()

    if command.startswith("!help"):
        response = (
            "Elérhető parancsok:\n"
            "`!raktar` - A raktár tartalmának listázása.\n"
            "`!raktar [termék]` - Egy adott termék keresése a raktárban.\n"
            "`!hozzaad [termék] [mennyiség]` - Új termék hozzáadása.\n"
            "`!modosit [termék] [új mennyiség]` - Termék mennyiségének módosítása.\n"
            "`!torol [termék]` - Termék törlése a raktárból.\n"
            "`!help` - Parancsok listájának megjelenítése."
        )
        conn.close()
        return response

    elif command.startswith("!raktar"):
        parts = command.split(" ", 1)
        if len(parts) > 1:  # Specific product search
            nev = parts[1]
            cursor.execute("SELECT * FROM raktar WHERE nev LIKE ?", (nev,))
        else:  # List all products
            cursor.execute("SELECT * FROM raktar")
        rows = cursor.fetchall()
        if rows:
            response = "Raktár tartalma:\n"
            for row in rows:
                response += f"**{row[1]}** - {row[2]} db\n"
        else:
            response = "A raktár üres vagy nincs ilyen termék."
        conn.close()
        return response

    elif command.startswith("!hozzaad"):
        try:
            _, nev, mennyiseg = command.split(" ", 2)
            if not nev.isalnum():
                return "A termék neve csak betűket és számokat tartalmazhat."
            mennyiseg = int(mennyiseg)
            if mennyiseg <= 0:
                return "A mennyiségnek pozitív számnak kell lennie."
            cursor.execute("INSERT INTO raktar (nev, mennyiseg) VALUES (?, ?)", (nev, mennyiseg))
            conn.commit()
            conn.close()
            return f"✅ **{nev}** hozzáadva a raktárhoz, {mennyiseg} db mennyiséggel!"
        except ValueError:
            return "Helytelen parancs. Használat: `!hozzaad [termék] [mennyiség]`"

    elif command.startswith("!modosit"):
        try:
            _, nev, uj_mennyiseg = command.split(" ", 2)
            uj_mennyiseg = int(uj_mennyiseg)
            if uj_mennyiseg < 0:
                return "A mennyiség nem lehet negatív."
            cursor.execute("UPDATE raktar SET mennyiseg = ? WHERE nev = ?", (uj_mennyiseg, nev))
            if cursor.rowcount == 0:
                response = f"Nincs ilyen nevű termék a raktárban: {nev}"
            else:
                response = f"**{nev}** mennyisége frissítve: {uj_mennyiseg} db."
            conn.commit()
            conn.close()
            return response
        except ValueError:
            return "Helytelen parancs. Használat: `!modosit [termék] [új mennyiség]`"

    elif command.startswith("!torol"):
        try:
            _, nev = command.split(" ", 1)
            cursor.execute("DELETE FROM raktar WHERE nev = ?", (nev,))
            if cursor.rowcount == 0:
                response = f"Nincs ilyen nevű termék a raktárban: {nev}"
            else:
                response = f"**{nev}** törölve a raktárból."
            conn.commit()
            conn.close()
            return response
        except ValueError:
            return "Helytelen parancs. Használat: `!torol [termék]`"

    return "Ismeretlen parancs. Írd be `!help`, hogy megismerd az elérhető parancsokat."

# STEP 5: HANDLING THE STARTUP FOR OUR BOT
@client.event
async def on_ready() -> None:
    print(f'{client.user} is now running!')

# STEP 6: HANDLING INCOMING MESSAGES
@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return

    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')
    await send_message(message, user_message)

# STEP 7: MAIN ENTRY POINT
def main() -> None:
    client.run(TOKEN)

if __name__ == '__main__':
    main()
