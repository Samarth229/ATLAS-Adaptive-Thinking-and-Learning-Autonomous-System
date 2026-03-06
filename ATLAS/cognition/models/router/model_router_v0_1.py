class ModelRouterV0_1:

    def __init__(self, default_model):
        self.default_model = default_model
        self.models = {}

    def register_model(self, name, model):
        self.models[name] = model

    def route(self, prompt, model_name=None):

        if model_name and model_name in self.models:
            model = self.models[model_name]
        else:
            model = self.default_model

        try:
            output = model.generate(prompt=prompt)

            if isinstance(output, dict):
                return output.get("text", "")

            return str(output)

        except Exception:
            return "Model execution failed."