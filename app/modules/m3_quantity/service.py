from .units import to_pieces
from .match import quantity_account

def run(payload: dict | None = None) -> dict:
    payload = payload or {"ordered": "10", "received": "9", "returned": "1", "unit": "piece", "pack_size": "1"}
    values = {key: to_pieces(payload[key], payload["unit"], payload["pack_size"]) for key in ("ordered", "received", "returned")}
    return quantity_account(values["ordered"], values["received"], values["returned"])

def demo():
    return run()

