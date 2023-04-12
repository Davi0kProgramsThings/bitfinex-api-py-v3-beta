# bitfinex-api-py (v3-beta)

Official implementation of the [Bitfinex APIs (V2)](https://docs.bitfinex.com/docs) for `Python 3.8+`.

> **DISCLAIMER:** \
Production use of v3.0.0b1 (and all future beta versions) is HIGHLY discouraged. \
Beta versions should not be used in applications which require user authentication. \
Provide your API-KEY/API-SECRET, and manage your account and funds at your own risk.

### Features
- User-friendly implementations for 75+ public and authenticated REST endpoints.
    * A complete list of available REST endpoints can be found [here](https://docs.bitfinex.com/reference).
- New WebSocket client to ensure fast, secure and persistent connections.
    * Support for all public channels + authenticated events and inputs (a list can be found [here](https://docs.bitfinex.com/docs/ws-public)).
    * Automatic reconnection system in case of network failure (both client and server side).
        - The WebSocket client logs every reconnection failure, success and attempt (as well as other events).
    * Connection multiplexing to allow subscribing to a large number of public channels (without affecting performances).
        - The WebSocket server sets a limit of 25 subscriptions per connection, connection multiplexing allows the WebSocket client to bypass this limit.
- Full type-hinting and type-checking support with [`mypy`](https://github.com/python/mypy). 
    * This allow text editors to show helpful hints about the value of a variable: ![example](https://i.imgur.com/aDjapcN.png "Type-hinting example on a random code snippet")

---

## Installation

To install the latest beta release of `bitfinex-api-py`:
```bash
python3 -m pip install --pre bitfinex-api-py
```
To install a specific beta version:
```bash
python3 -m pip install bitfinex-api-py==3.0.0b1
```

## Basic usage

---

## Index

* [WebSocket client documentation](#websocket-client-documentation)
* [Building the source code](#building-the-source-code)
* [How to contribute](#how-to-contribute)

---

# WebSocket client documentation

1. [Instantiating the client](#instantiating-the-client)
    * [Authentication](#authentication)
        - [Filtering the channels](#filtering-the-channels)
2. [Running the client](#running-the-client)
    * [Closing the connection](#closing-the-connection)
3. [Subscribing to public channels](#subscribing-to-public-channels)
    * [Unsubscribing from a public channel](#unsubscribing-from-a-public-channel)
    * [Setting a custom `sub_id`](#setting-a-custom-sub_id)
4. [Listening to events](#listening-to-events)

### Advanced features
* [Sending custom notifications](#sending-custom-notifications)
* [Setting up connection multiplexing](#setting-up-connection-multiplexing)

## Instantiating the client

```python
bfx = Client(wss_host=PUB_WSS_HOST)
```

`Client::wss` contains an instance of `BfxWebSocketClient` (core implementation of the WebSocket client). \
The `wss_host` argument is used to indicate the URL to which the WebSocket client should connect. \
The `bfxapi` package exports 2 constants to quickly set this URL:

Constant | URL | When to use
:--- | :--- | :---
WSS_HOST | wss://api.bitfinex.com/ws/2 | Suitable for all situations, supports authentication.
PUB_WSS_HOST | wss://api-pub.bitfinex.com/ws/2 | For public uses only, doesn't support authentication.

PUB_WSS_HOST is recommended over WSS_HOST for applications that don't require authentication.

> **NOTE:** The `wss_host` parameter is optional, and the default value is WSS_HOST.

### Authentication

Users can authenticate in their accounts by providing a pair of API-KEY and API-SECRET:
```python
bfx = Client(
    [...],
    api_key=os.getenv("BFX_API_KEY"),
    api_secret=os.getenv("BFX_API_SECRET")
)
```

If authentication succeeds, the client will emit the `authenticated` event. \
All operations that require authentication will fail if run before the emission of this event. \
The `data` argument contains various information about the authentication, such as the `userId`, the `auth_id`, etc...

```python
@bfx.wss.on("authenticated")
def on_authenticated(data: Dict[str, Any]):
    print(f"Successful login for user <{data['userId']}>.")
```

`data` can also be useful for checking API-KEY's permissions:

```python
@bfx.wss.on("authenticated")
def on_authenticated(data: Dict[str, Any]):
    if not data["caps"]["orders"]["read"]:
        raise Exception("This application requires read permissions on orders.")

    if not data["caps"]["positions"]["write"]:
        raise Exception("This application requires write permissions on positions.")
```

> **NOTE:** A guide on how to create, edit and revoke API-KEYs and API-SECRETs can be found [here](https://support.bitfinex.com/hc/en-us/articles/115003363429-How-to-create-and-revoke-a-Bitfinex-API-Key).


#### Filtering the channels

It is possible to select which channels the client should subscribe to using the `filters` argument:

```python
bfx = Client(
    [...],
    api_key=os.getenv("BFX_API_KEY"),
    api_secret=os.getenv("BFX_API_SECRET"),
    filters=[ "wallet" ]
)
```

Filtering can be very useful both for safety reasons and for lightening network traffic (by excluding useless channels). \
Ideally, you should always use `filters`, selecting only the channels your application will actually use. \
Below, you can find a complete list of available filters (and the channels they will subscribe the client to):

Filter | Subscribes the client to... | Available events are...
:--- | :--- | :---
trading | All channels regarding the user's orders, positions and trades (all trading pairs). | `order_snapshot`, `order_new`, `order_update`, `order_cancel`, `position_snapshot`, `position_new`, `position_update`, `position_close`, `trade_execution`, `trade_execution_update`
trading-tBTCUSD | All channels regarding the user's orders, positions and trades (tBTCUSD). | `order_snapshot`, `order_new`, `order_update`, `order_cancel`, `position_snapshot`, `position_new`, `position_update`, `position_close`, `trade_executed`, `trade_execution_update`
funding | All channels regarding the user's offers, credits and loans (all funding currencies). | `funding_offer_snapshot`, `funding_offer_new`, `funding_offer_update`, `funding_offer_cancel`, `funding_credit_snapshot`, `funding_credit_new`, `funding_credit_update`, `funding_credit_close`, `funding_loan_snapshot`, `funding_loan_new`, `funding_loan_update`, `funding_loan_close`
funding-fBTC | All channels regarding the user's offers, credits and loans (fBTC). | `funding_offer_snapshot`, `funding_offer_new`, `funding_offer_update`, `funding_offer_cancel`, `funding_credit_snapshot`, `funding_credit_new`, `funding_credit_update`, `funding_credit_close`, `funding_loan_snapshot`, `funding_loan_new`, `funding_loan_update`, `funding_loan_close`
wallet | All channels regarding user's exchange, trading and deposit wallets. | `wallet_snapshot`, `wallet_update`

## Running the client

The client can be run using `BfxWebSocketClient::run`:
```python
bfx.wss.run()
```

If an event loop is already running, users can start the client with `BfxWebSocketClient::start`:
```python
await bfx.wss.start()
```

If the client succeeds in connecting to the server, it will emit the `open` event. \
This is the right place for all bootstrap activities, such as subscribing to public channels. \
To learn more about events and public channels, see [Listening to events](#listening-to-events) and [Subscribing to public channels](#subscribing-to-public-channels).

```python
@bfx.wss.on("open")
async def on_open():
    await bfx.wss.subscribe(Channel.TICKER, symbol="tBTCUSD")
```

### Closing the connection

Users can close the connection with the WebSocket server using `BfxWebSocketClient::close`:
```python
await bfx.wss.close()
```

A custom [close code number](https://www.iana.org/assignments/websocket/websocket.xhtml#close-code-number), along with a verbose reason, can be given as parameters:
```python
await bfx.wss.close(code=1001, reason="Going Away")
```

After closing the connection, the client will emit the `disconnection` event:
```python
@bfx.wss.on("disconnection")
def on_disconnection(code: int, reason: str):
    print(f"Closing connection with code: <{code}>. Reason: {reason}.")
```

## Subscribing to public channels

Users can subscribe to public channels using `BfxWebSocketClient::subscribe`:
```python
await bfx.wss.subscribe("ticker", symbol="tBTCUSD")
```

On each successful subscription, the client will emit the `subscribed` event:
```python
@bfx.wss.on("subscribed")
def on_subscribed(subscription: subscriptions.Subscription):
    if subscription["channel"] == "ticker":
        print(f"{subscription['symbol']}: {subscription['subId']}") # tBTCUSD: f2757df2-7e11-4244-9bb7-a53b7343bef8
```

### Unsubscribing from a public channel

It is possible to unsubscribe from a public channel at any time. \
Unsubscribing from a public channel prevents the client from receiving any more data from it. \
This can be done using `BfxWebSocketClient::unsubscribe`, and passing the `sub_id` of the public channel you want to unsubscribe from:

```python
await bfx.wss.unsubscribe(sub_id="f2757df2-7e11-4244-9bb7-a53b7343bef8")
```

### Setting a custom `sub_id`

The client generates a random `sub_id` for each subscription. \
These values must be unique, as the client uses them to identify subscriptions. \
However, it is possible to force this value by passing a custom `sub_id` to `BfxWebSocketClient::subscribe`:

```python
await bfx.wss.subscribe("candles", key="trade:1m:tBTCUSD", sub_id="507f1f77bcf86cd799439011")
```

## Listening to events

Whenever the WebSocket client receives data, it will emit a specific event. \
Users can either ignore those events or listen for them by registering callback functions. \
These callback functions can also be asynchronous; in fact the client fully supports coroutines ([`asyncio`](https://docs.python.org/3/library/asyncio.html)).

To add a listener for a specific event, users can use the decorator `BfxWebSocketClient::on`:
```python
@bfx.wss.on("candles_update")
def on_candles_update(sub: subscriptions.Candles, candle: Candle):
    print(f"Candle update for key <{sub['key']}>: {candle}")
```

The same can be done without using decorators:
```python
bfx.wss.on("candles_update", callback=on_candles_update)
```

You can pass any number of events to register for the same callback function:
```python
bfx.wss.on("t_ticker_update", "f_ticker_update", callback=on_ticker_update)
```

# Advanced features

## Sending custom notifications

**Sending custom notifications requires user authentication.**

Users can send custom notifications using `BfxWebSocketClient::notify`:
```python
await bfx.wss.notify({ "foo": 1 })
```

Any data can be sent along with a custom notification.

Custom notifications are broadcast by the server on all user's open connections. \
So, each custom notification will be sent to every online client of the current user. \
Whenever a client receives a custom notification, it will emit the `notification` event:
```python
@bfx.wss.on("notification")
def on_notification(notification: Notification[Any]):
    print(notification.data) # { "foo": 1 }
```

## Setting up connection multiplexing

`BfxWebSocketClient::run` and `BfxWebSocketClient::start` accept a `connections` argument:
```python
bfx.wss.run(connections=3)
```

`connections` indicates the number of connections to run concurrently (through connection multiplexing).

Each of these connections can handle up to 25 subscriptions to public channels. \
So, using `N` connections will allow the client to handle at most `N * 25` subscriptions. \
You should always use the minimum number of connections necessary to handle all the subscriptions that will be made.

For example, if you know that your application will subscribe to 75 public channels, 75 / 25 = 3 connections will be enough to handle all the subscriptions.

The default number of connections is 5; therefore, if the `connections` argument is not given, the client will be able to handle a maximum of 25 * 5 = 125 subscriptions.

Keep in mind that using a large number of connections could slow down the client performance.

The use of more than 20 connections is not recommended.

---

# Building the source code

## Testing (with unittest)

## Linting the project with pylint

## Using mypy to ensure correct type-hinting

---

# How to contribute

## License
This project is released under the `Apache License 2.0`.

The complete license can be found here: https://www.apache.org/licenses/LICENSE-2.0.
