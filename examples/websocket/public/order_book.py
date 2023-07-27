# python -c "import examples.websocket.public.order_book"

from collections import OrderedDict

from typing import List

from bfxapi import Client, PUB_WSS_HOST

from bfxapi.types import TradingPairBook, Checksum
from bfxapi.websocket.subscriptions import Book
from bfxapi.websocket.enums import Channel, Error

class OrderBook:
    def __init__(self, symbols: List[str]):
        self.__order_book = {
            symbol: {
                "bids": OrderedDict(), "asks": OrderedDict() 
            } for symbol in symbols
        }

    def update(self, symbol: str, data: TradingPairBook) -> None:
        price, count, amount = data.price, data.count, data.amount

        kind = "bids" if amount > 0 else "asks"

        if count > 0:
            self.__order_book[symbol][kind][price] = {
                "price": price, 
                "count": count,
                "amount": amount 
            }

        if count == 0:
            if price in self.__order_book[symbol][kind]:
                del self.__order_book[symbol][kind][price]

SYMBOLS = [ "tBTCUSD" ]

order_book = OrderBook(symbols=SYMBOLS)

bfx = Client(wss_host=PUB_WSS_HOST)

@bfx.wss.on("wss-error")
def on_wss_error(code: Error, msg: str):
    print(code, msg)

@bfx.wss.on("open")
async def on_open():
    for symbol in SYMBOLS:
        await bfx.wss.subscribe(Channel.BOOK, symbol=symbol, enable_checksum=True)

@bfx.wss.on("subscribed")
def on_subscribed(subscription):
    print(f"Subscription successful for pair <{subscription['pair']}>")

@bfx.wss.on("t_book_snapshot")
def on_t_book_snapshot(subscription: Book, snapshot: List[TradingPairBook]):
    for data in snapshot:
        order_book.update(subscription["symbol"], data)

@bfx.wss.on("t_book_update")
def on_t_book_update(subscription: Book, data: TradingPairBook):
    order_book.update(subscription["symbol"], data)

@bfx.wss.on("checksum_update")
def on_checksum(subscription: Book, data: Checksum):
    # TODO: compare server checksum with local one and trigger re-fetching if needed
    print(subscription["symbol"], data)

bfx.wss.run()
