class WrongAnswer(Exception):

    def __init__(self, message, answer, asnwers):
        self.answer = answer
        self.answers = answers
        super(WrongAnswer, self).__init__(message)


class Choice:

    def __init__(self, title, answers, prompt=" > "):
        self.title = title
        self.answers = answers
        self.prompt = prompt

    def question(self):
        options = [" {}. - {}".format(i, a) for i, a in enumerate(self.answers)]
        return "{}\n\n{}\n".format(self.title, '\n'.join(options))

    def ask(self):
        print(self.question())
        answer = input(self.prompt)
        if type(answer) == int and int(answer) in range(0, len(self.answers)):
            index = int(answer)
            return index, self.answers[index]
        elif answer in self.answers:
            index = self.answers.index(answer)
            return index, answer
        else:
            raise WrongAnswer("Wrong answer", answer, self.answers)



if __name__ == '__main__':
    Choice(title="ZXCVADF", answers=["asdf", "zxcv"]).ask()
