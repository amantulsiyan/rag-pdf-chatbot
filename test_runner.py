"""
Automated Test Runner for RAG System
Executes all test queries and logs results with metrics
"""

import requests
import json
import time
from datetime import datetime
from test_queries import test_queries, expected_behaviors, failure_modes

API_BASE = "http://localhost:8000"

class RAGTester:
    def __init__(self):
        self.results = []
        self.summary = {
            "total_queries": 0,
            "successful": 0,
            "failed": 0,
            "avg_confidence": 0.0,
            "avg_response_time": 0.0,
            "categories": {}
        }
    
    def test_query(self, query, category):
        """Test a single query and return results"""
        print(f"\n{'='*80}")
        print(f"Testing: {query}")
        print(f"Category: {category}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_BASE}/ask_query",
                json={"question": query},
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                result = {
                    "query": query,
                    "category": category,
                    "answer": data.get("answer", ""),
                    "confidence": data.get("confidence", 0.0),
                    "confidence_breakdown": data.get("confidence_breakdown", {}),
                    "sources": data.get("sources", []),
                    "response_time": response_time,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"✓ Answer: {result['answer'][:200]}...")
                print(f"✓ Confidence: {result['confidence']:.2%}")
                print(f"✓ Response Time: {response_time:.2f}s")
                
                if result['confidence_breakdown']:
                    print(f"✓ Breakdown: Mean={result['confidence_breakdown'].get('mean_score', 0):.3f}, "
                          f"Agreement={result['confidence_breakdown'].get('agreement', 0):.3f}, "
                          f"Dominance={result['confidence_breakdown'].get('dominance', 0):.3f}")
                
                return result
            else:
                print(f"✗ API Error: {response.status_code}")
                return {
                    "query": query,
                    "category": category,
                    "error": f"HTTP {response.status_code}",
                    "status": "failed",
                    "response_time": response_time,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            print(f"✗ Exception: {str(e)}")
            return {
                "query": query,
                "category": category,
                "error": str(e),
                "status": "failed",
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def run_category(self, category, queries, limit=None):
        """Run all queries in a category"""
        print(f"\n{'#'*80}")
        print(f"# TESTING CATEGORY: {category.upper()}")
        print(f"# Expected: {expected_behaviors.get(category, 'N/A')}")
        print(f"{'#'*80}")
        
        category_results = []
        
        for i, query in enumerate(queries[:limit] if limit else queries, 1):
            print(f"\n[{i}/{len(queries[:limit] if limit else queries)}]")
            result = self.test_query(query, category)
            category_results.append(result)
            self.results.append(result)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Category summary
        successful = sum(1 for r in category_results if r["status"] == "success")
        avg_conf = sum(r.get("confidence", 0) for r in category_results if r["status"] == "success") / max(successful, 1)
        
        self.summary["categories"][category] = {
            "total": len(category_results),
            "successful": successful,
            "failed": len(category_results) - successful,
            "avg_confidence": avg_conf
        }
        
        print(f"\n{'='*80}")
        print(f"CATEGORY SUMMARY: {category}")
        print(f"Successful: {successful}/{len(category_results)}")
        print(f"Avg Confidence: {avg_conf:.2%}")
        print(f"{'='*80}")
    
    def run_all_tests(self, categories=None, limit_per_category=None):
        """Run all test categories"""
        print("\n" + "="*80)
        print("STARTING COMPREHENSIVE RAG SYSTEM TEST")
        print("="*80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        categories_to_test = categories if categories else test_queries.keys()
        
        for category in categories_to_test:
            if category in test_queries:
                self.run_category(category, test_queries[category], limit_per_category)
        
        self.generate_summary()
        self.save_results()
    
    def generate_summary(self):
        """Generate overall test summary"""
        self.summary["total_queries"] = len(self.results)
        self.summary["successful"] = sum(1 for r in self.results if r["status"] == "success")
        self.summary["failed"] = self.summary["total_queries"] - self.summary["successful"]
        
        successful_results = [r for r in self.results if r["status"] == "success"]
        if successful_results:
            self.summary["avg_confidence"] = sum(r.get("confidence", 0) for r in successful_results) / len(successful_results)
            self.summary["avg_response_time"] = sum(r.get("response_time", 0) for r in successful_results) / len(successful_results)
        
        # Identify issues
        self.summary["issues"] = {
            "high_conf_short_answer": [r for r in successful_results if r.get("confidence", 0) > 0.7 and len(r.get("answer", "")) < 50],
            "low_conf_long_answer": [r for r in successful_results if r.get("confidence", 0) < 0.3 and len(r.get("answer", "")) > 100],
            "slow_queries": [r for r in successful_results if r.get("response_time", 0) > 5.0],
            "i_dont_know_responses": [r for r in successful_results if "don't know" in r.get("answer", "").lower()],
        }
        
        print("\n" + "="*80)
        print("FINAL TEST SUMMARY")
        print("="*80)
        print(f"Total Queries: {self.summary['total_queries']}")
        print(f"Successful: {self.summary['successful']} ({self.summary['successful']/max(self.summary['total_queries'],1)*100:.1f}%)")
        print(f"Failed: {self.summary['failed']}")
        print(f"Avg Confidence: {self.summary['avg_confidence']:.2%}")
        print(f"Avg Response Time: {self.summary['avg_response_time']:.2f}s")
        
        print("\n" + "-"*80)
        print("CATEGORY BREAKDOWN:")
        print("-"*80)
        for cat, stats in self.summary["categories"].items():
            print(f"{cat:20s}: {stats['successful']}/{stats['total']} successful, "
                  f"Avg Conf: {stats['avg_confidence']:.2%}")
        
        print("\n" + "-"*80)
        print("POTENTIAL ISSUES:")
        print("-"*80)
        for issue_type, issues in self.summary["issues"].items():
            if issues:
                print(f"{issue_type}: {len(issues)} queries")
                for issue in issues[:3]:  # Show first 3
                    print(f"  - {issue['query'][:60]}... (conf: {issue.get('confidence', 0):.2f})")
    
    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        output = {
            "summary": self.summary,
            "results": self.results,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Results saved to {filename}")
        
        # Also save a human-readable report
        report_filename = f"test_report_{timestamp}.txt"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write("="*80 + "\n")
            f.write("RAG SYSTEM TEST REPORT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in self.results:
                f.write("-"*80 + "\n")
                f.write(f"Query: {result['query']}\n")
                f.write(f"Category: {result['category']}\n")
                if result['status'] == 'success':
                    f.write(f"Answer: {result['answer']}\n")
                    f.write(f"Confidence: {result['confidence']:.2%}\n")
                    f.write(f"Response Time: {result['response_time']:.2f}s\n")
                else:
                    f.write(f"ERROR: {result.get('error', 'Unknown')}\n")
                f.write("\n")
        
        print(f"✓ Human-readable report saved to {report_filename}")


if __name__ == "__main__":
    import sys
    
    tester = RAGTester()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        # Test specific categories
        categories = sys.argv[1].split(",")
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        tester.run_all_tests(categories=categories, limit_per_category=limit)
    else:
        # Run all tests with limit
        print("\nRunning quick test (3 queries per category)")
        print("For full test, run: python test_runner.py all")
        tester.run_all_tests(limit_per_category=3)
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
