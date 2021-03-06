import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter, ProtocolTypeRouter
from channels.testing import HttpCommunicator, ApplicationCommunicator, WebsocketCommunicator
from fakerinos.routing import application
from django.contrib.auth import get_user_model
from mixer.backend.django import mixer
from rest_framework.authtoken.models import Token
from fakerinos.routing import application
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.contrib.auth.models import Group
from django.test import Client
from rooms.models import Room
from articles.models import Tag

User = get_user_model()
channel_layer = get_channel_layer()

TEST_CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestWebSockets:

    async def auth_user(self):
        user = mixer.blend(User, is_superuser=True)
        token = Token.objects.create(user=user)
        user.save()
        client = Client()
        client.force_login(user=user)

        headers = [(b'authorization', "Token {}".format(token.key).encode())]
        communicator = WebsocketCommunicator(application, '/ws/rooms/', headers=headers)

        connected, subprotocol = await communicator.connect()
        return communicator, user


    async def test_send_json(self):
        user = mixer.blend(User, is_superuser=True)
        token = Token.objects.create(user=user)
        headers = [(b'Authorization', "Token {}".format(token.key).encode())]
        communicator = WebsocketCommunicator(application, '/ws/rooms/', headers=headers)
        try:
            message = "Connection error :: either you are not logged in or cannot provide authentication"
            await communicator.send_json_to(
                {
                "action": "admin",
                "message": message,
            })
        except Exception as e:
            pass
        await communicator.disconnect()

    async def test_joining(self,settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        room = mixer.blend(Room)
        tag = mixer.blend(Tag)
        communicator, user = await self.auth_user()
        user.player.room = room
        try:
            await communicator.send_json_to(
                {
                    "type": "receive_json",
                    "message": {
                        "action": "admin",
                        "schema": "request_to_join"
                    }
                })
        except Exception as e:
            pass
        await communicator.disconnect()

        async def test_create_room(self,settings):
            settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
            room = mixer.blend(Room)
            tag = mixer.blend(Tag)
            communicator, user = await self.auth_user()
            user.player.room = room
            try:
                await communicator.send_json_to(
                    {
                        "type": "receive_json",
                        "message": {
                            "action": "create_room",
                            "schema": "",
                        }
                    })
            except Exception as e:
                pass
            await communicator.disconnect()

    async def test_leaving(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        room = mixer.blend(Room)
        room.save()
        communicator, user = await self.auth_user()
        user.player.room = room
        user.save()
        room.save()
        try:
            await communicator.send_json_to(
                {
                    "type": "receive_json",
                    "message": {
                        "action": "admin",
                        "schema": "leave_room",
                    }
                })
        except Exception as e:
            pass
        await communicator.disconnect()

    async def test_choose_deck(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        room = mixer.blend(Room)
        tag = mixer.blend(Tag)
        communicator, user = await self.auth_user()
        user.player.room = room
        try:
            await communicator.send_json_to(
                {
                    "type": "receive_json",
                    "message": {
                        "action": "admin",
                        "schema": "choose_random_deck",
                    }
                })
        except Exception as e:
            pass
        await communicator.disconnect()




    async def test_connect(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        room = mixer.blend(Room)
        room.save()
        tag = mixer.blend(Tag)

        communicator, user = await self.auth_user()
        user.player.room = room
        user.save()
        room.save()
        try:
            await communicator.send_json_to(
                {
                    "type": "receive_json",
                    "message": {
                        "action": "admin",
                        "schema": "request_to_join"
                    }
                })

            await communicator.send_json_to(
                {
                    "type": "receive_json",
                    "message": {
                        "action": "create_room",
                        "schema": "",
                    }
                })
            await communicator.send_json_to(
                {
                    "type": "receive_json",
                    "message": {
                        "action": "admin",
                        "schema": "next_article",
                    }
                })
            await communicator.send_json_to(
                {
                    "type": "receive_json",
                    "message": {
                        "action": "admin",
                        "schema": "game_ready",
                    }

                })

            await communicator.send_json_to(
                {
                    "type": "receive_json",
                    "message": {
                        "action": "admin",
                        "schema": "check_ready",
                    }
                })

            await communicator.send_json_to(
                {
                    "type": "receive_json",
                    "message": {
                        "action": "admin",
                        "schema": "leave_room",
                    }
                })
            await communicator.send_json_to(
                {
                    "type": "receive_json",
                    "message": {
                        "action": "admin",
                        "schema": "choose_random_deck",
                    }
                })

            await communicator.disconnect()
        except ValueError:
            pass


    async def test_receive(self):
        user = mixer.blend(User, is_superuser=True)
        token = Token.objects.create(user=user)
        headers = [(b'Authorization', "Token {}".format(token.key).encode())]
        communicator = WebsocketCommunicator(application, '/ws/rooms/', headers=headers)
        try:
            await communicator.receive_json_from()
        except Exception as e:
            pass
        await communicator.disconnect()
