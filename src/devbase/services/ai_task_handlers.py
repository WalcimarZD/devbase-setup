"""
AI Task Handlers
================
Default task handlers used by the async AI worker.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger("devbase.ai_task_handlers")


def _get_llm_provider():
    """Get an LLM provider instance when available."""
    try:
        from devbase.ai.providers.groq import GroqProvider

        return GroqProvider()
    except Exception:
        return None


def default_classify_handler(payload: str) -> str:
    """Classify content payload using LLM with fallback."""
    data = json.loads(payload)
    content = data.get("content", "")
    categories = data.get("categories", ["general", "task", "note", "idea"])

    provider = _get_llm_provider()
    if provider:
        try:
            prompt = (
                f"Classify the following text into one of these categories: {', '.join(categories)}.\n"
                f"Text: {content}\n"
                "Respond with only the category name."
            )
            result = provider.complete(prompt).strip()
            result = result if result in categories else categories[0]
            return json.dumps({"category": result, "confidence": 0.9, "source": "llm"})
        except Exception as exc:
            logger.warning("LLM classify failed, using fallback: %s", exc)

    return json.dumps({"category": categories[0], "confidence": 0.5, "source": "fallback"})


def default_summarize_handler(payload: str) -> str:
    """Summarize content payload using LLM with fallback."""
    data = json.loads(payload)
    content = data.get("content", "")
    max_length = data.get("max_length", 50)

    provider = _get_llm_provider()
    if provider:
        try:
            prompt = f"Summarize the following text in at most {max_length} words:\n{content}"
            result = provider.complete(prompt)
            return json.dumps({"summary": result, "source": "llm"})
        except Exception as exc:
            logger.warning("LLM summarize failed, using fallback: %s", exc)

    truncated = content[: max_length * 5] + "..." if len(content) > max_length * 5 else content
    return json.dumps({"summary": truncated, "source": "fallback"})


def default_synthesize_handler(payload: str) -> str:
    """Synthesize response payload using LLM with fallback."""
    data = json.loads(payload)
    prompt = data.get("prompt", "")

    provider = _get_llm_provider()
    if provider:
        try:
            response = provider.complete(prompt)
            return json.dumps({"result": response, "source": "llm"})
        except Exception as exc:
            logger.warning("LLM synthesize failed, using fallback: %s", exc)

    return json.dumps({"result": "Task queued but LLM not available", "source": "fallback"})


def summarize_day_handler(payload: str) -> str:
    """Generate a daybook entry from activity logs."""
    try:
        from devbase.services.routine_agent import RoutineAgent

        data = json.loads(payload)
        target_date = data.get("date")
        if not target_date:
            return json.dumps({"error": "Missing date"})

        agent = RoutineAgent()
        summary = agent.generate_daybook_summary(target_date)

        template_path = Path("src/devbase/templates/pkm/12_private_vault/journal/template-daybook.md.template")
        if not template_path.exists():
            template_path = (
                Path(__file__).parents[1]
                / "templates"
                / "pkm"
                / "12_private_vault"
                / "journal"
                / "template-daybook.md.template"
            )

        if not template_path.exists():
            return json.dumps({"error": "Template not found"})

        template_content = template_path.read_text(encoding="utf-8")

        final_lines: list[str] = []
        lines = template_content.splitlines()
        index = 0

        while index < len(lines):
            line = lines[index]

            if "{{DATE}}" in line:
                final_lines.append(line.replace("{{DATE}}", summary.date))

            elif "## 🎯 Foco do Dia" in line:
                final_lines.append(line)
                final_lines.append("")
                final_lines.append(summary.focus)
                while index + 1 < len(lines) and lines[index + 1].strip().startswith("- [ ] ["):
                    index += 1

            elif "## 📝 Log de Trabalho" in line:
                final_lines.append(line)
                final_lines.append("")
                final_lines.append(summary.log_narrative)
                while index + 1 < len(lines) and (
                    lines[index + 1].strip().startswith("###")
                    or "[Atividade]" in lines[index + 1]
                    or "[Notas" in lines[index + 1]
                ):
                    index += 1

            elif "## 📊 Métricas" in line:
                final_lines.append(line)
                final_lines.append("")
                final_lines.append(f"- Commits: {summary.metrics.get('commits', 0)}")
                final_lines.append(f"- PRs: {summary.metrics.get('prs', 0)}")
                final_lines.append(f"- Issues fechadas: {summary.metrics.get('issues', 0)}")
                while index + 1 < len(lines) and lines[index + 1].strip().startswith("- "):
                    index += 1
            else:
                final_lines.append(line)

            index += 1

        final_content = "\n".join(final_lines)

        output_path = agent.journal_path / f"{summary.date}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(final_content, encoding="utf-8")

        return json.dumps({"path": str(output_path), "status": "created"})

    except Exception as exc:
        logger.error("Summarize day failed: %s", exc)
        return json.dumps({"error": str(exc)})


def register_default_handlers(worker) -> None:
    """Register default task handlers in an AI worker instance."""
    worker.register_handler("classify", default_classify_handler)
    worker.register_handler("summarize", default_summarize_handler)
    worker.register_handler("synthesize", default_synthesize_handler)
    worker.register_handler("summarize_day", summarize_day_handler)
