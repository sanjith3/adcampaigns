import json
from channels.generic.websocket import WebsocketConsumer #type: ignore
from asgiref.sync import async_to_sync #type: ignore

class AdUpdateConsumer(WebsocketConsumer):
    def connect(self):
        self.ad_group_name = 'ad_updates'

        # Join ad updates group
        async_to_sync(self.channel_layer.group_add)(
            self.ad_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        # Leave ad updates group
        async_to_sync(self.channel_layer.group_discard)(
            self.ad_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        # This consumer does not expect to receive messages from the client
        pass

    # Method to send update to the group
    def send_update(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
        }))
