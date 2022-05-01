from sqlbase import SQLBase
from datetime import datetime
import random


class Economy(SQLBase):
    def __init__(self, database: str):
        super().__init__(database)
        self.stimmy_amount = 100
        self.separator = '£$af34'
        self.create_database()
        self.create_main_table()
        self.create_gambas_table()
        self.apply_stimmy()

    def sufficient_balance(self, discord_id: int, amount: int)->bool:
        return self.select_row_by_id('points', discord_id)[0] >= amount

    def update_username(self, discord_id: int, discord_name: str):
        self.update_row_by_id(('username',), (discord_name,), discord_id)
       
    def apply_stimmy(self):       
        data = self.select_columns("id, points, last_stimmy")
        today = datetime.today()
        today = today.date()
        updated_last_stimmy = today.strftime('%Y-%m-%d')
        for row in data:
            discord_id = row[0]
            points = row[1] + ((today - row[2]).days * self.stimmy_amount)
            self.update_row_by_id(('points', 'last_stimmy'), (points, updated_last_stimmy), discord_id)

    def flip(self, discord_id: int, amount: int)->bool:
        self.set_as_active(discord_id)

        win = random.choice([True, False])
        data = self.select_row_by_id('points, flip_count, flip_wins, flip_winnings', discord_id)
        flip_count = data[1] + 1
        if win:
            flip_wins = data[2] + 1
            points = data[0] + amount
            flip_winnings = data[3] + amount
        else:
            flip_wins = data[2]
            points = data[0] - amount
            flip_winnings = data[3] - amount
        self.update_row_by_id(('points', 'flip_count', 'flip_wins', 'flip_winnings'), (points, flip_count, flip_wins, flip_winnings), discord_id)
        return win

    def send_tip(self, sender_id: int, receiver_id: int, amount: int):
        self.set_as_active(sender_id)

        sender_points = self.select_row_by_id('points', sender_id)[0] - amount
        receiver_points = self.select_row_by_id('points', receiver_id)[0] + amount
        self.update_row_by_id(('points',), (sender_points,), sender_id)
        self.update_row_by_id(('points',), (receiver_points,), receiver_id)
        return True

    def create_new_gamba(self, author: int, title: str, options: tuple)-> dict:
        self.set_as_active(author)
        ids = self.select_columns('id', 'gambas')
        ids = [x[0] for x in ids]
        if ids:
            new_id = max(ids) + 1
        else:
            new_id = 1
        options_alpha = ['ABCDEFGHIJKLMNOPQRSTUVWXYZ'[x] for x in range(len(options))]
        options_alpha_string = self.separator.join(options_alpha)
        options_string = self.separator.join(list(options))
        self.insert_gamba(new_id, title, author, options_string, options_alpha_string)
        self.create_gamba_table(new_id, options_alpha)     
        return {'id' : new_id,
                'options' : options,
                'options_alpha' : options_alpha}

    def add_bet(self, g_id: int, discord_id: int, discord_name: str, choice: str, amount: int)->bool:
        self.set_as_active(discord_id)
        self.insert_bet_data(g_id, discord_id, discord_name, choice, amount)
        points, alloc_points = self.select_row_by_id('points, alloc_points', discord_id)
        points -= amount
        alloc_points += amount
        self.update_row_by_id(('points', 'alloc_points'), (points, alloc_points), discord_id)
        return True

    def close_bet(self, g_id: int, result: str):
        data = self.select_columns('*', 'gamba{}'.format(g_id)) #[(, ), (, ),.]
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        winners, winners_bet_amounts, winner_names = [], [], []
        total_bet_amount = 0

        for row in data:
            row = list(row)
            userID = row[0]
            userName = row[1]
            player_bet_amount = sum(row[2:])
            w = False
            for i, option_bet_amount in enumerate(row[2:]):
                if alphabet[i] == result and option_bet_amount != 0:
                    winners.append(userID)
                    winners_bet_amounts.append(option_bet_amount)
                    winner_names.append(userName)
                    w = True
            
            alloc_points, gamba_count, gamba_winnings = self.select_row_by_id('alloc_points, gamba_count, gamba_winnings', userID)
            gamba_count += 1
            alloc_points -= player_bet_amount
            if not w:
                gamba_winnings -= player_bet_amount
            self.update_row_by_id(('alloc_points', 'gamba_count', 'gamba_winnings'), (alloc_points, gamba_count, gamba_winnings), userID)
            total_bet_amount += player_bet_amount

        total_of_winners = sum(winners_bet_amounts)
        winnings = [int((x / total_of_winners) * total_bet_amount) for x in winners_bet_amounts]     
        for i, winner in enumerate(winners):
            points, gamba_wins, gamba_winnings = self.select_row_by_id('points, gamba_wins, gamba_winnings', winner)
            points += winnings[i]
            gamba_wins += 1
            gamba_winnings += winnings[i]
            self.update_row_by_id(('points', 'gamba_wins', 'gamba_winnings'), (points, gamba_wins, gamba_winnings), winner)
        
        self.drop_table('gamba{}'.format(g_id))
        self.remove_gamba(g_id)  
        return {'winners' : winners,
                'winner_names' : winner_names,
                'winnings' : winnings}

    def cancel_bet(self, g_id: int):
        data = self.select_columns('*', 'gamba{}'.format(g_id)) #[(, ), (, ),.]
        for row in data:
            row = list(row)
            discord_id = row[0]
            player_bet_amount = sum(row[2:])
            points, alloc_points = self.select_row_by_id('points, alloc_points', discord_id)
            points += player_bet_amount
            alloc_points -= player_bet_amount
            self.update_row_by_id(('points', 'alloc_points'), (points, alloc_points), discord_id)     
        self.drop_table('gamba{}'.format(g_id))
        self.remove_gamba(g_id)

    def is_valid_g_id(self, g_id: int):
        return self.select_gamba_standings(g_id) != None

    def is_author(self, g_id: int, author: int):
        data = self.select_gamba_standings(g_id)
        return author == data[1]

    def is_valid_choice(self, g_id: int, choice: str):
        data = self.select_gamba_standings(g_id)
        choices = data[3].split(self.separator)
        return choice in choices

    def has_already_bet(self, g_id: int, author: int):
        data = self.select_columns('id', 'gamba{}'.format(g_id))
        bettors = [x[0] for x in data]
        return author in bettors

    def active_gambas(self):
        data = self.select_columns('id, title', 'gambas')
        return {x[0]:x[1] for x in data}

    def gamba_standings(self, g_id: int)->dict:
        title, author, options, options_alpha = self.select_gamba_standings(g_id)
        options = options.split(self.separator)
        options_alpha = options_alpha.split(self.separator)
        data = self.select_columns('*', 'gamba{}'.format(g_id)) #[(, ), (, ),.]
        totals = [0 for x in options]
        for row in data:
            row = list(row)[2:]
            for i, amount in enumerate(row):
                totals[i] += amount
        overall = sum(totals)
        if overall == 0:
            overall = 1
        percent = [int((x/overall)*100) for x in totals]

        return {'title' : title,
                'author' : author,
                'options' : options,
                'options_alpha' : options_alpha,
                'totals' : totals,
                'percent' : percent}
        
    def clear_all_gambas(self):
        '''For testing'''
        data = self.select_columns('id', 'gambas')
        print(data)
        data = [x[0] for x in data]
        print(data)
        for gamba_id in data:
            self.drop_table('gamba{}'.format(gamba_id))
        