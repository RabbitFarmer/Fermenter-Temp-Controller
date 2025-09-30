from kasa import SmartPlug
import asyncio
from logger import log_error

def kasa_worker(queue, status_dict):
    while True:
        try:
            command = queue.get()
            # command: {'mode': 'heating'/'cooling', 'url': url, 'action': 'on'/'off', 'enabled': True/False}
            if not command['enabled'] or not command['url']:
                print(f"{command['mode'].capitalize()} plug operation bypassed (not enabled or URL blank).")
                continue
            error = asyncio.run(kasa_control(command['url'], command['action'], command['mode']))
            mode = command['mode']
            # Update error state in status_dict
            if mode == 'heating':
                if error:
                    status_dict['heating_error'] = True
                    status_dict['heating_error_msg'] = error
                    log_error(f"HEATING ERROR: {error}")
                else:
                    status_dict['heating_error'] = False
                    status_dict['heating_error_msg'] = ""
            elif mode == 'cooling':
                if error:
                    status_dict['cooling_error'] = True
                    status_dict['cooling_error_msg'] = error
                    log_error(f"COOLING ERROR: {error}")
                else:
                    status_dict['cooling_error'] = False
                    status_dict['cooling_error_msg'] = ""
        except Exception as e:
            log_error(f"Kasa worker error: {e}")

async def kasa_control(url, action, mode):
    try:
        plug = SmartPlug(url)
        await asyncio.wait_for(plug.update(), timeout=2)  # 2 seconds timeout
        if action == 'on':
            await plug.turn_on()
            print(f"{mode.capitalize()} plug ON at {url}")
        else:
            await plug.turn_off()
            print(f"{mode.capitalize()} plug OFF at {url}")
        return None  # No error
    except Exception as e:
        log_error(f"{mode.capitalize()} plug at {url} error: {e}")
        return str(e)