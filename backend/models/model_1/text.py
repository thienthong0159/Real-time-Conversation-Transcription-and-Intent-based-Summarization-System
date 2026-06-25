import re

BLANK_TOKEN = "<blank>"
DEFAULT_VOCAB = [BLANK_TOKEN] + list("abcdefghijklmnopqrstuvwxyz '")


class TextTransform:
    def __init__(self, vocab=None):
        self.vocab = vocab or DEFAULT_VOCAB
        self.char_to_idx = {char: index for index, char in enumerate(self.vocab)}
        self.idx_to_char = {index: char for index, char in enumerate(self.vocab)}
        self.blank_index = self.char_to_idx[BLANK_TOKEN]

    def normalize(self, text):
        text = text.lower().replace("\u2019", "'")
        text = re.sub(r"[^a-z' ]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def encode(self, text):
        normalized = self.normalize(text)
        return [self.char_to_idx[char] for char in normalized if char in self.char_to_idx]

    def decode_greedy(self, token_ids):
        collapsed = []
        previous = None
        for token_id in token_ids:
            token_id = int(token_id)
            if token_id != previous and token_id != self.blank_index:
                collapsed.append(self.idx_to_char.get(token_id, ""))
            previous = token_id
        return "".join(collapsed).strip()

    def to_metadata(self):
        return {"vocab": self.vocab, "blank_index": self.blank_index}
