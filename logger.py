import json
import os
from datetime import datetime
from pyrogram import Client
from pyrogram.handlers import MessageHandler

ApiID = None
ApiHash = None
PhoneNumber = None
LogsFolder = 'chats'

# key is chat id, group name/username/user id
index = {}

if os.path.exists('settings.json'):
    with open('settings.json', 'r') as f:
        settings = json.load(f)

        ApiID = settings['apiID']
        ApiHash = settings['apiHash']
        PhoneNumber = settings['phoneNumber']
        LogsFolder = settings['logsFolder']
    
        print('Previous settings loaded successfully.')
else:
    ApiID = input('Enter your API ID: ')
    ApiHash = input('Enter your API Hash: ')
    PhoneNumber = input('Enter your phone number: ')

    with open('settings.json', 'w') as f:
        json.dump({
            'apiID': ApiID,
            'apiHash': ApiHash,
            'phoneNumber': PhoneNumber,
            'logsFolder': LogsFolder
        }, f)

    print('Settings saved successfully.')

# create folder if doesnt exist
if not os.path.exists(LogsFolder):
    os.mkdir(LogsFolder)

# load index
if os.path.exists(f'{LogsFolder}/index.txt'):
    with open(f'{LogsFolder}/index.txt', 'r') as f:
        for line in f.readlines():
            chatId = line.split(' | ')[0]
            chatname = line[len(chatId)+3:]
            index[int(chatId)] = chatname.strip()

def saveIndex():
    # saves as chatid:chatname
    with open(f'{LogsFolder}/index.txt', 'w', encoding='utf-8') as f:
        for key, value in index.items():
            f.write(f'{key} | {value}\n')

# message handler
def handle_message(client, message):
    text = message.text or message.caption
    if not text:
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

client = Client(
    'chat logger',
    api_id=ApiID,
    api_hash=ApiHash,
    phone_number=PhoneNumber
)

client.add_handler(MessageHandler(handle_message))

# start the client
if __name__ == '__main__':
    client.run()