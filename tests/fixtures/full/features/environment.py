"""Hooks for the full test fixture."""

import time


def before_all(context):
    context.config.setup_logging()


def before_scenario(context, scenario):
    context.start_time = time.time()


def after_scenario(context, scenario):
    elapsed = time.time() - getattr(context, "start_time", time.time())
    if elapsed > 0.1:
        pass  # Could log slow scenarios
