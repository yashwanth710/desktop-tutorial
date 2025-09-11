from langchain_mistralai import ChatMistralAI


class MistralModel:
    def __init__(self):
        self.llm = ChatMistralAI(
            model = "pixtral-12b-2409"
        )


    def generate(self):
        pass