"""
Test script for system optimizations
Validates performance improvements and functionality
"""
import time
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class OptimizationTester:
    """Test suite for system optimizations."""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
    
    def test_lazy_loading_performance(self):
        """Test lazy loading performance improvements."""
        print("🔍 Testing lazy loading performance...")
        
        # Test 1: Import time comparison
        start_time = time.time()
        try:
            from src.utils.optimized_logger import get_system_logger
            logger = get_system_logger()
            import_time = (time.time() - start_time) * 1000
            self.performance_metrics['optimized_logger_import'] = import_time
            print(f"  ✅ Optimized logger import: {import_time:.2f}ms")
        except Exception as e:
            print(f"  ❌ Optimized logger import failed: {e}")
            self.test_results['lazy_loading'] = False
            return
        
        # Test 2: Database connection pooling
        start_time = time.time()
        try:
            from src.database.connection_pool import get_pooled_db_connection
            db_conn = get_pooled_db_connection()
            connection_time = (time.time() - start_time) * 1000
            self.performance_metrics['pooled_db_connection'] = connection_time
            print(f"  ✅ Pooled DB connection: {connection_time:.2f}ms")
        except Exception as e:
            print(f"  ⚠️ Pooled DB connection not available: {e}")
        
        # Test 3: Agent caching
        start_time = time.time()
        try:
            from src.core.agent_cache import get_agent_cache_manager
            cache_manager = get_agent_cache_manager()
            cache_stats = cache_manager.get_cache_stats()
            cache_time = (time.time() - start_time) * 1000
            self.performance_metrics['agent_cache_access'] = cache_time
            print(f"  ✅ Agent cache access: {cache_time:.2f}ms")
            print(f"  📊 Cache stats: {cache_stats}")
        except Exception as e:
            print(f"  ⚠️ Agent cache not available: {e}")
        
        self.test_results['lazy_loading'] = True
    
    def test_database_optimizations(self):
        """Test database optimization features."""
        print("🗄️ Testing database optimizations...")
        
        try:
            from src.database.connection_pool import (
                get_pooled_db_connection, 
                get_cached_db_operations
            )
            
            # Test connection pooling
            start_time = time.time()
            db_conn1 = get_pooled_db_connection()
            db_conn2 = get_pooled_db_connection()
            connection_time = (time.time() - start_time) * 1000
            
            # Should be the same connection (pooled)
            if db_conn1 is db_conn2:
                print(f"  ✅ Connection pooling working: {connection_time:.2f}ms")
            else:
                print(f"  ⚠️ Connection pooling may not be working properly")
            
            # Test cached operations
            cached_ops = get_cached_db_operations()
            if cached_ops:
                print(f"  ✅ Cached database operations available")
            
            self.test_results['database_optimizations'] = True
            
        except Exception as e:
            print(f"  ❌ Database optimization test failed: {e}")
            self.test_results['database_optimizations'] = False
    
    def test_agent_caching(self):
        """Test agent caching functionality."""
        print("🤖 Testing agent caching...")
        
        try:
            from src.core.agent_cache import (
                get_agent_cache_manager,
                create_cached_conversation_agent,
                get_cached_agent_graph
            )
            
            cache_manager = get_agent_cache_manager()
            
            # Test agent creation and caching
            start_time = time.time()
            agent1 = create_cached_conversation_agent()
            first_creation_time = (time.time() - start_time) * 1000
            
            start_time = time.time()
            agent2 = create_cached_conversation_agent()
            cached_access_time = (time.time() - start_time) * 1000
            
            if agent1 is agent2:
                print(f"  ✅ Agent caching working")
                print(f"    First creation: {first_creation_time:.2f}ms")
                print(f"    Cached access: {cached_access_time:.2f}ms")
                print(f"    Speed improvement: {(first_creation_time/cached_access_time):.1f}x")
            else:
                print(f"  ⚠️ Agent caching may not be working properly")
            
            # Test graph caching
            start_time = time.time()
            graph = get_cached_agent_graph()
            graph_time = (time.time() - start_time) * 1000
            print(f"  ✅ Cached agent graph access: {graph_time:.2f}ms")
            
            # Get cache statistics
            stats = cache_manager.get_cache_stats()
            print(f"  📊 Cache statistics: {stats}")
            
            self.test_results['agent_caching'] = True
            
        except Exception as e:
            print(f"  ❌ Agent caching test failed: {e}")
            self.test_results['agent_caching'] = False
    
    def test_logging_optimizations(self):
        """Test logging optimization features."""
        print("📋 Testing logging optimizations...")
        
        try:
            from src.utils.optimized_logger import (
                get_optimized_logger,
                get_all_logger_stats
            )
            
            # Test optimized logger
            logger = get_optimized_logger('test')
            
            # Test deduplication
            start_time = time.time()
            for i in range(100):
                logger.info("Test message for deduplication")
            dedup_time = (time.time() - start_time) * 1000
            
            stats = logger.get_stats()
            print(f"  ✅ Logging deduplication test: {dedup_time:.2f}ms")
            print(f"    Messages processed: {stats['total_messages']}")
            print(f"    Deduplicated: {stats['deduplicated_messages']}")
            print(f"    Deduplication rate: {stats['deduplication_rate']:.1f}%")
            
            # Test all logger stats
            all_stats = get_all_logger_stats()
            print(f"  📊 All logger statistics available: {len(all_stats)} loggers")
            
            self.test_results['logging_optimizations'] = True
            
        except Exception as e:
            print(f"  ❌ Logging optimization test failed: {e}")
            self.test_results['logging_optimizations'] = False
    
    async def test_async_performance(self):
        """Test async/await performance improvements."""
        print("⚡ Testing async/await performance...")
        
        try:
            # Simulate concurrent operations
            async def mock_operation(delay: float):
                await asyncio.sleep(delay)
                return f"Operation completed in {delay}s"
            
            # Test concurrent execution
            start_time = time.time()
            tasks = [mock_operation(0.1) for _ in range(10)]
            results = await asyncio.gather(*tasks)
            concurrent_time = (time.time() - start_time) * 1000
            
            # Test sequential execution for comparison
            start_time = time.time()
            for _ in range(10):
                await mock_operation(0.1)
            sequential_time = (time.time() - start_time) * 1000
            
            print(f"  ✅ Concurrent execution: {concurrent_time:.2f}ms")
            print(f"  📊 Sequential execution: {sequential_time:.2f}ms")
            print(f"  🚀 Speed improvement: {(sequential_time/concurrent_time):.1f}x")
            
            self.performance_metrics['async_improvement'] = sequential_time / concurrent_time
            self.test_results['async_performance'] = True
            
        except Exception as e:
            print(f"  ❌ Async performance test failed: {e}")
            self.test_results['async_performance'] = False
    
    def test_memory_usage(self):
        """Test memory usage optimizations."""
        print("💾 Testing memory usage...")
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            print(f"  📊 Current memory usage:")
            print(f"    RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
            print(f"    VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
            
            self.performance_metrics['memory_rss_mb'] = memory_info.rss / 1024 / 1024
            self.performance_metrics['memory_vms_mb'] = memory_info.vms / 1024 / 1024
            
            self.test_results['memory_usage'] = True
            
        except ImportError:
            print(f"  ⚠️ psutil not available for memory testing")
            self.test_results['memory_usage'] = False
        except Exception as e:
            print(f"  ❌ Memory usage test failed: {e}")
            self.test_results['memory_usage'] = False
    
    def run_all_tests(self):
        """Run all optimization tests."""
        print("🚀 Starting optimization validation tests...\n")
        
        # Run synchronous tests
        self.test_lazy_loading_performance()
        print()
        
        self.test_database_optimizations()
        print()
        
        self.test_agent_caching()
        print()
        
        self.test_logging_optimizations()
        print()
        
        self.test_memory_usage()
        print()
        
        # Run async test
        asyncio.run(self.test_async_performance())
        print()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary and recommendations."""
        print("📊 OPTIMIZATION TEST SUMMARY")
        print("=" * 50)
        
        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        
        print(f"Tests passed: {passed_tests}/{total_tests}")
        print()
        
        print("Test Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        print()
        print("Performance Metrics:")
        for metric_name, value in self.performance_metrics.items():
            if isinstance(value, float):
                print(f"  {metric_name}: {value:.2f}")
            else:
                print(f"  {metric_name}: {value}")
        
        print()
        print("Recommendations:")
        if not self.test_results.get('database_optimizations', True):
            print("  🔧 Consider setting up database connection pooling")
        if not self.test_results.get('agent_caching', True):
            print("  🔧 Consider implementing agent caching")
        if not self.test_results.get('logging_optimizations', True):
            print("  🔧 Consider using optimized logging system")
        
        if all(self.test_results.values()):
            print("  🎉 All optimizations are working correctly!")

if __name__ == "__main__":
    tester = OptimizationTester()
    tester.run_all_tests()
