import unicodedata


class Parser:
    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return text
        return unicodedata.normalize('NFKC', text).replace('\n', '').strip()
