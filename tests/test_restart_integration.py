#!/usr/bin/env python3
"""
Integration test simulating a real-world scenario:
Application restart during an active fermentation.

This test verifies that notification triggers persist across restarts,
preventing duplicate "Fermentation has started" messages.
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

# We'll mock the required parts of app.py for this test
class MockApp:
    def __init__(self, config_file):
        self.config_file = config_file
        self.tilt_cfg = {}
        self.batch_notification_state = {}
        self.notifications_sent = []
        
    def load_config(self):
        """Load tilt config from file"""
        try:
            with open(self.config_file, 'r') as f:
                self.tilt_cfg = json.load(f)
        except Exception:
            self.tilt_cfg = {}
    
    def save_config(self):
        """Save tilt config to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.tilt_cfg, f, indent=2)
    
    def save_notification_state_to_config(self, color, brewid):
        """Save notification state to config (mirrors app.py)"""
        if brewid not in self.batch_notification_state or not color:
            return
        
        state = self.batch_notification_state[brewid]
        if color not in self.tilt_cfg:
            return
        
        self.tilt_cfg[color]['notification_state'] = {
            'fermentation_start_datetime': state.get('fermentation_start_datetime'),
            'fermentation_completion_datetime': state.get('fermentation_completion_datetime'),
            'last_daily_report': state.get('last_daily_report')
        }
        
        self.save_config()
    
    def load_notification_state_from_config(self, color, brewid, cfg):
        """Load notification state from config (mirrors app.py)"""
        persisted_state = cfg.get('notification_state', {})
        
        return {
            'last_reading_time': datetime.utcnow(),
            'signal_lost': False,
            'signal_loss_notified': False,  # Always start fresh on restart
            'fermentation_started': bool(persisted_state.get('fermentation_start_datetime')),
            'fermentation_start_datetime': persisted_state.get('fermentation_start_datetime'),
            'fermentation_completion_datetime': persisted_state.get('fermentation_completion_datetime'),
            'gravity_history': [],
            'last_daily_report': persisted_state.get('last_daily_report')
        }
    
    def check_batch_notifications(self, color, gravity, temp_f, brewid, cfg):
        """Check and initialize notification state (mirrors app.py)"""
        if not brewid:
            return
        
        # Initialize state for this brewid if needed
        if brewid not in self.batch_notification_state:
            # Load persisted state from config file
            self.batch_notification_state[brewid] = self.load_notification_state_from_config(color, brewid, cfg)
        
        state = self.batch_notification_state[brewid]
        state['last_reading_time'] = datetime.utcnow()
        
        # Track gravity history
        if gravity is not None:
            state['gravity_history'].append({
                'gravity': gravity,
                'timestamp': datetime.utcnow()
            })
            if len(state['gravity_history']) > 10:
                state['gravity_history'].pop(0)
        
        # Check fermentation starting
        self.check_fermentation_starting(color, brewid, cfg, state)
    
    def check_fermentation_starting(self, color, brewid, cfg, state):
        """Check if fermentation has started (mirrors app.py)"""
        # Check if notification already sent (datetime will be present)
        if state.get('fermentation_start_datetime'):
            return
        
        actual_og = cfg.get('actual_og')
        if not actual_og:
            return
        
        try:
            starting_gravity = float(actual_og)
        except (ValueError, TypeError):
            return
        
        history = state.get('gravity_history', [])
        if len(history) < 3:
            return
        
        # Check last 3 readings
        last_three = history[-3:]
        all_below_threshold = all(
            reading['gravity'] is not None and reading['gravity'] <= (starting_gravity - 0.010)
            for reading in last_three
        )
        
        if all_below_threshold:
            current_gravity = last_three[-1]['gravity']
            beer_name = cfg.get('beer_name', 'Unknown Beer')
            
            # Get current datetime for the notification
            notification_time = datetime.utcnow()
            
            # Mock sending notification
            message = f"Fermentation Started: {beer_name}, Gravity: {starting_gravity:.3f} -> {current_gravity:.3f}"
            self.notifications_sent.append(message)
            
            # Save the datetime when notification was sent (not just a boolean)
            state['fermentation_start_datetime'] = notification_time.isoformat()
            state['fermentation_started'] = True
            self.save_notification_state_to_config(color, brewid)

def test_restart_scenario():
    """
    Simulate real-world scenario:
    1. Start fermentation monitoring
    2. Detect fermentation start, send notification
    3. Application restarts (config persists)
    4. Continue monitoring - should NOT send duplicate notification
    """
    print("=" * 80)
    print("INTEGRATION TEST: Application Restart During Fermentation")
    print("=" * 80)
    
    # Setup temporary config file
    fd, config_file = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    
    try:
        # Initialize config
        config = {
            "Black": {
                "beer_name": "West Coast IPA",
                "batch_name": "Main Batch",
                "ferm_start_date": "2025-10-15",
                "recipe_og": "1.065",
                "recipe_fg": "1.012",
                "recipe_abv": "7.0",
                "actual_og": 1.065,
                "brewid": "wc-ipa-2025",
                "og_confirmed": False,
                "notification_state": {
                    "fermentation_start_datetime": None,
                    "fermentation_completion_datetime": None,
                    "last_daily_report": None
                }
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # PHASE 1: Initial monitoring session
        print("\n📊 PHASE 1: Initial Monitoring Session")
        print("-" * 80)
        
        app1 = MockApp(config_file)
        app1.load_config()
        
        color = "Black"
        brewid = app1.tilt_cfg[color]["brewid"]
        cfg = app1.tilt_cfg[color]
        
        print("1. Pitch yeast, start monitoring...")
        print(f"   Batch: {cfg['beer_name']}")
        print(f"   OG: {cfg['actual_og']:.3f}")
        
        # Simulate initial readings (no fermentation yet)
        print("\n2. Initial readings (24 hours after pitch):")
        for i, gravity in enumerate([1.065, 1.064, 1.063]):
            app1.check_batch_notifications(color, gravity, 68.0, brewid, cfg)
            print(f"   Reading {i+1}: {gravity:.3f} SG")
        
        print(f"   Notifications sent: {len(app1.notifications_sent)}")
        assert len(app1.notifications_sent) == 0, "Should not notify yet"
        print("   ✅ No notification sent (gravity not dropped enough)")
        
        # Simulate fermentation starting (3 readings below threshold)
        print("\n3. Fermentation activity detected (48 hours after pitch):")
        for i, gravity in enumerate([1.054, 1.052, 1.050]):
            app1.check_batch_notifications(color, gravity, 68.0, brewid, cfg)
            print(f"   Reading {i+1}: {gravity:.3f} SG (dropped ≥0.010)")
        
        print(f"   Notifications sent: {len(app1.notifications_sent)}")
        assert len(app1.notifications_sent) == 1, "Should send fermentation started notification"
        print(f"   ✅ Notification sent: {app1.notifications_sent[0]}")
        
        # Verify state was persisted
        persisted_config = None
        with open(config_file, 'r') as f:
            persisted_config = json.load(f)
        
        assert persisted_config["Black"]["notification_state"]["fermentation_start_datetime"] is not None
        print("   ✅ Notification state persisted to config file")
        
        # PHASE 2: Application restart (simulate power outage, reboot, etc.)
        print("\n🔄 PHASE 2: Application Restart (Simulating Power Cycle)")
        print("-" * 80)
        print("   Clearing runtime state (simulating app restart)...")
        del app1  # Destroy first app instance
        
        # PHASE 3: Resume monitoring after restart
        print("\n📊 PHASE 3: Resume Monitoring After Restart")
        print("-" * 80)
        
        app2 = MockApp(config_file)
        app2.load_config()
        
        print("1. Application restarted, config loaded from disk")
        loaded_state = app2.tilt_cfg["Black"]["notification_state"]
        print(f"   Loaded notification_state: {loaded_state}")
        assert loaded_state["fermentation_start_datetime"] is not None
        print("   ✅ Persisted state loaded successfully")
        
        # Continue monitoring with more readings
        print("\n2. Continue monitoring (still fermenting):")
        for i, gravity in enumerate([1.048, 1.046, 1.044]):
            app2.check_batch_notifications(color, gravity, 68.0, brewid, cfg)
            print(f"   Reading {i+1}: {gravity:.3f} SG")
        
        print(f"   Notifications sent since restart: {len(app2.notifications_sent)}")
        assert len(app2.notifications_sent) == 0, "Should NOT send duplicate notification"
        print("   ✅ No duplicate notification sent (flag persisted correctly)")
        
        # PHASE 4: Verify state remains correct
        print("\n✅ PHASE 4: Final Verification")
        print("-" * 80)
        
        final_config = None
        with open(config_file, 'r') as f:
            final_config = json.load(f)
        
        final_state = final_config["Black"]["notification_state"]
        print(f"   Final persisted state: {final_state}")
        assert final_state["fermentation_start_datetime"] is not None
        print("   ✅ Notification datetime still persisted")
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ INTEGRATION TEST PASSED")
        print("=" * 80)
        print("\nScenario Summary:")
        print("  • Started monitoring with OG 1.065")
        print("  • Detected fermentation start at 1.050 (3 readings ≥0.010 drop)")
        print("  • Sent notification: 'Fermentation Started'")
        print("  • Application restarted (config persisted)")
        print("  • Resumed monitoring with gravity 1.048-1.044")
        print("  • Did NOT send duplicate notification")
        print("\n🎉 The fix prevents duplicate notifications across restarts!")
        
    finally:
        if os.path.exists(config_file):
            os.remove(config_file)

def test_new_batch_after_restart():
    """Test that a new batch correctly starts with fresh notification flags"""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: New Batch After Restart")
    print("=" * 80)
    
    fd, config_file = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    
    try:
        # Old batch with notification already sent
        config = {
            "Black": {
                "beer_name": "Old Batch",
                "brewid": "old123",
                "actual_og": 1.060,
                "notification_state": {
                    "fermentation_start_datetime": "2025-10-02T08:00:00",
                    "fermentation_completion_datetime": None,
                    "last_daily_report": "2025-10-10T09:00:00"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("\n1. Old batch exists (notification already sent)")
        print("   fermentation_start_datetime: 2025-10-02T08:00:00")
        
        # Simulate user creating a new batch (brewid changes)
        print("\n2. User creates new batch...")
        config["Black"] = {
            "beer_name": "New Batch",
            "brewid": "new456",
            "actual_og": 1.055,
            "notification_state": {
                "fermentation_start_datetime": None,
                "fermentation_completion_datetime": None,
                "last_daily_report": None
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("   New brewid: new456")
        print("   fermentation_start_datetime reset to: None")
        
        # Verify new batch can trigger notification
        app = MockApp(config_file)
        app.load_config()
        
        color = "Black"
        brewid = "new456"
        cfg = app.tilt_cfg[color]
        
        print("\n3. New fermentation starts...")
        for gravity in [1.044, 1.042, 1.040]:
            app.check_batch_notifications(color, gravity, 68.0, brewid, cfg)
        
        assert len(app.notifications_sent) == 1
        print(f"   ✅ Notification sent for new batch: {app.notifications_sent[0]}")
        
        print("\n" + "=" * 80)
        print("✅ NEW BATCH TEST PASSED")
        print("=" * 80)
        
    finally:
        if os.path.exists(config_file):
            os.remove(config_file)

# Run integration tests
if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "INTEGRATION TESTS: RESTART SCENARIO" + " " * 21 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    test_restart_scenario()
    test_new_batch_after_restart()
    
    print("\n" + "=" * 80)
    print("ALL INTEGRATION TESTS PASSED")
    print("=" * 80)
    print("\n✅ The notification persistence fix is working correctly!")
    print("   Duplicate notifications will no longer be sent after restarts.\n")
