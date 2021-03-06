import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class MeanVarOptManager:
    def __init__(self):
        self.backtesting = dict()

    def simulation_portfolio(self, tickers, ticker_names, num_try=10):
        port_returns = []
        port_volatility = []
        sharpe_ratio = []
        stock_weights = []

        portfolio = {'returns': port_returns,
                     'volatility': port_volatility,
                     'sharpe_ratio': sharpe_ratio}

        num_of_tickers = len(ticker_names)

        for i in range(num_try):
            weights = self.get_randomized_weights(num_of_tickers)
            portfolio_summary = self.evaluate_portfolio(tickers, weights)

            port_returns.append(portfolio_summary['return'])
            port_volatility.append(portfolio_summary['volatility'])
            sharpe_ratio.append(portfolio_summary['sharpe'])
            stock_weights.append(weights)

        for idx, symbol in enumerate(ticker_names):
            portfolio[symbol + ' weight'] = [weights[idx] for weights in stock_weights]

        column_order = ['returns', 'volatility', 'sharpe_ratio'] + [stock+' weight' for stock in ticker_names]
        portfolio_df = pd.DataFrame(portfolio)
        return portfolio_df[column_order]

    def evaluate_portfolio(self, tickers, weights, display=False):
        sample_data_returns = tickers.pct_change()

        # variance
        portfolio_variance = self.get_variance(sample_data_returns, weights)

        # standard deviation
        portfolio_volatility = np.sqrt(portfolio_variance)

        # Expected return
        expected_return = self.get_annual_returns(sample_data_returns, weights)
        sharp_ratio = expected_return / portfolio_volatility

        if display:
            print('Variance of Portfolio', str(round(portfolio_variance, 4) * 100) + '%')
            print('Variance of Risk', str(round(portfolio_volatility, 4) * 100) + '%')

            sample_data_returns.plot(figsize=(20,14))

        portfolio_dic = dict()
        selected_tickers_name = [ticker.split('.')[0] for ticker in tickers.columns]

        portfolio_dic['tickers'] = selected_tickers_name
        portfolio_dic['weights'] = weights
        portfolio_dic['volatility'] = portfolio_volatility
        portfolio_dic['return'] = expected_return
        portfolio_dic['sharpe'] = sharp_ratio

        return portfolio_dic

    def get_simulation_summary(self, portfolio_df: pd.DataFrame, ticker_names, display=False):
        min_volatility = portfolio_df['volatility'].min()
        max_sharpe = portfolio_df['sharpe_ratio'].max()

        sharpe_portfolio = portfolio_df.loc[portfolio_df['sharpe_ratio'] == max_sharpe]
        min_variance_port = portfolio_df.loc[portfolio_df['volatility'] == min_volatility]

        if display:
            # use the min, max values to locate and create the two special portfolios

            plt.style.use('seaborn-dark')
            portfolio_df.plot.scatter(x='volatility', y='returns', c='sharpe_ratio',
                                      cmap='RdYlGn', edgecolors='black', figsize = (10, 8), grid=True)
            plt.scatter(x=sharpe_portfolio['volatility'],
                        y=sharpe_portfolio['returns'],
                        c='red', marker='D', s=200)
            plt.scatter(x=min_variance_port['volatility'],
                        y=min_variance_port['returns'],
                        c='blue', marker='D', s=200)

            plt.xlabel('Volatility (Std. Deviation)')
            plt.ylabel('Expected Returns')
            plt.title('Efficient Frontier')
            plt.show()

        simulation_result = {
            'min_volatility_portfolio': min_variance_port.T,
            'max_sharpe_portfolio': sharpe_portfolio.T,
            'min_volatility': min_volatility,
            'max_sharpe': max_sharpe,
            'tickers': ticker_names
        }

        return simulation_result

    def get_ticker_names(self, tickers):
      return [ticker.split('.')[0] for ticker in tickers.columns]

    def get_randomized_weights(self, size):
        randomized_values = np.random.random([size])
        return randomized_values / sum(randomized_values)

    def get_sample_selected_ticker(self, stock_prices: pd.DataFrame, num_of_tickers=None):
        if not num_of_tickers:
            num_of_tickers = len(stock_prices.columns)

        selected_tickers = np.random.permutation(stock_prices.columns)[:num_of_tickers]
        selected_data = stock_prices[selected_tickers]
        exist_range =\
            selected_data.notnull().as_matrix().astype(int).mean(axis=1) == 1
        exist_percent = sum(exist_range)/len(exist_range)

        return selected_data[exist_range]

    def get_variance(self, sample_data_returns, weights):
        cov_matrix_portfolio = sample_data_returns.cov() * 250
        variance = np.dot(weights.T, np.dot(cov_matrix_portfolio, weights))
        return variance

    def get_annual_returns(self, sample_data_returns, weights):
        annual_returns = sample_data_returns.mean() * 250
        expected_return = np.sum(annual_returns * weights)
        return expected_return


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    mvo_manager = MeanVarOptManager()
    date_rng = pd.date_range(start='1/1/2018', end='1/08/2018')
    sample_data = {'stockA': [3,4,5,], 'stockB': [4,5,6], 'stockC': [1,7,5]}
    sample_stock_price_df = pd.DataFrame(sample_data, index=date_rng[:3])
    for i in range(5):
        selected_ticker = mvo_manager.get_sample_selected_ticker(stock_prices=sample_stock_price_df, num_of_tickers=2)
        # print(selected_ticker)
        ticker_names = mvo_manager.get_ticker_names(tickers=selected_ticker)
        portfolio_df = mvo_manager.simulation_portfolio(selected_ticker, ticker_names=ticker_names, num_try=5)
        res = mvo_manager.get_simulation_summary(portfolio_df=portfolio_df, ticker_names=ticker_names)

        print("min_volatility_portfolio")
        pp.pprint(res['min_volatility_portfolio'])
        print()
        print("max_sharpe_portfolio")
        pp.pprint(res['max_sharpe_portfolio'])
        print('-' * 50)
