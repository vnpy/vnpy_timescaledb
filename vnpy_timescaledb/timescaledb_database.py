from datetime import datetime
from typing import Dict, List, Any

import psycopg2

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, TickData
from vnpy.trader.database import (
    BaseDatabase,
    BarOverview,
    TickOverview
)
from vnpy.trader.setting import SETTINGS

from .timescaledb_scripts import (
    CREATE_BAR_TABLE_SCRIPT,
    CREATE_BAR_HYPERTABLE_SCRIPT,
    CREATE_BAR_OVERVIEW_TABLE_SCRIPT,
    CREATE_TICK_OVERVIEW_TABLE_SCRIPT,
    LOAD_BAR_OVERVIEW_QUERY,
    LOAD_TICK_OVERVIEW_QUERY,
    COUNT_BAR_QUERY,
    SAVE_BAR_OVERVIEW_QUERY,
    SAVE_TICK_OVERVIEW_QUERY,
    DELETE_BAR_QUERY,
    DELETE_BAR_OVERVIEW_QUERY,
    DELETE_TICK_OVERVIEW_QUERY,
    LOAD_ALL_BAR_OVERVIEW_QUERY,
    LOAD_ALL_TICK_OVERVIEW_QUERY,
    LOAD_BAR_QUERY,
    CREATE_TICK_TABLE_SCRIPT,
    CREATE_TICK_HYPERTABLE_SCRIPT,
    COUNT_TICK_QUERY,
    DELETE_TICK_QUERY,
    LOAD_TICK_QUERY,
    SAVE_BAR_QUERY,
    SAVE_TICK_QUERY
)


class TimescaleDBDatabase(BaseDatabase):
    """TimescaleDB数据库接口"""

    def __init__(self) -> None:
        """"""
        self.user: str = SETTINGS["database.user"]
        self.password: str = SETTINGS["database.password"]
        self.host: str = SETTINGS["database.host"]
        self.port: int = SETTINGS["database.port"]
        self.db: str = SETTINGS["database.database"]

        # 连接数据库
        self.connection: psycopg2.connection = psycopg2.connect(f"postgres://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}")
        self.cursor: psycopg2.cursor = self.connection.cursor()

        self.cursor.execute(CREATE_BAR_TABLE_SCRIPT)
        self.cursor.execute(CREATE_BAR_HYPERTABLE_SCRIPT)
        self.cursor.execute(CREATE_TICK_TABLE_SCRIPT)
        self.cursor.execute(CREATE_TICK_HYPERTABLE_SCRIPT)
        self.cursor.execute(CREATE_BAR_OVERVIEW_TABLE_SCRIPT)
        self.cursor.execute(CREATE_TICK_OVERVIEW_TABLE_SCRIPT)
        self.connection.commit()

    def save_bar_data(self, bars: List[BarData], stream: bool = False) -> bool:
        """保存K线数据"""
        # 缓存字段参数
        bar: BarData = bars[0]
        symbol: str = bar.symbol
        exchange: Exchange = bar.exchange
        interval: Interval = bar.interval

        # 写入K线数据
        data: List[dict] = []

        for bar in bars:
            d: Dict[str, Any] = bar.__dict__
            d["exchange"] = d["exchange"].value
            d["interval"] = d["interval"].value
            data.append(d)

        self.execute(SAVE_BAR_QUERY, data)

        # 查询汇总信息
        params: dict = {
            "symbol": symbol,
            "exchange": exchange.value,
            "interval": interval.value
        }
        self.execute(LOAD_BAR_OVERVIEW_QUERY, params)
        row: tuple = self.cursor.fetchone()

        data: dict = {
            "symbol": symbol,
            "exchange": exchange.value,
            "interval": interval.value
        }

        # 没有该合约信息
        if not row:
            data["starttime"] = bars[0].datetime
            data["endtime"] = bars[-1].datetime
            data["count"] = len(bars)
        # 已有该合约信息
        elif stream:
            data["starttime"] = row[4]
            data["endtime"] = bars[-1].datetime
            data["count"] = row[3] + len(bars)
        else:
            self.execute(COUNT_BAR_QUERY, params)
            count = self.cursor.fetchone()[0]

            data["starttime"] = min(bars[0].datetime, row[4])
            data["endtime"] = max(bars[-1].datetime, row[5])
            data["count"] = count

        self.execute(SAVE_BAR_OVERVIEW_QUERY, data)

        return True

    def save_tick_data(self, ticks: List[TickData], stream: bool = False) -> bool:
        """保存tick数据"""
        # 缓存字段参数
        tick: TickData = ticks[0]
        symbol: str = tick.symbol
        exchange: Exchange = tick.exchange

        data: List[dict] = []

        for tick in ticks:
            d: Dict[str, Any] = tick.__dict__
            d["exchange"] = d["exchange"].value
            d["localt"] = d.pop("localtime")
            if not d["localt"]:
                d["localt"] = datetime.now()
            data.append(d)

        self.execute(SAVE_TICK_QUERY, data)

        # 查询Tick汇总信息
        params: dict = {
            "symbol": symbol,
            "exchange": exchange.value
        }
        self.execute(LOAD_TICK_OVERVIEW_QUERY, params)
        row: tuple = self.cursor.fetchone()

        data: dict = {
            "symbol": symbol,
            "exchange": exchange.value,
        }

        # 没有该合约信息
        if not row:
            data["starttime"] = ticks[0].datetime
            data["endtime"] = ticks[-1].datetime
            data["count"] = len(ticks)
        # 已有该合约信息
        elif stream:
            data["starttime"] = row[3]
            data["endtime"] = ticks[-1].datetime
            data["count"] = row[2] + len(ticks)
        else:
            self.execute(COUNT_TICK_QUERY, params)
            count = self.cursor.fetchone()[0]

            data["starttime"] = min(ticks[0].datetime, row[3])
            data["endtime"] = max(ticks[-1].datetime, row[4])
            data["count"] = count

        self.execute(SAVE_TICK_OVERVIEW_QUERY, data)

        return True

    def load_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: datetime,
        end: datetime
    ) -> List[BarData]:
        """加载K线数据"""
        # 从数据库读取数据
        params: dict = {
            "symbol": symbol,
            "exchange": exchange.value,
            "interval": interval.value,
            "start": str(start),
            "end": str(end)
        }
        self.execute(LOAD_BAR_QUERY, params)
        data: List[tuple] = self.cursor.fetchall()

        # 返回BarData列表
        bars: List[BarData] = []

        for row in data:
            bar = BarData(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                datetime=row[3],
                volume=row[4],
                turnover=row[5],
                open_interest=row[6],
                open_price=row[7],
                high_price=row[8],
                low_price=row[9],
                close_price=row[10],
                gateway_name="DB"
            )
            bars.append(bar)

        return bars

    def load_tick_data(
        self,
        symbol: str,
        exchange: Exchange,
        start: datetime,
        end: datetime
    ) -> List[BarData]:
        """加载tick数据"""
        # 从数据库读取数据
        params: dict = {
            "symbol": symbol,
            "exchange": exchange.value,
            "start": str(start),
            "end": str(end)
        }

        self.execute(LOAD_TICK_QUERY, params)
        data: List[tuple] = self.cursor.fetchall()

        # 返回TickData列表
        ticks: List[TickData] = []

        for row in data:
            tick = TickData(
                symbol=symbol,
                exchange=exchange,
                datetime=row[2],
                name=row[3],
                volume=row[4],
                turnover=row[5],
                open_interest=row[6],
                last_price=row[7],
                last_volume=row[8],
                limit_up=row[9],
                limit_down=row[10],
                open_price=row[11],
                high_price=row[12],
                low_price=row[13],
                pre_close=row[14],
                bid_price_1=row[15],
                bid_price_2=row[16],
                bid_price_3=row[17],
                bid_price_4=row[18],
                bid_price_5=row[19],
                ask_price_1=row[20],
                ask_price_2=row[21],
                ask_price_3=row[22],
                ask_price_4=row[23],
                ask_price_5=row[24],
                bid_volume_1=row[25],
                bid_volume_2=row[26],
                bid_volume_3=row[27],
                bid_volume_4=row[28],
                bid_volume_5=row[29],
                ask_volume_1=row[30],
                ask_volume_2=row[31],
                ask_volume_3=row[32],
                ask_volume_4=row[33],
                ask_volume_5=row[34],
                localtime=row[35],
                gateway_name="DB"
            )
            ticks.append(tick)

        return ticks

    def delete_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval
    ) -> int:
        """删除K线数据"""
        params: dict = {
            "symbol": symbol,
            "exchange": exchange.value,
            "interval": interval.value,
        }

        # 查询数据条数
        self.execute(COUNT_BAR_QUERY, params)
        count = self.cursor.fetchone()[0]

        # 执行K线删除
        self.execute(DELETE_BAR_QUERY, params)

        # 执行汇总删除
        self.cursor.execute(DELETE_BAR_OVERVIEW_QUERY, params)

        return count

    def delete_tick_data(
        self,
        symbol: str,
        exchange: Exchange,
    ) -> int:
        """删除tick数据"""
        params: dict = {
            "symbol": symbol,
            "exchange": exchange.value
        }

        # 查询数据条数
        self.execute(COUNT_TICK_QUERY, params)
        count = self.cursor.fetchone()[0]

        # 执行Tick删除
        self.execute(DELETE_TICK_QUERY, params)

        # 执行Tick汇总删除
        self.cursor.execute(DELETE_TICK_OVERVIEW_QUERY, params)

        return count

    def get_bar_overview(self) -> List[BarOverview]:
        """查询K线汇总"""
        self.execute(LOAD_ALL_BAR_OVERVIEW_QUERY)
        data: List[tuple] = self.cursor.fetchall()

        overviews: List[BarOverview] = []

        for row in data:
            overview = BarOverview(
                symbol=row[0],
                exchange=Exchange(row[1]),
                interval=Interval(row[2]),
                count=row[3],
                start=row[4],
                end=row[5],
            )
            overviews.append(overview)

        return overviews

    def get_tick_overview(self) -> List[TickOverview]:
        """查询Tick线汇总"""
        self.execute(LOAD_ALL_TICK_OVERVIEW_QUERY)
        data: List[tuple] = self.cursor.fetchall()

        overviews: List[TickOverview] = []

        for row in data:
            overview = TickOverview(
                symbol=row[0],
                exchange=Exchange(row[1]),
                count=row[2],
                start=row[3],
                end=row[4],
            )
            overviews.append(overview)

        return overviews

    def execute(self, query: str, data: Any = None) -> None:
        """执行SQL查询"""
        if query in {SAVE_BAR_QUERY, SAVE_TICK_QUERY}:
            self.cursor.executemany(query, data)
        else:
            self.cursor.execute(query, data)

        self.connection.commit()
