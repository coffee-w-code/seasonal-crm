from __future__ import annotations
from copy import deepcopy



INVENTORY_TOOLS = [
    {
        "type": "function",
        "name": "check_inventory",
        "description": (
            "Check the current stock of a specific product. "
            "Use this when the business owner asks how much stock "
            "is available at a location or in total."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": (
                        "The product name as spoken by the business owner."
                    ),
                },
                "location": {
                    "type": "string",
                    "enum": [
                        "HOME",
                        "SHOP",
                        "WAREHOUSE",
                    ],
                    "description": (
                        "Optional physical inventory location. "
                        "Leave empty when the owner asks for total stock."
                    ),
                },
            },
            "required": ["product_name"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "transfer_inventory",
        "description": (
            "Transfer existing inventory between two internal business "
            "locations. Use this for movements such as warehouse to shop, "
            "shop to home, or home to warehouse."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "The exact or spoken product name.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Number of units to transfer.",
                    "minimum": 1,
                },
                "source_location": {
                    "type": "string",
                    "enum": [
                        "HOME",
                        "SHOP",
                        "WAREHOUSE",
                    ],
                },
                "destination_location": {
                    "type": "string",
                    "enum": [
                        "HOME",
                        "SHOP",
                        "WAREHOUSE",
                    ],
                },
                "notes": {
                    "type": "string",
                    "description": "Optional reason or context for the transfer.",
                },
            },
            "required": [
                "product_name",
                "quantity",
                "source_location",
                "destination_location",
            ],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "dispatch_inventory",
        "description": (
            "Dispatch stock from one internal business location to an "
            "external customer or destination. Use this for sales, "
            "shipments, deliveries, or customer dispatches."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "The product being dispatched.",
                },
                "quantity": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of units being dispatched.",
                },
                "source_location": {
                    "type": "string",
                    "enum": [
                        "HOME",
                        "SHOP",
                        "WAREHOUSE",
                    ],
                },
                "customer_name": {
                    "type": "string",
                    "description": (
                        "Optional customer or store name receiving the stock."
                    ),
                },
                "notes": {
                    "type": "string",
                    "description": "Optional dispatch notes.",
                },
            },
            "required": [
                "product_name",
                "quantity",
                "source_location",
            ],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "receive_inventory",
        "description": (
            "Record newly received stock arriving from an external supplier "
            "or factory into an internal business location."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "The received product.",
                },
                "quantity": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of units received.",
                },
                "destination_location": {
                    "type": "string",
                    "enum": [
                        "HOME",
                        "SHOP",
                        "WAREHOUSE",
                    ],
                },
                "notes": {
                    "type": "string",
                    "description": "Optional receiving notes.",
                },
            },
            "required": [
                "product_name",
                "quantity",
                "destination_location",
            ],
            "additionalProperties": False,
        },
    },
]


def get_inventory_tools() -> list[dict]:
    """
    Return an isolated copy of the inventory tool registry.

    Prevents accidental mutation of nested tool definitions.
    """
    return deepcopy(INVENTORY_TOOLS)