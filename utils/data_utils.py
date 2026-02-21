import pandas as pd
from typing import List
from models.data_models import Candle

def candles_to_dataframe(candles: List[Candle]) -> pd.DataFrame:
    """Converts a list of Candle objects into a pandas DataFrame."""
    if not candles:
        return pd.DataFrame()

    data = {
        'timestamp': [c.timestamp for c in candles],
        'open': [float(c.open) for c in candles],
        'high': [float(c.high) for c in candles],
        'low': [float(c.low) for c in candles],
        'close': [float(c.close) for c in candles],
        'volume': [float(c.volume) for c in candles]
    }
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df