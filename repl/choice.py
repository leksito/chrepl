class Choice:
    def __init__(self, title, answers, prompt=" > "):
        self.title = title
        self.answers = answers
        self.prompt = prompt

    def question(self):
        options = []
        for index, answer in enumerate(self.answers):
            options.append("  {}. - {}".format(index, answer))
        return "{}\n\n{}\n".format(self.title, '\n'.join(options))

    def ask(self):
        return input(self.prompt)



print(Choice(title="ZXCVADF", answers=["asdf", "zxcv"]).question())
