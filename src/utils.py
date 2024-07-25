import json

def pretty_json(args: str):
    return json.dumps(args, indent=4)
