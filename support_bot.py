import json
import re
import csv
from pathlib import Path
from datetime import datetime


class SupportBot:
    """Rule-based чат-бот для FAQ."""

    def __init__(self, faq_path):
        """Загружает базу вопросов и ответов из JSON-файла."""
        self.faq_path = Path(faq_path)

        if not self.faq_path.exists():
            raise FileNotFoundError(f"Файл FAQ не найден: {self.faq_path}")

        with open(self.faq_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.faq = data["вопросы"]
        self.history = []

        # Предвычисляем набор ключевых слов (включая синонимы) для каждой записи,
        # чтобы не пересчитывать на каждом запросе (оптимизация для Шага 5 и 21).
        for item in self.faq:
            item["_keywords_set"] = self._build_keywords_set(item)

    def _normalize(self, text):
        """Приводит текст к нижнему регистру и убирает знаки препинания.
        Знаки препинания заменяются на пробел, чтобы не склеивать слова,
        дефис и апостроф сохраняются.
        """
        text = text.lower()
        text = re.sub(r"[^\w\s'-]", " ", text)
        return text

    def _tokenize(self, text):
        """Разбивает текст на отдельные слова (целые токены)."""
        return re.findall(r"[a-zа-яё0-9'-]+", text.lower())

    def _build_keywords_set(self, item):
        """Собирает множество нормализованных токенов из keywords и synonyms."""
        result = set()
        for keyword in item.get("keywords", []):
            normalized = self._normalize(keyword)
            result.update(self._tokenize(normalized))

        for synonym_list in item.get("synonyms", {}).values():
            for synonym in synonym_list:
                normalized = self._normalize(synonym)
                result.update(self._tokenize(normalized))
        return result

    def _compute_score(self, question_tokens, item):
        """Считает количество совпавших целых слов с ключевыми словами записи."""
        return len(set(question_tokens) & item["_keywords_set"])

    def get_answer(self, user_question):
        """Ищет ответ по ключевым словам и синонимам. Поддерживает спецкоманды."""

        # --- спецкоманды ---
        if user_question.strip().startswith("/"):
            return self._handle_command(user_question.strip())

        question = self._normalize(user_question)
        question_tokens = self._tokenize(question)

        best_score = 0
        best_answer = None

        for item in self.faq:
            score = self._compute_score(question_tokens, item)
            if score > best_score:
                best_score = score
                best_answer = item["answer"]

        if best_score > 0:
            answer = best_answer
        else:
            answer = "Извините, я не понял вопрос. Пожалуйста, уточните."
            self._log_unknown(user_question)

        self.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_question": user_question,
            "bot_answer": answer,
        })

        return answer

    def _handle_command(self, command):
        """Обрабатывает команды /help, /history, /export."""
        if command == "/help":
            return (
                "Доступные команды:\n"
                "/history — последние 5 вопросов-ответов\n"
                "/export  — сохранить историю в history.csv\n"
                "/help    — список команд"
            )

        if command == "/history":
            last = self.history[-5:]
            if not last:
                return "История пуста."
            lines = []
            for i, record in enumerate(last, start=1):
                lines.append(f"{i}. Q: {record['user_question']}\n   A: {record['bot_answer']}")
            return "\n".join(lines)

        if command == "/export":
            self.export_history("history.csv")
            return "История экспортирована в history.csv"

        return "Неизвестная команда. Введите /help."

    def export_history(self, filepath):
        """Сохраняет историю диалога в CSV-файл."""
        with open(filepath, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["timestamp", "user_question", "bot_answer"],
            )
            writer.writeheader()
            writer.writerows(self.history)

    def _log_unknown(self, question):
        """Записывает неизвестный вопрос в data/unknown_questions.log."""
        try:
            log_path = Path("data/unknown_questions.log")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as file:
                timestamp = datetime.now().isoformat()
                file.write(f"{timestamp} | {question}\n")
        except Exception:
            # Логирование не должно ломать ответ бота
            pass