class ModelRouterV0_1:

    def __init__(self, adapters):

        self.adapters = adapters

        self.coding_keywords = [
            "code",
            "program",
            "python",
            "java",
            "c++",
            "function",
            "class",
            "object",
            "oop",
            "algorithm",
            "data structure",
            "bug",
            "compile",
            "script"
        ]

        self.reasoning_keywords = [
            "explain",
            "why",
            "how",
            "reason",
            "theory",
            "concept"
        ]

        self.quick_keywords = [
            "quick",
            "fast",
            "short"
        ]

    # -----------------------------------------------------

    def select_model(self, prompt: str):

        text = prompt.lower()

        # 1️⃣ Programming domain (highest priority)
        if any(word in text for word in self.coding_keywords):
            return self.adapters.get("deepseek")

        # 2️⃣ Reasoning / explanation
        if any(word in text for word in self.reasoning_keywords):
            return self.adapters.get("llama")

        # 3️⃣ Lightweight response
        if any(word in text for word in self.quick_keywords):
            return self.adapters.get("phi")

        # 4️⃣ Default conversation
        return self.adapters.get("mistral")

    # -----------------------------------------------------

    def generate(self, prompt: str):

        model = self.select_model(prompt)

        if model is None:
            return {"text": "No model available."}

        try:
            return model.generate(prompt=prompt)
        except Exception as e:
            return {"text": f"Model error: {str(e)}"}