import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class ProgressConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'train_%s' % self.room_name

        print(self.room_group_name, self.channel_name)

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(text_data_json)
        if 'action' in text_data_json and text_data_json['action'] == 'disconnect':
            await self.disconnect(0)

        message = text_data_json['message']
        percentage = text_data_json['percentage']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'status',
                'message': message,
                'percentage': percentage
            }
        )

    # Receive message from room group
    def status(self, event):
        message = event['message']
        percentage = event['percentage']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'percentage': percentage
        }))