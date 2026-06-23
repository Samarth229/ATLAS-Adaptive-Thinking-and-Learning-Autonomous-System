_PRODUCTIVE_KEYWORDS = [
    "claude", "chatgpt", "gpt-4", "copilot", "github", "gitlab",
    "stackoverflow", "stack overflow", "docs.", "documentation",
    "localhost", "127.0.0.1", "leetcode", "hackerrank",
    "tutorial", "how to", "geeksforgeeks", "w3schools",
    "visual studio code", " - code", "terminal", "powershell",
    "jupyter", "colab", "kaggle", "postman", "figma",
    "notion", "google docs", "google sheets", "excel",
    "linkedin jobs", "indeed", "naukri",
]

_DISTRACTION_KEYWORDS = [
    "instagram", "facebook", "reddit", "twitter", " x.com",
    "tiktok", "snapchat", "pinterest",
    "netflix", "prime video", "hotstar",
    "league of legends", "valorant", "steam",
    "whatsapp", "telegram", "discord",
]

_ALWAYS_PRODUCTIVE_PROCESSES = {
    "code.exe", "code", "pycharm64.exe", "studio64.exe",
    "windowsterminal.exe", "cmd.exe", "powershell.exe",
    "excel.exe", "winword.exe", "powerpnt.exe",
}


def classify_window(process_name: str, title: str) -> str:
    """Returns 'productive', 'distraction', or 'neutral'."""
    process_lower = (process_name or "").lower()
    title_lower = (title or "").lower()

    if process_lower in _ALWAYS_PRODUCTIVE_PROCESSES:
        return "productive"

    for keyword in _PRODUCTIVE_KEYWORDS:
        if keyword in title_lower:
            return "productive"

    for keyword in _DISTRACTION_KEYWORDS:
        if keyword in title_lower:
            return "distraction"

    return "neutral"
