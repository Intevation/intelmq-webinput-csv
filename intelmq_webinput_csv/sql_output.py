"""
SPDX-FileCopyrightText: 2023 Bundesamt für Sicherheit in der Informationstechnik
SPDX-License-Identifier: AGPL-3.0-or-later
Software engineering by Intevation GmbH <https://intevation.de>

This is a special SQL Output Bot which re-uses a connection instance

Use this bot as module intelmq_webinput_csv.sql_output
"""

from intelmq.bots.outputs.sql.output import SQLOutputBot, itemgetter_tuple


class WebinputSQLOutputBot(SQLOutputBot):
    """
    Re-uses a given connection object to use the transaction
    Only postgresql is supported

    The bot must not do any error-handling by itself like re-connecting etc.
    If there's a fail, then raise, so the user gets informed.
    Thus, fail_on_errors is always set to true
    """

    def __init__(self, *args, connection: 'psycopg2.extensions.connection', **kwargs):  # noqa: F821
        """
        Initializes the WebinputSQLOutputBot with a pre-exisiting Postgres Connection
        """
        if not hasattr(self, 'fail_on_errors'):
            raise ValueError('This version of IntelMQ is too old. At least version 1.2.0 is required.')
        self.fail_on_errors = True

        self.con = connection
        self.autocommit = False
        if self.con.autocommit != self.autocommit:
            self.con.autocommit = False
        self.cur = self.con.cursor()
        self._engine = "postgresql"
        super().__init__(*args, **kwargs)

    def _init_postgresql(self):
        self.logger.info('Ignoring initialization of postgres connection.')

    def _init_mssql(self):
        raise NotImplementedError

    def _init_sqlite(self):
        raise NotADirectoryError

    def process(self):
        """
        Same as intelmq.bots.outputs.sql.output.SQLOutputBot.process
        except that the postgres commit is left out
        """
        event = self.receive_message().to_dict(jsondict_as_string=self.jsondict_as_string)

        key_names = self.fields
        if key_names is None:
            key_names = event.keys()
        valid_keys = [key for key in key_names if key in event]
        keys = '", "'.join(valid_keys)
        values = self.prepare_values(itemgetter_tuple(*valid_keys)(event))
        fvalues = len(values) * f'{self.format_char}, '
        query = (f'INSERT INTO {self.table} ("{keys}") VALUES ({fvalues[:-2]})')

        if self.execute(query, values, rollback=not self.fail_on_errors):
            self.acknowledge_message()


BOT = WebinputSQLOutputBot
