from prometheus_client import Counter, Histogram

# A "search" is an actual query. Landing-page loads with no query are counted
# separately (INDEX_VIEWS) so that "how much of my index traffic is searches?"
# is answerable without a `has_query="false"` series inside a search metric.
SEARCH_REQUESTS = Counter(
    "vvzapi_search_requests_total",
    "Search requests, by origin, client type and query shape.",
    ["source", "client_type", "query_type"],
)

INDEX_VIEWS = Counter(
    "vvzapi_index_views_total",
    "Index page loads (/) that did not perform a search, by client type.",
    ["client_type"],
)

SEARCH_DURATION = Histogram(
    "vvzapi_search_duration_seconds",
    "Full search duration (parse + count + fetch + ratings) in seconds.",
    [
        "source",
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

SEARCH_STAGE_DURATION = Histogram(
    "vvzapi_search_stage_duration_seconds",
    "Duration of the individual (disjoint) search stages in seconds.",
    ["stage"],
    buckets=(
        0.001,
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
        10.0,
    ),
)

SEARCH_RESULT_COUNT = Histogram(
    "vvzapi_search_result_count",
    'Number of grouped results returned per search request. The le="0" bucket is the zero-result count.',
    ["source"],
    buckets=(
        0.0,
        1.0,
        2.0,
        3.0,
        5.0,
        10.0,
        20.0,
        50.0,
        100.0,
        250.0,
        500.0,
        1000.0,
        2500.0,
        # The catalogue has thousands of units, so unfiltered searches land well
        # above 2500; without these the upper quantiles are NaN.
        5000.0,
        10000.0,
        25000.0,
    ),
)

SEARCH_ZERO_RESULTS = Counter(
    "vvzapi_search_zero_results_total",
    "Search requests that returned no results at all.",
    ["source"],
)

SEARCH_FILTER_USED = Counter(
    "vvzapi_search_filter_total",
    "Search filters (query fields such as `department` or `credits`) that were used.",
    ["filter_key"],
)

CLIENT_TYPE_REQUESTS = Counter(
    "vvzapi_client_requests_total",
    "Requests grouped by detected client type (browser/crawler/app) and request kind.",
    ["client_type", "request_kind"],
)

API_CLIENT_REQUESTS = Counter(
    "vvzapi_api_client_requests_total",
    "API requests grouped by endpoint, client type and client family.",
    ["endpoint", "client_type", "client_family"],
)
