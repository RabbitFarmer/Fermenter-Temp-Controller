#!/usr/bin/env python3
"""
Test to verify that test SMS has distinctive subject and body.
"""

import sys

# Import the send_sms function
try:
    from app import send_sms
except ImportError as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

def test_send_sms_signature():
    """Test that send_sms accepts subject parameter"""
    import inspect
    sig = inspect.signature(send_sms)
    params = list(sig.parameters.keys())
    
    # Check that send_sms accepts body and subject parameters
    assert 'body' in params, "send_sms should have 'body' parameter"
    assert 'subject' in params, "send_sms should have 'subject' parameter"
    
    # Check that subject has a default value
    subject_param = sig.parameters['subject']
    assert subject_param.default != inspect.Parameter.empty, "subject should have a default value"
    assert subject_param.default == "Fermenter Notification", f"subject default should be 'Fermenter Notification', got '{subject_param.default}'"
    
    print("✅ send_sms signature is correct:")
    print(f"   - Has 'body' parameter: Yes")
    print(f"   - Has 'subject' parameter: Yes")
    print(f"   - Default subject: '{subject_param.default}'")
    return True

def test_test_sms_message_content():
    """Test that test SMS message is distinctive"""
    # Read the app.py file to check the test message
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Check that the test message contains "TEST MESSAGE"
    assert '*** TEST MESSAGE ***' in content, "Test SMS should contain '*** TEST MESSAGE ***'"
    
    # Check that the test uses a distinctive subject
    assert 'TEST - Fermenter Controller' in content, "Test SMS should use 'TEST - Fermenter Controller' as subject"
    
    print("✅ Test SMS message content is distinctive:")
    print("   - Contains '*** TEST MESSAGE ***': Yes")
    print("   - Uses 'TEST - Fermenter Controller' subject: Yes")
    return True

if __name__ == '__main__':
    print("=" * 80)
    print("SMS MESSAGE TEST")
    print("=" * 80)
    print()
    
    try:
        test_send_sms_signature()
        print()
        test_test_sms_message_content()
        print()
        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        sys.exit(0)
    except AssertionError as e:
        print()
        print("=" * 80)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 80)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80)
        sys.exit(1)
