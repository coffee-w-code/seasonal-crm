from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.db import transaction
from django.db.models import F, QuerySet

from apps.tenants.models import Business

from ..models import InventoryItem, Product, StockMovement


class InventoryServiceError(Exception):
    """Base exception for inventory business-rule failures."""


class ProductNotFoundError(InventoryServiceError):
    """Raised when a product cannot be resolved for a business."""


class ProductAmbiguousError(InventoryServiceError):
    """Raised when a product search matches multiple products."""


class CustomerNotFoundError(InventoryServiceError):
    """Reserved for future customer-related inventory operations."""


class InvalidLocationError(InventoryServiceError):
    """Raised when an invalid inventory location is supplied."""


class InvalidQuantityError(InventoryServiceError):
    """Raised when an invalid quantity is supplied."""


class InsufficientStockError(InventoryServiceError):
    """Raised when the source location does not contain enough stock."""


class SameLocationTransferError(InventoryServiceError):
    """Raised when stock is transferred to the same location."""


@dataclass(frozen=True)
class InventoryOperationResult:
    """
    Immutable result returned by inventory operations.

    Keeping a structured result here makes the service easy to use from:
    - REST APIs
    - Django views
    - WebSocket consumers
    - AI tool routers
    - background jobs
    """

    product_id: int
    product_name: str
    quantity: int
    source_location: Optional[str]
    destination_location: Optional[str]
    movement_type: str
    source_quantity_after: Optional[int]
    destination_quantity_after: Optional[int]
    movement_id: int


class InventoryService:
    """
    Application service for inventory operations.

    Responsibilities:
    - Resolve products within a specific business.
    - Validate inventory locations.
    - Validate quantities.
    - Perform atomic inventory changes.
    - Prevent negative stock.
    - Maintain InventoryItem records.
    - Create immutable StockMovement records.
    - Guarantee tenant isolation.

    This service deliberately does NOT contain:
    - AI logic
    - WebSocket logic
    - HTTP logic
    - OpenAI logic
    - WhatsApp logic

    Those concerns belong in their respective layers.
    """

    INVENTORY_LOCATIONS = frozenset(
        {
            "HOME",
            "SHOP",
            "WAREHOUSE",
        }
    )

    MOVEMENT_LOCATIONS = frozenset(
        {
            "HOME",
            "SHOP",
            "WAREHOUSE",
            "EXTERNAL",
        }
    )

    INTERNAL_LOCATIONS = frozenset(
        {
            "HOME",
            "SHOP",
            "WAREHOUSE",
        }
    )

    MOVEMENT_TYPE_INCOMING = "INCOMING"
    MOVEMENT_TYPE_TRANSFER = "TRANSFER"
    MOVEMENT_TYPE_OUTGOING = "OUTGOING"
    MOVEMENT_TYPE_ADJUSTMENT = "ADJUSTMENT"

    # ------------------------------------------------------------------
    # Product resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_business(business: Business) -> None:
        """
        Validate that a business object was supplied.

        Tenant isolation depends on every inventory query being scoped
        through this business.
        """
        if business is None:
            raise InventoryServiceError(
                "A valid business is required for inventory operations."
            )

    @classmethod
    def _normalize_product_query(cls, value: str) -> str:
        """
        Normalize user/AI supplied product search text.
        """
        if not isinstance(value, str):
            raise ProductNotFoundError(
                "Product name must be a text value."
            )

        value = value.strip()

        if not value:
            raise ProductNotFoundError(
                "Product name cannot be empty."
            )

        return value

    @classmethod
    def resolve_product(
        cls,
        business: Business,
        *,
        product_id: Optional[int] = None,
        product_name: Optional[str] = None,
    ) -> Product:
        """
        Resolve exactly one product belonging to the supplied business.

        Preferred resolution order:
        1. product_id
        2. product_name

        Product IDs are preferred for internal calls because they are
        deterministic.

        Product names are supported for AI/voice commands.
        """

        cls._validate_business(business)

        if product_id is not None:
            try:
                product = Product.objects.get(
                    id=product_id,
                    business=business,
                )
            except Product.DoesNotExist as exc:
                raise ProductNotFoundError(
                    f"Product with id {product_id} was not found."
                ) from exc

            return product

        if not product_name:
            raise ProductNotFoundError(
                "Either product_id or product_name is required."
            )

        normalized_name = cls._normalize_product_query(product_name)

        products = Product.objects.filter(
            business=business,
            name__iexact=normalized_name,
        )

        count = products.count()

        if count == 1:
            return products.get()

        if count > 1:
            raise ProductAmbiguousError(
                f"Multiple products named '{normalized_name}' exist. "
                "Please specify the product details."
            )

        # Fall back to partial matching only when exact matching failed.
        products = Product.objects.filter(
            business=business,
            name__icontains=normalized_name,
        )

        count = products.count()

        if count == 1:
            return products.get()

        if count > 1:
            matches = list(
                products.values_list("name", flat=True)[:5]
            )

            raise ProductAmbiguousError(
                f"Multiple products match '{normalized_name}': "
                f"{', '.join(matches)}. "
                "Please specify the exact product."
            )

        raise ProductNotFoundError(
            f"No product matching '{normalized_name}' was found."
        )

    # ------------------------------------------------------------------
    # Location validation
    # ------------------------------------------------------------------

    @classmethod
    def _validate_internal_location(cls, location: str) -> str:
        """
        Validate a physical inventory location.
        """
        if not isinstance(location, str):
            raise InvalidLocationError(
                "Inventory location must be a string."
            )

        location = location.strip().upper()

        if location not in cls.INTERNAL_LOCATIONS:
            raise InvalidLocationError(
                f"Invalid inventory location '{location}'. "
                f"Allowed locations: "
                f"{', '.join(sorted(cls.INTERNAL_LOCATIONS))}."
            )

        return location

    @classmethod
    def _validate_movement_location(cls, location: str) -> str:
        """
        Validate a StockMovement location.

        EXTERNAL is allowed here because StockMovement supports
        inventory leaving or entering the business.
        """
        if not isinstance(location, str):
            raise InvalidLocationError(
                "Movement location must be a string."
            )

        location = location.strip().upper()

        if location not in cls.MOVEMENT_LOCATIONS:
            raise InvalidLocationError(
                f"Invalid movement location '{location}'. "
                f"Allowed locations: "
                f"{', '.join(sorted(cls.MOVEMENT_LOCATIONS))}."
            )

        return location

    @staticmethod
    def _validate_quantity(quantity: int) -> int:
        """
        Validate a stock quantity.

        Inventory quantities are integers and must always be positive
        for movement operations.
        """
        if isinstance(quantity, bool):
            raise InvalidQuantityError(
                "Quantity must be a positive integer."
            )

        if not isinstance(quantity, int):
            raise InvalidQuantityError(
                "Quantity must be a positive integer."
            )

        if quantity <= 0:
            raise InvalidQuantityError(
                "Quantity must be greater than zero."
            )

        return quantity

    # ------------------------------------------------------------------
    # Inventory item helpers
    # ------------------------------------------------------------------

    @classmethod
    def _get_inventory_item_for_update(
        cls,
        *,
        business: Business,
        product: Product,
        location: str,
        create_if_missing: bool = True,
    ) -> InventoryItem:
        """
        Retrieve an InventoryItem while locking its database row.

        select_for_update() is critical here because multiple users,
        API requests, or AI commands could modify the same stock
        simultaneously.
        """

        location = cls._validate_internal_location(location)

        try:
            return (
                InventoryItem.objects
                .select_for_update()
                .get(
                    business=business,
                    product=product,
                    location=location,
                )
            )
        except InventoryItem.DoesNotExist:
            if not create_if_missing:
                raise InventoryServiceError(
                    f"No inventory record exists for "
                    f"'{product.name}' at {location}."
                )

            return InventoryItem.objects.create(
                business=business,
                product=product,
                location=location,
                quantity=0,
            )

    # ------------------------------------------------------------------
    # Inventory queries
    # ------------------------------------------------------------------

    @classmethod
    def get_stock(
        cls,
        business: Business,
        *,
        product_id: Optional[int] = None,
        product_name: Optional[str] = None,
        location: Optional[str] = None,
    ) -> dict:
        """
        Return current stock for a product.

        If location is supplied, only that location is returned.

        If location is omitted, all physical locations are returned.
        """

        cls._validate_business(business)

        product = cls.resolve_product(
            business,
            product_id=product_id,
            product_name=product_name,
        )

        queryset = InventoryItem.objects.filter(
            business=business,
            product=product,
        )

        if location:
            location = cls._validate_internal_location(location)
            queryset = queryset.filter(location=location)

        queryset = queryset.order_by("location")

        stock = {
            item.location: item.quantity
            for item in queryset
        }

        total = sum(stock.values())

        return {
            "product_id": product.id,
            "product_name": product.name,
            "locations": stock,
            "total_quantity": total,
        }

    @classmethod
    def list_inventory(
        cls,
        business: Business,
        *,
        location: Optional[str] = None,
    ) -> QuerySet[InventoryItem]:
        """
        Return inventory records for a business.

        This method returns a QuerySet so API layers can add pagination
        or additional filtering without moving database logic into
        consumers.
        """

        cls._validate_business(business)

        queryset = (
            InventoryItem.objects
            .filter(business=business)
            .select_related("product")
            .order_by("product__name", "location")
        )

        if location:
            location = cls._validate_internal_location(location)
            queryset = queryset.filter(location=location)

        return queryset

    # ------------------------------------------------------------------
    # Transfer
    # ------------------------------------------------------------------

    @classmethod
    @transaction.atomic
    def transfer(
        cls,
        business: Business,
        *,
        product_id: Optional[int] = None,
        product_name: Optional[str] = None,
        quantity: int,
        source_location: str,
        destination_location: str,
        notes: Optional[str] = None,
    ) -> InventoryOperationResult:
        """
        Atomically transfer stock between two internal locations.

        Example:

            WAREHOUSE -> SHOP
            quantity = 20

        Database result:

            warehouse = warehouse - 20
            shop      = shop + 20
            movement  = TRANSFER

        If any part fails, the entire transaction rolls back.
        """

        cls._validate_business(business)

        quantity = cls._validate_quantity(quantity)

        source_location = cls._validate_internal_location(
            source_location
        )

        destination_location = cls._validate_internal_location(
            destination_location
        )

        if source_location == destination_location:
            raise SameLocationTransferError(
                "Source and destination locations must be different."
            )

        product = cls.resolve_product(
            business,
            product_id=product_id,
            product_name=product_name,
        )

        # Lock both rows in deterministic location order.
        #
        # This helps reduce the chance of deadlocks when two concurrent
        # requests transfer stock in opposite directions.
        locations = sorted(
            [source_location, destination_location]
        )

        items = {}

        for location in locations:
            items[location] = cls._get_inventory_item_for_update(
                business=business,
                product=product,
                location=location,
            )

        source_item = items[source_location]
        destination_item = items[destination_location]

        if source_item.quantity < quantity:
            raise InsufficientStockError(
                f"Insufficient stock for '{product.name}' at "
                f"{source_location}. "
                f"Available: {source_item.quantity}, "
                f"requested: {quantity}."
            )

        source_item.quantity -= quantity
        destination_item.quantity += quantity

        source_item.save(
            update_fields=[
                "quantity",
                "last_updated",
            ]
        )

        destination_item.save(
            update_fields=[
                "quantity",
                "last_updated",
            ]
        )

        movement = StockMovement.objects.create(
            business=business,
            product=product,
            quantity=quantity,
            movement_type=cls.MOVEMENT_TYPE_TRANSFER,
            source_location=source_location,
            destination_location=destination_location,
            notes=notes or "Inventory transfer.",
        )

        return InventoryOperationResult(
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            source_location=source_location,
            destination_location=destination_location,
            movement_type=cls.MOVEMENT_TYPE_TRANSFER,
            source_quantity_after=source_item.quantity,
            destination_quantity_after=destination_item.quantity,
            movement_id=movement.id,
        )

    # ------------------------------------------------------------------
    # Outgoing stock
    # ------------------------------------------------------------------

    @classmethod
    @transaction.atomic
    def dispatch(
        cls,
        business: Business,
        *,
        product_id: Optional[int] = None,
        product_name: Optional[str] = None,
        quantity: int,
        source_location: str,
        notes: Optional[str] = None,
    ) -> InventoryOperationResult:
        """
        Remove stock from an internal location and dispatch it externally.

        Example:

            WAREHOUSE -> EXTERNAL
            quantity = 20

        This is appropriate for:
        - customer dispatch
        - wholesale sale
        - delivery
        - shipment
        """

        cls._validate_business(business)

        quantity = cls._validate_quantity(quantity)

        source_location = cls._validate_internal_location(
            source_location
        )

        product = cls.resolve_product(
            business,
            product_id=product_id,
            product_name=product_name,
        )

        source_item = cls._get_inventory_item_for_update(
            business=business,
            product=product,
            location=source_location,
        )

        if source_item.quantity < quantity:
            raise InsufficientStockError(
                f"Insufficient stock for '{product.name}' at "
                f"{source_location}. "
                f"Available: {source_item.quantity}, "
                f"requested: {quantity}."
            )

        source_item.quantity -= quantity

        source_item.save(
            update_fields=[
                "quantity",
                "last_updated",
            ]
        )

        movement = StockMovement.objects.create(
            business=business,
            product=product,
            quantity=quantity,
            movement_type=cls.MOVEMENT_TYPE_OUTGOING,
            source_location=source_location,
            destination_location="EXTERNAL",
            notes=notes or "Stock dispatched externally.",
        )

        return InventoryOperationResult(
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            source_location=source_location,
            destination_location="EXTERNAL",
            movement_type=cls.MOVEMENT_TYPE_OUTGOING,
            source_quantity_after=source_item.quantity,
            destination_quantity_after=None,
            movement_id=movement.id,
        )

    # ------------------------------------------------------------------
    # Incoming stock
    # ------------------------------------------------------------------

    @classmethod
    @transaction.atomic
    def receive(
        cls,
        business: Business,
        *,
        product_id: Optional[int] = None,
        product_name: Optional[str] = None,
        quantity: int,
        destination_location: str,
        notes: Optional[str] = None,
    ) -> InventoryOperationResult:
        """
        Add newly received stock to an internal location.

        Example:

            EXTERNAL -> WAREHOUSE
            quantity = 100
        """

        cls._validate_business(business)

        quantity = cls._validate_quantity(quantity)

        destination_location = cls._validate_internal_location(
            destination_location
        )

        product = cls.resolve_product(
            business,
            product_id=product_id,
            product_name=product_name,
        )

        destination_item = cls._get_inventory_item_for_update(
            business=business,
            product=product,
            location=destination_location,
        )

        destination_item.quantity += quantity

        destination_item.save(
            update_fields=[
                "quantity",
                "last_updated",
            ]
        )

        movement = StockMovement.objects.create(
            business=business,
            product=product,
            quantity=quantity,
            movement_type=cls.MOVEMENT_TYPE_INCOMING,
            source_location="EXTERNAL",
            destination_location=destination_location,
            notes=notes or "Stock received.",
        )

        return InventoryOperationResult(
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            source_location="EXTERNAL",
            destination_location=destination_location,
            movement_type=cls.MOVEMENT_TYPE_INCOMING,
            source_quantity_after=None,
            destination_quantity_after=destination_item.quantity,
            movement_id=movement.id,
        )

    # ------------------------------------------------------------------
    # Inventory adjustment
    # ------------------------------------------------------------------

    @classmethod
    @transaction.atomic
    def adjust(
        cls,
        business: Business,
        *,
        product_id: Optional[int] = None,
        product_name: Optional[str] = None,
        location: str,
        new_quantity: int,
        notes: Optional[str] = None,
    ) -> InventoryOperationResult:
        """
        Set physical inventory to a verified quantity.

        This should be used for:
        - stock counts
        - reconciliation
        - correcting a confirmed counting error

        It should NOT be used as a shortcut for normal sales/transfers.

        Example:

            Current: 95
            Physical count: 90

            Adjustment: -5
            Final: 90
        """

        cls._validate_business(business)

        if isinstance(new_quantity, bool):
            raise InvalidQuantityError(
                "new_quantity must be a non-negative integer."
            )

        if not isinstance(new_quantity, int):
            raise InvalidQuantityError(
                "new_quantity must be a non-negative integer."
            )

        if new_quantity < 0:
            raise InvalidQuantityError(
                "new_quantity cannot be negative."
            )

        location = cls._validate_internal_location(location)

        product = cls.resolve_product(
            business,
            product_id=product_id,
            product_name=product_name,
        )

        item = cls._get_inventory_item_for_update(
            business=business,
            product=product,
            location=location,
        )

        previous_quantity = item.quantity
        difference = new_quantity - previous_quantity

        if difference == 0:
            raise InventoryServiceError(
                f"Inventory for '{product.name}' at {location} "
                "is already at the requested quantity."
            )

        item.quantity = new_quantity

        item.save(
            update_fields=[
                "quantity",
                "last_updated",
            ]
        )

        movement = StockMovement.objects.create(
            business=business,
            product=product,
            quantity=abs(difference),
            movement_type=cls.MOVEMENT_TYPE_ADJUSTMENT,
            source_location=location,
            destination_location=location,
            notes=(
                notes
                or (
                    f"Inventory adjustment: "
                    f"{previous_quantity} -> {new_quantity}."
                )
            ),
        )

        return InventoryOperationResult(
            product_id=product.id,
            product_name=product.name,
            quantity=abs(difference),
            source_location=location,
            destination_location=location,
            movement_type=cls.MOVEMENT_TYPE_ADJUSTMENT,
            source_quantity_after=new_quantity,
            destination_quantity_after=new_quantity,
            movement_id=movement.id,
        )

    # ------------------------------------------------------------------
    # Movement history
    # ------------------------------------------------------------------

    @classmethod
    def get_movement_history(
        cls,
        business: Business,
        *,
        product_id: Optional[int] = None,
        limit: int = 50,
    ) -> QuerySet[StockMovement]:
        """
        Return immutable stock movement history for a business.
        """

        cls._validate_business(business)

        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        if limit > 500:
            limit = 500

        queryset = (
            StockMovement.objects
            .filter(business=business)
            .select_related("product")
            .order_by("-timestamp")
        )

        if product_id is not None:
            queryset = queryset.filter(product_id=product_id)

        return queryset[:limit]