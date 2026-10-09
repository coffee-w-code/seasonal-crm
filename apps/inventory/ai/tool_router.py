from __future__ import annotations

import json
import logging
from typing import Any

from django.core.exceptions import ObjectDoesNotExist

from ..services.inventory_service import (
    InventoryService,
    InventoryServiceError,
)

logger = logging.getLogger(__name__)


class AIToolRouter:
    """
    Routes validated AI function calls to application services.

    The AI never receives direct access to Django models.

    Flow:

        OpenAI tool call
            ↓
        AIToolRouter
            ↓
        InventoryService
            ↓
        Database
    """

    def __init__(self, business):
        self.business = business

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> str:
        """
        Execute an AI tool and return a JSON-safe string response.

        AI APIs generally expect tool output to be serialized.
        """

        handlers = {
            "check_inventory": self._check_inventory,
            "transfer_inventory": self._transfer_inventory,
            "dispatch_inventory": self._dispatch_inventory,
            "receive_inventory": self._receive_inventory,
        }

        handler = handlers.get(tool_name)

        if handler is None:
            logger.warning(
                "AI attempted to call unknown tool: %s",
                tool_name,
            )

            return self._error(
                "UNKNOWN_TOOL",
                f"Tool '{tool_name}' is not available.",
            )

        try:
            return handler(arguments)

        except InventoryServiceError as exc:
            logger.info(
                "Inventory tool rejected by business rules. "
                "tool=%s business_id=%s error=%s",
                tool_name,
                getattr(self.business, "id", None),
                str(exc),
            )

            return self._error(
                "INVENTORY_OPERATION_REJECTED",
                str(exc),
            )

        except ObjectDoesNotExist as exc:
            logger.warning(
                "Related database object not found. "
                "tool=%s business_id=%s error=%s",
                tool_name,
                getattr(self.business, "id", None),
                str(exc),
            )

            return self._error(
                "RESOURCE_NOT_FOUND",
                "The requested business record could not be found.",
            )

        except (TypeError, ValueError, KeyError) as exc:
            logger.warning(
                "Invalid AI tool arguments. "
                "tool=%s business_id=%s error=%s",
                tool_name,
                getattr(self.business, "id", None),
                str(exc),
            )

            return self._error(
                "INVALID_ARGUMENTS",
                "The requested operation contains invalid arguments.",
            )

        except Exception:
            logger.exception(
                "Unexpected AI tool failure. "
                "tool=%s business_id=%s",
                tool_name,
                getattr(self.business, "id", None),
            )

            return self._error(
                "INTERNAL_ERROR",
                "The inventory operation could not be completed.",
            )

    # ------------------------------------------------------------------
    # Inventory tools
    # ------------------------------------------------------------------

    def _check_inventory(
        self,
        arguments: dict[str, Any],
    ) -> str:
        product_name = self._required_string(
            arguments,
            "product_name",
        )

        location = self._optional_string(
            arguments,
            "location",
        )

        result = InventoryService.get_stock(
            self.business,
            product_name=product_name,
            location=location,
        )

        return self._success(
            "inventory_checked",
            result,
        )

    def _transfer_inventory(
        self,
        arguments: dict[str, Any],
    ) -> str:
        product_name = self._required_string(
            arguments,
            "product_name",
        )

        quantity = self._required_positive_integer(
            arguments,
            "quantity",
        )

        source_location = self._required_string(
            arguments,
            "source_location",
        )

        destination_location = self._required_string(
            arguments,
            "destination_location",
        )

        notes = self._optional_string(
            arguments,
            "notes",
        )

        result = InventoryService.transfer(
            self.business,
            product_name=product_name,
            quantity=quantity,
            source_location=source_location,
            destination_location=destination_location,
            notes=notes,
        )

        return self._success(
            "inventory_transferred",
            {
                "product_id": result.product_id,
                "product_name": result.product_name,
                "quantity": result.quantity,
                "source_location": result.source_location,
                "destination_location": result.destination_location,
                "source_quantity_after": result.source_quantity_after,
                "destination_quantity_after": (
                    result.destination_quantity_after
                ),
                "movement_id": result.movement_id,
            },
        )

    def _dispatch_inventory(
        self,
        arguments: dict[str, Any],
    ) -> str:
        product_name = self._required_string(
            arguments,
            "product_name",
        )

        quantity = self._required_positive_integer(
            arguments,
            "quantity",
        )

        source_location = self._required_string(
            arguments,
            "source_location",
        )

        customer_name = self._optional_string(
            arguments,
            "customer_name",
        )

        notes = self._optional_string(
            arguments,
            "notes",
        )

        # IMPORTANT:
        # Customer resolution is intentionally not implemented here yet.
        #
        # Your current database has Customer, but there is no Order/Sale
        # model connecting a dispatch to a financial transaction.
        #
        # For now, we safely record the inventory dispatch itself.
        #
        # We will add customer/order integration as a separate service.

        if customer_name:
            notes = self._append_note(
                notes,
                f"Customer: {customer_name}",
            )

        result = InventoryService.dispatch(
            self.business,
            product_name=product_name,
            quantity=quantity,
            source_location=source_location,
            notes=notes,
        )

        return self._success(
            "inventory_dispatched",
            {
                "product_id": result.product_id,
                "product_name": result.product_name,
                "quantity": result.quantity,
                "source_location": result.source_location,
                "destination_location": result.destination_location,
                "remaining_source_quantity": (
                    result.source_quantity_after
                ),
                "movement_id": result.movement_id,
                "customer_name": customer_name,
            },
        )

    def _receive_inventory(
        self,
        arguments: dict[str, Any],
    ) -> str:
        product_name = self._required_string(
            arguments,
            "product_name",
        )

        quantity = self._required_positive_integer(
            arguments,
            "quantity",
        )

        destination_location = self._required_string(
            arguments,
            "destination_location",
        )

        notes = self._optional_string(
            arguments,
            "notes",
        )

        result = InventoryService.receive(
            self.business,
            product_name=product_name,
            quantity=quantity,
            destination_location=destination_location,
            notes=notes,
        )

        return self._success(
            "inventory_received",
            {
                "product_id": result.product_id,
                "product_name": result.product_name,
                "quantity": result.quantity,
                "source_location": result.source_location,
                "destination_location": result.destination_location,
                "destination_quantity_after": (
                    result.destination_quantity_after
                ),
                "movement_id": result.movement_id,
            },
        )

    # ------------------------------------------------------------------
    # Argument validation
    # ------------------------------------------------------------------

    @staticmethod
    def _required_string(
        arguments: dict[str, Any],
        key: str,
    ) -> str:
        value = arguments.get(key)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"'{key}' is required."
            )

        return value.strip()

    @staticmethod
    def _optional_string(
        arguments: dict[str, Any],
        key: str,
    ) -> str | None:
        value = arguments.get(key)

        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                f"'{key}' must be a string."
            )

        value = value.strip()

        return value or None

    @staticmethod
    def _required_positive_integer(
        arguments: dict[str, Any],
        key: str,
    ) -> int:
        value = arguments.get(key)

        if isinstance(value, bool):
            raise ValueError(
                f"'{key}' must be a positive integer."
            )

        if not isinstance(value, int):
            raise ValueError(
                f"'{key}' must be a positive integer."
            )

        if value <= 0:
            raise ValueError(
                f"'{key}' must be greater than zero."
            )

        return value

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _success(
        operation: str,
        data: dict[str, Any],
    ) -> str:
        return json.dumps(
            {
                "status": "success",
                "operation": operation,
                "data": data,
            },
            default=str,
        )

    @staticmethod
    def _error(
        error_code: str,
        message: str,
    ) -> str:
        return json.dumps(
            {
                "status": "error",
                "error_code": error_code,
                "message": message,
            }
        )

    @staticmethod
    def _append_note(
        existing: str | None,
        additional: str,
    ) -> str:
        if not existing:
            return additional

        return f"{existing} | {additional}"