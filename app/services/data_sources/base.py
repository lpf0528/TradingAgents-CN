"""
Base classes and shared typing for data source adapters
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict
import pandas as pd


class DataSourceAdapter(ABC):
    """数据源适配器基类"""

    def __init__(self):
        self._priority: Optional[int] = None  # 动态优先级，从数据库加载

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        raise NotImplementedError

    @property
    def priority(self) -> int:
        """数据源优先级（数字越小优先级越高）"""
        # 如果有动态设置的优先级，使用动态优先级；否则使用默认优先级
        if self._priority is not None:
            return self._priority
        return self._get_default_priority()

    @abstractmethod
    def _get_default_priority(self) -> int:
        """获取默认优先级（子类实现）"""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        raise NotImplementedError

    @abstractmethod
    def get_stock_list(self) -> Optional[pd.DataFrame]:
        """获取股票列表"""
        raise NotImplementedError

    @abstractmethod
    def get_daily_basic(self, trade_date: str) -> Optional[pd.DataFrame]:
        """获取每日基础财务数据"""
        raise NotImplementedError

    @abstractmethod
    def find_latest_trade_date(self) -> Optional[str]:
        """查找最新交易日期"""
        raise NotImplementedError

    # 新增：全市场实时快照（近实时价格/涨跌幅/成交额），键为6位代码
    @abstractmethod
    def get_realtime_quotes(self) -> Optional[Dict[str, Dict[str, Optional[float]]]]:
        """返回 { '000001': {'close': 10.0, 'pct_chg': 1.2, 'amount': 1.2e8}, ... }"""
        raise NotImplementedError

    # 新增：K线与新闻抽象接口
    @abstractmethod
    def get_kline(self, code: str, period: str = "day", limit: int = 120, adj: Optional[str] = None):
        """获取K线，返回按时间正序的列表: [{time, open, high, low, close, volume, amount}]"""
        raise NotImplementedError

    @abstractmethod
    def get_news(self, code: str, days: int = 2, limit: int = 50, include_announcements: bool = True):
        """获取新闻/公告，返回 [{title, source, time, url, type}]，type in ['news','announcement']"""
        raise NotImplementedError


def filter_stocks_by_prefix(df: Optional[pd.DataFrame], code_col: str = "symbol") -> Optional[pd.DataFrame]:
    """
    根据系统配置过滤股票代码前缀（如开启过滤且允许 ['60', '00']，则仅保留沪深主板股票）

    Args:
        df: 包含股票代码列的 DataFrame
        code_col: 股票代码列名（默认为 'symbol'，也可为 'code' 或 'ts_code'）

    Returns:
        过滤后的 DataFrame
    """
    if df is None or getattr(df, "empty", True):
        return df

    try:
        from app.core.config import settings
        if not getattr(settings, "STOCK_CODE_PREFIX_FILTER_ENABLED", False):
            return df

        allowed_prefixes = tuple(settings.effective_allowed_prefixes)
        if not allowed_prefixes:
            return df

        # 校验列是否存在
        target_col = None
        for col in [code_col, "symbol", "code", "ts_code"]:
            if col in df.columns:
                target_col = col
                break

        if not target_col:
            return df

        # 提取 6 位纯数字股票代码并匹配前缀
        series = df[target_col].astype(str)
        # 如果是 ts_code (例如 600000.SH)，先提纯数字部分
        clean_codes = series.str.extract(r"(\d{6})")[0].fillna(series)
        mask = clean_codes.str.startswith(allowed_prefixes)

        filtered_df = df[mask].copy()
        import logging
        logging.getLogger(__name__).info(
            f"🔍 [股票前缀过滤] 从 {len(df)} 条过滤保留 {len(filtered_df)} 条 (允许前缀: {allowed_prefixes})"
        )
        return filtered_df
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"⚠️ [股票前缀过滤] 执行过滤失败: {e}")
        return df
