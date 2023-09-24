import json
import modules.tools as t
import os
import pandas as pd
import requests

from pandas import DataFrame


# Read the api documentation for more info: https://t212public-api-docs.redoc.ly/

class T212():

    """
    This class requests information from the Trading 212 endpoins using one API key.
    Please fill the API KEY on the config file.

    You can retrieve data by calling properties individually or by using the control method.
    
    Parsing functions have a default and an optional block of code for customizability.
    
    """

    def __init__(self) -> None:
        self.resources = None
        self._fetch_resources()
   

    def _fetch_resources(self):
        config_path = os.path.join(os.path.abspath("./"), "resources", "t212_config.json")
        with open (config_path) as r_file:
            self.resources = json.load(r_file)

    @property
    def cash(self) -> json:
        """
        Makes a request to the api endpoint and returns a json file
        """
        response = requests.get(self.resources["cash"], headers = self.resources["headers"])
        response.raise_for_status()
        return response.json()


    @property
    def instruments (self) -> json:
        """
        Makes a request to the api endpoint and returns a json file
        """
        response = requests.get(self.resources["instruments"], headers = self.resources["headers"])
        response.raise_for_status()
        return response.json()
  

    @property
    def pies (self) -> json:
        """
        Makes a request to the api endpoint and returns a json file
        """
        response = requests.get(self.resources["pies"], headers = self.resources["headers"])
        response.raise_for_status()
        return response.json()


    @property
    def portfolio(self) -> json:
        """
        Makes a request to the api endpoint and returns a json file
        """
        response = requests.get(self.resources["portfolio"], headers = self.resources["headers"])
        response.raise_for_status()
        return response.json()

 
    def parse_cash(self, cash: json, custom=False) -> DataFrame:
        """
        Parses the Json file into a Dataframe.
        Args: 
        Cash = cash data json file 
        Custom = set to true to run the optional block of code
        """
        df = DataFrame.from_dict(cash, orient="index", columns=["Value"]).T

        if custom is True:
        # CUSTOMIZABLE DATA PROCESSING
            df = df ["free"].reset_index()
            df.loc[0, "index"] = "Cash"

        return df
    

    def parse_instruments(self, instruments: json, custom=False) -> DataFrame:

        """
        Parses the Json file into a Dataframe.
        Args: 
        instruments = instruments data json file 
        Custom = set to true to run the optional block of code
        """
        df = DataFrame(instruments)

        if custom is True:
            # CUSTOMIZABLE DATA PROCESSING
            pass

        return df
    

    def parse_pies(self, pies: json, custom=False) -> DataFrame:
        """
        Parses the Json file into a Dataframe.
        Args: 
        pies = pies data json file 
        Custom = set to true to run the optional block of code
        """

        df = pd.json_normalize(pies)

        if custom is True:
            # CUSTOMIZABLE DATA PROCESSING

            # LOAD JSON DATA FOR PIE LABLES
            pie_label_path = os.path.join(os.path.abspath("./"), "resources", "t212_pie_labels.json")
            with open(pie_label_path) as pie_label_files:
                pie_labels_json = json.load(pie_label_files)

            # CREATE A DF WITH PIE LABELS
            pie_labels_df = pd.DataFrame(pie_labels_json).T.reset_index()
            pie_labels_df.rename(columns={"index":"id"}, inplace=True)
            pie_labels_df["id"] = pie_labels_df["id"].astype(int)

            # MERGE DATAFRAMES
            df = pd.merge(df,pie_labels_df, on="id", how="inner")
            del pie_labels_df

            # FILTER AND RENAME COLUMNS
            df = df [[0, "result.value", 1]]
            df.columns = ["Asset", "Value","Name"]

        return df


    def parse_portfolio(self, portfolio: json, custom=False) -> DataFrame:
        df = DataFrame(portfolio)

        """
        Parses the Json file into a Dataframe.
        Args: 
        portfolio = portfolio data json file 
        Custom = set to true to run the optional block of code
        """
        
        if custom is True:
            # CUSTOMIZABLE DATA PROCESSING

            # FILTER OUT PIE INVESTMENS & CALCULATE POSITION VALUE
            df = df[df["frontend"] != "AUTOINVEST"]
            df["value"] = df["quantity"] * df["currentPrice"]

            # ADD LABELS
            df['asset'] = ["Corporate equity"] * len(df) 

            instrument_label_path = os.path.join(os.path.abspath("./"), "resources", "T212_Labels.csv")            
            label_df = pd.read_csv(instrument_label_path)[["ticker", "currencyCode", "name"]]

            df = pd.merge(df, label_df, on= "ticker", how="inner")


            # CONVERTs VALUE TO EUR
            currencies = list(df["currencyCode"].unique())
            if currencies != ["EUR"]:
                xcg = t.xchange2euro (currencies) # RETURNS THE EXCHANGE RATE "ARGUMENT/EURO"
                for cur in currencies:
                    df.loc[df["currencyCode"] == cur, "value"] *= xcg[cur]
                                
            df["value"] = df["value"].apply(lambda x: round(x,2))            
            df = df.sort_values(by="value", ascending=False)
            df = df[["asset", "value", "name"]]

        return df
   
 
    def control(self, cash:bool=False, portfolio:bool=False, pies:bool=False, instruments:bool=False, parse:bool=False, custom_parse:bool=False) -> dict [str, str|float|DataFrame]:
        """"
        This method controls the entire class in one go.
       Args: choose which data you want to retrieve + if you want to parse it

       Returns a dictionary containing the requested json data.

       The dictionary will contain DataFrames if parse == True
        """
        output = {}

        if cash is True:
            cash_data = self.cash
            if parse is True:
                cash_data = self.parse_cash(cash_data, custom=custom_parse)

            output["cash"] = cash_data

        if instruments is True:
            insturments_data = self.instruments
            if parse is True:
                insturments_data = self.parse_instruments(insturments_data, custom=custom_parse)

            output["instruments"] = insturments_data
        
        if pies is True:
            pies_data = self.pies
            if parse is True:
                pies_data = self.parse_pies(pies_data, custom=custom_parse)
            
            output["pies"] = pies_data

        if portfolio is True:
            portfolio_data = self.portfolio
            if parse is True:
                portfolio_data = self.parse_portfolio(portfolio_data, custom=custom_parse)
            
            output["portfolio"] = portfolio_data
        
        return output

       

# SAMPLE CODE
t212 = T212()

# 1- Individual Properties
cash = t212.cash
cash = t212.parse_cash(cash, custom=True)

portfolio = t212.portfolio
portofio = t212.parse_portfolio(portfolio, custom=True)

pies = t212.pies
pies = t212.parse_pies(pies, custom=True)


# 2 - Control Function
  
settings = {
    "cash": True,
    "instruments": False,
    "portfolio": True,
    "pies": True,
    "parse": True,
    "custom_parse": True,
    }

    data_dict = t212.control(**settings)
     # This will return a dictionary with 3 dataframes:
     #{"cash": DataFrame,
     #"portfolio": DataFrame,
     #"pies": DataFrame,}
    
