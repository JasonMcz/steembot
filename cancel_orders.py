import sys, time, pickle, datetime
from pprint import pprint
from steemexchange import SteemExchange

if len(sys.argv)<2:
  print("Please call python3 mm.py [username] [WIF key]")
  sys.exit()
username = sys.argv[1]
key = sys.argv[2]

class Config():
    witness_url     = "wss://steemit.com/wstmp3"
    account         = username
    wif             = key

orders_file = "orders.obj"

def save_obj(filename, obj):
    pickle.dump( obj, open( filename, "wb" ) )

def load_obj(filename, default=None):
    try:
        obj = pickle.load( open( filename, "rb" ) )
        return obj
    except:
        return default

def cancel_order(order):
    try:
        if order['username']==username:
            steem.cancel(order['order_id'])
    except:
        pass
    if order['order_id'] in orders:
        del orders[order['order_id']]
        save_obj(orders_file, orders)

steem = SteemExchange(Config, safe_mode=False)
orders = load_obj(orders_file, {})

for order_id in list(orders):
    order = orders[order_id]
    print(order)
    cancel_order(order)

for i in range(3,len(sys.argv)):
    if i<len(sys.argv):
        cancel_order({'order_id': sys.argv[i], 'username': username})
