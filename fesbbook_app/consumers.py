import asyncio
import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import datetime

from .models import Message, ChatRoom, Student

class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print("connected", event)
        await self.send({
            "type": "websocket.accept"
        })

        chatFriend = self.scope["url_route"]["kwargs"]["username"]
        loggedInUser = self.scope["session"]["loggedInUser"]
        # print(chatFriend, loggedInUser)
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
        print("receive", event)
        message_input = event.get("text", None)

        if message_input is not None:
            loaded_dict_data = json.loads(message_input)
            message_text = loaded_dict_data.get("messageText")

            loggedInUser = await self.get_logged_in_user()
            print(loggedInUser)

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
    def create_new_message(self, messageText):
        sender = Student.objects.get(username=self.loggedInUser)
        receiver = Student.objects.get(username=self.chatFriend)
        return Message.objects.create(message=messageText, sender=sender, receiver=receiver, chat_room=self.chat_room_obj)

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