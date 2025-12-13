"""
Evaluation Pipeline - Runs SQL through SQLAgent and sends to Scorer

Usage:
    python run_evaluation_pipeline.py "SELECT * FROM users"
    python run_evaluation_pipeline.py --file query.sql
    python run_evaluation_pipeline.py --file query.sql --expected expected_results.json
"""

import argparse
import json
import sys
from typing import Dict, Any, List, Optional

from executor.sql_agent import SQLAgent
from evaluation.data_structures import (
    AgentResult,
    ExecutionResult,
    ComparisonResult,
)
from evaluation.result_comparator import DefaultResultComparator
from evaluation.scorer import DefaultScorer


def load_sql_from_file(filepath: str) -> str:
    """Load SQL query from a file."""
    with open(filepath, 'r') as f:
        return f.read().strip()


def load_expected_results(filepath: str) -> List[Dict[str, Any]]:
    """Load expected results from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def run_sql_agent(sql: str, database_url: str) -> Dict[str, Any]:
    """
    Run SQL through the SQLAgent.
    
    Returns the raw agent output dictionary.
    """
    agent = SQLAgent(database_url)
    result = agent.process_query(sql, verbose=True)
    return result


def convert_to_execution_result(agent_output: Dict[str, Any]) -> ExecutionResult:
    """
    Convert SQLAgent output to ExecutionResult for scoring.
    """
    agent_result = AgentResult.from_agent_output(agent_output)
    return agent_result.to_execution_result()


def compare_results(
    actual: List[Dict[str, Any]],
    expected: List[Dict[str, Any]],
) -> ComparisonResult:
    """
    Compare actual results with expected results.
    """
    comparator = DefaultResultComparator()
    return comparator.compare(actual, expected)


def score_execution(
    comparison: ComparisonResult,
    execution_result: ExecutionResult,
) -> Dict[str, Any]:
    """
    Score the execution using the DefaultScorer.
    
    Returns a dictionary with all score dimensions.
    """
    scorer = DefaultScorer()
    score = scorer.score(comparison, execution_result)
    
    return {
        "overall": round(score.overall, 4),
        "dimensions": {
            "correctness": round(score.correctness, 4),
            "efficiency": round(score.efficiency, 4),
            "safety": round(score.safety, 4),
            "result_completeness": round(score.result_completeness, 4),
        },
        "sub_scores": {
            "validation_score": round(score.validation_score, 4),
            "performance_score": round(score.performance_score, 4),
            "hallucination_score": round(score.hallucination_score, 4),
        },
        "weights": score.weights,
        "details": score.details,
    }


def run_evaluation_pipeline(
    sql: str,
    database_url: str,
    expected_results: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Complete evaluation pipeline:
    1. Run SQL through SQLAgent
    2. Convert output to ExecutionResult
    3. Compare with expected results (if provided)
    4. Score the execution
    5. Return comprehensive results
    """
    print("\n" + "=" * 80)
    print("🚀 EVALUATION PIPELINE")
    print("=" * 80)
    
    # Step 1: Run SQL through agent
    print("\n📥 Step 1: Running SQL through SQLAgent...")
    agent_output = run_sql_agent(sql, database_url)
    
    # Step 2: Convert to ExecutionResult
    print("\n🔄 Step 2: Converting to ExecutionResult...")
    execution_result = convert_to_execution_result(agent_output)
    print(f"   ✅ Execution success: {execution_result.success}")
    print(f"   📊 Rows returned: {execution_result.rows_returned}")
    print(f"   ⏱️  Execution time: {execution_result.execution_time_ms:.2f}ms")
    
    # Step 3: Compare results
    print("\n⚖️  Step 3: Comparing results...")
    actual_data = execution_result.data
    
    if expected_results is not None:
        comparison = compare_results(actual_data, expected_results)
        print(f"   📋 Expected rows: {len(expected_results)}")
        print(f"   {'✅' if comparison.is_match else '❌'} Match: {comparison.is_match}")
        print(f"   📈 Match score: {comparison.match_score:.2%}")
    else:
        # No expected results - create a "self-comparison" (perfect match)
        comparison = ComparisonResult(
            is_match=True,
            match_score=1.0,
            row_count_match=True,
            column_count_match=True,
            details={"message": "No expected results provided - using self-comparison"},
        )
        print("   ⚠️  No expected results provided - assuming correctness")
    
    # Step 4: Score execution
    print("\n🏆 Step 4: Scoring execution...")
    scores = score_execution(comparison, execution_result)
    
    print(f"\n   {'=' * 40}")
    print(f"   📊 SCORES")
    print(f"   {'=' * 40}")
    print(f"   🎯 Overall Score: {scores['overall']:.2%}")
    print(f"   {'─' * 40}")
    print(f"   📋 Correctness:    {scores['dimensions']['correctness']:.2%} (weight: 40%)")
    print(f"   ⚡ Efficiency:     {scores['dimensions']['efficiency']:.2%} (weight: 20%)")
    print(f"   🛡️  Safety:         {scores['dimensions']['safety']:.2%} (weight: 25%)")
    print(f"   📦 Completeness:   {scores['dimensions']['result_completeness']:.2%} (weight: 15%)")
    print(f"   {'=' * 40}")
    
    # Compile final output
    pipeline_result = {
        "query": sql,
        "agent_status": agent_output.get("overall_status", "UNKNOWN"),
        "execution_result": {
            "success": execution_result.success,
            "rows_returned": execution_result.rows_returned,
            "execution_time_ms": execution_result.execution_time_ms,
            "is_valid": execution_result.is_valid,
            "validation_errors": execution_result.validation_errors,
        },
        "comparison": {
            "is_match": comparison.is_match,
            "match_score": comparison.match_score,
            "details": comparison.details,
        },
        "scores": scores,
    }
    
    return pipeline_result


def main():
    parser = argparse.ArgumentParser(
        description="Run SQL through SQLAgent and score with Evaluation pipeline"
    )
    parser.add_argument(
        "sql",
        nargs="?",
        help="SQL query to execute (or use --file)",
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to a .sql file containing the query",
    )
    parser.add_argument(
        "--expected", "-e",
        help="Path to a JSON file containing expected results",
    )
    parser.add_argument(
        "--database-url", "-d",
        default="postgresql://testuser:testpass@localhost:5432/testdb",
        help="PostgreSQL connection string",
    )
    parser.add_argument(
        "--output", "-o",
        help="Path to save the results as JSON",
    )
    
    args = parser.parse_args()
    
    # Get SQL query
    if args.file:
        sql = load_sql_from_file(args.file)
    elif args.sql:
        sql = args.sql
    else:
        print("❌ Error: Please provide a SQL query or use --file")
        sys.exit(1)
    
    # Load expected results if provided
    expected_results = None
    if args.expected:
        expected_results = load_expected_results(args.expected)
    
    # Run the pipeline
    result = run_evaluation_pipeline(sql, args.database_url, expected_results)
    
    # Save output if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {args.output}")
    
    # Print final summary
    print("\n" + "=" * 80)
    print("✅ PIPELINE COMPLETE")
    print("=" * 80)
    print(f"Final Score: {result['scores']['overall']:.2%}")
    print("=" * 80 + "\n")
    
    return result


if __name__ == "__main__":
    main()
