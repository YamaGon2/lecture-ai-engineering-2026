from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    class FakeChat:
        def send_message(self, question):
            return SimpleNamespace(
                text="answer",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=12,
                    candidates_token_count=7,
                ),
            )

    assert ask_module.ask(FakeChat(), "question") == "answer"
    assert "[トークン] 入力: 12, 出力: 7" in capsys.readouterr().out


def test_main_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(text=f"answer to {question}", usage_metadata=None)

    chat = FakeChat()
    fake_client = SimpleNamespace(chats=SimpleNamespace(create=lambda **kwargs: chat))
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: fake_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["app.ask", "first question"])
    answers = iter(["follow-up question", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    ask_module.main()

    assert chat.questions == ["first question", "follow-up question"]
    assert "answer to follow-up question" in capsys.readouterr().out