import logging
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from rapidfuzz import fuzz, process

from locations import LOCATION_DB
from model import ExternalBikeApiResponse, KnownLocation, LocatorResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

mcp = FastMCP("4maLocator")

# 全局状态存储
_SEARCH_INDEX: dict[str, Any] = {
    "names": [],
    "mapping": {},
    "is_initialized": False,  # 增加初始化标记
}

API_URL = "https://newmapi.7mate.cn/api/new/surrounding/car"
HTTP_TIMEOUT = 10.0


def _ensure_initialized():
    """
    懒加载初始化函数。
    检查是否已初始化，如果没有，则构建索引。
    """
    if _SEARCH_INDEX["is_initialized"]:
        return

    logging.info("[Init] Building search index...")
    names_set: set[str] = set()
    temp_map: dict[str, KnownLocation] = {}

    # 构建映射
    for loc in LOCATION_DB:
        names_set.add(loc.name)
        temp_map[loc.name] = loc

        for alias in loc.aliases:
            names_set.add(alias)
            temp_map[alias] = loc

    _SEARCH_INDEX["names"] = list(names_set)
    _SEARCH_INDEX["mapping"] = temp_map
    _SEARCH_INDEX["is_initialized"] = True

    logging.info(f"[Init] Search index built with {len(names_set)} unique keys.")


def find_best_match(query: str, threshold: int = 70) -> KnownLocation | None:
    """查找最佳匹配，包含自动初始化检查"""
    _ensure_initialized()  # 确保数据已准备好

    choices = _SEARCH_INDEX["names"]
    if not choices:
        return None

    # RapidFuzz extractOne 返回 (match, score, index)
    result = process.extractOne(query, choices, scorer=fuzz.WRatio)

    if result:
        matched_name, score, _ = result
        if score >= threshold:
            return _SEARCH_INDEX["mapping"].get(matched_name)

    return None


@mcp.tool(
    name="find_7ma_shared_bikes",
    description="Locate 7ma shared bikes near a location name (e.g., 'Library').",
)
async def find_bikes(query: str) -> LocatorResponse:
    """Find shared bikes near user-specified location."""
    logging.info(f"[Query] Received: {query}")

    # 1. 查找位置
    matched_location = find_best_match(query)

    if not matched_location:
        message = f"No matching location found for query: '{query}'"
        logging.warning(f"[Match] {message}")
        return _create_response(query, False, None, message, None)

    primary_name = matched_location.name
    logging.info(f"[Match] '{query}' -> '{primary_name}'")

    # 2. 调用 API
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(
                API_URL,
                params={
                    "latitude": matched_location.latitude,
                    "longitude": matched_location.longitude,
                },
            )
            resp.raise_for_status()
            raw_data = resp.json()

    except httpx.TimeoutException:
        return _create_response(
            query, True, primary_name, "API request timed out", None
        )
    except httpx.HTTPStatusError as e:
        return _create_response(
            query, True, primary_name, f"API error: {e.response.status_code}", None
        )
    except Exception as e:
        logging.exception(f"[API] Error: {e}")
        return _create_response(query, True, primary_name, f"System error: {e}", None)

    # 3. 解析数据
    try:
        data_payload = raw_data.get("data") or {}
        zhuli_data = data_payload.get("zhuli") or {}

        bikes_data = ExternalBikeApiResponse.model_validate(zhuli_data)

    except Exception as e:
        logging.exception(f"[Validation] Error: {e}")
        return _create_response(
            query, True, primary_name, f"Data parsing error: {e}", None
        )

    message = f"Found {bikes_data.total} bikes near {primary_name}."
    logging.info(f"[Success] {message}")

    return _create_response(query, True, primary_name, message, bikes_data)


def _create_response(query, found, name, msg, data):
    """Helper to create LocatorResponse"""
    return LocatorResponse(
        query=query,
        match_found=found,
        matched_name=name,
        message=msg,
        bike_data=data,
    )


if __name__ == "__main__":
    _ensure_initialized()
    mcp.run(transport="stdio")
