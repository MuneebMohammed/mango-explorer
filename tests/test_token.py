from .context import mango

from decimal import Decimal
from solana.publickey import PublicKey


def test_token_constructor():
    symbol = "TEST"
    name = "Test Token"
    mint = PublicKey("11111111111111111111111111111113")
    decimals = Decimal(18)
    actual = mango.Token(symbol, name, mint, decimals)
    assert actual is not None
    assert actual.logger is not None
    assert actual.symbol == symbol
    assert actual.name == name
    assert actual.mint == mint
    assert actual.decimals == decimals
