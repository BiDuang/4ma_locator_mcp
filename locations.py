from model import KnownLocation

LOCATION_DB: list[KnownLocation] = [
    KnownLocation(
        name="711便利店",
        aliases=[
            "711",
            "听海苑4号楼",
            "听4",
            "听四",
            "瑞幸咖啡",
            "瑞幸",
            "便利店",
            "听海空间",
        ],
        latitude=35.7770006634243,
        longitude=120.03395328902104,
    ),
    KnownLocation(
        name="听海苑5号楼",
        aliases=["听海苑五号楼", "听5", "听五"],
        latitude=35.77703994470518,
        longitude=120.03317022973238,
    ),
    KnownLocation(
        name="听海餐厅",
        aliases=["听海食堂", "听海"],
        latitude=35.77640878814769,
        longitude=120.03199314505878,
    ),
    KnownLocation(
        name="信息南楼",
        aliases=["信南"],
        latitude=35.77257382743309,
        longitude=120.0306027206907,
    ),
    KnownLocation(
        name="信息北楼",
        aliases=["信北"],
        latitude=35.77432286030404,
        longitude=120.03058288472312,
    ),
    KnownLocation(
        name="山海佳苑",
        aliases=["山海"],
        latitude=35.77635370047299,
        longitude=120.02266514105418,
    ),
]
