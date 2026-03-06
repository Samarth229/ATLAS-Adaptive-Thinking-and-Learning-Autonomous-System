class VolatilityReflectionEngineV0_1:
    def __init__(self):
        self.stability_threshold = -3
        self.meta_uncertainty_threshold = 3
        self.volatility_counter = 0

    def evaluate(
        self,
        state,
        meta_flags,
        previous_meta_flags
    ):
        trigger_reflection = False

        stability_score = state.get("stability_score", 0)

        if stability_score <= self.stability_threshold:
            trigger_reflection = True

        if meta_flags and meta_flags.get("low_confidence", False):
            self.volatility_counter += 1

        if self.volatility_counter >= self.meta_uncertainty_threshold:
            trigger_reflection = True
            self.volatility_counter = 0

        if trigger_reflection:
            return {
                "trigger": True,
                "message": (
                    "I am detecting sustained volatility in emotional "
                    "or interpretive stability. Initiating internal recalibration."
                )
            }

        return {
            "trigger": False,
            "message": None
        }