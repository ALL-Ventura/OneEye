import requests
import json
import pandas as pd
import modules.tools as t
import os


# Read the api documentation for more info: https://t212public-api-docs.redoc.ly/

class T212():

    def __init__(self) -> None:
        self.resources = ""
        self.headers = ""
        self.data = {}
        self.fetch_resources()

    def fetch_resources(self):
        config_path = os.path.join(os.path.abspath("./"), "resources", "t212_config.json")
        with open (config_path) as r_file:
            self.resources = json.load(r_file)
        self.headers = self.resources["headers"]
    
    def get(self, input:str):
        """
        Uses commands to request data from the API endpoint.
        Available commands: \n
        instruments = returns all the securities available (>8k entries!).\n
        portfolio = returns the securities held.\n
        cash = returns the current cash balances.\n
        pies = returns details of the account pies. 
        """
        command = input.lower()
        if command in self.resources:
            response = requests.get(self.resources[command], headers = self.headers)
            response.raise_for_status()
            self.data[command] = response.json()
        else:
            raise KeyError("Invalid command!")
    def parse(self):
        """
        Parses the data stored in self.data into DatadFrames.
        Use it after storing all the data you need
        """   
        if self.data == {}:
            raise ValueError ("No data stored in the Class")
        
        # AVAILABLE COMMANDS
        INSTRUMENTS_CMD = "instruments"
        PORTFOLIO_CMD = "portfolio"
        CASH_CMD = "cash"
        PIES_CMD = "pies"
        
        for command in self.data:

            # PARSE INSTRUMENTS ----------------------------------
            if command == INSTRUMENTS_CMD:
                df = pd.DataFrame(self.data[command])


            # PARSE PORTFOLIO ----------------------------------
            if command == PORTFOLIO_CMD:
                df = pd.DataFrame(self.data[command])
               # OPTIONAL CODE BELOW! THIS IS JUST HOW I LIKE TO PARSE MY DATA!

                df = df[df["frontend"] != "AUTOINVEST"]
                df['asset'] = ["Corporate equity"] * len(df)
                df["value"] = df["quantity"] * df["currentPrice"]

                # IMPORT LABELS AND MERGE DFS                

                instrument_label_path = os.path.join(os.path.abspath("./"), "resources", "T212_Labels.xlsx")            
                label_df = pd.read_excel(instrument_label_path)[["ticker", "currencyCode", "name"]]

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
                

            # PARSE CASH ------------------------------------------
            if command == CASH_CMD:
                df = pd.DataFrame.from_dict(self.data[command], orient="index", columns=["Value"]).T
                # OPTIONAL CODE BELOW! THIS IS JUST HOW I LIKE TO PARSE MY DATA!
                # Cash: Only shows the free account cash
                df = df ["free"].reset_index()
                df.loc[0, "index"] = "Cash"
    

            # PARSE PIES -----------------------------------------------
            if command == PIES_CMD:
                df = pd.json_normalize(self.data[command])

                # OPTIONAL CODE BELOW! THIS IS JUST HOW I LIKE TO PARSE MY DATA!
                # Pies: only shows the total value with Custom Labels

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
                

            # STORE AS CLASS ATRIBUTE
            setattr(self,command, df)




