# Obsolete Files - Candidates for Deletion

This document lists files that are no longer used by the current application and can be safely deleted.

## Temperature Control Logs (Old Per-Color Format)

**Location:** `/temp_control/`

### Files:
- `temp_control_Black.jsonl` - Old per-color temperature control log
- `temp_control_Blue.jsonl` - Old per-color temperature control log

**Reason for Obsolescence:**
These files use an old logging format where temperature control events were logged separately per tilt color. The current application uses a unified `temp_control_log.jsonl` file that contains all temperature control events regardless of tilt color.

**Replacement:**
All temperature control logging now goes to `/temp_control/temp_control_log.jsonl`

**Safe to Delete:** Yes - No references found in active code

---

## Batch History (Old Format)

**Location:** `/batches/`

### Files:
- `batch_history_Blue.jsonl` - Old format batch history with readings mixed in

**Reason for Obsolescence:**
This file uses an old format where individual tilt readings were logged alongside batch metadata. It contains 488 lines with individual readings (gravity, temp_f, rssi, timestamp) that are now logged in separate batch data files.

**Current Format:**
- Batch metadata is stored in JSON array format in `batch_history_{color}.json` files
- Individual readings are stored in per-batch JSONL files in `/batches/` with naming pattern: `{brewname}_{YYYYmmdd}_{brewid}.jsonl`

**Safe to Delete:** Likely yes, but user should verify if they need to migrate any batch metadata from this file first

---

## Migration/Utility Scripts

**Location:** Root directory

### Files:
- `backfill_temp_control_jsonl.py` - Code fragment, not a complete script

**Reason for Obsolescence:**
This appears to be a code fragment or snippet from a one-time migration script. It only contains a single function definition for `update_live_tilt()` which is already present in `app.py`.

**Safe to Delete:** Yes - No references found in active code, appears to be leftover from development

---

## Unused Modules

**Location:** Root directory

### Files:
- `batch_storage.py` - Batch storage utilities using different directory structure

**Reason for Obsolescence:**
This module implements batch storage using a `Batches/` directory (capital B) that doesn't exist in the current application. The current application uses the `batches/` directory with different file naming and structure.

Key differences:
- Uses `Batches/` directory instead of `batches/`
- Uses different filename pattern: `{color}_{beer}_{batch}_{date}_{brewid}.jsonl`
- Current pattern: `{brewname}_{YYYYmmdd}_{brewid}.jsonl`

**Safe to Delete:** Yes - No references found in active code

---

## Summary

**Confirmed Safe to Delete:**
1. `/temp_control/temp_control_Black.jsonl`
2. `/temp_control/temp_control_Blue.jsonl`
3. `backfill_temp_control_jsonl.py`
4. `batch_storage.py`

**User Decision Required:**
1. `/batches/batch_history_Blue.jsonl` - May contain historical batch metadata that should be reviewed/migrated first

**Total Space to be Freed:** ~93 KB (excluding batch_history_Blue.jsonl which is 143 KB)
