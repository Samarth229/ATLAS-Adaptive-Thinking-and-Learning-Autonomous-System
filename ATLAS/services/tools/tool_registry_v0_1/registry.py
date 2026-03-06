class ToolRegistryV0_1:

    def __init__(self):
        self._tools = {}

    def register(self, tool_instance):
        self._tools[tool_instance.name()] = tool_instance

    def get(self, tool_name):
        return self._tools.get(tool_name)

    def list_tools(self):
        return list(self._tools.keys())