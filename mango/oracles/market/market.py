# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://markets/) support is available at:
#   [Docs](https://docs.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)


import rx
import rx.operators as ops
import typing

from datetime import datetime
from decimal import Decimal

from ...context import Context
from ...ensuremarketloaded import ensure_market_loaded
from ...loadedmarket import LoadedMarket
from ...market import Market
from ...observables import observable_pipeline_error_reporter
from ...oracle import Oracle, OracleProvider, OracleSource, Price, SupportedOracleFeature
from ...orders import Order, Side


# # 🥭 Market
#
# This file contains code for a 'market' oracle. A market can be one of:
# * Serum market
# * Mango spot market
# * Mango perp market
#


# # 🥭 MarketOracleConfidence constant
#
# Market doesn't provide a confidence value.
#
MarketOracleConfidence: Decimal = Decimal(0)


# # 🥭 MarketOracle class
#
# Implements the `Oracle` abstract base class specialised to the Mango market.
#
class MarketOracle(Oracle):
    def __init__(self, market: LoadedMarket):
        name = f"Market Oracle for {market.symbol}"
        super().__init__(name, market)
        self.loaded_market: LoadedMarket = market
        features: SupportedOracleFeature = SupportedOracleFeature.TOP_BID_AND_OFFER
        self.source: OracleSource = OracleSource("Market", name, features, market)

    def fetch_price(self, context: Context) -> Price:
        orders: typing.Sequence[Order] = self.loaded_market.orders(context)
        top_bid = max([order.price for order in orders if order.side == Side.BUY])
        top_ask = min([order.price for order in orders if order.side == Side.SELL])
        mid_price = (top_bid + top_ask) / 2

        return Price(self.source, datetime.now(), self.market, top_bid, mid_price, top_ask, MarketOracleConfidence)

    def to_streaming_observable(self, context: Context) -> rx.core.Observable:
        return rx.interval(1).pipe(
            ops.observe_on(context.create_thread_pool_scheduler()),
            ops.start_with(-1),
            ops.map(lambda _: self.fetch_price(context)),
            ops.catch(observable_pipeline_error_reporter),
            ops.retry(),
        )


# # 🥭 MarketOracleProvider class
#
# Implements the `OracleProvider` abstract base class specialised to the Mango markets.
#
class MarketOracleProvider(OracleProvider):
    def __init__(self) -> None:
        super().__init__("Market Oracle Factory")

    def oracle_for_market(self, context: Context, market: Market) -> typing.Optional[Oracle]:
        loaded_market: LoadedMarket = ensure_market_loaded(context, market)
        return MarketOracle(loaded_market)

    def all_available_symbols(self, context: Context) -> typing.Sequence[str]:
        all_markets = context.market_lookup.all_markets()
        symbols: typing.List[str] = []
        for market in all_markets:
            symbols += [market.symbol]
        return symbols
