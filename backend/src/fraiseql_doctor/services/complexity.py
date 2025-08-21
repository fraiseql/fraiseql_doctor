"""
GraphQL Query Complexity Analyzer.

Analyzes GraphQL queries to compute complexity scores and provide
optimization recommendations.
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ComplexityLevel(Enum):
    """Query complexity levels."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ComplexityMetrics:
    """Query complexity analysis metrics."""
    depth: int
    field_count: int
    complexity_score: int
    complexity_level: ComplexityLevel
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "depth": self.depth,
            "field_count": self.field_count,
            "complexity_score": self.complexity_score,
            "complexity_level": self.complexity_level.value,
            "recommendations": self.recommendations
        }


class QueryComplexityAnalyzer:
    """
    Analyzes GraphQL query complexity for optimization.
    
    Provides depth analysis, field counting, and optimization
    recommendations to help optimize query performance.
    """
    
    # Complexity scoring weights
    DEPTH_WEIGHT = 5
    FIELD_WEIGHT = 1
    NESTED_FIELD_WEIGHT = 3
    LIST_FIELD_WEIGHT = 5
    
    # Complexity thresholds
    LOW_THRESHOLD = 20
    MEDIUM_THRESHOLD = 50
    HIGH_THRESHOLD = 100
    
    def __init__(self):
        """Initialize the complexity analyzer."""
        self.field_patterns = {
            'list_fields': re.compile(r'\w+\s*\([^)]*(?:limit|first|last):', re.IGNORECASE),
            'nested_fields': re.compile(r'{\s*\w+\s*{'),
            'fragments': re.compile(r'fragment\s+\w+\s+on\s+\w+', re.IGNORECASE),
            'directives': re.compile(r'@\w+'),
            'arguments': re.compile(r'\w+\s*\([^)]+\)'),
        }
    
    def analyze_query(self, query: str) -> ComplexityMetrics:
        """
        Analyze GraphQL query complexity.
        
        Args:
            query: GraphQL query string
            
        Returns:
            ComplexityMetrics with analysis results
        """
        # Clean and normalize query
        normalized_query = self._normalize_query(query)
        
        # Calculate metrics
        depth = self._calculate_depth(normalized_query)
        field_count = self._count_fields(normalized_query)
        complexity_score = self._calculate_complexity_score(
            normalized_query, depth, field_count
        )
        
        # Determine complexity level
        complexity_level = self._determine_complexity_level(complexity_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            normalized_query, depth, field_count, complexity_score
        )
        
        return ComplexityMetrics(
            depth=depth,
            field_count=field_count,
            complexity_score=complexity_score,
            complexity_level=complexity_level,
            recommendations=recommendations
        )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query string for analysis."""
        # Remove comments
        query = re.sub(r'#.*$', '', query, flags=re.MULTILINE)
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query)
        
        # Remove leading/trailing whitespace
        query = query.strip()
        
        return query
    
    def _calculate_depth(self, query: str) -> int:
        """Calculate the maximum nesting depth of the query."""
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
        """Count the total number of fields in the query."""
        # Remove operation keywords
        query_body = re.sub(r'^(query|mutation|subscription)\s*[^{]*', '', query, flags=re.IGNORECASE)
        
        # Remove arguments from fields
        query_body = re.sub(r'\([^)]*\)', '', query_body)
        
        # Remove braces and extract field names
        fields = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', query_body)
        
        # Filter out keywords and directives
        keywords = {'query', 'mutation', 'subscription', 'fragment', 'on', 'true', 'false', 'null'}
        fields = [f for f in fields if f.lower() not in keywords and not f.startswith('__')]
        
        return len(fields)
    
    def _calculate_complexity_score(self, query: str, depth: int, field_count: int) -> int:
        """Calculate overall complexity score."""
        base_score = (depth * self.DEPTH_WEIGHT) + (field_count * self.FIELD_WEIGHT)
        
        # Add penalties for complex patterns
        nested_fields = len(self.field_patterns['nested_fields'].findall(query))
        list_fields = len(self.field_patterns['list_fields'].findall(query))
        
        complexity_score = (
            base_score +
            (nested_fields * self.NESTED_FIELD_WEIGHT) +
            (list_fields * self.LIST_FIELD_WEIGHT)
        )
        
        return max(1, complexity_score)  # Minimum score of 1
    
    def _determine_complexity_level(self, score: int) -> ComplexityLevel:
        """Determine complexity level based on score."""
        if score <= self.LOW_THRESHOLD:
            return ComplexityLevel.LOW
        elif score <= self.MEDIUM_THRESHOLD:
            return ComplexityLevel.MEDIUM
        elif score <= self.HIGH_THRESHOLD:
            return ComplexityLevel.HIGH
        else:
            return ComplexityLevel.VERY_HIGH
    
    def _generate_recommendations(
        self, 
        query: str, 
        depth: int, 
        field_count: int, 
        score: int
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Depth recommendations
        if depth > 5:
            recommendations.append(
                f"Query depth ({depth}) is high. Consider breaking into multiple queries."
            )
        
        # Field count recommendations
        if field_count > 20:
            recommendations.append(
                f"High field count ({field_count}). Consider using fragments or selecting fewer fields."
            )
        
        # List field recommendations
        list_fields = self.field_patterns['list_fields'].findall(query)
        if len(list_fields) > 3:
            recommendations.append(
                "Multiple list fields detected. Consider pagination and limiting results."
            )
        
        # Nested field recommendations
        nested_fields = self.field_patterns['nested_fields'].findall(query)
        if len(nested_fields) > 3:
            recommendations.append(
                "Deep nesting detected. Consider flattening the query structure."
            )
        
        # Argument recommendations
        arguments = self.field_patterns['arguments'].findall(query)
        if len(arguments) > 5:
            recommendations.append(
                "Many field arguments detected. Ensure proper indexing on filtered fields."
            )
        
        # Overall score recommendations
        if score > self.HIGH_THRESHOLD:
            recommendations.append(
                "Very high complexity score. Consider caching or breaking into smaller queries."
            )
        elif score > self.MEDIUM_THRESHOLD:
            recommendations.append(
                "Medium-high complexity. Monitor performance and consider optimization."
            )
        
        # No recommendations for simple queries
        if not recommendations and score <= self.LOW_THRESHOLD:
            recommendations.append("Query complexity is optimal.")
        
        return recommendations
    
    def estimate_execution_time(self, complexity_score: int) -> Tuple[float, float]:
        """
        Estimate query execution time range based on complexity.
        
        Args:
            complexity_score: Calculated complexity score
            
        Returns:
            Tuple of (min_time_ms, max_time_ms)
        """
        # Base execution time estimates (in milliseconds)
        base_time = 10  # Base 10ms
        
        if complexity_score <= self.LOW_THRESHOLD:
            return (base_time, base_time * 3)
        elif complexity_score <= self.MEDIUM_THRESHOLD:
            return (base_time * 2, base_time * 8)
        elif complexity_score <= self.HIGH_THRESHOLD:
            return (base_time * 5, base_time * 20)
        else:
            return (base_time * 10, base_time * 50)
    
    def suggest_optimizations(self, metrics: ComplexityMetrics) -> List[str]:
        """
        Suggest specific optimizations based on complexity metrics.
        
        Args:
            metrics: ComplexityMetrics from analysis
            
        Returns:
            List of specific optimization suggestions
        """
        optimizations = []
        
        if metrics.complexity_level in [ComplexityLevel.HIGH, ComplexityLevel.VERY_HIGH]:
            optimizations.extend([
                "Use query result caching with appropriate TTL",
                "Implement DataLoader pattern for N+1 prevention",
                "Consider query whitelisting for production",
                "Add query complexity limits at the server level"
            ])
        
        if metrics.depth > 4:
            optimizations.extend([
                "Break deep queries into multiple shallow queries",
                "Use GraphQL fragments to reuse common field selections",
                "Implement query depth limiting middleware"
            ])
        
        if metrics.field_count > 15:
            optimizations.extend([
                "Select only necessary fields for the use case",
                "Use field-level caching for expensive computations",
                "Consider creating specialized query endpoints"
            ])
        
        return optimizations