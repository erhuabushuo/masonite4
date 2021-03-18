"""Broadcast notification driver."""

from .BaseDriver import BaseDriver


class BroadcastDriver(BaseDriver):
    def __init__(self, application):
        self.application = application
        self.options = {}

    def set_options(self, options):
        self.options = options
        return self

    def send(self, notifiable, notification):
        """Used to broadcast a notification."""
        data = self.get_data("broadcast", notifiable, notification)
        channels = notification.broadcast_on() or notifiable.route_notification_for(
            "broadcast"
        )
        self.application.make("broadcast").channel(channels, data)

    def queue(self, notifiable, notification):
        """Used to queue the notification to be broadcasted."""
        # Makes sense ??????
        # data = self.get_data("broadcast", notifiable, notification)
        # channels = notification.broadcast_on() or notifiable.route_notification_for(
        #     "broadcast"
        # )
        # self.application.make("queue").push(driver.channel, args=(channel, data))
