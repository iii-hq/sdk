from typing import Any

from .bridge import bridge


class State:
    async def get(self, group_id: str, item_id: str) -> Any | None:
        return await bridge.invoke_function("state.get", {"group_id": group_id, "item_id": item_id})

    async def set(self, group_id: str, item_id: str, data: Any) -> Any:
        return await bridge.invoke_function("state.set", {"group_id": group_id, "item_id": item_id, "data": data})

    async def delete(self, group_id: str, item_id: str) -> None:
        return await bridge.invoke_function("state.delete", {"group_id": group_id, "item_id": item_id})

    async def get_group(self, group_id: str) -> list[Any]:
        return await bridge.invoke_function("state.getGroup", {"group_id": group_id})


state = State()
