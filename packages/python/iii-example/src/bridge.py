import os

from iii import Bridge, BridgeOptions

engine_ws_url = os.environ.get("III_BRIDGE_URL", "ws://localhost:49134")

bridge = Bridge(address=engine_ws_url, options=BridgeOptions(worker_name="iii-example"))
