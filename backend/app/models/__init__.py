"""SQLAlchemy ORM-Modelle — alle Modelle hier importieren damit Alembic sie erkennt."""
from app.models.asset import AssetModel
from app.models.event import EventModel
from app.models.signal import SignalModel
from app.models.regime_state import RegimeStateModel
from app.models.recommendation import RecommendationModel
from app.models.trade import TradeModel
from app.models.watchlist import WatchlistModel
from app.models.alert import AlertModel
from app.models.portfolio import PortfolioTradeModel

__all__ = [
    "AssetModel",
    "EventModel",
    "SignalModel",
    "RegimeStateModel",
    "RecommendationModel",
    "TradeModel",
    "WatchlistModel",
    "AlertModel",
    "PortfolioTradeModel",
]
