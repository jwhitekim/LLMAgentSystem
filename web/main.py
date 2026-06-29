import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "agent_system"))

from web.api.flask_app import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
