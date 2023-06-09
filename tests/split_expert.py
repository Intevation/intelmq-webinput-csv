"""
"""
from intelmq.lib.bot import ExpertBot


class SplitExpertBot(ExpertBot):
    counter: int = 0

    def init(self):
        self.counter = 0

    def process(self):
        event = self.receive_message()
        event_copy = event.copy()
        event_copy.change('event_description.text', event['event_description.text'] + '0')
        self.send_message(event_copy)
        event_copy1 = event.copy()
        event_copy1.change('event_description.text', event['event_description.text'] + '1')
        self.send_message(event_copy1)
        self.acknowledge_message()


BOT = SplitExpertBot
