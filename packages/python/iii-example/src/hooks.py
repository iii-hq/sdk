from typing import Any, Awaitable, Callable

from iii import ApiRequest, ApiResponse, FunctionInfo, get_context

from .bridge import bridge


def use_api(
    config: dict[str, Any],
    handler: Callable[[ApiRequest[Any], Any], Awaitable[ApiResponse[Any]]],
) -> None:
    api_path = config["api_path"]
    http_method = config["http_method"]
    function_id = f"api.{http_method.lower()}.{api_path}"

    async def wrapped(data: Any) -> dict[str, Any]:
        req = ApiRequest(**data) if isinstance(data, dict) else data
        ctx = get_context()
        result = await handler(req, ctx)
        return result.model_dump(by_alias=True)

    bridge.register_function(function_id, wrapped)
    bridge.register_trigger(
        trigger_type="api",
        function_id=function_id,
        config={
            "api_path": api_path,
            "http_method": http_method,
            "description": config.get("description"),
            "metadata": config.get("metadata"),
        },
    )


def use_functions_available(callback: Callable[[list[FunctionInfo]], None]) -> Callable[[], None]:
    return bridge.on_functions_available(callback)
