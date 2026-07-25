import requests
from telethon import TelegramClient, events

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

@client.on(events.NewMessage)
async def handler(event):
    # Only listen to group chats
    if not event.is_group:
        return
        
    text = event.message.text or event.message.message
    if not text:
        return
        
    # Check if the message is a transaction notification
    if is_transaction_message(text):
        sender = await event.get_sender()
        sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'username', 'Bank')
        print(f"Relaying notification from group {event.chat_id} (sent by {sender_name})...")
        
        # Build payload matching Telegram Bot API format
        payload = {
            "message": {
                "chat": {
                    "id": event.chat_id
                },
                "message_id": event.message.id,
                "date": int(event.message.date.timestamp()),
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
            print("Response from Google Sheets Webhook:", response.text)
        except Exception as e:
            print("Error forwarding to Google Sheets:", e)

print("Userbot is running and listening to all groups...")
client.start()
client.run_until_disconnected()
