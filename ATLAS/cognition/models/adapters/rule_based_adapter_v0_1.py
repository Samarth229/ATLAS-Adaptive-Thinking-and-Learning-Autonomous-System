class RuleBasedAdapterV0_1:

    def __init__(self, text_engine):
        self.text_engine = text_engine

    def generate(self, prompt: str, context: dict = None) -> dict:

        response = self.text_engine.process(prompt)

        return {
            "text": response,
            "confidence": 1.0,
            "meta": {
                "source": "rule_based"
            }
        }