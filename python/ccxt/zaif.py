# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.base.exchange import Exchange
import hashlib
import math
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import BadRequest


class zaif (Exchange):

    def describe(self):
        return self.deep_extend(super(zaif, self).describe(), {
            'id': 'zaif',
            'name': 'Zaif',
            'countries': ['JP'],
            'rateLimit': 2000,
            'version': '1',
            'has': {
                'CORS': False,
                'createMarketOrder': False,
                'fetchOpenOrders': True,
                'fetchClosedOrders': True,
                'withdraw': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766927-39ca2ada-5eeb-11e7-972f-1b4199518ca6.jpg',
                'api': 'https://api.zaif.jp',
                'www': 'https://zaif.jp',
                'doc': [
                    'https://techbureau-api-document.readthedocs.io/ja/latest/index.html',
                    'https://corp.zaif.jp/api-docs',
                    'https://corp.zaif.jp/api-docs/api_links',
                    'https://www.npmjs.com/package/zaif.jp',
                    'https://github.com/you21979/node-zaif',
                ],
                'fees': 'https://zaif.jp/fee?lang=en',
            },
            'fees': {
                'trading': {
                    'percentage': True,
                    'taker': 0.1 / 100,
                    'maker': 0,
                },
            },
            'api': {
                'public': {
                    'get': [
                        'depth/{pair}',
                        'currencies/{pair}',
                        'currencies/all',
                        'currency_pairs/{pair}',
                        'currency_pairs/all',
                        'last_price/{pair}',
                        'ticker/{pair}',
                        'trades/{pair}',
                    ],
                },
                'private': {
                    'post': [
                        'active_orders',
                        'cancel_order',
                        'deposit_history',
                        'get_id_info',
                        'get_info',
                        'get_info2',
                        'get_personal_info',
                        'trade',
                        'trade_history',
                        'withdraw',
                        'withdraw_history',
                    ],
                },
                'ecapi': {
                    'post': [
                        'createInvoice',
                        'getInvoice',
                        'getInvoiceIdsByOrderNumber',
                        'cancelInvoice',
                    ],
                },
                'tlapi': {
                    'post': [
                        'get_positions',
                        'position_history',
                        'active_positions',
                        'create_position',
                        'change_position',
                        'cancel_position',
                    ],
                },
                'fapi': {
                    'get': [
                        'groups/{group_id}',
                        'last_price/{group_id}/{pair}',
                        'ticker/{group_id}/{pair}',
                        'trades/{group_id}/{pair}',
                        'depth/{group_id}/{pair}',
                    ],
                },
            },
            'options': {
                # zaif schedule defines several market-specific fees
                'fees': {
                    'BTC/JPY': {'maker': 0, 'taker': 0},
                    'BCH/JPY': {'maker': 0, 'taker': 0.3 / 100},
                    'BCH/BTC': {'maker': 0, 'taker': 0.3 / 100},
                    'PEPECASH/JPY': {'maker': 0, 'taker': 0.01 / 100},
                    'PEPECASH/BT': {'maker': 0, 'taker': 0.01 / 100},
                },
            },
            'exceptions': {
                'exact': {
                    'unsupported currency_pair': BadRequest,  # {"error": "unsupported currency_pair"}
                },
                'broad': {
                },
            },
        })

    def fetch_markets(self, params={}):
        markets = self.publicGetCurrencyPairsAll(params)
        result = []
        for i in range(0, len(markets)):
            market = markets[i]
            id = self.safe_string(market, 'currency_pair')
            name = self.safe_string(market, 'name')
            baseId, quoteId = name.split('/')
            base = self.common_currency_code(baseId)
            quote = self.common_currency_code(quoteId)
            symbol = base + '/' + quote
            precision = {
                'amount': -math.log10(market['item_unit_step']),
                'price': market['aux_unit_point'],
            }
            fees = self.safe_value(self.options['fees'], symbol, self.fees['trading'])
            taker = fees['taker']
            maker = fees['maker']
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'active': True,  # can trade or not
                'precision': precision,
                'taker': taker,
                'maker': maker,
                'limits': {
                    'amount': {
                        'min': self.safe_float(market, 'item_unit_min'),
                        'max': None,
                    },
                    'price': {
                        'min': self.safe_float(market, 'aux_unit_min'),
                        'max': None,
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                },
                'info': market,
            })
        return result

    def fetch_balance(self, params={}):
        self.load_markets()
        response = self.privatePostGetInfo(params)
        balances = self.safe_value(response, 'return', {})
        result = {'info': response}
        funds = self.safe_value(balances, 'funds', {})
        currencyIds = list(funds.keys())
        for i in range(0, len(currencyIds)):
            currencyId = currencyIds[i]
            balance = self.safe_value(funds, currencyId)
            code = currencyId
            if currencyId in self.currencies_by_id:
                code = self.currencies_by_id[currencyId]['code']
            else:
                code = self.common_currency_code(currencyId.upper())
            account = {
                'free': balance,
                'used': 0.0,
                'total': balance,
            }
            if 'deposit' in balances:
                if currencyId in balances['deposit']:
                    account['total'] = self.safe_float(balances['deposit'], currencyId)
                    account['used'] = account['total'] - account['free']
            result[code] = account
        return self.parse_balance(result)

    def fetch_order_book(self, symbol, limit=None, params={}):
        self.load_markets()
        request = {
            'pair': self.market_id(symbol),
        }
        response = self.publicGetDepthPair(self.extend(request, params))
        return self.parse_order_book(response)

    def fetch_ticker(self, symbol, params={}):
        self.load_markets()
        request = {
            'pair': self.market_id(symbol),
        }
        ticker = self.publicGetTickerPair(self.extend(request, params))
        timestamp = self.milliseconds()
        vwap = self.safe_float(ticker, 'vwap')
        baseVolume = self.safe_float(ticker, 'volume')
        quoteVolume = None
        if baseVolume is not None and vwap is not None:
            quoteVolume = baseVolume * vwap
        last = self.safe_float(ticker, 'last')
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high'),
            'low': self.safe_float(ticker, 'low'),
            'bid': self.safe_float(ticker, 'bid'),
            'bidVolume': None,
            'ask': self.safe_float(ticker, 'ask'),
            'askVolume': None,
            'vwap': vwap,
            'open': None,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': baseVolume,
            'quoteVolume': quoteVolume,
            'info': ticker,
        }

    def parse_trade(self, trade, market=None):
        side = self.safe_string(trade, 'trade_type')
        side = 'buy' if (side == 'bid') else 'sell'
        timestamp = self.safe_integer(trade, 'date')
        if timestamp is not None:
            timestamp *= 1000
        id = self.safe_string_2(trade, 'id', 'tid')
        price = self.safe_float(trade, 'price')
        amount = self.safe_float(trade, 'amount')
        cost = None
        if price is not None:
            if amount is not None:
                cost = amount * price
        if market is None:
            marketId = self.safe_string(trade, 'currency_pair')
            if marketId in self.markets_by_id:
                market = self.markets_by_id[marketId]
        symbol = None
        if market is not None:
            symbol = market['symbol']
        return {
            'id': id,
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'type': None,
            'side': side,
            'price': price,
            'amount': amount,
            'cost': cost,
        }

    def fetch_trades(self, symbol, since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'pair': market['id'],
        }
        response = self.publicGetTradesPair(self.extend(request, params))
        numTrades = len(response)
        if numTrades == 1:
            firstTrade = response[0]
            if not firstTrade:
                response = []
        return self.parse_trades(response, market, since, limit)

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        self.load_markets()
        if type != 'limit':
            raise ExchangeError(self.id + ' allows limit orders only')
        request = {
            'currency_pair': self.market_id(symbol),
            'action': 'bid' if (side == 'buy') else 'ask',
            'amount': amount,
            'price': price,
        }
        response = self.privatePostTrade(self.extend(request, params))
        return {
            'info': response,
            'id': str(response['return']['order_id']),
        }

    def cancel_order(self, id, symbol=None, params={}):
        request = {
            'order_id': id,
        }
        return self.privatePostCancelOrder(self.extend(request, params))

    def parse_order(self, order, market=None):
        side = self.safe_string(order, 'action')
        side = 'buy' if (side == 'bid') else 'sell'
        timestamp = self.safe_integer(order, 'timestamp')
        if timestamp is not None:
            timestamp *= 1000
        if not market:
            marketId = self.safe_string(order, 'currency_pair')
            if marketId in self.markets_by_id:
                market = self.markets_by_id[marketId]
        price = self.safe_float(order, 'price')
        amount = self.safe_float(order, 'amount')
        cost = None
        if price is not None:
            if amount is not None:
                cost = price * amount
        id = self.safe_string(order, 'id')
        symbol = None
        if market is not None:
            symbol = market['symbol']
        return {
            'id': id,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'lastTradeTimestamp': None,
            'status': 'open',
            'symbol': symbol,
            'type': 'limit',
            'side': side,
            'price': price,
            'cost': cost,
            'amount': amount,
            'filled': None,
            'remaining': None,
            'trades': None,
            'fee': None,
        }

    def parse_orders(self, orders, market=None, since=None, limit=None, params={}):
        result = []
        ids = list(orders.keys())
        symbol = None
        if market is not None:
            symbol = market['symbol']
        for i in range(0, len(ids)):
            id = ids[i]
            order = self.extend({'id': id}, orders[id])
            result.append(self.extend(self.parse_order(order, market), params))
        return self.filter_by_symbol_since_limit(result, symbol, since, limit)

    def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        self.load_markets()
        market = None
        request = {
            # 'is_token': False,
            # 'is_token_both': False,
        }
        if symbol is not None:
            market = self.market(symbol)
            request['currency_pair'] = market['id']
        response = self.privatePostActiveOrders(self.extend(request, params))
        return self.parse_orders(response['return'], market, since, limit)

    def fetch_closed_orders(self, symbol=None, since=None, limit=None, params={}):
        self.load_markets()
        market = None
        request = {
            # 'from': 0,
            # 'count': 1000,
            # 'from_id': 0,
            # 'end_id': 1000,
            # 'order': 'DESC',
            # 'since': 1503821051,
            # 'end': 1503821051,
            # 'is_token': False,
        }
        if symbol is not None:
            market = self.market(symbol)
            request['currency_pair'] = market['id']
        response = self.privatePostTradeHistory(self.extend(request, params))
        return self.parse_orders(response['return'], market, since, limit)

    def withdraw(self, code, amount, address, tag=None, params={}):
        self.check_address(address)
        self.load_markets()
        currency = self.currency(code)
        if code == 'JPY':
            raise ExchangeError(self.id + ' withdraw() does not allow ' + code + ' withdrawals')
        request = {
            'currency': currency['id'],
            'amount': amount,
            'address': address,
            # 'message': 'Hinot ',  # XEM and others
            # 'opt_fee': 0.003,  # BTC and MONA only
        }
        if tag is not None:
            request['message'] = tag
        result = self.privatePostWithdraw(self.extend(request, params))
        return {
            'info': result,
            'id': result['return']['txid'],
            'fee': result['return']['fee'],
        }

    def nonce(self):
        nonce = float(self.milliseconds() / 1000)
        return '{:.8f}'.format(nonce)

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'] + '/'
        if api == 'public':
            url += 'api/' + self.version + '/' + self.implode_params(path, params)
        elif api == 'fapi':
            url += 'fapi/' + self.version + '/' + self.implode_params(path, params)
        else:
            self.check_required_credentials()
            if api == 'ecapi':
                url += 'ecapi'
            elif api == 'tlapi':
                url += 'tlapi'
            else:
                url += 'tapi'
            nonce = self.nonce()
            body = self.urlencode(self.extend({
                'method': path,
                'nonce': nonce,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Key': self.apiKey,
                'Sign': self.hmac(self.encode(body), self.encode(self.secret), hashlib.sha512),
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def handle_errors(self, httpCode, reason, url, method, headers, body, response):
        if response is None:
            return
        #
        #     {"error": "unsupported currency_pair"}
        #
        feedback = self.id + ' ' + body
        error = self.safe_string(response, 'error')
        if error is not None:
            exact = self.exceptions['exact']
            if error in exact:
                raise exact[error](feedback)
            broad = self.exceptions['broad']
            broadKey = self.findBroadlyMatchedKey(broad, error)
            if broadKey is not None:
                raise broad[broadKey](feedback)
            raise ExchangeError(feedback)  # unknown message
        success = self.safe_value(response, 'success', True)
        if not success:
            raise ExchangeError(feedback)
