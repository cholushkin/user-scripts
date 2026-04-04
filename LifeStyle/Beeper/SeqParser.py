# -------------------------
# TOKEN
# -------------------------

class Token:
    def __init__(self, name, count=1):
        self.name = name
        self.count = count

    def __repr__(self):
        return f"{self.name}*{self.count}" if self.count > 1 else self.name


# -------------------------
# PARSER
# -------------------------

class SequenceParser:
    def __init__(self, text):
        self.text = text
        self.pos = 0

    # ---------- ENTRY ----------

    def parse(self):
        items = self.parse_sequence()
        self.skip_ws()

        if self.pos != len(self.text):
            raise ValueError(f"Unexpected input at {self.pos}")

        return items

    # ---------- CORE ----------

    def parse_sequence(self):
        items = []

        while self.pos < len(self.text):
            self.skip_ws()

            if self.peek() in ")]}":
                break

            items.extend(self.parse_item())

        return items

    def parse_item(self):
        self.skip_ws()

        # prefix repeat: 2*(...)
        if self.peek().isdigit():
            return self.parse_prefix_repeat()

        # group
        if self.peek() in "([{":
            group = self.parse_group()

            self.skip_ws()
            if self.peek() == "*":
                self.pos += 1
                count = self.consume_number()
                return self.multiply(group, count)

            return group

        # token
        token = self.parse_token()

        self.skip_ws()

        # postfix repeat: M*3
        if self.peek() == "*":
            self.pos += 1
            count = self.consume_number()
            return [Token(token.name, token.count * count)]

        return [token]

    # ---------- TOKEN ----------

    def parse_token(self):
        name = self.consume_name()

        count = 1

        # postfix number: M2, _2
        if self.peek().isdigit():
            count = self.consume_number()

        return Token(name, count)

    # ---------- GROUP ----------

    def parse_group(self):
        open_char = self.consume()
        close_char = {"(": ")", "[": "]", "{": "}"}[open_char]

        items = self.parse_sequence()

        if self.consume() != close_char:
            raise ValueError("Unclosed group")

        return items

    # ---------- PREFIX REPEAT ----------

    def parse_prefix_repeat(self):
        count = self.consume_number()

        self.skip_ws()

        if self.peek() != "*":
            raise ValueError("Expected '*' after number")

        self.pos += 1
        self.skip_ws()

        if self.peek() in "([{":
            group = self.parse_group()
        else:
            group = self.parse_item()

        return self.multiply(group, count)

    # ---------- MULTIPLY ----------

    def multiply(self, tokens, count):
        result = []
        for _ in range(count):
            for t in tokens:
                result.append(Token(t.name, t.count))
        return result

    # ---------- HELPERS ----------

    def skip_ws(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def peek(self):
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def consume(self):
        ch = self.text[self.pos]
        self.pos += 1
        return ch

    def consume_number(self):
        start = self.pos
        while self.peek().isdigit():
            self.pos += 1
        return int(self.text[start:self.pos])

    def consume_name(self):
        start = self.pos
        while self.peek().isalpha() or self.peek() == "_":
            self.pos += 1
        return self.text[start:self.pos]


# -------------------------
# TIMELINE BUILDER
# -------------------------

def build_timeline(tokens):
    timeline = []

    for t in tokens:
        timeline.extend([t.name] * t.count)

    return timeline


# -------------------------
# TESTS (10 cases)
# -------------------------

def test(seq):
    print("\nINPUT:   ", seq)

    tokens = SequenceParser(seq).parse()
    print("TOKENS:  ", tokens)

    timeline = build_timeline(tokens)
    print("TIMELINE:", timeline)
    print("VISUAL:  ", " ".join(timeline))


if __name__ == "__main__":

    # 1 basic
    test("M")

    # 2 postfix number
    test("M3")

    # 3 postfix repeat
    test("M*3")

    # 4 silence shorthand
    test("_2")

    # 5 mixed simple
    test("M _2 S")

    # 6 prefix repeat (group)
    test("2*(M _ S)")

    # 7 postfix repeat (group)
    test("(M _2 S)*2")

    # 8 nested
    test("2*(M (_2 S)*2)")

    # 9 mixed styles
    test("M2 S*2 3*K")

    # 10 complex (your real case)
    test("2*(M _2 (K*2 S))")