import os
import telebot
import logging

# init the tgBot.
# Acces_token is env var in Heroku config.
telegramBot = telebot.TeleBot(str(os.environ.get('ACCSES_TOKEN')))




@telegramBot.channel_post_handler()
def repost_message(message):
    """
        Main function.
        Reposting messages from channels to channels :)

    """
    if message.text != "/addtochannel":
        to_group = Base().get_to_groups_id()
        for group in to_group:
            try:
                telegramBot.forward_message(group, message.chat.id, message.message_id)
            except Exception:
                Base().del_to_group(group)
    else:
        Base().add_to_groups(message.chat.id)

"""
    to_group = Base().get_to_groups() # getting groups where bot have to repost.
    groups = [group[-1] for group in to_group]
    if message.text != '/addtochannel': # if the message.text is not the command
        if message.chat.id not in groups:
            for group in groups:
                try:
                    telegramBot.forward_message(group, message.chat.id, message.message_id)
                except Exception as exp:
                    # In case, if bot has been deleted from channel
                    logging.warning(exp)
                    Base().del_to_group(group)
    else:
        Base().add_to_groups(message.chat.id)
"""



@telegramBot.channel_post_handler(content_types=['photo'])
def repost_message_photo(message):
    """ If the message contains photos. """
    repost_message(message)


class Base:
    def __init__(self):
        from urllib import parse
        import psycopg2

        parse.uses_netloc.append("postgres")
        url = parse.urlparse(os.environ["DATABASE_URL"])

        self.connection = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )

        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS toGroups (groupID bigint unique)")
        self.connection.commit()

    def add_to_groups(self, groupid):
        try:
            self.cursor.execute("INSERT INTO toGroups VALUES ({0})".format(int(groupid)))
        except Exception:
            # MAKING ROLLBACK - IT IS IMPORTANT WHEN USING POSTGRESQL
            self.connection.rollback()
        else:
            logging.info('BOT HAS ADDED TO CHANNEL {0}'.format(groupid))
            self.connection.commit()

    def get_to_groups_id(self):
        # SELECTING ALL ID FROM TO GROUPS
        # USING FOR SPAMMING
        self.cursor.execute("SELECT id FROM toGroups")

        # MAKING ALL ID IN ONE ARRAY
        data = list(map(lambda x: x[0], self.cursor.fetchall()))
        return data

    def del_to_group(self, channel_id):
        # DELETE ID FROM DATABASE IF BOT HAD REMOVED FROM CHANNEL
        self.cursor.execute("DELETE FROM toGroups WHERE id = {0}".format(int(channel_id)))
        self.connection.commit()


if __name__ == '__main__':
    # Configuration of logger.
    logging.basicConfig(format='[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level=logging.DEBUG)

    # Write msg about starting.
    logging.info('STARTING BOT')
    telegramBot.polling(none_stop=True)