import scrapy
import json
from scrapy.crawler import CrawlerProcess
import os.path
from tkinter import *
from pandas import DataFrame, Series

class GarPRScraper(scrapy.Spider):
	name = 'GarPRScraper'
	
	def start_requests(self):
		yield scrapy.Request("https://www.notgarpr.com:3001/georgia/tournaments/{}".format(app.text.get().split("/")[-1]), self.parse)
		
	def parse(self, response):
		# yield json.loads(response.body)
		app.log.insert(index=END, chars="Loading response data.\n")
		global data 
		data = json.loads(response.body)

class Application(Frame):
	def __init__(self, master):
		Frame.__init__(self, master)
		self.grid()
		self.create_widgets()
		
	def create_widgets(self):
		self.lbl_add_tourney = Label(self, text="Add Tournment to Database")
		self.lbl_add_tourney.grid(row = 0, sticky=W)
	
		self.lbl_tourney_url = Label(self, text="Tournament URL:")
		self.lbl_tourney_url.grid(row = 1, sticky=W)
		
		self.text = Entry(self, width=77)
		self.text.grid(row=1, column=0, sticky=E)
		
		self.bttn = Button(self, text="Calculate", command=self.calculate)
		self.bttn.grid(row=2, sticky=W)
		
		self.log = Text(self, height=15, width=70)
		self.log.grid(row=3)
		
		self.lbl_Del_Player_header = Label(self, text="Delete Player from Database")
		self.lbl_Del_Player_header.grid(row=4, sticky=W)
		
		self.lbl_Del_Player = Label(self, text="Player Name:")
		self.lbl_Del_Player.grid(row=5, sticky=W)
		
		self.text_Del_Player_Name = Entry(self, width=81)
		self.text_Del_Player_Name.grid(row=5, column=0, sticky=E)
		
		self.bttn_Del_Player = Button(self, text="Delete Player", command=self.del_player)
		self.bttn_Del_Player.grid(row=6, sticky=W)
		
	def calculate(self):
		self.log.insert(index=END, chars="Beginning scraping process.\n")
		#app.log.insert()
		process = CrawlerProcess()

		process.crawl(GarPRScraper)
		process.start()

		#check if tournament has already been run through the system by checking if the response data is saved in the Tournament_Data folder
		#if so, save the data and run the rest of the code, if not do nuthin'
		if os.path.isfile("Tournament_Data/tournament_data_{}.json".format(data['name'])) == False:
			
			self.log.insert(index=END,chars="Loading player data.\n")
			#open player database
			#structure players = {player: {'dan':num, 'points':num, 'matches':num}}
			with open('players.json', 'r') as file:
				players = json.loads(file.read())

			self.log.insert(index=END,chars="Calculating player points earned and adjusting dans.\n")
			#iterate through matches from json data (data['matches'][match#]) and award points
			for i in range(len(data['matches'])):
				
				#get 'loser_name' and 'winner_name' and strip sponsor name
				loser = data['matches'][i]['loser_name'].split("|")[-1].strip()
				winner = data['matches'][i]['winner_name'].split("|")[-1].strip()
				#for each check if player is in database
					#if so,  carry on (dict.has_key(key))
					#if not, add player to players database, set dan=0, points=0
				if loser not in players.keys():
					players[loser] = {'dan':1, 'points':0, 'matches_played':0}
				if winner not in players.keys():
					players[winner] = {'dan':1, 'points':0, 'matches_played':0}
				#check each player's dan
				#calc dan difference
				dan_diff = abs(players[winner]['dan'] - players[loser]['dan'])
				#if abs(dan diff)<2
				if dan_diff < 2:
					#reward winner with +1, penalize loser with -1, check dan change and increment matches_played
					players[winner]['points'] += 1
					players[loser]['points'] -= 1
					#check for winner dan change
					if players[winner]['points'] > 2:
						players[winner]['dan'] += 1
						players[winner]['points'] = 0
					if players[winner]['points'] < -2 and players[winner]['dan'] > 1:
						players[winner]['dan'] -= 1
						players[winner]['points'] = 0
					elif players[winner]['points'] < -2 and players[winner]['dan'] == 1:
						players[winner]['points'] = -3
					#check for loser dan change
					if players[loser]['points'] > 2:
						players[loser]['dan'] += 1
						players[loser]['points'] = 0
					if players[loser]['points'] < -2 and players[loser]['dan'] > 1:
						players[loser]['dan'] -= 1
						players[loser]['points'] = 0
					elif players[loser]['points'] < -2 and players[loser]['dan'] == 1:
						players[loser]['points'] = -3
					players[winner]['matches_played']+=1
					players[loser]['matches_played']+=1

			self.log.insert(index=END,chars="Creating Dans data table.\n")
			#create dans database
			dans = {1:[]}
			#find max dan number
			temp = []
			for player in players.keys():
				temp.append(players[player]['dan'])
			max_dan = max(temp)
			#for each number, if that dan does not exist, create it
			for i in range(1, max_dan+1):
				if i not in dans.keys():
					dans[i] = []
			#insert player name into each dan
			for player in players.keys():
				dans[players[player]['dan']].append(player)
			#check for empty dans
			#move everything down
			for key in range(1, max(dans.keys())):
				i = 1
				while dans[key] == [] and dans[max(dans.keys())] != []:
					dans[key] = dans[key+i]
					dans[key+i] = []
					i+=1
			#delete empty dans
			for key in range(max(dans.keys()), 1, -1):
				if dans[key] == []:
					del dans[key]
			
			#back up the old player and dan data
			self.log.insert(index=END,chars="Saving old player data file 'players_previous.json'.\n")
			with open("players.json", 'r') as file:
				with open("players_previous.json", 'w') as f:
					f.writelines(file.readlines())
			self.log.insert(index=END,chars="Saving old dan data file 'dans_previous.json'.\n")
			with open('dans.json', 'r') as file:
				with open("dans_previous.json",'w') as f:
					f.writelines(file.readlines())
			self.log.insert(index=END,chars="Writing new data files.\n")
			#write logs for computed tournaments
			tourney_name = data['name']
			for c in "/\:*?<>|":
					tourney_name = tourney_name.replace(c, "")
			with open("Tournament_Data/tournament_data_{}.json".format(tourney_name), 'w') as file:
				file.write(json.dumps(data))
			with open("Tournament_Data/tournaments_computed.txt",'a') as file:
				file.write("\n"+str(data['name']))
			#save new player and dan data
			self.log.insert(index=END,chars="Saving new dan data file 'dans.json'.\n")
			with open("dans.json", 'w') as file:
				file.write(json.dumps(dans))
			self.log.insert(index=END,chars="Saving new player data file 'players.json'.\n")
			with open("players.json", 'w') as file:
				file.write(json.dumps(players))
			#save dans as CSV
			self.log.insert(index=END,chars="Saving old dan data as csv file.\n")
			#dan data format
			#{
			#	"1": ['Player1', 'Player2',...]
			#	"2": ['Player3', 'Player4',...]
			#	....
			#}
			
			#Create DataFrame for CSV saving
			#find biggest dan to insert first
			temp=[]
			temp_dans_list = []
			for dan in dans:
				temp_dans_list.append(dan)
				if len(dans[dan]) > len(temp):
					temp=dans[dan]
					biggest_dan = dan
			del temp_dans_list[int(biggest_dan)-1]
			#create dataframe using biggest dan
			csvFrame = DataFrame(dans[biggest_dan], columns=[biggest_dan])
			#add other dans
			for item in temp_dans_list:
				csvFrame[item] = Series(dans[item])
			csvFrame = csvFrame.sort_index(axis=1)
			
			#save as csv
			self.log.insert(index=END,chars="Saving dans csv.\n")
			csvFrame.to_csv('dans.csv', index=False)
			
			self.log.insert(index=END,chars="Done!\n")
					
		else:
			self.log.insert(index=END,chars="This tournament has already be accounted for.")
	def del_player(self):
		#delete from players database
		#delete from dans database
	
root = Tk()
root.title("Danisen Manager")
root.geometry("600x400")

app = Application(root)
root.mainloop()