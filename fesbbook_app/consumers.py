import asyncio
import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import datetime
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from .models import Message, ChatRoom, Student

class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        # print("connected", event)
        await self.send({
            "type": "websocket.accept"
        })

        chatFriend = self.scope["url_route"]["kwargs"]["username"]
        loggedInUser = self.scope["session"]["loggedInUser"]

        chat_room_obj = await self.get_chat_room(loggedInUser, chatFriend) 

        chat_room = f"room_{chat_room_obj.id}"
        self.chat_room = chat_room
        self.chat_room_obj=chat_room_obj
        self.loggedInUser = loggedInUser
        self.chatFriend = chatFriend

        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )

    async def websocket_receive(self, event):
        # print("receive", event)
        message_input = event.get("text", None)

        if message_input is not None:
            loaded_dict_data = json.loads(message_input)
            message_text = loaded_dict_data.get("messageText")
            input_file = loaded_dict_data.get("inputFile")
            file_name = loaded_dict_data.get("fileName")
            file_icon = loaded_dict_data.get("fileIcon")

            loggedInUser = await self.get_logged_in_user()

            if input_file != None:
                fileBytes = list(input_file.values())
                fileBytes = bytearray(fileBytes)
                newFile = ContentFile(fileBytes)

                base_file_path = "files/" + self.loggedInUser + "/" + datetime.now().strftime("%y%m%d%H%M%S")

                fs = FileSystemStorage("media/" + base_file_path)
                nf = fs.save(file_name, newFile)
                full_file_path = base_file_path + fs.url(nf)

                myResponse = {
                    "message_text": message_text,
                    "date_sent": datetime.now().strftime("%#d. %#m. %Y. %#H:%M"),
                    "sender": loggedInUser,
                    "file_url": full_file_path,
                    "file_name": file_name,
                    "file_icon": file_icon
                }
                await self.create_new_message(message_text, full_file_path, file_name, file_icon)
            else:
                myResponse = {
                    "message_text": message_text,
                    "date_sent": datetime.now().strftime("%#d. %#m. %Y. %#H:%M"),
                    "sender": loggedInUser
                }
                await self.create_new_message(message_text)

            await self.channel_layer.group_send(
                self.chat_room,
                {
                    "type": "chat_message",
                    "text": json.dumps(myResponse)
                }
            )

    async def chat_message(self, event):
        await self.send({
            "type": "websocket.send",
            "text": event["text"]
        })
    
    async def websocket_disconnect(self, event):
        print("disconnected", event)
        # await self.send({
        #     "type": "websocket.close"
        # })

    @database_sync_to_async
    def get_chat_room(self, loggedInUser, chatFriend):
        return ChatRoom.objects.get_or_new(loggedInUser, chatFriend)[0]

    @database_sync_to_async
    def create_new_message(self, messageText, messageFile=None, messageFileName=None, messageFileIcon=None):
        sender = Student.objects.get(username=self.loggedInUser)
        receiver = Student.objects.get(username=self.chatFriend)
        newMessage = Message.objects.create(message=messageText, sender=sender, receiver=receiver, chat_room=self.chat_room_obj)
        if messageFile:
            newMessage.message_file = messageFile
            newMessage.message_file_name = messageFileName
            newMessage.message_file_icon = messageFileIcon
        newMessage.save()

    @database_sync_to_async
    def get_logged_in_user(self):
        loggedInUser = Student.objects.get(username=self.loggedInUser)
        return {"username": loggedInUser.username, "profile_image": loggedInUser.profile_image.name, "isActive": loggedInUser.isActive}

class ConversationConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print("connected", event)
    async def websocket_receive(self, event):
        print("receive", event)
    async def websocket_disconnect(self, event):
        print("disconnected", event)