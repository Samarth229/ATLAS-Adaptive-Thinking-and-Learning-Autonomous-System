class ConfidenceAdaptiveResponseEngineV0_1:
    def __init__(self):
        self.high_threshold = 0.8
        self.medium_threshold = 0.5

    def adapt(
        self,
        response: str,
        confidence: float
    ) -> str:

        # High confidence → concise
        if confidence >= self.high_threshold:
            return response

        # Medium confidence → slight elaboration
        if confidence >= self.medium_threshold:
            return (
                f"{response} "
                "This assessment is based on current observed patterns."
            )

        # Low confidence → explicit uncertainty framing
        return (
            f"{response} "
            "However, my confidence in this interpretation is limited."
        )