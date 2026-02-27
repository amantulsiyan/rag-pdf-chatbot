class DummyLLM:
    def generate(self, prompt: str) -> str:
        return "This is a demo response. The document has been analyzed and this answer is based on the retrieved context. Please configure a valid GROQ_API_KEY to get real AI-powered answers."