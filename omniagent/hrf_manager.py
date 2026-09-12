import os
import json

HRF_CONFIG_PATH = os.path.expanduser("~/.omniagent_hrf.json")
DEFAULT_BASELINE = 7.0
STABILIZATION_RATE = 0.10 # Moves 10% towards baseline per step

class HRFManager:
    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if os.path.exists(HRF_CONFIG_PATH):
            try:
                with open(HRF_CONFIG_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"models": {}}

    def _save_state(self):
        try:
            with open(HRF_CONFIG_PATH, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception:
            pass

    def _ensure_model(self, model_name: str):
        if "models" not in self.state:
            self.state["models"] = {}
        if model_name not in self.state["models"]:
            self.state["models"][model_name] = {
                "baseline": DEFAULT_BASELINE,
                "current_threshold": DEFAULT_BASELINE
            }

    def get_threshold(self, model_name: str) -> float:
        self._ensure_model(model_name)
        return self.state["models"][model_name]["current_threshold"]

    def get_baseline(self, model_name: str) -> float:
        self._ensure_model(model_name)
        return self.state["models"][model_name]["baseline"]

    def trust(self, model_name: str):
        """Increases threshold (trusts local model more, makes Oracle routing less likely)."""
        self._ensure_model(model_name)
        current = self.state["models"][model_name]["current_threshold"]
        new_val = min(10.0, current + 1.0)
        self.state["models"][model_name]["current_threshold"] = new_val
        self._save_state()
        return new_val

    def doubt(self, model_name: str):
        """Decreases threshold (trusts local model less, routes to Oracle faster)."""
        self._ensure_model(model_name)
        current = self.state["models"][model_name]["current_threshold"]
        new_val = max(1.0, current - 1.0)
        self.state["models"][model_name]["current_threshold"] = new_val
        self._save_state()
        return new_val

    def bs(self, model_name: str, weight: float = 3.0):
        """Instantly drops the threshold by a massive weight penalty."""
        self._ensure_model(model_name)
        current = self.state["models"][model_name]["current_threshold"]
        new_val = max(1.0, current - float(weight))
        self.state["models"][model_name]["current_threshold"] = new_val
        self._save_state()
        return new_val

    def reset(self, model_name: str):
        """Restores the model's trust completely back to its baseline (clean slate)."""
        self._ensure_model(model_name)
        baseline = self.state["models"][model_name]["baseline"]
        self.state["models"][model_name]["current_threshold"] = baseline
        self._save_state()
        return baseline

    def stabilize(self, model_name: str):
        """Naturally drifts the threshold back toward the model's baseline."""
        self._ensure_model(model_name)
        current = self.state["models"][model_name]["current_threshold"]
        baseline = self.state["models"][model_name]["baseline"]
        
        if abs(current - baseline) < 0.05:
            new_val = baseline
        else:
            # Move 10% closer to the baseline
            new_val = current + (baseline - current) * STABILIZATION_RATE
            
        self.state["models"][model_name]["current_threshold"] = round(new_val, 2)
        self._save_state()
        return new_val
