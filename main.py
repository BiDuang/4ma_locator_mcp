import httpx
from fuzzywuzzy import process
from mcp.server.fastmcp import FastMCP

from locations import LOCATION_DB
from model import ExternalBikeApiResponse, KnownLocation, LocatorResponse

mcp = FastMCP("4maLocator")


def _build_search_mappings():
    global ALL_NAMES_TO_SEARCH, NAME_TO_LOCATION_MAP

    names_set: set[str] = set()
    temp_map: dict[str, KnownLocation] = {}

    for loc in LOCATION_DB:
        names_set.add(loc.name)
        temp_map[loc.name] = loc

        for alias in loc.aliases:
            names_set.add(alias)
            temp_map[alias] = loc

    ALL_NAMES_TO_SEARCH = list(names_set)
    NAME_TO_LOCATION_MAP = temp_map

    print(f"[Init] Alias mappings built with {len(ALL_NAMES_TO_SEARCH)} unique names.")


def find_best_match(query: str, threshold: int = 70) -> KnownLocation | None:
    best_match = process.extractOne(query, ALL_NAMES_TO_SEARCH)
    if best_match and best_match[1] >= threshold:
        matched_name = best_match[0]
        return NAME_TO_LOCATION_MAP.get(matched_name)

    return None


ALL_NAMES_TO_SEARCH: list[str] = []
NAME_TO_LOCATION_MAP: dict[str, KnownLocation] = {}


@mcp.tool()
async def find_bikes(query: str) -> LocatorResponse:
    """
    Find nearby bikes based on a location query.

    :param query: The location query string
    :type query: str
    :return: LocatorResponse containing the results
    :rtype: LocatorResponse
    """

    print(f"[Tool] Received query: {query}")
    matched_location = find_best_match(query)

    if not matched_location:
        message = f"No matching location found for query: '{query}'"
        print(f"[Tool] {message}")
        return LocatorResponse(
            query=query,
            match_found=False,
            matched_name=None,
            message=message,
            bike_data=None,
        )

    primary_name = matched_location.name
    print(f"[Tool] Matched location: {query} -> {primary_name}")

    resp = await httpx.AsyncClient().get(
        "https://newmapi.7mate.cn/api/new/surrounding/car",
        params={
            "latitude": matched_location.latitude,
            "longitude": matched_location.longitude,
        },
    )
    try:
        bikes_data = ExternalBikeApiResponse.model_validate(
            resp.json().get("data", {}).get("zhuli", {}),
        )
    except Exception as e:
        message = f"Error parsing bike API data: {e}"
        print(f"[Tool] {message}")
        return LocatorResponse(
            query=query,
            match_found=True,
            matched_name=primary_name,
            message=message,
            bike_data=None,
        )

    message = f"Found {bikes_data.total} bikes near {primary_name}."
    print(f"[Tool] {message}")

    return LocatorResponse(
        query=query,
        match_found=True,
        matched_name=primary_name,
        message=message,
        bike_data=bikes_data,
    )


if __name__ == "__main__":
    _build_search_mappings()
    mcp.run(transport="stdio")
