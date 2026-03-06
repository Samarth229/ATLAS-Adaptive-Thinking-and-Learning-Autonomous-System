class ToolExecutorV0_1:

    def __init__(self, registry):
        self.registry = registry

    def execute(self, tool_name, input_data):
        tool = self.registry.get(tool_name)

        if not tool:
            return {
                "success": False,
                "output": None,
                "error": f"Tool '{tool_name}' not found."
            }

        try:
            result = tool.execute(input_data)
            return result
        except Exception as e:
            return {
                "success": False,
                "output": None,
                "error": str(e)
            }