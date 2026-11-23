"""
Neo4j Driver 单例封装。

说明：
- 仅负责建立 / 缓存 Driver，业务逻辑请放 data_display/services.py
- 配置读取自 config.services.NEO4J
- Django 启动时不会自动创建连接，首次调用 get_driver() 才建立（懒加载）
"""
from __future__ import annotations

from typing import Optional

from neo4j import Driver, GraphDatabase

from config import services as svc_config

_driver: Optional[Driver] = None


def get_driver() -> Driver:
    """获取全局 Neo4j Driver 单例，首次调用时按 config.services.NEO4J 创建。"""
    global _driver
    if _driver is not None:
        return _driver

    cfg = svc_config.NEO4J
    uri = cfg.get('URI') or cfg.get('BOLT_URL') or 'neo4j://127.0.0.1:7687'
    user = cfg.get('USER', 'neo4j')
    password = cfg.get('PASSWORD', '')

    # Neo4j Python 驱动 6.x 不允许在 URI 里塞 user:password，必须用 auth 参数
    _driver = GraphDatabase.driver(
        uri,
        auth=(user, password),
        max_connection_pool_size=int(cfg.get('MAX_POOL', 50)),
    )
    # verify_connectivity 默认检查 'neo4j' 数据库，若实例只有自定义库会失败
    # 这里跳过验证，实际查询时若连接有问题会在 session.run 时报错
    return _driver


def close_driver() -> None:
    """Django 进程退出时调用（可选）。"""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def get_database() -> str:
    """返回默认 database 名称。"""
    return svc_config.NEO4J.get('DATABASE', 'neo4j')
