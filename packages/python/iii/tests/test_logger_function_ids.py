from iii.logger import Logger


def test_logger_invokes_engine_log_function_ids() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    logger = Logger(
        invoker=lambda function_id, payload: calls.append((function_id, payload)),
        trace_id="trace-1",
        function_name="step.fn",
    )

    logger.info("info message", {"k": 1})
    logger.warn("warn message")
    logger.error("error message")
    logger.debug("debug message")

    assert [function_id for function_id, _ in calls] == [
        "engine.log.info",
        "engine.log.warn",
        "engine.log.error",
        "engine.log.debug",
    ]

