import os
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from time import sleep
from datetime import datetime

class CryptoAPIHandler:
  def __init__(self, api_key, output_dir, output_file="API.csv"):
        self.url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        self.parameters = {
            'start': '1',
            'limit': '100',  
            'convert': 'USD'
        }
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key
        }
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, output_file)
        self.session = Session()
        self.session.headers.update(self.headers)
        self.dataframe = pd.DataFrame()

  def fetch_data(self):
        """Fetch data from the API."""
        try:
            response = self.session.get(self.url, params=self.parameters)
            data = json.loads(response.text)
            return data['data']
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(f"Error fetching data: {e}")
            return None
        
  def save_data(self, data, save_csv=True):
        """Normalize JSON data and save it."""
        self.dataframe = pd.json_normalize(data)
        self.dataframe['timestamp'] = pd.to_datetime('now')                                  # If you automate pulling data, thaen you need to know the time of pulling each row

        if save_csv:
            if not os.path.isfile(self.output_file):                                         # If the file doesn't exist, then you need to create the csv file
                self.dataframe.to_csv(self.output_file, index=False, header=True)
            else:
                self.dataframe.to_csv(self.output_file, index=False, mode='a', header=False) # If the file exists, then the data will be appended to the existed file
  
  def load_data(self):
        """Load data from the saved CSV file."""
        if os.path.isfile(self.output_file):
            return pd.read_csv(self.output_file)
        else:
            print("No data file found.")
            return None
        
  def automate_data_pull(self, interval, runs):
        """Automate the data pull process."""
        for i in range(runs):
            print(f"Run {i+1}/{runs}: Pulling data at {datetime.now()}")
            data = self.fetch_data()
            if data:
                self.save_data(data)
            print(f"Run {i+1} completed. Sleeping for {interval} seconds...\n")
            sleep(interval)

class DataTransformer:
    @staticmethod
    def transform_data(dataframe):
        """Transform data for analysis."""
        pd.set_option('display.float_format', lambda x: '%.5f' % x)
        df_grouped = dataframe.groupby('name', sort=False)[[
            'quote.USD.percent_change_1h', 
            'quote.USD.percent_change_24h', 
            'quote.USD.percent_change_7d', 
            'quote.USD.percent_change_30d', 
            'quote.USD.percent_change_60d', 
            'quote.USD.percent_change_90d'
        ]].mean()
        
        df_stacked = df_grouped.stack().to_frame(name='values').reset_index()
        df_transformed = df_stacked.rename(columns={'level_1': 'Percent_Change'})
        df_transformed['Percent_Change'] = df_transformed['Percent_Change'].replace(
            [
                'quote.USD.percent_change_1h', 'quote.USD.percent_change_24h',
                'quote.USD.percent_change_7d', 'quote.USD.percent_change_30d',
                'quote.USD.percent_change_60d', 'quote.USD.percent_change_90d'
            ],
            ['1h', '24h', '7d', '30d', '60d', '90d']
        )
        return df_transformed
    
    @staticmethod
    def filter_coin_data(dataframe, coin_name):
        """Filter data for a specific cryptocurrency."""
        return dataframe.query(f'name == "{coin_name}"')
    
class DataVisualizer:
    @staticmethod
    def plot_percent_change(dataframe):
        """Visualize percent change over time."""
        plot = sns.catplot(
            x='Percent_Change',
            y='values',
            hue='name',
            data=dataframe,
            kind='point',
            height=6,
            palette='deep'
        )
        plt.title("Cryptocurrency Percent Change")
        plt.show()

    @staticmethod
    def plot_price_over_time(dataframe):                                        # If you automate pulling data over time this visualisation will be usefull
        """Visualize price changes over time for a specific cryptocurrency."""  
        sns.set_theme(style='darkgrid')
        sns.lineplot(data=dataframe, x='timestamp', y='quote.USD.price')
        plt.title("Price Over Time")
        plt.show()
        

    @staticmethod
    def Market_Capitalization_vs_Volume(dataframe):
        """Highlight the relationship between market capitalization, trading volume, and price."""
        plt.figure(figsize=(10, 6))
        plt.scatter(
            dataframe['quote.USD.market_cap'], 
            dataframe['quote.USD.volume_24h'], 
            s=dataframe['quote.USD.price'] / 10,  # Bubble size proportional to price
            alpha=0.6, 
            c='blue'
        )
        plt.xscale('log')
        plt.yscale('log')
        plt.title('Market Cap vs. Volume (Bubble Size: Price)')
        plt.xlabel('Market Cap (Log Scale)')
        plt.ylabel('Trading Volume (24h, Log Scale)')
        plt.show()
    
    @staticmethod
    def Top5_Cryptocurrencies_Market_Dominance(dataframe):
        """Visualize market dominance of the top 5 cryptocurrencies by market capitalization"""
        top_5 = dataframe.nlargest(5, 'quote.USD.market_cap')
        plt.pie(top_5['quote.USD.market_cap'], labels=top_5['name'], autopct='%1.1f%%', startangle=140)
        plt.title('Market Dominance of Top 5 Cryptocurrencies')
        plt.show()


if __name__ == "__main__":
    api_key = '5a1eb4fe-7fbf-4e57-96b1-ab705c41da2b'
    output_dir = r'C:\\Users\\hp\\Desktop\\All\\college\\Third_year\\Data_Warehouse\\HW1_API_'

    # Initialize the API handler
    api_handler = CryptoAPIHandler(api_key, output_dir)

    # Automate data pulling
    interval = 60  # Fetch data every 60 seconds
    runs = 3  # Number of runs
    api_handler.automate_data_pull(interval, runs)

    # Fetch and save data
    data = api_handler.fetch_data()
    #print(data)

    if data:
        api_handler.save_data(data)

    # Load data for analysis
    saved_data = api_handler.load_data()
    #print(saved_data)
    
    if saved_data is not None:
        # Transform data
        transformer = DataTransformer()
        transformed_data = transformer.transform_data(saved_data)

        # Visualize data
        visualizer = DataVisualizer()
        visualizer.plot_percent_change(transformed_data)
        visualizer.Market_Capitalization_vs_Volume(saved_data)

        # Filter and visualize specific coin data,if you use automating pull
        bitcoin_data = transformer.filter_coin_data(saved_data, "Bitcoin")
        visualizer.plot_price_over_time(bitcoin_data)




    
    
  







