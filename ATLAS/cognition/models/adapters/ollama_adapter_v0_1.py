import requests


class OllamaAdapterV0_1:

    def __init__(self, model_name):
        self.model_name = model_name
        self.url = "http://localhost:11434/api/generate"

    def generate(self, prompt):

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.url, json=payload, timeout=120)

            data = response.json()

            return {
                "text": data.get("response", "")
            }

        except Exception:
            return {
                "text": f"Local model execution failed: "  #try checking if ollama is running and the model is available
            }