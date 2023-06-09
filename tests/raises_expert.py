"""
"""
from intelmq.lib.bot import ExpertBot


class RaisesExpertBot(ExpertBot):
    def process(self):
        event = self.receive_message()
        if not event['event_description.text'].endswith('0'):
            raise ValueError('some random error')
        else:
            self.send_message(event)
        self.acknowledge_message()


BOT = RaisesExpertBot
