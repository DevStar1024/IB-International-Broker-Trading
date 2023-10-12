from ib_insync import *
#from ibapi.client import *
#from ibapi.wrapper import *




util.startLoop()  # uncom
import pandas as pd

# connect to IB

ib = IB()
ib.connect("127.0.0.1", 7497, clientId=6)

# user setting

lot = 1
maxloss = 10
maxprofit = 10
position = "none"
posi_price = 0
str = ""

# open txt file to write data

file = open("output.txt", "a")

# define contract

contract = Forex()
contract.symbol = "MHI"
contract.exchange = "HKFE"
contract.secType = "FUT"
contract.localSymbol = "MHIU3"
contract.currency = "HKD"
contract.lastTradeDateOrContractMonth = "202309"
ib.qualifyContracts(contract)

data = ib.reqMktData(contract)        # current data

#historical data

historical_data = ib.reqHistoricalData(
    contract,
    endDateTime="",
    durationStr="1 D",
    barSizeSetting="1 min",
    whatToShow="TRADES",
    useRTH=0,
    keepUpToDate=True,
)


def on_new_bar(bars: BarDataList, has_new_bar: bool):
    if has_new_bar:

        global position
        global posi_price
        global str

        
        df = util.df(historical_data)  # dataframe of historical data

        # define functions which get current sma and previous sma

        def curr_sma(x):
            return df.close.rolling(x).mean().iloc[-1]

        def prev_sma(x):
            return df.close.rolling(x).mean().iloc[-2]
        
        # when 3sma crossover 8sma

        #print(data.close,prev_sma(3),curr_sma(3),prev_sma(8),curr_sma(8))
        #print(data.time,data.bid, data.ask)
        print("prev_sma:",prev_sma(3),prev_sma(8))
        print("manual_prev_sma:", (bars[-4].close + bars[-3].close + bars[-2].close)/3, (bars[-9].close+bars[-8].close+bars[-7].close+bars[-6].close + bars[-5].close+bars[-4].close+bars[-3].close+bars[-2].close)/8)
        print("curr_sma:",curr_sma(3),curr_sma(8))
        print("manual_curr_sma:", (bars[-1].close + bars[-3].close + bars[-2].close) / 3, (bars[-1].close + bars[-8].close + bars[-7].close + bars[-6].close + bars[-5].close + bars[-4].close + bars[-3].close + bars[-2].close) / 8)
              
        if (prev_sma(3) < prev_sma(8) and curr_sma(3) > curr_sma(8)):

            if position == "none":  # place a long order
                position = "buy"
                posi_price = data.ask
                trade = ib.placeOrder(contract, MarketOrder("BUY", lot))
                str = "Open position: bought for {} at {}\n"
                time = trade.log[0].dict()['time']
                file.write(str.format(data.ask, time))
                print(str.format(data.ask, time))
            elif position == "sell":  # close the position
                position = "none"
                trade = ib.placeOrder(contract, MarketOrder("BUY", lot))
                str = "Close position: bought for {} at {}\n"
                time = trade.log[0].dict()['time']
                file.write(str.format(data.ask, time))
                print(str.format(data.ask, time))

        if (prev_sma(3) > prev_sma(8) and curr_sma(3) < curr_sma(8)):

            if position == "none":  # place a short order
                position = "sell"
                posi_price = data.bid
                trade = ib.placeOrder(contract, MarketOrder("SELL", lot))
                str = "Open position: sold for {} at {}\n"
                time = trade.log[0].dict()['time']
                file.write(str.format(data.bid, time))
                print(str.format(data.bid, time))
            elif position == "buy":  # close the position
                position = "none"
                trade = ib.placeOrder(contract, MarketOrder("SELL", lot))
                str = "Close position: sold for {} at {}\n"
                time = trade.log[0].dict()['time']
                file.write(str.format(data.bid, time))
                print(str.format(data.bid, time))


        # set limits

        if position == "buy" and (data.bid >= posi_price + maxprofit or data.bid <= posi_price - maxloss):
            position = "none"
            trade = ib.placeOrder(contract, MarketOrder("SELL", lot))
            str = "Close OCA : sold for {} at {}\n"
            time = trade.log[0].dict()['time']
            file.write(str.format(data.bid, time))
            print(str.format(data.bid, time))

        if position == "sell" and (data.ask <= posi_price - maxprofit or data.ask >= posi_price + maxloss):
            position = "none"
            trade = ib.placeOrder(contract, MarketOrder("BUY", lot))
            str = "Close OCA : sold for {} at {}\n"
            time = trade.log[0].dict()['time']
            file.write(str.format(data.ask, time))
            print(str.format(data.ask, time))


# Set callback function for streaming bars

historical_data.updateEvent += on_new_bar

# Run infinitely

ib.run()

# close txt file

file.close()