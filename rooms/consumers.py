from channels.generic.websocket import JsonWebsocketConsumer, WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Room
from articles.models import Deck
import logging
from articles.models import Article
import json
import channels.layers
import websockets
from django.core import serializers

"""
### TODOs
1. how to send extra content through json --> subject 
    -- self.scope['url_route']['kwargs'][<url_part_name_self_defined_yeah>]
2. what is in websocket_connect(self,message) ==> WHATS IN MESSAGE
3. ARE WE USING ASYNC TO SYNC
4. ROOM must have host
5. WHY DOESNT room 1 WORK ??????
6. SERIOUSLY HOW TO DELETE ROOMS LA
###

types --> determines which handler is called for
vanilla types:
    A. websocket_connect
    B. receive_json
    C. send_json
    D. websocket_disconnect

main receive types:
    A. find_room
        checks if available game (with right subject && has vacancy)
        i. join_room
        else
        ii. create_room

        .. and waits ..
        .. till operational.game_start ..

    B. operational
        i. game_start
        .. creates waiting_list [players.size] ..

        ii. indicate_ready
        .. update all room's waiting lists ..

        iii. next_article && submit score
        #TODO who gets article (?) client || server
        
        iv. submit score
        
    C. message_print
        takes a message and sends to client to print

main send types: 
    A. game_start
    B. next_article
    C. join_room / create_room

"""

class RoomConsumer(JsonWebsocketConsumer):

    def websocket_connect(self, message):
        logging.info(message)
        self.user = self.scope['user']
        self.accept()
        # this is working
        # self.send(text_data=json.dumps({"message": "connected"}))
        # self.send_json({
        #     "message": "hello again",
        # })
        # self.<handler_name>(args)
        self.find_room(message=message)

    def find_room(self, message):
        #TODO deck needs to be initialized YOOOO
        logging.info(".. entering find_room handler ..")
        logging.info("i need to know the type " + str(type(self.scope['url_route']['kwargs']['subject'])))
        subject = self.scope['url_route']['kwargs']['subject']
        room_pk = None
        #TODO am i searching for subject
        try:
            room_pk = self.scope['url_route']['kwargs']['room_pk']
        except Exception as e:
            logging.info("find room :: No room name found")
            logging.info(e)
        if room_pk != None:
            self.join_room(Room.objects.get(pk=room_pk))
            pass

        # TODO get search from input (during connection)
        # if there is rooms with same subject -> check if avail -> else if not ->
        if Room.objects.filter(subject=subject).exists():
            for room in Room.objects.filter(subject=subject):
                logging.info("wow SAME SUBJECT FOUND")
                self.join_room(room)
            # if there is still no room available
            if self.user.player.room is None:
                logging.info("all rooms filled")
                self.create_room(subject)

        # means no room with same subject
        else:
            logging.info("room doesnt exist")
            # create room
            self.create_room(subject)


    def create_room(self, subject):
        logging.info(".. entering create room handler ..")
        # TODO create room with subject and add host
        room = Room.objects.create(subject=subject)
        logging.info("User {} CREATED room {}".format(self.scope['user'].id, room.id))
        self.room_group_name = 'room_%s' % self.user.player.room.pk
        self.user.player.room = room
        self.user.player.save()
        # TODO create group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        # async_to_sync(self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         "type": "send_json",
        #         "message": "please work",
        #     }
        # ))

    def join_room(self, room_object):
        room = room_object
        if self.user.is_authenticated and self.user.profile not in room.players.all() and len(room.players.all()) < room.max_players:
            logging.info("User {} joined room {}".format(self.scope['user'].id, room.id))
            self.user.player.room = room
            self.user.player.save()
            # TODO add into group
            self.room_group_name = 'room_%s' % room.pk
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
            logging.info("you here")
            # async_to_sync(self.channel_layer.group_send)(
            #     self.room_group_name,
            #     {
            #         "type": "send_json",
            #         "message": "please work",
            #     }
            # )

        elif self.user.profile in room.players.all():
            # TODO how to handle if user already in room --> will that happen lol
            logging.info("Already in room bro")
            return None


    # def websocket_connect(self, message):
    #     self.room_id = self.scope['url_route']['kwargs']['room_name']
    #     self.deck_id = self.scope['url_route']['kwargs']['deck_name']
    #     logging.info(self.deck_id)
    #     self.room_group_name = 'room_%s' % self.room_id
    #     room = Room.objects.get(id=self.room_id)
    #     user = self.scope['user']
    #     players = room.players.all()
    #     async_to_sync(self.channel_layer.group_add)(
    #         self.room_group_name,
    #         self.channel_name
    #     )
    #     if user.is_authenticated and user.profile not in players and len(players) < room.max_players:
    #         self.accept()
    #         logging.info("User {} joined room {}".format(self.scope['user'].id, room.id))
    #         user.player.room = room
    #         user.player.save()
    #         self.deck = None
    #         logging.info(self.deck_id)
    #
    #     elif user.profile in players:
    #         self.accept()
    #         self.deck = None
    #         if Deck.objects.filter(pk=self.deck_id):
    #             self.deck = serializers.serialize("json", [Deck.objects.get(pk=self.deck_id).articles])
    #         self.send({
    #             'message': self.deck
    #         })
    #     else:
    #         self.close()

    def disconnect(self, code):
        logging.info(".. entering disconnect handler ..")
        logging.info("precheck all rooms")
        logging.info(Room.objects.all())
        user = self.scope['user']
        room = user.player.room
        logging.info("deleting room from player and room itself")
        try:
            #TODO what if room is still exists because plaayer disconnects wrongly
            if user.is_authenticated:
                # logging.info("how many people in room :: " + str(len(room.players.all())))
                user.player.room = None
                user.save()
                # logging.info("just for good measure")
                # logging.info(user.player.room)
                # logging.info(user.player.hosted_room)
                # if user.player.hosted_room.pk == room.pk:
                #     logging.info('yes same')
                # logging.info("so you left ?")
                logging.info("REALLY ??? :: " + str(len(room.players.all())))
                logging.info("User {} left room {}".format(user.pk, room.pk))
                room.delete_if_empty()
                logging.info("confirm room is deleted")
                logging.info(Room.objects.all())
        except Exception as e:
            logging.error("Disconnect ERROR :::")
            logging.error(e)

    def receive_json(self, content, **kwargs):
        logging.info("######################### receiving ##########################")
        # TODO handle bad input types
        # MUST BE double quotes !!! ""
        # check which handler to send content to
        try:
            logging.info(content["message"])
            content_message = json.loads(content["message"])
            get_type = content_message["type"]
            get_message_to_handler = content_message["message"]
            getattr(self, get_type)(get_message_to_handler)
            logging.info("uh huh")
        except Exception as e:
            logging.error("Receive_json error ::: ")
            logging.error(e)

    def start_game(self, message):
        #TODO check if user is host and check his game
        #TODO send everyone article
        #TODO get specific articles
        # Anyone can start game model
        async_to_sync(self.channel_layer.group_send)({
            self.room_group_name,
            {
                "type": "article_request",
                "message": json.dumps('{"message": 1}'),
            }
        })
        # doesnt work
        self.send_everyone(self.article_request(1))

        #TODO start time and counter

    def article_request(self, article_pk):
        try:
            if Article.objects.filter(pk=article_pk).exists():
                article = serializers.serialize("json", [Article.objects.get(pk=article_pk)])
            else:
                article = "Article Not Found"
            self.send(text_data=json.dumps({
                'message': article
            }))
        except Exception as e:
            self.send_json({"message": "beeeeeeeech you cant even send request properly like whaaAaaAAAaaAAttT"})
            logging.error("article request ::: ")
            logging.error(e)

    def update_score(self):
        user = self.scope['user']
        # TODO update score

    def submit_final_score(self):
        user = self.scope['user']

    def send_everyone(self, message):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "send_json",
                "message": message,
            }
        )


# class GameConsumer(WebsocketConsumer):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         async_to_sync(self.channel_layer.group_add)(
#             "gameconsumer",
#             self.channel_name
#         )
#
#     def websocket_connect(self, message):
#         """self.game_group_name = 'game_%s'"""
#         self.accept()
#
#     def websocket_disconnect(self, message):
#         """
#         # async_to_sync(self.channel_layer.send(
#         #
#         # ))"""

