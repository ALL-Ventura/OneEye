import json
import pandas as pd
import modules.tools as t
import os
import websocket

from pandas import DataFrame

# Read the API documentation for more information http://developers.xstore.pro/documentation/
class XTB():

    """
    This class requests information from the XTB Websocket using your Xstantion Credentials.
    Please fill you userID and password on the config file.

    You can retrieve data by calling properties individually or by using the control method.
    
    Parsing functions have a default and an optional block of code for customizability.
    
    """

    def __init__(self) -> None: 
        # self.ssid = "" To be implemeented with the Stream Websocket
        self._wss = None # websocket Class
        self._commands = None
        self._fetch_resources()   
        self._connect_wss() 
 
  
    def _fetch_resources(self):
        """
        Loads the configuration file
        """
        c_path = os.path.join(os.path.abspath("./"), "resources", "xtb_config.json")
        with open (c_path) as c_file:
            self._commands = json.load(c_file)


    def _send_command(self, command:str):
        """
        Converts dictionary commands into json string and sends them to the websocket
        
        """
        dictionary_commands = self._commands[command]
        json_string_command = json.dumps(dictionary_commands)
        self._wss.send(json_string_command)
        return self._wss.recv()


    def _connect_wss(self):
    
        """ Connects to the Websocket and sends login command """
        
        # websocket.enableTrace(True) # FOR DEBUGGING
        WEBSOCKET_URN = "wss://ws.xtb.com/real"
        self._wss = websocket.create_connection(WEBSOCKET_URN)
        
        # SENDS LOGIN COMMAND
        self._send_command("login")
    

    def _get(self, command:str):
        """ 
        Sends chosen command to the wss and returns the received data
        
        Command list: 
        > symbols: gets all the symbols available (>5k entries!)
        > trades: gets the open positions.
        > margin: gets the balance/margin details"""

        data = self._send_command(command)
        data = json.loads(data)

        return data
        

    @property
    def trades(self) -> json:
        """ Sends a command to the Websocket and returns Json data """
        return self._get("trades")

    
    @property
    def symbols(self) -> json:
        """ Sends a command to the Websocket and returns Json data """
        return self._get("symbols")
    
    @property
    def margin(self) -> json:
        """ Sends a command to the Websocket and returns Json data """
        return self._get("margin")
      

    def parse_trades(self, trades, custom=False) -> DataFrame:
        """ Parses the json data into dataframes \n
        Args: \n
        Trades = trades json data \n
        custom = set to true to run the option code block        
        
        """   

        df = pd.json_normalize(trades["returnData"])

        if custom is True:

            df["equity"] = df["nominalValue"] + df["profit"]
            df = df[["equity", "symbol"]]
            

            # --- LOAD TICKER DATABASE
            td_path = os.path.join(os.path.abspath("./"), "resources", "XTB_Labels.csv")
            TD = pd.read_csv(td_path)
            
            # --- PROCESS DATA
            df = pd.merge(df, TD, on="symbol", how= "inner")
            df["categoryName"] = "ETF - Stocks" * len(df)
            df = df [["categoryName", "equity", "description"]]

        return df


    def parse_margin(self, margin, custom=False) -> DataFrame:
        """ Parses the json data into dataframes \n
        Args: \n
        margin = margin json data \n
        custom = set to true to run the option code block        
        
        """   

        df = pd.DataFrame.from_dict(margin["returnData"], orient="index", columns=["Value"]).T
        
        if custom is True:

            df = df [["credit", "balance", "currency"]]
            df["credit"] = "Cash"

        return df


    def parse_symbols(self, symbols, custom=False) -> DataFrame:
        """ Parses the json data into dataframes \n
        Args: \n
        symbols = symbols json data \n
        custom = set to true to run the option code block        
        
        """   
        """ Parses the json data into dataframes"""     
        df = DataFrame(symbols["returnData"])

        if custom is True:
            pass

        return df


    def control(self, trades:bool=False, margin:bool=False, symbols:bool=False, parse:bool=False, custom_parse:bool=False) -> dict [str, str|float|DataFrame]:
        """"
        This method controls the entire class in one go. \n
        trades: requests the trades \n
        margin: requests the margin \n
        symbols: requests the symbols \n
        parse: parses the requested data into dataframes \n
        custom_parse: runs the optional block of code in the parse functions \n
         \n
        **settings = {"trades":True, "margin":True, "symbols":False, "parse": True, "custom_parse": True, } \n
         \n
       Returns a dictionary containing the requested json data or Dataframes (if parsed) \n
        """
        output = {}

        if trades is True:
            data = self.trades
            if parse is True:
                data = self.parse_trades(data, custom=custom_parse)
            
            output["trades"] = data

        if margin is True:
            data = self.margin
            if parse is True:
                data = self.parse_margin(data, custom=custom_parse)
            output["margin"] = data

        if symbols is True:
            data = self.symbols
            if parse is True:
                data = self.parse_symbols(data, custom=custom_parse)
            
            output["symbols"] = data

        return output



# SAMPLE CODE
xtb = XTB()

# 1- Individual Properties
margin = xtb.margin # margin = dictionary with the margin data
margin = xtb.parse_margin(margin, custom=False) # margin = DataFrame with the margin data

trades = xtb.trades # trades = dictionary with the trades data
trades = xtb.parse_trades(trades, custom=False) # trades = DataFrame with the trades data

# 2 - Control Function
  
xtb_settings = {
                "trades":True, 
                "margin":True, 
                "symbols":False, 
                "parse": True, 
                "custom_parse": False, 
                }

xtb_dict = xtb.control(**xtb_settings)

# This will return a dictionary with 2 dataframes:
#{"trades": DataFrame,
#"margin": DataFrame,}

              
