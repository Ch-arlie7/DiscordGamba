import mysql.connector
import pandas as pd
from datetime import datetime
import random


class Gamba(object):   
    def __init__(self, author: int, title: str, options: tuple):
        """
        Attributes
        -------
        author: int
        title: str
        options : list
            ('Yes', 'No', 'Maybe')
        options_alpha: list
            ['A', 'B', 'C']
        bets : dict
            {'A': [(1, 30)], 'B': [(2, 20)], 'C': []} where tuple = (discord_id, amount)
        gamblers : dict
            {discord_id : discord_name}          
        """
        self.author = author 
        self.title = title
        self.options = list(options) 
        self.options_alpha = ['ABCDEFGHIJKLMNOPQRSTUVWXYZ'[x] for x in range(len(options))]       
        self.bets = {x : [] for x in self.options_alpha}
        self.gamblers = {}
         
    def addBet(self, discord_id: int, discord_name: str, choice: str, amount: int):

        self.gamblers[discord_id] = discord_name
        self.bets[choice].append((discord_id, amount))
        
    def getStandings(self):
        """
        Returns: dict:
            {'options': ('Yes', 'No', 'Maybe'), 'options_alpha': ['A', 'B', 'C'], 'totals': [30, 20, 0], 'percent': [60, 40, 0]}
        """
        total_per_choice = []
        for option in self.bets: 
            count = 0
            for bet in self.bets[option]:
                count += bet[1]
            total_per_choice.append(count)
        total = sum(total_per_choice)
        if not total:
            return False     
        percent_per_choice = [int(x/total * 100) for x in total_per_choice]
        
        return {'options' : self.options,
                'options_alpha' : self.options_alpha,
                'totals' : total_per_choice,
                'percent' : percent_per_choice}
    
    def getEndBetData(self, result: str):
        """
        Returns: dict:
            {'discord_id': [1, 2], 'discord_name': ['Charlie', 'Evan'], 'amount': [30, -20], 'winnings': [50, -20]}
        """
        discord_id, discord_name, amount= [],[],[]
        for option in self.bets:
            for bet in self.bets[option]:
                discord_id.append(bet[0])
                discord_name.append(self.gamblers[bet[0]])
                if option == result:
                    amount.append(bet[1])
                else:
                    amount.append(-bet[1])
        total = sum([abs(x) for x in amount])
        total_of_winners = sum([x for x in amount if x > 0])
        winnings = []
        for a in amount:
            if a >= 0:
                winnings.append(int((a/total_of_winners) * total))
            else:
                winnings.append(a)
        amount = [abs(x) for x in amount]
        return {'discord_id' : discord_id,
                'discord_name' : discord_name,
                'amount' : amount,
                'winnings' : winnings}
    
    def getCancelBetData(self):
        """
        Returns: dict: 
            {'discord_id': [1, 2], 'option': ['A', 'B'], 'amount': [30, 20]}
        """
        discord_id, option, amount = [],[],[]
        for o in self.bets:
            for bet in self.bets[o]:
                discord_id.append(bet[0])
                option.append(o)
                amount.append(bet[1])
                
        return {'discord_id' : discord_id,
                'option' : option,
                'amount' : amount}


if __name__ == '__main__':
    g = Gamba(1234, "Will I win this soloq game?", ('Yes', 'No', '"maybe xd"'))
    g.addBet(1234, 'Charlie', 'A', 20)
    g.addBet(1235, 'Edd', 'B', 15)
    g.addBet(1236, 'Joe', 'C', 99)
    g.addBet(1237, 'Evan', 'A', 12)
    print(g.bets)
    print(g.options)
    print(g.options_alpha)
    print(g.title)
    print(g.getCancelBetData())
    print(g.getEndBetData('B'))
    print(g.getStandings())