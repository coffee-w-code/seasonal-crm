import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from apps.accounts.models import BusinessMembership, UserBusinessContext
from apps.customers.models import Customer
from apps.customers.services.customer_service import (
    CustomerHasOrdersError,
    CustomerNotFoundError,
    CustomerService,
)
from apps.orders.models import Order
from apps.tenants.models import Business


User = get_user_model()


class CustomerServiceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business_one = Business.objects.create(
            name="Business One",
            owner_name="Owner One",
        )

        cls.business_two = Business.objects.create(
            name="Business Two",
            owner_name="Owner Two",
        )

        cls.user = User.objects.create_user(
            username="customer-service-user",
            password="test-password",
        )

        cls.customer_one = Customer.objects.create(
            business=cls.business_one,
            store_name="Store One",
            owner_name="Customer One",
            phone_number="9000000001",
            state_region="Uttar Pradesh",
        )

        cls.customer_two = Customer.objects.create(
            business=cls.business_two,
            store_name="Store Two",
            owner_name="Customer Two",
            phone_number="9000000002",
            state_region="Bihar",
        )

    def test_get_customer_from_correct_business(self):
        customer = CustomerService.get_customer(
            business=self.business_one,
            customer_id=self.customer_one.id,
        )

        self.assertEqual(customer.id, self.customer_one.id)
        self.assertEqual(customer.business_id, self.business_one.id)

    def test_get_customer_from_wrong_business_is_blocked(self):
        with self.assertRaises(CustomerNotFoundError):
            CustomerService.get_customer(
                business=self.business_two,
                customer_id=self.customer_one.id,
            )

    def test_create_customer_assigns_business(self):
        customer = CustomerService.create_customer(
            business=self.business_one,
            store_name="New Store",
            owner_name="New Owner",
            phone_number="9000000010",
            state_region="Delhi",
        )

        self.assertEqual(customer.business_id, self.business_one.id)
        self.assertEqual(customer.store_name, "New Store")

    def test_delete_customer_without_orders_succeeds(self):
        customer = Customer.objects.create(
            business=self.business_one,
            store_name="Delete Store",
            owner_name="Delete Owner",
            phone_number="9000000011",
            state_region="Punjab",
        )

        CustomerService.delete_customer(
            business=self.business_one,
            customer_id=customer.id,
        )

        self.assertFalse(
            Customer.objects.filter(id=customer.id).exists()
        )

    def test_delete_customer_with_orders_is_blocked(self):
        customer = Customer.objects.create(
            business=self.business_one,
            store_name="Order Store",
            owner_name="Order Owner",
            phone_number="9000000012",
            state_region="Haryana",
        )

        Order.objects.create(
            business=self.business_one,
            customer=customer,
            created_by=self.user,
            subtotal="1000.00",
            discount="0.00",
            tax="0.00",
            total="1000.00",
        )

        with self.assertRaises(CustomerHasOrdersError):
            CustomerService.delete_customer(
                business=self.business_one,
                customer_id=customer.id,
            )

        self.assertTrue(
            Customer.objects.filter(id=customer.id).exists()
        )

    def test_delete_customer_from_wrong_business_is_blocked(self):
        with self.assertRaises(CustomerNotFoundError):
            CustomerService.delete_customer(
                business=self.business_two,
                customer_id=self.customer_one.id,
            )


class CustomerAPITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business_one = Business.objects.create(
            name="API Business One",
            owner_name="API Owner One",
        )

        cls.business_two = Business.objects.create(
            name="API Business Two",
            owner_name="API Owner Two",
        )

        cls.user = User.objects.create_user(
            username="api-customer-user",
            password="test-password",
        )

        cls.other_user = User.objects.create_user(
            username="api-other-user",
            password="test-password",
        )

        BusinessMembership.objects.create(
            user=cls.user,
            business=cls.business_one,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        BusinessMembership.objects.create(
            user=cls.user,
            business=cls.business_two,
            role=BusinessMembership.Role.MANAGER,
            is_active=True,
        )

        BusinessMembership.objects.create(
            user=cls.other_user,
            business=cls.business_two,
            role=BusinessMembership.Role.STAFF,
            is_active=True,
        )

        UserBusinessContext.objects.create(
            user=cls.user,
            current_business=cls.business_one,
        )

        UserBusinessContext.objects.create(
            user=cls.other_user,
            current_business=cls.business_two,
        )

        cls.customer_one = Customer.objects.create(
            business=cls.business_one,
            store_name="API Store One",
            owner_name="API Customer One",
            phone_number="9100000001",
            state_region="Uttar Pradesh",
            gstin="09AAAAA0000A1Z5",
            remaining_balance=Decimal("5000.00"),
        )

        cls.customer_two = Customer.objects.create(
            business=cls.business_two,
            store_name="API Store Two",
            owner_name="API Customer Two",
            phone_number="9100000002",
            state_region="Bihar",
            gstin="10BBBBB0000B1Z5",
            remaining_balance=Decimal("2500.00"),
        )

    def _login(self):
        logged_in = self.client.login(
            username="api-customer-user",
            password="test-password",
        )

        self.assertTrue(logged_in)

    def test_list_requires_authentication(self):
        response = self.client.get("/customers/")

        self.assertEqual(response.status_code, 401)

        data = response.json()

        self.assertEqual(
            data["code"],
            "AUTHENTICATION_REQUIRED",
        )

    def test_create_requires_authentication(self):
        response = self.client.post(
            "/customers/create/",
            data=json.dumps(
                {
                    "store_name": "Unauthenticated Store",
                    "owner_name": "Owner",
                    "phone_number": "9200000001",
                    "state_region": "Delhi",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_list_returns_only_current_business_customers(self):
        self._login()

        response = self.client.get("/customers/")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["status"], "success")

        customer_ids = {
            customer["id"]
            for customer in data["customers"]
        }

        self.assertIn(
            self.customer_one.id,
            customer_ids,
        )

        self.assertNotIn(
            self.customer_two.id,
            customer_ids,
        )

    def test_list_search_filters_current_business(self):
        self._login()

        response = self.client.get(
            "/customers/?search=API Store One"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            len(data["customers"]),
            1,
        )

        self.assertEqual(
            data["customers"][0]["id"],
            self.customer_one.id,
        )

    def test_create_customer_uses_current_business(self):
        self._login()

        response = self.client.post(
            "/customers/create/",
            data=json.dumps(
                {
                    "store_name": "Created Store",
                    "owner_name": "Created Owner",
                    "phone_number": "9200000010",
                    "state_region": "Delhi",
                    "gstin": "07CCCCC0000C1Z5",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(
            data["status"],
            "success",
        )

        customer_id = data["customer"]["id"]

        customer = Customer.objects.get(
            id=customer_id,
        )

        self.assertEqual(
            customer.business_id,
            self.business_one.id,
        )

    def test_create_rejects_unsupported_fields(self):
        self._login()

        response = self.client.post(
            "/customers/create/",
            data=json.dumps(
                {
                    "store_name": "Invalid Store",
                    "owner_name": "Invalid Owner",
                    "phone_number": "9200000011",
                    "state_region": "Delhi",
                    "business_id": self.business_two.id,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()

        self.assertEqual(
            data["code"],
            "INVALID_CUSTOMER",
        )

    def test_create_rejects_duplicate_phone_in_current_business(self):
        self._login()

        response = self.client.post(
            "/customers/create/",
            data=json.dumps(
                {
                    "store_name": "Duplicate Store",
                    "owner_name": "Duplicate Owner",
                    "phone_number": self.customer_one.phone_number,
                    "state_region": "Delhi",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)

        data = response.json()

        self.assertEqual(
            data["code"],
            "DUPLICATE_CUSTOMER",
        )

    def test_detail_returns_current_business_customer(self):
        self._login()

        response = self.client.get(
            f"/customers/{self.customer_one.id}/"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["customer"]["id"],
            self.customer_one.id,
        )

    def test_detail_blocks_cross_business_customer(self):
        self._login()

        response = self.client.get(
            f"/customers/{self.customer_two.id}/"
        )

        self.assertEqual(response.status_code, 404)

        data = response.json()

        self.assertEqual(
            data["code"],
            "CUSTOMER_NOT_FOUND",
        )

    def test_update_customer_succeeds(self):
        self._login()

        response = self.client.patch(
            f"/customers/{self.customer_one.id}/update/",
            data=json.dumps(
                {
                    "store_name": "Updated Store",
                    "owner_name": "Updated Owner",
                    "phone_number": "9300000001",
                    "state_region": "Rajasthan",
                    "gstin": "08DDDDD0000D1Z5",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        self.customer_one.refresh_from_db()

        self.assertEqual(
            self.customer_one.store_name,
            "Updated Store",
        )

        self.assertEqual(
            self.customer_one.owner_name,
            "Updated Owner",
        )

        self.assertEqual(
            self.customer_one.phone_number,
            "9300000001",
        )

    def test_update_blocks_cross_business_customer(self):
        self._login()

        response = self.client.patch(
            f"/customers/{self.customer_two.id}/update/",
            data=json.dumps(
                {
                    "store_name": "Should Not Update",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

        data = response.json()

        self.assertEqual(
            data["code"],
            "CUSTOMER_NOT_FOUND",
        )

    def test_remaining_balance_cannot_be_modified(self):
        self._login()

        original_balance = self.customer_one.remaining_balance

        response = self.client.patch(
            f"/customers/{self.customer_one.id}/update/",
            data=json.dumps(
                {
                    "store_name": "Balance Test Store",
                    "remaining_balance": "999999.00",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()

        self.assertEqual(
            data["code"],
            "INVALID_CUSTOMER",
        )

        self.customer_one.refresh_from_db()

        self.assertEqual(
            self.customer_one.remaining_balance,
            original_balance,
        )

    def test_delete_customer_succeeds(self):
        self._login()

        customer = Customer.objects.create(
            business=self.business_one,
            store_name="Delete API Store",
            owner_name="Delete API Owner",
            phone_number="9400000001",
            state_region="Punjab",
        )

        response = self.client.delete(
            f"/customers/{customer.id}/delete/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Customer.objects.filter(
                id=customer.id
            ).exists()
        )

    def test_delete_blocks_cross_business_customer(self):
        self._login()

        response = self.client.delete(
            f"/customers/{self.customer_two.id}/delete/"
        )

        self.assertEqual(response.status_code, 404)

        data = response.json()

        self.assertEqual(
            data["code"],
            "CUSTOMER_NOT_FOUND",
        )

    def test_delete_customer_with_orders_returns_conflict(self):
        self._login()

        customer = Customer.objects.create(
            business=self.business_one,
            store_name="Protected API Store",
            owner_name="Protected API Owner",
            phone_number="9400000002",
            state_region="Haryana",
        )

        Order.objects.create(
            business=self.business_one,
            customer=customer,
            created_by=self.user,
            subtotal="1500.00",
            discount="0.00",
            tax="0.00",
            total="1500.00",
        )

        response = self.client.delete(
            f"/customers/{customer.id}/delete/"
        )

        self.assertEqual(response.status_code, 409)

        data = response.json()

        self.assertEqual(
            data["code"],
            "CUSTOMER_HAS_ORDERS",
        )

        self.assertTrue(
            Customer.objects.filter(
                id=customer.id
            ).exists()
        )

    def test_invalid_json_returns_bad_request(self):
        self._login()

        response = self.client.post(
            "/customers/create/",
            data="{invalid-json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()

        self.assertEqual(
            data["code"],
            "INVALID_CUSTOMER",
        )


class CustomerCSRFSecurityTestCase(TestCase):
    """
    Explicitly tests Django CSRF protection for
    state-changing Customer API endpoints.

    These tests use a Django test client with
    enforce_csrf_checks=True so that @csrf_protect
    behaves like it does for a real browser request.
    """

    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(
            name="CSRF Test Business",
            owner_name="CSRF Test Owner",
        )

        cls.user = User.objects.create_user(
            username="csrf-customer-user",
            password="test-password",
        )

        BusinessMembership.objects.create(
            user=cls.user,
            business=cls.business,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        UserBusinessContext.objects.create(
            user=cls.user,
            current_business=cls.business,
        )

        cls.customer = Customer.objects.create(
            business=cls.business,
            store_name="CSRF Store",
            owner_name="CSRF Owner",
            phone_number="9500000001",
            state_region="Uttar Pradesh",
        )

    def setUp(self):
        self.client = Client(
            enforce_csrf_checks=True,
        )

    def _login(self):
        logged_in = self.client.login(
            username="csrf-customer-user",
            password="test-password",
        )

        self.assertTrue(logged_in)

    def _get_csrf_token(self):
        """
        Request the application's CSRF endpoint.

        The endpoint should create/set the csrftoken cookie
        used by browser clients.
        """

        response = self.client.get(
            "/api/auth/csrf/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        token = self.client.cookies.get("csrftoken")

        self.assertIsNotNone(
            token,
            "The CSRF endpoint did not set a csrftoken cookie.",
        )

        return token.value

    def test_create_rejected_without_csrf_token(self):
        self._login()

        response = self.client.post(
            "/customers/create/",
            data=json.dumps(
                {
                    "store_name": "No CSRF Store",
                    "owner_name": "No CSRF Owner",
                    "phone_number": "9500000010",
                    "state_region": "Delhi",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_create_succeeds_with_valid_csrf_token(self):
        self._login()

        csrf_token = self._get_csrf_token()

        response = self.client.post(
            "/customers/create/",
            data=json.dumps(
                {
                    "store_name": "Valid CSRF Store",
                    "owner_name": "Valid CSRF Owner",
                    "phone_number": "9500000011",
                    "state_region": "Delhi",
                }
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            Customer.objects.filter(
                business=self.business,
                phone_number="9500000011",
            ).exists()
        )

    def test_update_rejected_without_csrf_token(self):
        self._login()

        response = self.client.patch(
            f"/customers/{self.customer.id}/update/",
            data=json.dumps(
                {
                    "store_name": "Should Be Rejected",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.customer.refresh_from_db()

        self.assertEqual(
            self.customer.store_name,
            "CSRF Store",
        )

    def test_update_succeeds_with_valid_csrf_token(self):
        self._login()

        csrf_token = self._get_csrf_token()

        response = self.client.patch(
            f"/customers/{self.customer.id}/update/",
            data=json.dumps(
                {
                    "store_name": "Valid CSRF Update",
                }
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.customer.refresh_from_db()

        self.assertEqual(
            self.customer.store_name,
            "Valid CSRF Update",
        )

    def test_delete_rejected_without_csrf_token(self):
        self._login()

        response = self.client.delete(
            f"/customers/{self.customer.id}/delete/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertTrue(
            Customer.objects.filter(
                id=self.customer.id
            ).exists()
        )

    def test_delete_succeeds_with_valid_csrf_token(self):
        self._login()

        csrf_token = self._get_csrf_token()

        response = self.client.delete(
            f"/customers/{self.customer.id}/delete/",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Customer.objects.filter(
                id=self.customer.id
            ).exists()
        )