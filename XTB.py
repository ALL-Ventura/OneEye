import websocket
import json
import os
import pandas as pd

import modules.tools as t


class XTB():

    def __init__(self) -> None: 
        # self.ssid = "" To be implemeented with the Stream Websocket
        self.ws = "" # websocket Class
        self.data = {} # Data retrieved by get()
        self.command_holder = "" # Temporarily holds commands for Get()
        self.import_commands()   
        self.connect_real() 
  
    def import_commands(self):
        c_path = os.path.join(os.path.abspath("./"), "resources", "xtb_commands.json")
        with open (c_path) as c_file:
            self.commands = json.load(c_file)


    def get_command(self, command:str):
        self.command_holder = json.dumps(self.commands[command])


    def connect_real(self):
        # CONNECTS TO THE WEBSOCKET

        # websocket.enableTrace(True) - For DebugginG
        WEBSOCKET_URN = "wss://ws.xtb.com/real" # Stream websocket to be implemented: "wss://ws.xtb.com/realStream"
        self.ws = websocket.create_connection(WEBSOCKET_URN)
        
        # SENDS LOGIN COMMAND
        self.get_command("login")
        self.ws.send(self.command_holder)
        in_tag = self.ws.recv()
        in_tag = in_tag.split('"')
        # self.ssid = in_tag[5] To be implemented with the Stream Websocket
        print("-------------------------", in_tag[9])
   
   
    def logout(self):

        # SENDS LOGOUT COMMAND
        self.get_command("logout")
        self.ws.send(self.command_holder)
        out_tag = self.ws.recv()
        out_tag = out_tag.split('"')[5]
        print("-------------------------", out_tag)

      
    def get(self, command:str):
        """ 
        Sends chosen command to request data and store it in the Class
        
        Command list: 
        > symbols: gets all the symbols available (>5k entries)
        > trades: gets the open positions.
        > margin: gets the balance/margin details"""

        if command.lower() in self.commands:
            self.get_command(command.lower())
            self.ws.send(self.command_holder)
            work_data = self.ws.recv()
            self.data[command] = json.loads(work_data)
        else:
            raise KeyError ("Invalid command")
        
        
    def parse(self):     
        """
        Parses the data stored in self.data into DatadFrames.
        Use it after storing all the data you need
        """   
        if self.data == {}:
            raise ValueError ("No data stored in the Class")
        
        # AVAILABLE COMMANDS
        SYMBOLS_CMD = "symbols"
        TRADES_CMD = "trades"
        MARGIN_CMD = "margin"
        
        for command in self.data:
            work_data = self.data[command]

            # PARSE SYMBOLS --------------------------------------------------------------------
            if command == SYMBOLS_CMD:
                self.data[command] = pd.DataFrame(work_data["returnData"]) 

            # PARSE TRADES --------------------------------------------------------------------
            elif command == TRADES_CMD:
                work_data = pd.json_normalize(work_data["returnData"])
                work_data = work_data[["nominalValue", "symbol"]]

                # --- LOAD TICKER DATABASE
                td_path = os.path.join(os.path.abspath("./"), "resources", "XTB_Labels.xlsx")
                TD = pd.read_excel(td_path)
                
                # --- PROCESS DATA
                work_data = pd.merge(work_data, TD, on="symbol", how= "inner")
                work_data["categoryName"] = "ETF - Stocks" * len(work_data)
                work_data = work_data [["categoryName", "nominalValue", "description"]]

            # PARSE MARGIN --------------------------------------------------------------------
            elif command == MARGIN_CMD:
                work_data = pd.DataFrame.from_dict(work_data["returnData"], orient="index", columns=["Value"]).T
                work_data = work_data [["credit", "balance", "currency"]]
                work_data["credit"] = "Cash"

            # STORE THE PARSED DATA AS CLASS ATRIBUTES
            setattr(self, command, work_data)
            


# Sample code --- see output in /sample data

api = XTB()

api.get("trades")
api.get("margin")
api.get("symbols")

t.save_as_json(api.data)

api.parse()

t.save_as_csv(api.trades)
t.save_as_csv(api.margin)
t.save_as_csv(api.symbols)


api.logout()
