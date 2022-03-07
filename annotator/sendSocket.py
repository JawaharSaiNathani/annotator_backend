import channels.layers
from asgiref.sync import async_to_sync

channel_layer = channels.layers.get_channel_layer()
async_to_sync(channel_layer.group_send)('train_1', {'type': 'status', 'message': 'Hello', 'percentage': 12})
async_to_sync(channel_layer.group_send)('train_1', {'action': 'disconnect'})