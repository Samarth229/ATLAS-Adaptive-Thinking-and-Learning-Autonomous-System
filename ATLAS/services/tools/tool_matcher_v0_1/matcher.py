import re


class ToolMatcher:

    def __init__(self):
        self._patterns = []

    def register(self, keywords, handler, needs_arg=False):
        self._patterns.append((keywords, handler, needs_arg))

    def match(self, text: str):
        text_lower = text.lower().strip()
        for keywords, handler, needs_arg in self._patterns:
            if any(kw in text_lower for kw in keywords):
                if needs_arg:
                    arg = self._extract_arg(text_lower, keywords)
                    return {"handler": handler, "arg": arg}
                return {"handler": handler, "arg": None}
        return None

    def match_all(self, text: str) -> list:
        segments = re.split(r'\s+and\s+|\s+then\s+|\s+also\s+', text, flags=re.IGNORECASE)
        matches = []
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            result = self.match(segment)
            if result:
                matches.append(result)
        return matches

    def _extract_arg(self, text, matched_keywords):
        for kw in sorted(matched_keywords, key=len, reverse=True):
            if kw in text:
                idx = text.find(kw) + len(kw)
                remainder = text[idx:].strip()
                for prefix in ("for ", "to ", "in ", "about "):
                    if remainder.startswith(prefix):
                        remainder = remainder[len(prefix):]
                        break
                return remainder if remainder else None
        return None
