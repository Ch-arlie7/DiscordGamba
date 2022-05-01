import mysql.connector
import pandas as pd
from dotenv import load_dotenv
import os

class SQLBase(object):
    def __init__(self, database: str):
        """
        Class to interact with MYSQL.
        """
        load_dotenv()
        self.user = os.getenv('DB_USERNAME')
        self.password = os.getenv('DB_PASSWORD')
        self.host = os.getenv('DB_HOST')
        self.port = int(os.getenv('DB_PORT'))    
        self.database = database
        self.table = 'main'

    def create_database(self):
        connection = mysql.connector.connect(user=self.user,
                                        password = self.password,
                                        host = self.host,
                                        port = self.port,
                                        auth_plugin = 'mysql_native_password')
        cursor = connection.cursor()
        try:
            cursor.execute("CREATE DATABASE {}".format(self.database))
            print('Database: {} successfully created'.format(self.database))
        except mysql.connector.Error as err:
            if err.errno != 1007:
                raise
        connection.close()

    def open_connection(self):
        return mysql.connector.connect(user=self.user,
                                        password = self.password,
                                        host = self.host,
                                        port = self.port,
                                        database = self.database,
                                        auth_plugin = 'mysql_native_password')

    def create_main_table(self):
        connection = self.open_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("CREATE TABLE {} (id BIGINT PRIMARY KEY, "
                                                "username VARCHAR(40), "
                                                "points INT DEFAULT 1000, " 
                                                "alloc_points INT DEFAULT 0, "
                                                "start_date DATE, "
                                                "last_stimmy DATE, "
                                                "active INT DEFAULT 0, "
                                                "flip_count INT DEFAULT 0, "
                                                "flip_wins INT DEFAULT 0, "
                                                "flip_winnings INT DEFAULT 0, "
                                                "gamba_count INT DEFAULT 0, "
                                                "gamba_wins INT DEFAULT 0, "
                                                "gamba_winnings INT DEFAULT 0, "
                                                "summoner_name VARCHAR(30) DEFAULT '');".format(self.table))
        except mysql.connector.Error as err:
            pass
            #print('Error: {}'.format(err))
        connection.close()
    
    def insert_user(self, discord_id: int, discord_name: str, date: str):
        """
        Inserts row for discord user if ID not already in database.
        date : str
            format: "2021-01-03"
        """     
        data = (discord_id, discord_name, date, date)
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT IGNORE INTO {} (id, username, start_date, last_stimmy) VALUES (%s, %s, %s, %s)".format(self.table), data)
        connection.commit()
        connection.close()

    def show_table(self, table: str = None):
        """
        Prints out pandas version of main table (for testing)
        """     
        if not table:
            table = self.table
        connection = self.open_connection()
        sql = 'SELECT * FROM {}'.format(table)    
        table = pd.read_sql(sql, connection)
        print(table)
        connection.close()
    
    def set_as_active(self, discord_id: int):
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE {} SET active = 1 where id = %s".format(self.table), (discord_id,))
        connection.commit()
        connection.close()

    def is_valid_discord_id(self, discord_id: int)->bool:
        '''Returns True if valid, else False'''
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT EXISTS(SELECT * from {} WHERE id = %s)".format(self.table), (discord_id,))
        result = cursor.fetchone()[0] == True
        connection.close()
        return result
  
    def get_leaderboard_stats(self)->list:
        '''Returns [(), (),..]'''
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT username, points FROM {} WHERE active = 1 ORDER BY points DESC".format(self.table))
        result = cursor.fetchall()
        connection.close()
        return result
    
    def drop_table(self, table: str = None):
        if not table:
            table = self.table
        connection = self.open_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DROP TABLE {}".format(table))
            connection.commit()
        except mysql.connector.Error as err:
            print('Error: {}'.format(err))
        connection.close()

    def select_row_by_id(self, columns: str, discord_id: int, table: str = None)-> tuple:
        '''Select single row data for a given ID.
        columns: string of column names eg. "id, points".
        Returns (col1, col2,..)
        '''
        if not table:
            table = self.table
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT {} FROM {} WHERE id = %s".format(columns, table), (discord_id,))
        result = cursor.fetchone()
        connection.close()
        return result

    def select_columns(self, columns: str, table: str = None)-> list:
        '''Select all values in given columns.
        columns: string of column names eg. "id, points".
        Returns [(), (),..]
        '''
        if not table:
            table = self.table
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT {} FROM {}".format(columns, table))
        result = cursor.fetchall()
        connection.close()
        return result
    
    def update_row_by_id(self, columns: tuple, values: tuple, discord_id: int, table: str = None):
        '''Update columns of a given ID.
        columns: tuple of strings: ("points", "alloc_points", "last_stimmy").
        values: tuple of values (100, 20, "2022-01-01").
        If single value, make sure it's a tuple: (10,) rather than (10).
        '''
        if not table:
            table = self.table
        updates = ''
        for column_name in columns:
            updates += '{} = %s, '.format(column_name)
        updates = updates[:-2]
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE {} SET {} WHERE id = %s".format(table, updates), (*values, discord_id))
        connection.commit()
        connection.close()

    def create_gamba_table(self, gamba_id: int, options_alpha: list):
        columns = '(id BIGINT PRIMARY KEY, username VARCHAR(40), '
        for option in options_alpha:
            columns += '{} INT DEFAULT 0, '.format(option)
        columns = columns[:-2]
        columns += ')'
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE gamba{} {};'.format(gamba_id, columns))
        connection.close()

    def create_gambas_table(self):
        try:
            connection = self.open_connection()
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE gambas (id int PRIMARY KEY, "
                                                    "title VARCHAR(100) NOT NULL, "
                                                    "open INT DEFAULT 1, "
                                                    "author BIGINT NOT NULL, "
                                                    "options VARCHAR(2000), "
                                                    "options_alpha VARCHAR(500));")
        except mysql.connector.Error as err:
            pass
            #print('Error: {}'.format(err))
        connection.close()

    def insert_bet_data(self, gamba_id: int, discord_id: int, discord_name: str, choice: str, amount: int):
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO gamba{} (id, username, {}) VALUES (%s, %s, %s);".format(gamba_id, choice), (discord_id, discord_name, amount))
        connection.commit()
        connection.close()

    def insert_gamba(self, gamba_id: int, title: str, author: int, options: str, options_alpha: str):
        '''Options and OptionsAlpha needs to be ''.joined list with an obscure separator that can be filtered out during gamba creation'''
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO gambas (id, title, author, options, options_alpha) VALUES (%s, %s, %s, %s, %s)", (gamba_id, title, author, options, options_alpha))
        connection.commit()
        connection.close()
    
    def remove_gamba(self, gamba_id: int):
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM gambas WHERE id = %s", (gamba_id,))
        connection.commit()
        connection.close()

    def select_gamba_standings(self, gamba_id: int):
        connection = self.open_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT title, author, options, options_alpha FROM gambas WHERE id = %s", (gamba_id,))
        result = cursor.fetchone()
        connection.close()
        return result

