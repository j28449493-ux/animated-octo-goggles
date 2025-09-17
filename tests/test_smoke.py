import importlib

MODULES = [
    "config",
    "main",
    "sources.simplify_client",
    "sources.rss_client",
    "tracker.sheets_client",
    "generator.llm",
    "generator.resume_tailor",
    "generator.cover_letter",
    "reminders.calendar_client",
    "prep.mock_interview",
]


def test_imports():
    for module in MODULES:
        importlib.import_module(module)
