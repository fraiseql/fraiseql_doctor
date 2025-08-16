"""FraiseQL query complexity analysis."""
import re
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ComplexityMetrics:
    """Query complexity analysis results."""
    total_score: int
    depth: int
    field_count: int
    nested_queries: int
    estimated_cost: float
    recommendations: List[str]


class QueryComplexityAnalyzer:
    """Analyze GraphQL query complexity for FraiseQL optimization."""
    
    def __init__(self, max_depth: int = 10, max_complexity: int = 1000):
        self.max_depth = max_depth
        self.max_complexity = max_complexity
    
    def analyze_query(self, query: str) -> ComplexityMetrics:
        """Analyze query complexity and provide recommendations."""
        # Parse query structure
        depth = self._calculate_depth(query)
        field_count = self._count_fields(query)
        nested_queries = self._count_nested_queries(query)
        
        # Calculate complexity score
        total_score = self._calculate_complexity_score(depth, field_count, nested_queries)
        estimated_cost = self._estimate_cost(total_score, depth)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            depth, field_count, nested_queries, total_score
        )
        
        return ComplexityMetrics(
            total_score=total_score,
            depth=depth,
            field_count=field_count,
            nested_queries=nested_queries,
            estimated_cost=estimated_cost,
            recommendations=recommendations
        )
    
    def _calculate_depth(self, query: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        for char in query:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth -= 1
        
        return max_depth
    
    def _count_fields(self, query: str) -> int:
        """Count total number of fields requested."""
        # Remove comments and strings
        cleaned_query = re.sub(r'#.*$', '', query, flags=re.MULTILINE)
        cleaned_query = re.sub(r'"[^"]*"', '""', cleaned_query)
        
        # Find field selections (word followed by optional arguments and either { or end)
        field_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?\s*(?:\{|$|,|\s)'
        matches = re.findall(field_pattern, cleaned_query)
        
        # Filter out GraphQL keywords and fragments
        keywords = {
            'query', 'mutation', 'subscription', 'fragment', 'on', 'true', 'false', 
            'null', 'if', 'skip', 'include', '__typename', '__schema', '__type'
        }
        
        fields = [match for match in matches if match.lower() not in keywords]
        return len(fields)
    
    def _count_nested_queries(self, query: str) -> int:
        """Count nested object selections."""
        return query.count('{') - 1  # Subtract the root query
    
    def _calculate_complexity_score(self, depth: int, fields: int, nested: int) -> int:
        """Calculate overall complexity score."""
        # Weight factors for different aspects
        depth_weight = 10
        field_weight = 2
        nested_weight = 5
        
        # FraiseQL specific considerations
        # Deeper queries are more expensive in PostgreSQL
        depth_penalty = depth ** 2 if depth > 5 else depth * depth_weight
        
        return int(depth_penalty + (fields * field_weight) + (nested * nested_weight))
    
    def _estimate_cost(self, complexity: int, depth: int) -> float:
        """Estimate query execution cost in relative units."""
        base_cost = complexity * 0.1
        
        # FraiseQL specific cost factors
        # Deep queries require more JOIN operations
        depth_penalty = (depth * 0.05) if depth > 3 else 0
        
        # PostgreSQL connection overhead
        connection_overhead = 0.1
        
        return base_cost + depth_penalty + connection_overhead
    
    def _generate_recommendations(
        self, depth: int, fields: int, nested: int, score: int
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        if depth >= self.max_depth:
            recommendations.append(
                f"Query depth ({depth}) exceeds recommended maximum ({self.max_depth}). "
                "Consider breaking into multiple queries or using fragments."
            )
        
        if score >= self.max_complexity:
            recommendations.append(
                f"Query complexity ({score}) exceeds limit ({self.max_complexity}). "
                "Reduce field selections or query depth."
            )
        
        if fields > 50:
            recommendations.append(
                "High field count detected. Consider using GraphQL fragments "
                "or selecting only required fields."
            )
        
        if nested > 8:
            recommendations.append(
                "Deep nesting detected. Consider flattening the query structure "
                "or using separate queries with data stitching."
            )
        
        # FraiseQL specific recommendations
        if depth > 6:
            recommendations.append(
                "Deep queries may cause performance issues in PostgreSQL. "
                "Consider using FraiseQL's pagination or cursor-based loading."
            )
        
        if self._has_potential_n_plus_1(nested, fields):
            recommendations.append(
                "Potential N+1 query pattern detected. Ensure your FraiseQL "
                "resolvers use efficient batch loading."
            )
        
        return recommendations
    
    def _has_potential_n_plus_1(self, nested: int, fields: int) -> bool:
        """Detect potential N+1 query patterns."""
        # Heuristic: high field count with moderate nesting
        # suggests potential N+1 issues
        return nested > 3 and fields > 20 and (fields / nested) > 5
    
    def validate_query_limits(self, query: str) -> Dict[str, Any]:
        """Validate query against complexity limits."""
        metrics = self.analyze_query(query)
        
        violations = []
        
        if metrics.depth > self.max_depth:
            violations.append({
                "type": "max_depth_exceeded",
                "current": metrics.depth,
                "limit": self.max_depth
            })
        
        if metrics.total_score > self.max_complexity:
            violations.append({
                "type": "max_complexity_exceeded", 
                "current": metrics.total_score,
                "limit": self.max_complexity
            })
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "metrics": metrics,
            "estimated_execution_time_ms": metrics.estimated_cost * 100  # Rough estimate
        }