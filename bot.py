from TwitchWebsocket import TwitchWebsocket
import json
import requests
import sys

BOT_USER_ID = 'CHANGE_ME_TO_YOUR_BOTS_USER_ID'  # This is the User ID of the chat bot
OAUTH_TOKEN = 'CHANGE_ME_TO_YOUR_OAUTH_TOKEN'  # Needs scopes user:bot, user:read:chat, user:write:chat
CLIENT_ID = 'CHANGE_ME_TO_YOUR_CLIENT_ID'

CHAT_CHANNEL_USER_ID = 'CHANGE_ME_TO_THE_CHAT_CHANNELS_USER_ID'  # This is the User ID of the channel that the bot will join and listen to chat messages of

EVENTSUB_WEBSOCKET_URL = 'wss://eventsub.wss.twitch.tv/ws'

TwitchWebsocket_session_id = None

async def get_auth():
    # https://dev.twitch.tv/docs/authentication/validate-tokens/#how-to-validate-a-token
    response = requests.get('https://id.twitch.tv/oauth2/validate', headers={
        'Authorization': f'OAuth {OAUTH_TOKEN}'
    })

    if response.status_code != 200:
        data = response.json()
        print(f"Token is not valid. /oauth2/validate returned status code {response.status_code}", file=sys.stderr)
        print(data, file=sys.stderr)
        sys.exit(1)

    print("Validated token.")

def on_message(ws, message):
    handle_websocket_message(json.loads(message))

def on_error(ws, error):
    print(error, file=sys.stderr)

def on_open(ws):
    print(f'WebSocket connection opened to {EVENTSUB_WEBSOCKET_URL}')

def start_websocket_client():
    TwitchWebsocket.enableTrace(True)
    ws = TwitchWebsocket.WebSocketApp(EVENTSUB_WEBSOCKET_URL,
        on_message=on_message,
        on_error=on_error,
        on_open=on_open)
    ws.run_forever()

def handle_websocket_message(data):
    global websocket_session_id
    
    if data['metadata']['message_type'] == 'session_welcome':
        websocket_session_id = data['payload']['session']['id']
        register_eventsub_listeners()
    elif data['metadata']['message_type'] == 'notification':
        if data['metadata']['subscription_type'] == 'channel.chat.message':
            print(f"MSG #{data['payload']['event']['broadcaster_user_login']} <{data['payload']['event']['chatter_user_login']}> {data['payload']['event']['message']['text']}")
            
            if data['payload']['event']['message']['text'].strip() == "HeyGuys":
                send_chat_message("VoHiYo")

def send_chat_message(chat_message):
    response = requests.post('https://api.twitch.tv/helix/chat/messages', 
    headers={
        'Authorization': f'Bearer {OAUTH_TOKEN}',
        'Client-Id': CLIENT_ID,
        'Content-Type': 'application/json'
    },
    json={
        'broadcaster_id': CHAT_CHANNEL_USER_ID,
        'sender_id': BOT_USER_ID,
        'message': chat_message
    })

    if response.status_code != 200:
        data = response.json()
        print("Failed to send chat message", file=sys.stderr)
        print(data, file=sys.stderr)
    else:
        print(f"Sent chat message: {chat_message}")

def register_eventsub_listeners():
    response = requests.post('https://api.twitch.tv/helix/eventsub/subscriptions',
    headers={
        'Authorization': f'Bearer {OAUTH_TOKEN}',
        'Client-Id': CLIENT_ID,
        'Content-Type': 'application/json'
    },
    json={
        'type': 'channel.chat.message',
        'version': '1',
        'condition': {
            'broadcaster_user_id': CHAT_CHANNEL_USER_ID,
            'user_id': BOT_USER_ID
        },
        'transport': {
            'method': 'websocket',
            'session_id': websocket_session_id
        }
    })

    if response.status_code != 202:
        data = response.json()
        print(f"Failed to subscribe to channel.chat.message. API call returned status code {response.status_code}", file=sys.stderr)
        print(data, file=sys.stderr)
        sys.exit(1)
    else:
        data = response.json()
        print(f"Subscribed to channel.chat.message [{data['data'][0]['id']}]")

if __name__ == "__main__":
    get_auth()
    start_websocket_client()