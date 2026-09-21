"""Telegram-бот для Pokémon Team Strategist.

Формат ввода: покемоны через запятую | противник
Пример: pikachu, charizard, blastoise | mewtwo
"""

import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.graph import graph

load_dotenv()
BOT_KEY = os.getenv("TELEGRAM_BOT_KEY")

HELP_TEXT = (
    "Привет! Я анализирую команду покемонов.\n\n"
    "Формат:\n"
    "`покемоны через запятую | противник`\n\n"
    "Пример:\n"
    "`pikachu, charizard, blastoise | mewtwo`"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ответ на /start."""
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать текстовое сообщение."""
    text = (update.message.text or "").strip()

    if "|" not in text:
        await update.message.reply_text(
            "Не вижу разделитель `|`. " + HELP_TEXT,
            parse_mode="Markdown",
        )
        return

    team_part, opponent_part = text.split("|", 1)
    selected = [s.strip().lower() for s in team_part.split(",") if s.strip()]
    opponent = [o.strip().lower() for o in opponent_part.split(",") if o.strip()]

    if not selected or not opponent:
        await update.message.reply_text(
            "Нужно указать и команду, и противника. " + HELP_TEXT,
            parse_mode="Markdown",
        )
        return

    # Сообщаем, что начали — запрос к PokéAPI занимает несколько секунд
    await update.message.reply_text("Анализирую команду, подожди пару секунд…")

    # thread_id = id пользователя. Один и тот же пользователь продолжит диалог
    thread_id = str(update.effective_user.id)
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(
            {
                "selected": selected,
                "opponent": opponent,
                "attempts": 0,
                "max_attempts": 3,
            },
            config,
        )
    except Exception as exc:
        await update.message.reply_text(f"Ошибка при обработке: {exc}")
        return

    if result.get("error"):
        await update.message.reply_text(f"Ошибка: {result['error']}")
        return

    # Собираем ответ
    lines = [result["analysis"], ""]

    proposed = result.get("proposed")
    if proposed:
        lines += [
            "## Предложенная замена",
            f"- Убрать: {proposed['out']}",
            f"- Добавить: {proposed['in']}",
            f"- Причина: {proposed['reason']}",
            "",
        ]

    lines.append(f"Попыток: {result.get('attempts', 0)} из {result.get('max_attempts', 3)}")
    lines.append("")
    lines.append("## Источники")
    for src in result.get("sources", [])[:6]:
        lines.append(f"- {src}")

    await update.message.reply_text("\n".join(lines))


def main() -> None:
    """Запустить бота."""
    if not BOT_KEY:
        raise RuntimeError("Добавь TELEGRAM_BOT_KEY в файл .env")

    app = Application.builder().token(BOT_KEY).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram-бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()