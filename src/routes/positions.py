from fastapi import FastAPI

api = FastAPI()

positions = {}


@api.get("/position/{user_id}")
async def get_positions(user_id: str):
    return {"status": "Not implemented"}
    #
    # TODO: Implement get position logic
    #
    # user_positions = positions.get(user_id, [])
    # return {"user_id": user_id, "positions": user_positions}


@api.post("/position/{position_id}")
async def open_position(position_id: str):
    return {"status": "Not implemented"}
    #
    # TODO: Implement position open logic
    #
    # if position_id in positions:
    #     return {"status": "Position already exists", "position_id": position_id}
    # positions[position_id] = {"status": "open"}
    # return {"status": "Position opened", "position_id": position_id}


@api.put("/position/{position_id}")
async def update_position(position_id: str):
    return {"status": "Not implemented"}
    #
    # TODO: Implement position update logic
    #
    # return not implemeneted error
    # if position_id not in positions:
    #     return {"status": "Position not found", "position_id": position_id}
    # return {"status": "Position updated", "position_id": position_id}
