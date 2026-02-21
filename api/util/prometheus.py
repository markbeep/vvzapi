from prometheus_client import Counter, Histogram

SEARCH_QUERY_COUNTER = Counter(
    "vvzapi_search_query_total",
    "Total number of search queries",
    ["has_query"],
)


SEARCH_QUERY_DURATION = Histogram(
    "vvzapi_search_query_duration_seconds",
    "Search query execution duration in seconds",
    [
        "has_query",
        "order_by",
        "order",
        "view",
    ],
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
    ),
)
