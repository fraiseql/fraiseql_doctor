"""Performance metrics collection for FraiseQL queries."""
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from statistics import mean, median
from uuid import UUID


@dataclass
class QueryMetrics:
    """Individual query execution metrics."""
    query_id: str
    endpoint_id: str
    operation_name: Optional[str]
    execution_time_ms: int
    response_size_bytes: int
    complexity_score: Optional[int]
    success: bool
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    cached: bool = False
    retry_count: int = 0
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Collect and analyze performance metrics."""
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: List[QueryMetrics] = []
        self.max_metrics = max_metrics
        self._endpoint_metrics: Dict[str, List[QueryMetrics]] = {}
    
    def record_query(self, metrics: QueryMetrics) -> None:
        """Record query execution metrics."""
        self.metrics.append(metrics)
        
        # Track per-endpoint metrics
        endpoint_id = metrics.endpoint_id
        if endpoint_id not in self._endpoint_metrics:
            self._endpoint_metrics[endpoint_id] = []
        self._endpoint_metrics[endpoint_id].append(metrics)
        
        # Keep only recent metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
        
        # Keep endpoint metrics trimmed
        for endpoint_metrics in self._endpoint_metrics.values():
            if len(endpoint_metrics) > self.max_metrics // 10:  # Keep 1/10th per endpoint
                endpoint_metrics[:] = endpoint_metrics[-(self.max_metrics // 10):]
    
    def get_performance_summary(
        self, 
        endpoint_id: Optional[str] = None,
        time_window_seconds: int = 3600
    ) -> Dict[str, Any]:
        """Get performance summary for time window."""
        cutoff_time = time.time() - time_window_seconds
        
        # Filter metrics based on criteria
        if endpoint_id:
            filtered_metrics = [
                m for m in self._endpoint_metrics.get(endpoint_id, [])
                if m.timestamp >= cutoff_time
            ]
        else:
            filtered_metrics = [
                m for m in self.metrics 
                if m.timestamp >= cutoff_time
            ]
        
        if not filtered_metrics:
            return {"error": "No metrics found for criteria"}
        
        successful_metrics = [m for m in filtered_metrics if m.success]
        failed_metrics = [m for m in filtered_metrics if not m.success]
        
        response_times = [m.execution_time_ms for m in successful_metrics]
        complexity_scores = [m.complexity_score for m in successful_metrics if m.complexity_score]
        
        summary = {
            "total_queries": len(filtered_metrics),
            "successful_queries": len(successful_metrics),
            "failed_queries": len(failed_metrics),
            "success_rate": len(successful_metrics) / len(filtered_metrics) * 100,
            "cached_queries": len([m for m in filtered_metrics if m.cached]),
            "cache_hit_rate": len([m for m in filtered_metrics if m.cached]) / len(filtered_metrics) * 100,
        }
        
        # Response time statistics
        if response_times:
            summary.update({
                "avg_response_time_ms": mean(response_times),
                "median_response_time_ms": median(response_times),
                "max_response_time_ms": max(response_times),
                "min_response_time_ms": min(response_times),
                "p95_response_time_ms": self._percentile(response_times, 95),
                "p99_response_time_ms": self._percentile(response_times, 99),
            })
        else:
            summary.update({
                "avg_response_time_ms": 0,
                "median_response_time_ms": 0,
                "max_response_time_ms": 0,
                "min_response_time_ms": 0,
                "p95_response_time_ms": 0,
                "p99_response_time_ms": 0,
            })
        
        # Complexity statistics
        if complexity_scores:
            summary.update({
                "avg_complexity_score": mean(complexity_scores),
                "max_complexity_score": max(complexity_scores),
                "min_complexity_score": min(complexity_scores),
            })
        
        # Error analysis
        if failed_metrics:
            error_types = {}
            for metric in failed_metrics:
                error_type = metric.error_type or "unknown"
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            summary["error_breakdown"] = error_types
            summary["most_common_error"] = max(error_types.keys(), key=error_types.get)
        
        return summary
    
    def get_endpoint_comparison(self, time_window_seconds: int = 3600) -> Dict[str, Any]:
        """Compare performance across all endpoints."""
        endpoint_summaries = {}
        
        for endpoint_id in self._endpoint_metrics:
            summary = self.get_performance_summary(endpoint_id, time_window_seconds)
            if "error" not in summary:
                endpoint_summaries[endpoint_id] = summary
        
        if not endpoint_summaries:
            return {"error": "No endpoint metrics found"}
        
        # Find best and worst performing endpoints
        response_times = {
            ep: summary["avg_response_time_ms"] 
            for ep, summary in endpoint_summaries.items()
            if summary["avg_response_time_ms"] > 0
        }
        
        success_rates = {
            ep: summary["success_rate"]
            for ep, summary in endpoint_summaries.items()
        }
        
        comparison = {
            "endpoints": endpoint_summaries,
            "total_endpoints": len(endpoint_summaries),
        }
        
        if response_times:
            fastest_endpoint = min(response_times.keys(), key=response_times.get)
            slowest_endpoint = max(response_times.keys(), key=response_times.get)
            
            comparison.update({
                "fastest_endpoint": {
                    "id": fastest_endpoint,
                    "avg_response_time_ms": response_times[fastest_endpoint]
                },
                "slowest_endpoint": {
                    "id": slowest_endpoint,
                    "avg_response_time_ms": response_times[slowest_endpoint]
                }
            })
        
        if success_rates:
            most_reliable = max(success_rates.keys(), key=success_rates.get)
            least_reliable = min(success_rates.keys(), key=success_rates.get)
            
            comparison.update({
                "most_reliable_endpoint": {
                    "id": most_reliable,
                    "success_rate": success_rates[most_reliable]
                },
                "least_reliable_endpoint": {
                    "id": least_reliable,
                    "success_rate": success_rates[least_reliable]
                }
            })
        
        return comparison
    
    def get_slow_queries(
        self, 
        threshold_ms: int = 1000,
        limit: int = 10,
        time_window_seconds: int = 3600
    ) -> List[Dict[str, Any]]:
        """Get slowest queries above threshold."""
        cutoff_time = time.time() - time_window_seconds
        
        slow_queries = [
            m for m in self.metrics
            if (m.timestamp >= cutoff_time and 
                m.success and 
                m.execution_time_ms > threshold_ms)
        ]
        
        # Sort by execution time descending
        slow_queries.sort(key=lambda x: x.execution_time_ms, reverse=True)
        
        return [
            {
                "query_id": m.query_id,
                "endpoint_id": m.endpoint_id,
                "operation_name": m.operation_name,
                "execution_time_ms": m.execution_time_ms,
                "complexity_score": m.complexity_score,
                "timestamp": m.timestamp,
                "cached": m.cached
            }
            for m in slow_queries[:limit]
        ]
    
    def get_error_analysis(self, time_window_seconds: int = 3600) -> Dict[str, Any]:
        """Analyze error patterns."""
        cutoff_time = time.time() - time_window_seconds
        
        failed_metrics = [
            m for m in self.metrics
            if m.timestamp >= cutoff_time and not m.success
        ]
        
        if not failed_metrics:
            return {"error": "No failed queries found"}
        
        # Error type breakdown
        error_types = {}
        endpoint_errors = {}
        
        for metric in failed_metrics:
            error_type = metric.error_type or "unknown"
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            endpoint_id = metric.endpoint_id
            if endpoint_id not in endpoint_errors:
                endpoint_errors[endpoint_id] = 0
            endpoint_errors[endpoint_id] += 1
        
        return {
            "total_errors": len(failed_metrics),
            "error_types": error_types,
            "errors_by_endpoint": endpoint_errors,
            "error_rate": len(failed_metrics) / len([
                m for m in self.metrics if m.timestamp >= cutoff_time
            ]) * 100 if len([m for m in self.metrics if m.timestamp >= cutoff_time]) > 0 else 0
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f + 1 < len(sorted_data):
            return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
        else:
            return sorted_data[f]
    
    def clear_metrics(self, older_than_seconds: Optional[int] = None) -> int:
        """Clear old metrics, optionally only those older than specified time."""
        if older_than_seconds is None:
            # Clear all metrics
            count = len(self.metrics)
            self.metrics.clear()
            self._endpoint_metrics.clear()
            return count
        
        cutoff_time = time.time() - older_than_seconds
        
        # Remove old metrics
        old_metrics = [m for m in self.metrics if m.timestamp < cutoff_time]
        self.metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        # Clean endpoint metrics
        for endpoint_id in list(self._endpoint_metrics.keys()):
            self._endpoint_metrics[endpoint_id] = [
                m for m in self._endpoint_metrics[endpoint_id]
                if m.timestamp >= cutoff_time
            ]
            
            # Remove empty endpoint entries
            if not self._endpoint_metrics[endpoint_id]:
                del self._endpoint_metrics[endpoint_id]
        
        return len(old_metrics)
    
    def get_total_metrics_count(self) -> int:
        """Get total number of stored metrics."""
        return len(self.metrics)