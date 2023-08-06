import json
import os
from datetime import datetime
import pyrogram
from pyrogram import Client
from pyrogram.handlers import MessageHandler, DisconnectHandler, DeletedMessagesHandler
from pyrogram.methods.utilities.idle import idle
import asyncio


ApiID = None
ApiHash = None
PhoneNumber = None
OnlyDMs = False
LogsFolder = 'chats'
DataFolder = 'data'

# key is chat id, group name/username/user id
index = {}

# key is chat id, value is list of message ids
data = {}

if os.path.exists('settings.json'):
    with open('settings.json', 'r') as f:
        settings = json.load(f)

        ApiID = settings['apiID']
        ApiHash = settings['apiHash']
        PhoneNumber = settings['phoneNumber']
        LogsFolder = settings['logsFolder']

        if 'onlyDMs' in settings:
            OnlyDMs = settings['onlyDMs']

        if 'dataFolder' in settings:
            DataFolder = settings['dataFolder']

        print('Previous settings loaded successfully.')
else:
    ApiID = input('Enter your API ID: ')
    ApiHash = input('Enter your API Hash: ')
    PhoneNumber = input('Enter your phone number: ')

    with open('settings.json', 'w') as f:
        json.dump(
            {
                'apiID': ApiID,
                'apiHash': ApiHash,
                'phoneNumber': PhoneNumber,
                'logsFolder': LogsFolder,
                'dataFolder': DataFolder,
                'onlyDMs': OnlyDMs,
            },
            f,
        )

    print('Settings saved successfully.')

if not os.path.exists(DataFolder):
    os.mkdir(DataFolder)

# create folder if doesnt exist
if not os.path.exists(LogsFolder):
    os.mkdir(LogsFolder)

if os.path.exists(f'{DataFolder}/msgs.json'):
    with open(f'{DataFolder}/msgs.json') as f:
        data = json.load(f)

# load index
if os.path.exists(f'{LogsFolder}/index.txt'):
    with open(f'{LogsFolder}/index.txt', 'r') as f:
        for line in f.readlines():
            chatId = line.split(' | ')[0]
            chatname = line[len(chatId) + 3 :]
            index[int(chatId)] = chatname.strip()

def saveIndex():
    # saves as chatid | chatname
    with open(f'{LogsFolder}/index.txt', 'w', encoding='utf-8') as f:
        for key, value in index.items():
            f.write(f'{key} | {value}\n')

# message handler
def handle_message(client, message: pyrogram.types.Message):
    # only process is chat is valid and chat is not a group/channel
    if message.chat and message.chat.id and message.id and message.chat.id > 0:
        chat_id = str(message.chat.id)
        msgs = data.get(chat_id, [])
        if not message.id in msgs:
            msgs.append(message.id)
            data[chat_id] = msgs

            with open(f'{DataFolder}/msgs.json', 'w') as f:
                json.dump(data, f)

    text = message.text or message.caption
    if not text or (OnlyDMs and message.chat.id <= 0):
        return

    # format the message
    text = text.replace('\n', '\\n').replace('\r', '\\r')

    # some users dont use a username, so we use their first name instead
    author = message.from_user.username
    if not author:
        author = message.from_user.first_name
        if author and message.from_user.last_name:
            author += f' {message.from_user.last_name}'
    else:
        author = f'@{author}'

    # get the current time in dd/mm/yyyy hh:mm:ss format
    time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    # ignore the ugly code
    chatname = message.chat.title
    if not chatname:
        chatname = message.chat.username
        if not chatname:
            chatname = message.chat.first_name
        else:
            chatname = f'@{chatname}'

        if message.chat.is_verified:
            # add a checkmark if the user is verified
            chatname += ' (\u2713)'

    chatId = message.chat.id
    if chatId not in index or index[chatId] != chatname:
        index[chatId] = chatname
        saveIndex()

    text = f'[{time}] {author}: {text}'
    print(f'[{chatId}] {text}')

    with open(f'{LogsFolder}/{chatId}.txt', 'a', encoding='utf-8') as f:
        f.write(f'{text}\n')

def cleared_chats_handler(client, messages: list):
    if len(messages) == 0:
        print(f'No messages were cleared')
        return
    
    # key is chat id, value is int
    counts = {}

    for msg in messages:
        id = msg.id

        for chatId, msgs in data.items():
            if id in msgs:
                count = counts.get(chatId, 0)
                count += 1
                counts[chatId] = count
                break

    for chatId, count in counts.items():
        text = f'[{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}] {str(count)} message{"s" if count != 1 else ""} deleted'
        print(text)

        with open(f'{LogsFolder}/{chatId}.txt', 'a', encoding='utf-8') as f:
            f.write(f'{text}\n')
                
async def run():
    # pyrogram has weird bug, create new client each time to fix it
    client = Client(
        'chat logger', api_id=ApiID, api_hash=ApiHash, phone_number=PhoneNumber
    )
    
    client.add_handler(MessageHandler(handle_message))
    client.add_handler(DeletedMessagesHandler(cleared_chats_handler))

    # wait for disconnect
    disconnected = False
    async def disconnect_handler(client: Client):
        nonlocal disconnected
        disconnected = True

    client.add_handler(DisconnectHandler(disconnect_handler))

    try:
        await client.start()
        print('Client started successfully.')

        while not disconnected:
            await asyncio.sleep(1)

        await client.stop(True)
        await client.disconnect()
    except Exception as e:
        print('Error:', e)
        

def main():
    loop = asyncio.get_event_loop()
    while True:
        try:
            loop.run_until_complete(run())
        except KeyboardInterrupt:
            print('Exiting...')
            exit()

# start the client
if __name__ == '__main__':
    main()
