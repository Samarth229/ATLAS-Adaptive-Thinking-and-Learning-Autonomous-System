from services.tools.tool_definitions.vision_v0_1.screen_vision import ask_about_screen


def _what_on_screen(arg=None):
    question = arg.strip() if arg and arg.strip() else None
    return ask_about_screen(question)


def register_all(matcher):
    matcher.register([
        "what's on my screen", "what is on my screen", "describe my screen",
        "look at my screen", "what do you see", "what can you see on screen",
        "tell me what's on screen", "check my screen",
    ], _what_on_screen, needs_arg=True)
