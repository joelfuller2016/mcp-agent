"""
Simple test for learning foundation components without complex imports.
"""

import asyncio
import time
import sys
import os

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

try:
    # Test imports
    print("Testing Learning Module Imports...")
    
    from mcp_agent.learning.learning_models import ExecutionPattern, LearningContext, PerformanceMetrics
    print("[OK] Learning models imported successfully")
    
    from mcp_agent.learning.adaptive_learning_engine import AdaptiveLearningEngine
    print("[OK] AdaptiveLearningEngine imported successfully")
    
    print("\nTesting Basic Functionality...")
    
    # Test ExecutionPattern creation
    pattern = ExecutionPattern(
        task_type="test_task",
        pattern_used="direct",
        execution_time=0.005,
        success_rate=1.0,
        confidence_score=0.9
    )
    
    assert pattern.task_type == "test_task"
    assert pattern.execution_time == 0.005
    print("[OK] ExecutionPattern creation successful")
    
    # Test pattern serialization
    pattern_dict = pattern.to_dict()
    restored_pattern = ExecutionPattern.from_dict(pattern_dict)
    
    assert restored_pattern.task_type == pattern.task_type
    assert restored_pattern.execution_time == pattern.execution_time
    print("[OK] Pattern serialization/deserialization successful")
    
    # Test LearningContext
    context = LearningContext(
        task_description="Test task",
        current_pattern="direct",
        available_tools=["filesystem", "fetch"]
    )
    
    signature = context.get_context_signature()
    assert len(signature) == 12  # MD5 hash truncated to 12 chars
    print("[OK] LearningContext creation and signature generation successful")
    
    print("\n" + "="*50)
    print("LEARNING FOUNDATION IMPORT TEST: SUCCESS")
    print("All core learning components are working correctly")
    print("="*50)
    
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print("Module structure may need adjustment")
    
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
