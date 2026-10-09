from __future__ import annotations

from typing import Optional

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.db.models import Q, QuerySet

from apps.customers.models import Customer
from apps.tenants.models import Business


class CustomerServiceError(Exception):
    """Base exception for customer business-rule failures."""


class CustomerNotFoundError(CustomerServiceError):
    """Raised when a customer cannot be found for a business."""


class DuplicateCustomerError(CustomerServiceError):
    """Raised when a customer would duplicate an existing record."""


class InvalidCustomerError(CustomerServiceError):
    """Raised when customer data fails validation."""


class CustomerHasOrdersError(CustomerServiceError):
    """
    Raised when a customer cannot be deleted because
    historical orders still reference that customer.
    """


class CustomerService:
    """
    Application service for customer operations.

    Responsibilities:
    - Validate business context.
    - Enforce tenant isolation.
    - Validate customer input.
    - Create customers.
    - Retrieve customers.
    - Search customers.
    - Update customers.
    - Delete customers safely.

    This service deliberately does NOT contain:
    - HTTP logic
    - React logic
    - AI logic
    - WebSocket logic
    - OpenAI logic
    """

    # ---------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------

    @staticmethod
    def _validate_business(business: Business) -> None:
        """
        Ensure a valid business context exists.

        Every customer query must be scoped to a business.
        """

        if business is None:
            raise CustomerServiceError(
                "A valid business is required for customer operations."
            )

    @staticmethod
    def _validate_customer_id(customer_id: int) -> int:
        """
        Validate a customer ID before querying the database.
        """

        if isinstance(customer_id, bool):
            raise InvalidCustomerError(
                "Customer ID must be a positive integer."
            )

        if not isinstance(customer_id, int):
            raise InvalidCustomerError(
                "Customer ID must be a positive integer."
            )

        if customer_id <= 0:
            raise InvalidCustomerError(
                "Customer ID must be greater than zero."
            )

        return customer_id

    @staticmethod
    def _clean_text(
        value: Optional[str],
        *,
        field_name: str,
        required: bool = False,
        max_length: Optional[int] = None,
    ) -> Optional[str]:
        """
        Normalize and validate text input.
        """

        if value is None:
            if required:
                raise InvalidCustomerError(
                    f"{field_name} is required."
                )

            return None

        if not isinstance(value, str):
            raise InvalidCustomerError(
                f"{field_name} must be text."
            )

        value = value.strip()

        if required and not value:
            raise InvalidCustomerError(
                f"{field_name} cannot be empty."
            )

        if max_length is not None and len(value) > max_length:
            raise InvalidCustomerError(
                f"{field_name} cannot exceed {max_length} characters."
            )

        return value

    @classmethod
    def _validate_customer_data(
        cls,
        *,
        store_name: Optional[str] = None,
        owner_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        state_region: Optional[str] = None,
        gstin: Optional[str] = None,
        partial: bool = False,
    ) -> dict:
        """
        Validate and normalize customer fields.

        When partial=True, only supplied fields are returned.
        """

        data = {}

        if not partial or store_name is not None:
            data["store_name"] = cls._clean_text(
                store_name,
                field_name="Store name",
                required=True,
                max_length=150,
            )

        if not partial or owner_name is not None:
            data["owner_name"] = cls._clean_text(
                owner_name,
                field_name="Owner name",
                required=True,
                max_length=100,
            )

        if not partial or phone_number is not None:
            phone_number = cls._clean_text(
                phone_number,
                field_name="Phone number",
                required=True,
                max_length=15,
            )

            if phone_number and not phone_number.isdigit():
                raise InvalidCustomerError(
                    "Phone number must contain digits only."
                )

            if phone_number and len(phone_number) != 10:
                raise InvalidCustomerError(
                    "Phone number must contain exactly 10 digits."
                )

            data["phone_number"] = phone_number

        if not partial or state_region is not None:
            data["state_region"] = cls._clean_text(
                state_region,
                field_name="State/region",
                required=True,
                max_length=50,
            )

        if not partial or gstin is not None:
            gstin = cls._clean_text(
                gstin,
                field_name="GSTIN",
                required=False,
                max_length=15,
            )

            if gstin:
                gstin = gstin.upper()

                if len(gstin) != 15:
                    raise InvalidCustomerError(
                        "GSTIN must contain exactly 15 characters."
                    )

            data["gstin"] = gstin

        return data

    # ---------------------------------------------------------------
    # Customer resolution
    # ---------------------------------------------------------------

    @classmethod
    def get_customer(
        cls,
        business: Business,
        customer_id: int,
    ) -> Customer:
        """
        Retrieve one customer belonging to the supplied business.

        Tenant isolation is enforced by filtering on BOTH:
        - customer ID
        - business
        """

        cls._validate_business(business)

        customer_id = cls._validate_customer_id(customer_id)

        try:
            return Customer.objects.get(
                id=customer_id,
                business=business,
            )
        except Customer.DoesNotExist as exc:
            raise CustomerNotFoundError(
                "Customer was not found."
            ) from exc

    # ---------------------------------------------------------------
    # Customer listing
    # ---------------------------------------------------------------

    @classmethod
    def list_customers(
        cls,
        business: Business,
        *,
        search: Optional[str] = None,
    ) -> QuerySet[Customer]:
        """
        Return customers belonging only to the supplied business.

        Optional search:
        - store name
        - owner name
        - phone number
        - GSTIN
        - state/region
        """

        cls._validate_business(business)

        queryset = (
            Customer.objects
            .filter(business=business)
            .order_by("store_name", "id")
        )

        if search is not None:
            search = search.strip()

            if search:
                queryset = queryset.filter(
                    Q(store_name__icontains=search)
                    | Q(owner_name__icontains=search)
                    | Q(phone_number__icontains=search)
                    | Q(gstin__icontains=search)
                    | Q(state_region__icontains=search)
                )

        return queryset

    # ---------------------------------------------------------------
    # Customer creation
    # ---------------------------------------------------------------

    @classmethod
    @transaction.atomic
    def create_customer(
        cls,
        business: Business,
        *,
        store_name: str,
        owner_name: str,
        phone_number: str,
        state_region: str,
        gstin: Optional[str] = None,
    ) -> Customer:
        """
        Create a customer belonging to the supplied business.

        The business is supplied by trusted backend context.
        It is never accepted from the frontend request body.
        """

        cls._validate_business(business)

        data = cls._validate_customer_data(
            store_name=store_name,
            owner_name=owner_name,
            phone_number=phone_number,
            state_region=state_region,
            gstin=gstin,
            partial=False,
        )

        duplicate_query = Customer.objects.filter(
            business=business,
            phone_number=data["phone_number"],
        )

        if duplicate_query.exists():
            raise DuplicateCustomerError(
                "A customer with this phone number already exists."
            )

        try:
            return Customer.objects.create(
                business=business,
                **data,
            )
        except IntegrityError as exc:
            raise DuplicateCustomerError(
                "The customer could not be created because "
                "a conflicting customer record already exists."
            ) from exc

    # ---------------------------------------------------------------
    # Customer update
    # ---------------------------------------------------------------

    @classmethod
    @transaction.atomic
    def update_customer(
        cls,
        business: Business,
        customer_id: int,
        *,
        store_name: Optional[str] = None,
        owner_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        state_region: Optional[str] = None,
        gstin: Optional[str] = None,
    ) -> Customer:
        """
        Update an existing customer.

        Only supplied editable fields are changed.

        remaining_balance is deliberately excluded.
        """

        cls._validate_business(business)

        customer = cls.get_customer(
            business,
            customer_id,
        )

        data = cls._validate_customer_data(
            store_name=store_name,
            owner_name=owner_name,
            phone_number=phone_number,
            state_region=state_region,
            gstin=gstin,
            partial=True,
        )

        if not data:
            raise InvalidCustomerError(
                "At least one customer field must be provided."
            )

        if "phone_number" in data:
            duplicate_query = (
                Customer.objects
                .filter(
                    business=business,
                    phone_number=data["phone_number"],
                )
                .exclude(id=customer.id)
            )

            if duplicate_query.exists():
                raise DuplicateCustomerError(
                    "A customer with this phone number already exists."
                )

        for field, value in data.items():
            setattr(customer, field, value)

        try:
            customer.save(
                update_fields=[
                    *data.keys(),
                    "updated_at",
                ]
            )
        except IntegrityError as exc:
            raise DuplicateCustomerError(
                "The customer could not be updated because "
                "a conflicting customer record already exists."
            ) from exc

        return customer

    # ---------------------------------------------------------------
    # Customer deletion
    # ---------------------------------------------------------------

    @classmethod
    @transaction.atomic
    def delete_customer(
        cls,
        business: Business,
        customer_id: int,
    ) -> None:
        """
        Delete a customer belonging to the supplied business.

        Order.customer uses PROTECT, so a customer with existing
        orders cannot be deleted.

        The database protection error is translated into a
        domain-level exception so the HTTP layer does not need
        to understand Django's ProtectedError.
        """

        cls._validate_business(business)

        customer = cls.get_customer(
            business,
            customer_id,
        )

        try:
            customer.delete()

        except ProtectedError as exc:
            raise CustomerHasOrdersError(
                "This customer cannot be deleted because "
                "orders are associated with the customer."
            ) from exc

        except IntegrityError as exc:
            raise CustomerServiceError(
                "The customer could not be deleted."
            ) from exc