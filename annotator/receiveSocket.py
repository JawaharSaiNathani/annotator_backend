import channels.layers
from asgiref.sync import async_to_sync

channel_layer = channels.layers.get_channel_layer()
async_to_sync(channel_layer.receive)('train_1')