import gradio as gr
import requests
import asyncio
import threading
from telethon import TelegramClient, events

# Import spaces for Hugging Face ZeroGPU compatibility
try:
    import spaces
    has_spaces = True
except ImportError:
    has_spaces = False

# --- CONFIGURATION ---
API_ID = 33956030
API_HASH = "86796851bec72ad4da9a9c627c416b68"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxWVKVElwwYv1xhY5y9XfWAJN6nN2vBFstaNldZdU1F0IgOB1UOFk_i2Xe2zjjJEvjvEQ/exec"

client = TelegramClient('autosum_session', API_ID, API_HASH)

def is_transaction_message(text):
    if not text:
        return False
    text_lower = text.lower()
    
    # Khmer terms (ACLEDA, AMRET, etc.)
    khmer_terms = ["បានទទួល", "ទទួលប្រាក់", "ប្រាក់ចំនួន", "រៀល", "ដុល្លារ"]
    for term in khmer_terms:
        if term in text:
            return True
            
    # English terms (ABA, Payway, etc.)
    english_terms = ["paid by", "payway by aba", "trx. id", "payment received"]
    for term in english_terms:
        if term in text_lower:
            return True
            
    return False

async def process_and_send(chat_id, message_id, timestamp, text, sender):
    sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'username', 'Bank')
    print(f"Relaying transaction message from chat {chat_id} (sent by {sender_name})...")
    
    payload = {
        "message": {
            "chat": {
                "id": chat_id
            },
            "message_id": message_id,
            "date": int(timestamp),
            "text": text,
            "from": {
                "id": sender.id if sender else 0,
                "first_name": getattr(sender, 'first_name', 'Bank'),
                "last_name": getattr(sender, 'last_name', ''),
                "username": getattr(sender, 'username', '')
            }
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        print("Response from Google Sheets:", response.text)
    except Exception as e:
        print("Error forwarding to Google Sheets:", e)

@client.on(events.NewMessage)
async def handler(event):
    if not event.is_group:
        return
        
    text = event.message.text or event.message.message
    if not text:
        return
        
    if is_transaction_message(text):
        sender = await event.get_sender()
        await process_and_send(event.chat_id, event.message.id, event.message.date.timestamp(), text, sender)

async def catch_up_recent():
    await asyncio.sleep(5)  # Wait for connection stabilization
    print("Checking recent history for missed transactions...")
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                async for msg in client.iter_messages(dialog.id, limit=15):
                    text = msg.text or msg.message
                    if is_transaction_message(text):
                        sender = await msg.get_sender()
                        await process_and_send(dialog.id, msg.id, msg.date.timestamp(), text, sender)
    except Exception as e:
        print("Error in catch up scan:", e)

# Function to run Telethon client in a background thread
def start_userbot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("Userbot is starting...")
    client.start()
    
    # Run catch-up scan in background
    loop.create_task(catch_up_recent())
    
    print("Userbot is running and listening to all groups...")
    client.run_until_disconnected()

# Dummy GPU function for Hugging Face compatibility
if has_spaces:
    @spaces.GPU
    def dummy_gpu_task():
        return "GPU check passed"
else:
    def dummy_gpu_task():
        return "No GPU required"

# Start userbot in background thread
threading.Thread(target=start_userbot, daemon=True).start()

# Launch a simple Gradio Web Page
with gr.Blocks(title="AutoSum Userbot") as demo:
    gr.Markdown("# 📊 AutoSum Telegram Userbot")
    gr.Markdown("This userbot is running 24/7 in the cloud and listening for transaction messages.")
    
    btn = gr.Button("Verify Cloud Connection")
    out = gr.Textbox(label="Status")
    btn.click(fn=dummy_gpu_task, outputs=out)

demo.launch(server_name="0.0.0.0", server_port=7860)
