#!/usr/bin/env python3
"""
Verification test for chat functionality.
Simulates a 3-turn conversation to verify history tracking.
"""

import sys
sys.path.insert(0, '/home/human/THINGS/T-HUB')

from paisa.chat import ConversationHistory
from paisa.classifier import classify

def test_conversation_history():
    """Test that conversation history correctly tracks all turns and models."""
    
    history = ConversationHistory()
    
    # Simulate 3 turns
    turns = [
        "What is Docker?",
        "Give me an example of a Dockerfile",
        "Now write a complete microservices architecture using Docker with Kubernetes orchestration and service mesh"
    ]
    
    print("Simulating 3-turn conversation...\n")
    
    for turn_num, turn in enumerate(turns, 1):
        label, confidence = classify(turn)
        history.add_user(turn)
        history.add_assistant(f"[simulated response for {label}]", f"model-for-{label}")
        
        print(f"Turn {turn_num}: {turn[:50]}...")
        print(f"Label: {label} (confidence: {confidence:.2f})")
        print(f"History length: {len(history.get_messages())} messages")
        print(f"Summary: {history.summary()}")
        print()
    
    # Verify history has all messages
    print("Verification checks:")
    print(f"Total messages in history: {len(history.messages)}")
    print(f"Expected: 6 (3 user + 3 assistant)")
    assert len(history.messages) == 6, f"Expected 6 messages, got {len(history.messages)}"
    print("✓ Message count correct")
    
    print(f"\nTotal turns tracked: {len(history.model_log)}")
    print(f"Expected: 3")
    assert len(history.model_log) == 3, f"Expected 3 model log entries, got {len(history.model_log)}"
    print("✓ Model log correct")
    
    # Verify message structure
    messages = history.get_messages()
    assert messages[0]["role"] == "user", "First message should be user"
    assert messages[1]["role"] == "assistant", "Second message should be assistant"
    print("✓ Message structure correct")
    
    # Verify summary
    summary = history.summary()
    print(f"\nFinal summary: {summary}")
    assert "3 turns" in summary, "Summary should show 3 turns"
    assert "models used:" in summary, "Summary should show models"
    print("✓ Summary format correct")
    
    # Verify copy behavior
    messages_copy = history.get_messages()
    messages_copy.append({"role": "user", "content": "test"})
    assert len(history.messages) == 6, "get_messages() should return a copy"
    print("✓ get_messages() returns independent copy")
    
    print("\n" + "="*40)
    print("PASSED: All verification checks passed!")
    print("="*40)

if __name__ == "__main__":
    test_conversation_history()
