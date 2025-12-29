from prometheus_client import Counter, Histogram

# Total inference calls
INFERENCE_REQUESTS = Counter(
    "inference_requests_total",
    "Total number of inference requests"
)

# Redis cache hits
CACHE_HITS = Counter(
    "redis_cache_hits_total",
    "Total number of Redis cache hits"
)

# Inference latency
INFERENCE_LATENCY = Histogram(
    "inference_latency_seconds",
    "Time spent performing inference",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 2)
)
