from prometheus_client import Counter, Histogram, Gauge




REDIS_STREAM_LAG = Gauge(
    "redis_stream_lag",
    "Number of pending messages in Redis stream consumer group"
)

# =====================================================
# INFERENCE METRICS
# =====================================================

INFERENCE_REQUESTS = Counter(
    "inference_requests_total",
    "Total number of inference requests"
)

INFERENCE_LATENCY = Histogram(
    "inference_latency_seconds",
    "Time spent performing inference",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 2)
)

# =====================================================
# CACHE METRICS
# =====================================================

CACHE_HITS = Counter(
    "redis_cache_hits_total",
    "Total number of Redis cache hits"
)

# =====================================================
# PREDICTION CLASS COUNTERS (🔥 REQUIRED FOR GRAFANA)
# =====================================================

PREDICTION_NORMAL = Counter(
    "prediction_normal_total",
    "Total normal predictions"
)

PREDICTION_FRAUD = Counter(
    "prediction_fraud_total",
    "Total fraud predictions"
)

# =====================================================
# STREAMING METRICS
# =====================================================

CONSUMER_LAG = Gauge(
    "redis_stream_consumer_lag",
    "Number of unprocessed messages in Redis stream"
)
