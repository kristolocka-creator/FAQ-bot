import os

from support_bot import SupportBot


def main():
    bot = SupportBot("data/faq.json")

    questions = [
    "Как сменить пароль?",          # точное совпадение
    "Как поменять пароль?",         # синоним
    "Как приготовить борщ?",       # неизвестный вопрос
    "Как изменить пароль и адрес?" # равные максимальные score
]

    print("=" * 60)
    print("Демонстрация диалога")
    print("=" * 60)

    for question in questions:
        print(f"USER: {question}")
        print(f"BOT : {bot.get_answer(question)}")
        print("-" * 60)

    print("\n>>> /history")
    print(bot.get_answer("/history"))
    print("-" * 60)

    print("\n>>> /export")
    print(bot.get_answer("/export"))
    print("-" * 60)

    print("\n>>> /help")
    print(bot.get_answer("/help"))
    print("-" * 60)

    # Проверки
    assert os.path.exists("history.csv"), "history.csv не создан!"
    assert os.path.exists("data/unknown_questions.log"), \
        "unknown_questions.log не создан!"

    print("\n✅ demo прошло успешно: history.csv и лог созданы.")


if __name__ == "__main__":
    main()