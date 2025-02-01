import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

class Backtest:
    def __init__(self, trade_signals, stock_price_history, _market=None):
        self.trade_signals = trade_signals
        self.stock_price_history = stock_price_history
        self._market = _market


    def run_backtest(self,):
        """Backtest the trading strategy, compare with the market, and calculate the performance metrics

        Args:
            crossover_dates (pd.DataFrame): .index = date, .columns = ['signal'], .values = ['buy', 'sell']
            stock_price_history (pd.DataFrame): from yfinance
            _market (pd.DataFrame): ^GSPC from yfinance

        Returns:
            _type_: _description_
        """
        # Get dates where crossovers occur
        self.market_returns = 0
        self.trade_signals = self.trade_signals.copy()
        self.trade_signals.dropna(inplace=True)
        self.trade_signals = self.trade_signals[self.trade_signals.signal.ne(self.trade_signals.signal.shift())]
        first_buy_date = self.trade_signals[self.trade_signals['signal'] == 'buy'].index[0]
        last_sell_date = self.trade_signals[self.trade_signals['signal'] == 'sell'].index[-1]

        self.trade_signals = self.trade_signals.loc[first_buy_date:last_sell_date]
        self.stock_price_history = self.stock_price_history.loc[first_buy_date:last_sell_date].copy()
        if self._market:
            self._market =yf.Ticker('^GSPC').history(start=first_buy_date,end=last_sell_date)
            self._market = self._market.loc[first_buy_date:last_sell_date]
            self.market_returns = (self._market['Close'].iloc[-1]-self._market['Close'].iloc[0])*100/self._market['Close'].iloc[0]


        self.stock_price_history['signal'] = 'hold'
        self.stock_price_history.loc[self.trade_signals.index, 'signal'] = self.trade_signals['signal']

        self.trade_signals['return'] = np.where(self.trade_signals['signal']=='sell', self.trade_signals['Close'].pct_change(),0)
        #trade_signals['value'] = (1+trade_signals['return']).cumprod()

        returns=self.trade_signals['return'].to_numpy(dtype=float)
        returns=returns[returns!=0]
        total_return = np.prod(1+returns)-1

        self.portfolio_value = pd.Series(index=self.stock_price_history.index, dtype=float)
        self.portfolio_value.iloc[0] = self.stock_price_history['Close'].iloc[0]
        position = 0
        trades = []

        for i in range(1, len(self.stock_price_history)):
            if self.stock_price_history['signal'].iloc[i-1] == 'buy' and position == 0:
                # Buy
                position = 1
                trades.append(('buy', self.stock_price_history.index[i], self.stock_price_history['Close'].iloc[i]))
                
            elif self.stock_price_history['signal'].iloc[i-1] == 'sell' and position == 1:
                # Sell
                position = 0
                trades.append(('sell', self.stock_price_history.index[i], self.stock_price_history['Close'].iloc[i]))
            
            if position == 1:
                self.portfolio_value.iloc[i] = self.portfolio_value.iloc[i-1] * (self.stock_price_history['Close'].iloc[i]/self.stock_price_history['Close'].iloc[i-1])
            else:
                self.portfolio_value.iloc[i] = self.portfolio_value.iloc[i-1]

        self.portfolio_returns = (self.portfolio_value.iloc[-1]-self.portfolio_value.iloc[0])*100/self.portfolio_value.iloc[0]
        self.stock_returns = (self.stock_price_history['Close'].iloc[-1]-self.stock_price_history['Close'].iloc[0])*100/self.stock_price_history['Close'].iloc[0]
        

        self.num_trades = len(self.trade_signals)
        self.hit_rate = len(returns[returns>0])*100/len(returns)
        self.total_time = self.trade_signals.index[-1]-self.trade_signals.index[0]


        self.buy_dates = [t[1] for t in trades if t[0]=='buy']
        self.buy_prices = [t[2] for t in trades if t[0]=='buy']
        self.sell_dates = [t[1] for t in trades if t[0]=='sell'] 
        self.sell_prices = [t[2] for t in trades if t[0]=='sell']
        
        #return self.portfolio_value, self.stock_price_history, self.buy_dates, self.buy_prices, self.sell_dates, self.sell_prices, self.portfolio_returns, self.stock_returns, self.market_returns, self.num_trades, self.hit_rate, self.total_time

    def plot_strategy(self, tikr='AAPL', ax=None):

        print('Number of trades:',self.num_trades)
        print(f"Hit rate: {self.hit_rate:.2f}%")
        print(f'Total time: {self.total_time}')

        show_plot=False
        if ax is None:
            show_plot=True
            plt.rcParams['mathtext.fontset'] = 'stix'
            plt.rcParams['font.family'] = 'STIXGeneral'


            SMALL_SIZE = 12
            MEDIUM_SIZE = 14
            BIGGER_SIZE = 14

            plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
            plt.rc('axes', titlesize=BIGGER_SIZE)     # fontsize of the axes title
            plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
            plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
            plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
            plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize


            fig, ax = plt.subplots(figsize=(12,6))
            ax.set_title(f"{tikr} Trading Strategy Performance")
            ax.set_xlabel('Date')
            ax.set_ylabel('Value')
            ax.grid(True)

        ax.plot(self.portfolio_value, linewidth=2, label=f'Portfolio Value: {self.portfolio_returns:,.2f}%')
        ax.plot(self.stock_price_history['Close'], linewidth=2, label=f'Stock Price: {self.stock_returns:,.2f}%', alpha=0.7)
        if self._market is not None:
            ax.plot(self._market['Close']*self.stock_price_history['Close'].iloc[0]/self._market['Close'].iloc[0], linewidth=2, label=f'Market: {self.market_returns:,.2f}%', alpha=0.7)


        ax.plot(self.buy_dates, self.buy_prices, '^', color='g', markersize=10, label='Buy')
        ax.plot(self.sell_dates, self.sell_prices, 'v', color='r', markersize=10, label='Sell')

        
        if show_plot:
            plt.legend()
            #plt.savefig('figures/'+tikr+'_portfolio_performance.png',dpi=300,bbox_inches='tight')
            plt.show()
        else:
            return ax
            