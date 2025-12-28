#!/usr/bin/env python3
"""
app.py - FermenterApp main Flask application.

This file provides the full Flask app used in the conversation:
- BLE scanning (BleakScanner) if available
- Per-brew JSONL files under batches/{brewid}.jsonl (migrates legacy batch_{COLOR}_{BREWID}_{MMDDYYYY}.jsonl)
- Restricted control log in temp_control_log.jsonl
- Kasa worker integration (if kasa_worker available)
- Per-batch append_sample_to_batch_jsonl and forward_to_third_party_if_configured
- Chart Plotly page and /chart_data/<identifier> endpoint
- UI routes: dashboard, tilt_config, batch_settings, temp_config, update_temp_config, temp_report,
  export_temp_csv, scan_kasa_plugs, live_snapshot, reset_logs, exit_system, system_config
- Program entry runs Flask on 0.0.0.0:5000 in debug mode (when run directly)
"""

import asyncio
import hashli...