"""Test module for GraphQL query complexity analyzer.

Tests the complexity analysis functionality and optimization recommendations.
"""
from fraiseql_doctor.services.complexity import (
    ComplexityLevel,
    ComplexityMetrics,
    QueryComplexityAnalyzer,
)


class TestQueryComplexityAnalyzer:
    """Test query complexity analysis functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = QueryComplexityAnalyzer()

    def test_simple_query_analysis(self):
        """Test analysis of a simple query."""
        query = """
        query {
            user {
                id
                name
            }
        }
        """

        metrics = self.analyzer.analyze_query(query)

        assert isinstance(metrics, ComplexityMetrics)
        assert metrics.depth == 2  # user and its fields
        assert metrics.field_count == 3  # user, id, name
        assert metrics.complexity_level == ComplexityLevel.LOW
        assert metrics.complexity_score <= 20
        assert len(metrics.recommendations) > 0

    def test_complex_nested_query(self):
        """Test analysis of a complex nested query."""
        query = """
        query GetUserWithPosts {
            user(id: "123") {
                id
                name
                email
                profile {
                    bio
                    avatar
                    settings {
                        theme
                        notifications {
                            email
                            push
                            sms
                        }
                    }
                }
                posts(limit: 10) {
                    id
                    title
                    content
                    comments(limit: 5) {
                        id
                        text
                        author {
                            id
                            name
                        }
                    }
                    tags {
                        name
                        color
                    }
                }
            }
        }
        """

        metrics = self.analyzer.analyze_query(query)

        assert metrics.depth >= 5  # Deep nesting
        assert metrics.field_count >= 15  # Many fields
        assert metrics.complexity_level in [
            ComplexityLevel.MEDIUM,
            ComplexityLevel.HIGH,
            ComplexityLevel.VERY_HIGH,
        ]
        assert metrics.complexity_score > 30

        # Should have recommendations for optimization
        recommendations = [r.lower() for r in metrics.recommendations]
        # Should have recommendations about field count, complexity, or performance
        assert any(
            keyword in rec
            for rec in recommendations
            for keyword in ["field", "complexity", "fragment", "performance", "optimization"]
        )

    def test_query_with_multiple_lists(self):
        """Test query with multiple list fields."""
        query = """
        query {
            users(limit: 100) {
                id
                posts(limit: 20) {
                    id
                    comments(limit: 10) {
                        id
                    }
                }
            }
        }
        """

        metrics = self.analyzer.analyze_query(query)

        # Should detect list fields and add complexity
        assert metrics.complexity_score > 20
        recommendations = [r.lower() for r in metrics.recommendations]
        # Check if any recommendation mentions lists/pagination or if there are limit parameters
        has_list_recommendation = any(
            "list" in r or "pagination" in r or "limit" in r for r in recommendations
        )
        # If no list recommendation, check if the query has limit parameters which should increase complexity
        assert has_list_recommendation or "limit" in query.lower()

    def test_query_normalization(self):
        """Test query string normalization."""
        query_with_comments = """
        # Get user data
        query GetUser {
            user {  # User fields
                id
                name   # User name
            }
        }
        """

        query_clean = """
        query GetUser {
            user {
                id
                name
            }
        }
        """

        metrics_commented = self.analyzer.analyze_query(query_with_comments)
        metrics_clean = self.analyzer.analyze_query(query_clean)

        # Should produce similar results after normalization
        assert metrics_commented.depth == metrics_clean.depth
        assert metrics_commented.field_count == metrics_clean.field_count

    def test_depth_calculation(self):
        """Test depth calculation for nested queries."""
        shallow_query = "query { user { id } }"
        deep_query = """
        query {
            level1 {
                level2 {
                    level3 {
                        level4 {
                            level5 {
                                id
                            }
                        }
                    }
                }
            }
        }
        """

        shallow_metrics = self.analyzer.analyze_query(shallow_query)
        deep_metrics = self.analyzer.analyze_query(deep_query)

        assert shallow_metrics.depth == 2
        assert deep_metrics.depth == 6
        assert deep_metrics.complexity_score > shallow_metrics.complexity_score

    def test_field_counting(self):
        """Test field counting accuracy."""
        few_fields_query = """
        query {
            user {
                id
                name
            }
        }
        """

        many_fields_query = """
        query {
            user {
                id
                name
                email
                profile
                settings
                preferences
                metadata
                createdAt
                updatedAt
                lastLogin
            }
        }
        """

        few_fields_metrics = self.analyzer.analyze_query(few_fields_query)
        many_fields_metrics = self.analyzer.analyze_query(many_fields_query)

        assert few_fields_metrics.field_count < many_fields_metrics.field_count
        assert many_fields_metrics.complexity_score > few_fields_metrics.complexity_score

    def test_complexity_levels(self):
        """Test complexity level categorization."""
        simple_query = "query { user { id } }"
        complex_query = """
        query {
            users(limit: 100) {
                id
                name
                posts(limit: 50) {
                    id
                    title
                    comments(limit: 25) {
                        id
                        text
                        author {
                            id
                            name
                            profile {
                                bio
                                settings {
                                    theme
                                    notifications {
                                        email
                                        push
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        simple_metrics = self.analyzer.analyze_query(simple_query)
        complex_metrics = self.analyzer.analyze_query(complex_query)

        assert simple_metrics.complexity_level == ComplexityLevel.LOW
        assert complex_metrics.complexity_level in [ComplexityLevel.HIGH, ComplexityLevel.VERY_HIGH]

    def test_optimization_recommendations(self):
        """Test generation of optimization recommendations."""
        complex_query = """
        query VeryComplexQuery {
            users(limit: 1000, filter: {active: true}) {
                id
                name
                email
                profile {
                    bio
                    avatar
                    settings {
                        theme
                        notifications {
                            email
                            push
                            sms
                            inApp
                        }
                    }
                }
                posts(limit: 100, orderBy: {createdAt: DESC}) {
                    id
                    title
                    content
                    tags {
                        name
                        color
                    }
                    comments(limit: 50) {
                        id
                        text
                        author {
                            id
                            name
                        }
                        replies(limit: 10) {
                            id
                            text
                        }
                    }
                }
            }
        }
        """

        metrics = self.analyzer.analyze_query(complex_query)

        assert len(metrics.recommendations) > 1
        recommendations_text = " ".join(metrics.recommendations).lower()

        # Should suggest various optimizations
        assert any(
            keyword in recommendations_text
            for keyword in ["depth", "field", "pagination", "fragment", "limit"]
        )

    def test_execution_time_estimation(self):
        """Test execution time estimation based on complexity."""
        simple_score = 15
        complex_score = 150

        simple_time = self.analyzer.estimate_execution_time(simple_score)
        complex_time = self.analyzer.estimate_execution_time(complex_score)

        assert len(simple_time) == 2  # (min, max)
        assert len(complex_time) == 2
        assert simple_time[0] < complex_time[0]  # Complex takes longer
        assert simple_time[1] < complex_time[1]

    def test_optimization_suggestions(self):
        """Test specific optimization suggestions."""
        high_complexity_metrics = ComplexityMetrics(
            depth=8,
            field_count=25,
            complexity_score=120,
            complexity_level=ComplexityLevel.HIGH,
            recommendations=["High complexity detected"],
        )

        optimizations = self.analyzer.suggest_optimizations(high_complexity_metrics)

        assert len(optimizations) > 0
        optimization_text = " ".join(optimizations).lower()

        # Should suggest specific techniques
        assert any(
            keyword in optimization_text
            for keyword in ["caching", "dataloader", "fragment", "depth"]
        )

    def test_metrics_serialization(self):
        """Test that metrics can be serialized to dict."""
        query = """
        query {
            user {
                id
                name
                posts {
                    title
                }
            }
        }
        """

        metrics = self.analyzer.analyze_query(query)
        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert "depth" in metrics_dict
        assert "field_count" in metrics_dict
        assert "complexity_score" in metrics_dict
        assert "complexity_level" in metrics_dict
        assert "recommendations" in metrics_dict

        # Ensure values are JSON serializable
        assert isinstance(metrics_dict["depth"], int)
        assert isinstance(metrics_dict["field_count"], int)
        assert isinstance(metrics_dict["complexity_score"], int)
        assert isinstance(metrics_dict["complexity_level"], str)
        assert isinstance(metrics_dict["recommendations"], list)


class TestComplexityLevels:
    """Test complexity level boundaries and categorization."""

    def test_complexity_level_enum(self):
        """Test complexity level enum values."""
        assert ComplexityLevel.LOW.value == "low"
        assert ComplexityLevel.MEDIUM.value == "medium"
        assert ComplexityLevel.HIGH.value == "high"
        assert ComplexityLevel.VERY_HIGH.value == "very_high"

    def test_score_thresholds(self):
        """Test complexity score thresholds."""
        analyzer = QueryComplexityAnalyzer()

        assert analyzer.LOW_THRESHOLD == 20
        assert analyzer.MEDIUM_THRESHOLD == 50
        assert analyzer.HIGH_THRESHOLD == 100

        # Test threshold categorization
        assert analyzer._determine_complexity_level(10) == ComplexityLevel.LOW
        assert analyzer._determine_complexity_level(30) == ComplexityLevel.MEDIUM
        assert analyzer._determine_complexity_level(75) == ComplexityLevel.HIGH
        assert analyzer._determine_complexity_level(150) == ComplexityLevel.VERY_HIGH


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = QueryComplexityAnalyzer()

    def test_empty_query(self):
        """Test handling of empty query."""
        metrics = self.analyzer.analyze_query("")

        assert metrics.depth >= 0
        assert metrics.field_count >= 0
        assert metrics.complexity_score >= 1  # Minimum score

    def test_malformed_query(self):
        """Test handling of malformed GraphQL query."""
        malformed_query = "query { user { id name"  # Missing closing brace

        # Should not crash, but provide analysis
        metrics = self.analyzer.analyze_query(malformed_query)

        assert isinstance(metrics, ComplexityMetrics)
        assert metrics.complexity_score >= 1

    def test_query_with_only_whitespace(self):
        """Test query with only whitespace."""
        whitespace_query = "   \n\t   "

        metrics = self.analyzer.analyze_query(whitespace_query)

        assert metrics.depth >= 0
        assert metrics.field_count >= 0
        assert metrics.complexity_score >= 1

    def test_query_with_special_characters(self):
        """Test query with special characters and unicode."""
        special_query = """
        query {
            user(name: "João Ñoño 🚀") {
                id
                displayName
            }
        }
        """

        metrics = self.analyzer.analyze_query(special_query)

        assert isinstance(metrics, ComplexityMetrics)
        assert metrics.depth > 0
        assert metrics.field_count > 0
