import mysql.connector
import pandas as pd
from datetime import datetime
import random
from gamba import Gamba

class SQLCommands(object):
    def __init__(self, user: str, password: str, host: str, port: str, database: str, table: str):
        """
        Class to interact with MQSql.
        """
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.database = database
        self.table = table       
        self.mydb = self.initDB()
        self.mycursor = self.mydb.cursor()

    def initDB(self):
        return mysql.connector.connect(user=self.user,
                                    password = self.password,
                                    host = self.host,
                                    port = self.port,
                                    database = self.database,
                                    auth_plugin = 'mysql_native_password',
                                    use_pure = True)


    def dropTable(self):
        """
        Drops table (self.table) if it exists.
        
        """
        try:
            self.mycursor.execute("DROP TABLE {};".format(self.table))
            self.mydb.commit()
        except mysql.connector.Error as err:
            print("Error: {}".format(err))
            
    def createTable(self):
        """
        Creates table (self.table) if it doesn't exist.
        """
        try:
            self.mycursor.execute("CREATE TABLE {} (id BIGINT PRIMARY KEY, "
                                                "username VARCHAR(40), "
                                                "points INT DEFAULT 1000, " 
                                                "alloc_points INT DEFAULT 0, "
                                                "start_date DATE, "
                                                "last_stimmy DATE, "
                                                "active INT DEFAULT 0);".format(self.table))
        except mysql.connector.Error as err:
            print("Error: {}".format(err))
    
    def insertRow(self, discord_id: int, discord_name: str, date: str):
        """
        Inserts row for discord user if ID not already in database.
        date : str
            format: "2021-01-03"
        """     
        data = (discord_id, discord_name, date, date)
        self.mycursor.execute("INSERT IGNORE INTO {} (id, username, start_date, last_stimmy) VALUES (%s, %s, %s, %s);".format(self.table), data)
        self.mydb.commit()
        
    def showTable(self):
        """
        Prints out pandas version of db (for testing)
        """
        sql = 'SELECT * FROM {}'.format(self.table)
        table = pd.read_sql(sql, self.mydb)
        table = table[['id', 'username', 'points', 'alloc_points', 'active', 'last_stimmy']]
        print(table)
    
    def selectPoints(self, discord_id: int):
        self.mycursor.execute("SELECT points FROM {} WHERE id = %s;".format(self.table), (discord_id,))
        return self.mycursor.fetchone()[0]
    
    def selectAllocPoints(self, discord_id: int):
        self.mycursor.execute("SELECT alloc_points FROM {} WHERE id = %s;".format(self.table), (discord_id,))
        return self.mycursor.fetchone()[0]
    
    def selectName(self, discord_id: int):
        self.mycursor.execute("SELECT username FROM {} WHERE id = %s;".format(self.table), (discord_id,))
        return self.mycursor.fetchone()[0]
      
    def updatePoints(self, discord_id: int, new_value: int):
        self.mycursor.execute("UPDATE {} SET points = %s WHERE id = %s;".format(self.table), (new_value, discord_id))
        self.mydb.commit()
        
    def updateAllocPoints(self, discord_id: int, new_value: int):
        self.mycursor.execute("UPDATE {} SET alloc_points = %s WHERE id = %s;".format(self.table), (new_value, discord_id))
        self.mydb.commit()

    def updateName(self, discord_id: int, new_value: str):
        self.mycursor.execute("UPDATE {} SET username = %s WHERE id = %s;".format(self.table), (new_value, discord_id))
        self.mydb.commit()


    def setAsActive(self, discord_id: int):
        self.mycursor.execute("UPDATE {} SET active = 1 where id = %s;".format(self.table), (discord_id,))
        self.mydb.commit()
        
    def sufficientBalance(self, discord_id: int, amount: int):
        points = self.selectPoints(discord_id)
        return points >= amount
        
    def refundAll(self):
        """
        Moves alloc_points back into points column and then resets alloc_points back to 0
        """
        self.mycursor.execute("SELECT points, alloc_points, id FROM {}".format(self.table))
        values = self.mycursor.fetchall()
        refunded = [(x[0] + x[1], 0, x[2]) for x in values]
        for _tuple in refunded:
            self.mycursor.execute("UPDATE {} SET points = %s, alloc_points = %s WHERE id = %s".format(self.table), (_tuple[0], _tuple[1], _tuple[2]))
            self.mydb.commit()
            
    def applyStimmy(self, amount_per_day: int):
        """
        points += #days since stimmy * amount per day
        last_stimmy = today's date
        """       
        self.mycursor.execute("SELECT id, points, last_stimmy FROM {}".format(self.table))
        values = self.mycursor.fetchall()
        today = datetime.today()
        today = today.date()             
        for _tuple in values:
            _id = _tuple[0]
            points = _tuple[1]
            last_stimmy = _tuple[2]
            
            days_since_stimmy = (today - last_stimmy).days
            points += days_since_stimmy * amount_per_day
            last_stimmy = today.strftime('%Y-%m-%d')
            
            self.mycursor.execute("UPDATE {} SET points = %s, last_stimmy = %s where id = %s".format(self.table), (points, last_stimmy, _id))
            self.mydb.commit()
            
    def isValidDiscordID(self, discord_id: int):
        """
        Returns
        -------
        bool
            True if discord_id exists in database, else False.
        """
        self.mycursor.execute("SELECT id FROM {}".format(self.table))
        for id_tuple in self.mycursor.fetchall():
            if id_tuple[0] == discord_id:
                return True
        return False
    
    def leaderboardStats(self):
        self.mycursor.execute("SELECT points, username FROM {} WHERE active != 0".format(self.table))
        result = self.mycursor.fetchall()
        if not result:
            return False
        result = sorted(result, reverse=True)
        result = list(zip(*result))
        return {'names' : list(result[1]), 
                  'points' : list(result[0])}
                  
class Economy(SQLCommands):
    def __init__(self, user: str, password: str, host: str, port: str, database: str, table: str):
        super().__init__(user, password, host, port, database, table)      
        self._ids = set([])
        self.gambas = {}
        
    def createNewGamba(self, author: int, title: str, options: tuple):
        if self._ids:
            new_id = max(self._ids) + 1
        else:
            new_id = 1
        self._ids.add(new_id)    
        self.gambas[new_id] = Gamba(author, title, options)
        
        return {'id' : new_id,
                'options' : self.gambas[new_id].options,
                'options_alpha' : self.gambas[new_id].options_alpha}
    
    def newBet(self, _id: int, discord_id: int, discord_name: str, choice: str, amount: int):
        try:
            self.setAsActive(discord_id)
            self.gambas[_id].addBet(discord_id, discord_name, choice, amount)
            
            points = self.selectPoints(discord_id) - amount
            alloc_points = self.selectAllocPoints(discord_id) + amount

            self.updatePoints(discord_id, points)
            self.updateAllocPoints(discord_id, alloc_points)
            return True
        except:
            return False
        
    def closeBet(self, _id: int, result: str):
        try:
            data = self.gambas[_id].getEndBetData(result)
            if len(data['discord_id']) == 0:
                self._ids.remove(_id)
                del self.gambas[_id]
                return 1                                     #<--- Clumsy way to handle case where noone bets.
            for i, discord_id in enumerate(data['discord_id']):
                points = self.selectPoints(discord_id)
                alloc_points = self.selectAllocPoints(discord_id)
                winnings = data['winnings'][i]
                bet_amount = data['amount'][i]
                if winnings > 0:
                    points += winnings
                    alloc_points -= bet_amount
                else:
                    alloc_points -= bet_amount
                self.updatePoints(discord_id, points)
                self.updateAllocPoints(discord_id, alloc_points)    
            self._ids.remove(_id)
            del self.gambas[_id]

            # create return value for discord bot output.
            winners, winnings = [], []
            for i, v in enumerate(data['winnings']):
                if v > 0:
                    winners.append(data['discord_name'][i])
                    winnings.append(v)
            return {'winnings' : winnings,
                    'winners' : winners}
        except:
            return False
                    
    def cancelBet(self, _id: int):
        try:
            data = self.gambas[_id].getCancelBetData()
            if len(data['discord_id']) == 0:
                self._ids.remove(_id)
                del self.gambas[_id]
                return True
            for i, discord_id in enumerate(data['discord_id']):
                points = self.selectPoints(discord_id) + data['amount'][i]
                alloc_points = self.selectAllocPoints(discord_id) - data['amount'][i]
                
                self.updatePoints(discord_id, points)
                self.updateAllocPoints(discord_id, alloc_points)
            self._ids.remove(_id)
            del self.gambas[_id]
            return True
        except:
            return False
            
    def flip(self, discord_id: int, amount: int):  
        self.setAsActive(discord_id)
        win = True
        if random.randint(1, 100) >= 48:
            amount *= -1
            win = False
        points = self.selectPoints(discord_id) + amount
        self.updatePoints(discord_id, points)
        return win
           
    def sendTip(self, sender_id: int, receiver_id: int, amount: int):
        self.setAsActive(sender_id)
        try:
            sender_points = self.selectPoints(sender_id) - amount
            receiver_points = self.selectPoints(receiver_id) + amount    
            self.updatePoints(sender_id, sender_points)
            self.updatePoints(receiver_id, receiver_points)
            return True
        except:
            return False


if __name__ == '__main__':
    e = Economy('root', 'password', '127.0.0.1', '3306', 'testdb', 'swedistan')
    e.createTable()
    e.insertRow(123, 'Charlie', '2021-01-03')
    e.insertRow(12, 'Evan', '2021-01-03')
    e.insertRow(132, 'Joe', '2021-01-03')
    e.insertRow(865, 'Edd', '2021-01-03')
    e.insertRow(27, 'Glen', '2021-01-03')
    e.showTable()
    
    e.createNewGamba(123, "Will this work?", ("yes", "no", "maybe"))

    
    e.newBet(1, 12, 'Evan', 'A', 15)
    e.newBet(1, 27, 'Glen', 'B', 20)
    e.newBet(1, 123, 'Charlie', 'C', 12)
    e.newBet(1, 132, 'Joe', 'A', 99)
    
    print(e.gambas)
    print(e._ids)
    print(e.gambas[1].options_alpha)
    print(e.gambas[1].options)
    print(e.gambas[1].bets)
    
    e.showTable()
    
    # e.closeBet(1, 'A')
    e.cancelBet(1)
    e.showTable()
    e.flip(12, 20)
    e.showTable()
    
    e.sendTip(132, 123, 95)
    
    e.showTable()
    
    
    
    
    
    
    
    
    
    
    e.dropTable()

    

         

         
         
         
    
    
    
    
    
    
    