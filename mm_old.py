from pprint import pprint
from steemexchange import SteemExchange
import time, datetime, sys, pickle, traceback, urllib.request

if len(sys.argv)<3:
  print("Please call python3 mm.py [trading_mode] [username] [WIF] [username2 OPTIONAL] [WIF2 OPTIONAL]")
  sys.exit()
username = sys.argv[2]
key = sys.argv[3]

username2 = None
key2 = None
if len(sys.argv)>=5:
    username2 = sys.argv[4]
    key2 = sys.argv[5]

witness_urls = ["wss://steemit.com/wstmp3","wss://this.piston.rocks/"]
witness_url = None

for url in witness_urls:
    req = urllib.request.Request(url.replace("wss","http"))
    try:
      urllib.request.urlopen(req)
      witness_url = url
      break
    except urllib.error.HTTPError as e:
      print("ERR"+e.code)

class Config():
    witness_url     = witness_url
    account         = username
    wif             = key

class Config2():
    witness_url     = witness_url
    account         = username2
    wif             = key2

steem = None
steem2 = None
steem = SteemExchange(Config,safe_mode=False)
steem2 = None
if username2:
    steem2 = SteemExchange(Config2,safe_mode=False)

# Config Information
trading_mode = sys.argv[1]
orders_file = "orders.obj"

def save_obj(filename, obj):
    pickle.dump( obj, open( filename, "wb" ) )

def load_obj(filename, default=None):
    try:
        obj = pickle.load( open( filename, "rb" ) )
        return obj
    except:
        return default

open_orders = load_obj(orders_file, {})

def place_trade(steem, action, ticker, size, price, expiration):
    "this function triggers the limit order placing"
    if action == 'buy':
        print(action, size, ticker, price)
        buy_order = steem.buy(size, ticker, price, expiration)
        pprint(buy_order)
        order_id = buy_order['operations'][0][1]['orderid']
        order = {'order_id': order_id, 'price': price, 'size': size, 'action': action, 'expiration': expiration, 'timestamp': datetime.datetime.now(), 'username': steem.myAccount['name']}
        open_orders[order_id] = order
        save_obj(orders_file, open_orders)
        return order
    elif action == 'sell':
        print(action, size, ticker, price)
        sell_order = steem.sell(size, ticker, price, expiration)
        pprint(sell_order)
        order_id = sell_order['operations'][0][1]['orderid']
        order = {'order_id': order_id, 'price': price, 'size': size, 'action': action, 'expiration': expiration, 'timestamp': datetime.datetime.now(), 'username': steem.myAccount['name']}
        open_orders[order_id] = order
        save_obj(orders_file, open_orders)
        return order
    else:
        return

def get_whale_order():
    "this function will find the floor and ceilings of where whale orders are"
    orderbook = steem.ws.get_order_book(25, api="market_history")
    whale_bid = -1
    whale_ask = -1
    for i in range(0,len(orderbook['asks'])):
        if float(orderbook['asks'][i]['steem']) >= 1000000:
            whale_ask = float(orderbook['asks'][i]['price'])
            break

    for i in range(0,len(orderbook['bids'])):
        if float(orderbook['bids'][i]['steem']) >= 1000000:
            whale_bid = float(orderbook['bids'][i]['price'])
            break

    return {'wBid':whale_bid,'wAsk':whale_ask}

def cancel_order(order):
    try:
        if order['username']==username:
            steem.cancel(order['order_id'])
        elif order['username']==username2:
            steem2.cancel(order['order_id'])
    except:
        pass
    if order['order_id'] in open_orders:
        del open_orders[order['order_id']]
        save_obj(orders_file, open_orders)

def run_strategy_iteration(trading_mode):
    "this function will triggers the strategy we are running"
    if trading_mode == '0':
        # Setting up data
        our_bid = float(steem.get_higest_bid()['STEEM:SBD'][0]['price']) + 0.01
        our_ask = float(steem.get_lowest_ask()['STEEM:SBD'][0]['price']) - 0.01
        market_history = steem.ws.get_order_book(10, api="market_history")
        # Account Balances
        steem_balance = float(steem.getMyAccount()["balance"][0:-6])
        sbd_balance = float(steem.getMyAccount()["sbd_balance"][0:-4])

        print('#1Bot: Listening the market, STEEM:' ,steem_balance, '| SBD:' ,sbd_balance, datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p"))

        if sbd_balance > 1:
            place_trade(steem,'buy','STEEM', 0.50 * sbd_balance/our_bid, our_bid - 0.00001, 43200)
            place_trade(steem,'buy','STEEM', 0.50 * sbd_balance/our_bid, our_bid - 0.00002, 43200)

        if steem_balance > 1:
            place_trade(steem,'sell','STEEM', 0.50 * steem_balance, our_ask + 0.00001, 43200)
            place_trade(steem,'sell','STEEM', 0.50 * steem_balance, our_ask + 0.00002, 43200)

        # Sleep
        time.sleep(1)

    elif trading_mode == '3':
        best_ask_price = float(steem.get_lowest_ask()['STEEM:SBD'][0]['price'])
        best_ask_size = float(steem.get_lowest_ask()['STEEM:SBD'][0]['steem'])/100
        best_bid_price = float(steem.get_higest_bid()['STEEM:SBD'][0]['price'])
        best_bid_size = float(steem.get_higest_bid()['STEEM:SBD'][0]['steem'])/100
        wBBO = (best_bid_size * best_ask_price + best_ask_size * best_bid_price) / (best_ask_size + best_bid_size)
        market_history = steem.ws.get_order_book(10, api="market_history")
        # Account Balances
        steem_balance = float(steem.getMyAccount()["balance"][0:-6])
        sbd_balance = float(steem.getMyAccount()["sbd_balance"][0:-4])

        print('#3Bot: Listening the market, STEEM:' ,steem_balance, '| SBD:' ,sbd_balance, datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p"))

        if sbd_balance > 1:
            place_trade(steem,'buy','STEEM', 0.10 * sbd_balance/best_bid_price, wBBO, 30)
            place_trade(steem,'buy','STEEM', 0.20 * sbd_balance/best_bid_price, wBBO * 0.9999, 30) #0.2% adjustment
            place_trade(steem,'buy','STEEM', 0.30 * sbd_balance/best_bid_price, wBBO * 0.9979, 30) #0.2% adjustment
            place_trade(steem,'buy','STEEM', 0.40 * sbd_balance/best_bid_price, wBBO * 0.9976, 30) #0.2% adjustment

        if steem_balance > 0.5:
            place_trade(steem,'sell','STEEM', 0.10 * steem_balance, wBBO, 30)
            place_trade(steem,'sell','STEEM', 0.20 * steem_balance, wBBO + 1.0020, 30) #0.2% adjustment
            place_trade(steem,'sell','STEEM', 0.30 * steem_balance, wBBO + 1.0040, 30) #0.2% adjustment
            place_trade(steem,'sell','STEEM', 0.40 * steem_balance, wBBO + 1.0060, 30) #0.2% adjustment

        # Sleep
        time.sleep(1)

    elif trading_mode == '4':

        # Setting up data
        best_ask_price = float(steem.get_lowest_ask()['STEEM:SBD'][0]['price'])
        best_bid_price = float(steem.get_higest_bid()['STEEM:SBD'][0]['price'])
        mid_market = (best_ask_price + best_bid_price)/2.0
        whale_order = get_whale_order()
        whale_ask = whale_order['wAsk']
        whale_bid = whale_order['wBid']

        # Account Balances
        steem_balance = float(steem.getMyAccount()["balance"][0:-6])
        sbd_balance = float(steem.getMyAccount()["sbd_balance"][0:-4])

        # Set our bid and ask
        our_bid = None
        our_ask = None
        our_bid_size = None
        our_ask_size = None
        if whale_bid>0 and abs(whale_bid-best_bid_price)>0.05:
            our_bid = whale_bid + 0.001
            our_bid_size = 1.0 * sbd_balance/our_bid
        else:
            our_bid = best_bid_price - 0.05
            our_bid_size = 1.0 * sbd_balance/our_bid
        if whale_ask>0 and abs(whale_ask-best_ask_price)>0.05:
            our_ask = whale_ask - 0.001
            our_ask_size = 1.0 * steem_balance
        else:
            our_ask = best_ask_price + 0.05
            our_ask_size = 1.0 * steem_balance
        #if our intended market is tighter than a penny, widen by 10c
        if our_ask-our_bid<0.01:
            our_bid = our_bid - 0.025
            our_ask = our_ask + 0.025
            our_bid_size = 0.1 * sbd_balance/our_bid
            our_ask_size = 0.1 * steem_balance

        print('#4Bot: Listening the market, STEEM:' ,steem_balance, '| SBD:' ,sbd_balance, datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p"))
        print("Top level bid and ask: ",best_bid_price,best_ask_price)
        print("Whale bid and ask: ",whale_bid,whale_ask)
        print("Algo_Bid: ", our_bid, "x Algo_Ask: ", our_ask)

        if sbd_balance > 0.5 and our_bid_size > 25:
            place_trade(steem,'buy','STEEM', our_bid_size, our_bid, 43200)

        if steem_balance > 0.5 and our_ask_size > 100:
            place_trade(steem,'sell','STEEM', our_ask_size, our_ask, 43200)

        #cancel orders if conditions have changed
        for order_id in list(open_orders):
            order = open_orders[order_id]
            if order['action']=='buy' and (order['price']>our_bid or abs(order['price']-our_bid)>0.02) and order['username']==username:
                cancel_order(order)
            elif order['action']=='sell' and (order['price']<our_ask or abs(order['price']-our_ask)>0.02) and order['username']==username:
                cancel_order(order)

        #check if second account can take out orders
        # if steem2:
        #     steem_balance2 = float(steem2.getMyAccount()["balance"][0:-6])
        #     sbd_balance2 = float(steem2.getMyAccount()["sbd_balance"][0:-4])
        #     for order_id in list(open_orders):
        #         order = open_orders[order_id]
        #         #if an order has lasted long enough to qualify:
        #         if (datetime.datetime.now()-order['timestamp']).total_seconds()>60*30:
        #             #if it's a buy and it's the top level:
        #             if order['action']=='buy' and order['price']>=best_bid_price:
        #                 place_trade(steem2,'sell','STEEM', min(steem_balance2*0.9,order['size']), order['price'], 1) #expires in 1 second
        #             #if it's a sell and it's the top level:
        #             if order['action']=='sell' and order['price']<=best_ask_price:
        #                 place_trade(steem2,'buy','STEEM', min(sbd_balance2*0.9/order['price'],order['size']), order['price'], 1) #expires in 1 second
        # Sleep

    elif trading_mode == '5':

        # Setting up data
        best_ask_price = float(steem.get_lowest_ask()['STEEM:SBD'][0]['price'])
        best_bid_price = float(steem.get_higest_bid()['STEEM:SBD'][0]['price'])
        mid_market = (best_ask_price + best_bid_price)/2.0
        whale_order = get_whale_order()
        whale_ask = whale_order['wAsk']
        whale_bid = whale_order['wBid']

        # Account Balances
        steem_balance = float(steem.getMyAccount()["balance"][0:-6])
        sbd_balance = float(steem.getMyAccount()["sbd_balance"][0:-4])

        # Set our bid and ask
        our_bid = None
        our_ask = None
        our_bid_size = None
        our_ask_size = None
        if whale_bid>0:
            our_bid = whale_bid - 0.0001
            our_bid_size = 1.0 * sbd_balance/our_bid
        else:
            our_bid = best_bid_price - 0.025
            our_bid_size = 1.0 * sbd_balance/our_bid
        if whale_ask>0:
            our_ask = whale_ask + 0.0001
            our_ask_size = 1.0 * steem_balance
        else:
            our_ask = best_ask_price + 0.025
            our_ask_size = 1.0 * steem_balance

        print('#4Bot: Listening the market, STEEM:' ,steem_balance, '| SBD:' ,sbd_balance, datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p"))
        print("Top level bid and ask: ",best_bid_price,best_ask_price)
        print("Whale bid and ask: ",whale_bid,whale_ask)
        print("Algo_Bid: ", our_bid, "x Algo_Ask: ", our_ask)

        if sbd_balance > 0.5 and our_bid_size > 25:
            place_trade(steem,'buy','STEEM', our_bid_size, our_bid, 43200)

        if steem_balance > 0.5 and our_ask_size > 100:
            place_trade(steem,'sell','STEEM', our_ask_size, our_ask, 43200)

        #cancel orders if conditions have changed
        for order_id in list(open_orders):
            order = open_orders[order_id]
            if order['action']=='buy' and abs(order['price']-our_bid)>0 and order['username']==username and (datetime.datetime.now()-order['timestamp']).total_seconds()<60*30:
                cancel_order(order)
            elif order['action']=='sell' and abs(order['price']-our_ask)>0 and order['username']==username and (datetime.datetime.now()-order['timestamp']).total_seconds()<60*30:
                cancel_order(order)

        #check if second account can take out orders
        # if steem2:
        #     steem_balance2 = float(steem2.getMyAccount()["balance"][0:-6])
        #     sbd_balance2 = float(steem2.getMyAccount()["sbd_balance"][0:-4])
        #     for order_id in list(open_orders):
        #         order = open_orders[order_id]
        #         #if an order has lasted long enough to qualify:
        #         if (datetime.datetime.now()-order['timestamp']).total_seconds()>60*30:
        #             #if it's a buy and it's the top level:
        #             if order['action']=='buy' and order['price']>=best_bid_price:
        #                 place_trade(steem2,'sell','STEEM', min(steem_balance2*0.9,order['size']), order['price'], 1) #expires in 1 second
        #             #if it's a sell and it's the top level:
        #             if order['action']=='sell' and order['price']<=best_ask_price:
        #                 place_trade(steem2,'buy','STEEM', min(sbd_balance2*0.9/order['price'],order['size']), order['price'], 1) #expires in 1 second
        # Sleep
        #time.sleep(2)

    elif trading_mode == '100':
        #size is in steem
        ask_price = 2.81
        ask_size = 0
        if ask_size>0:
            place_trade(steem,'sell','STEEM', ask_size, ask_price, 86400)

        #size is in steem
        bid_price = 2.97
        bid_size = 0/bid_price
        if bid_size>0:
            place_trade(steem,'buy','STEEM', bid_size, bid_price, 86400)

print("Running strategy #"+str(trading_mode))
run_strategy_iteration(trading_mode)
