from __future__ import annotations

import asyncio
import base64
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from channels.routing import URLRouter

from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import path

from apps.accounts.models import BusinessMembership
from apps.inventory.consumers import RealtimeVoiceCRMConsumer
from apps.tenants.models import Business


User = get_user_model()


class FakeOpenAIWebSocket:
    """
    Fake OpenAI WebSocket used by tests.

    It never connects to the real OpenAI API.
    It only records events sent by the consumer.
    """

    def __init__(self):
        self.sent_messages = []
        self.closed = False

    async def send(self, message):
        self.sent_messages.append(json.loads(message))

    async def close(self):
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        await asyncio.sleep(3600)
        raise StopAsyncIteration


class RealtimeVoiceCRMConsumerTests(TransactionTestCase):
    """
    Tests for RealtimeVoiceCRMConsumer.

    OpenAI is completely mocked.
    These tests never consume OpenAI API credits.
    """

    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )

        self.business = Business.objects.create(
            name="Test Fishing Nets",
            owner_name="Test Owner",
            phone_number="9999999999",
            email="test@example.com",
            state_region="Uttar Pradesh",
            is_active=True,
        )

        BusinessMembership.objects.create(
            user=self.user,
            business=self.business,
            is_active=True,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def communicator(self, business_id=None, user=None):
        """
        Create a WebSocket communicator with the requested Django user.
        """

        if business_id is None:
            business_id = self.business.id

        if user is None:
            user = self.user

        application = URLRouter(
            [
                path(
                    "ws/ai/<int:business_id>/",
                    RealtimeVoiceCRMConsumer.as_asgi(),
                ),
            ]
        )

        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai/{business_id}/",
        )

        # Inject authenticated user into ASGI scope.
        communicator.scope["user"] = user

        return communicator
    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def test_unauthenticated_user_is_rejected(self):
        anonymous_user = SimpleNamespace(
            is_anonymous=True,
            id=None,
        )

        communicator = self.communicator(
            user=anonymous_user,
        )

        connected, close_code = await communicator.connect()

        self.assertFalse(connected)
        self.assertEqual(close_code, 4001)

        await communicator.disconnect()

    # ------------------------------------------------------------------
    # Tenant authorization
    # ------------------------------------------------------------------

    async def test_user_cannot_access_another_business(self):
        another_business = await sync_to_async(
            Business.objects.create
        )(
            name="Another Business",
            owner_name="Another Owner",
            phone_number="8888888888",
            email="another@example.com",
            state_region="Delhi",
            is_active=True,
        )

        communicator = self.communicator(
            business_id=another_business.id,
        )

        connected, close_code = await communicator.connect()

        self.assertFalse(connected)
        self.assertEqual(close_code, 4003)

        await communicator.disconnect()

    async def test_inactive_membership_is_rejected(self):
        membership = await sync_to_async(
            BusinessMembership.objects.get
        )(
            user=self.user,
            business=self.business,
        )

        membership.is_active = False

        await sync_to_async(
            membership.save
        )()

        communicator = self.communicator()

        connected, close_code = await communicator.connect()

        self.assertFalse(connected)
        self.assertEqual(close_code, 4003)

        await communicator.disconnect()

    # ------------------------------------------------------------------
    # OpenAI API key
    # ------------------------------------------------------------------

    async def test_missing_openai_api_key_is_rejected(self):
        with patch.dict(
            "os.environ",
            {},
            clear=True,
        ):
            communicator = self.communicator()

            connected, close_code = await communicator.connect()

            self.assertFalse(connected)
            self.assertEqual(close_code, 4500)

            await communicator.disconnect()

    # ------------------------------------------------------------------
    # OpenAI connection
    # ------------------------------------------------------------------

    async def test_openai_connection_failure_returns_4501(self):
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "test-key"},
        ), patch(
            "apps.inventory.consumers.websockets.connect",
            new=AsyncMock(
                side_effect=Exception("OpenAI unavailable")
            ),
        ):
            communicator = self.communicator()

            connected, close_code = await communicator.connect()

            self.assertFalse(connected)
            self.assertEqual(close_code, 4501)

            await communicator.disconnect()

    # ------------------------------------------------------------------
    # Successful connection
    # ------------------------------------------------------------------

    async def test_successful_connection_configures_openai_session(self):
        fake_openai = FakeOpenAIWebSocket()

        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "test-key"},
        ), patch(
            "apps.inventory.consumers.websockets.connect",
            new=AsyncMock(return_value=fake_openai),
        ), patch(
            "apps.inventory.consumers.get_inventory_tools",
            return_value=[],
        ):

            communicator = self.communicator()

            connected, _ = await communicator.connect()

            self.assertTrue(connected)

            self.assertTrue(
                len(fake_openai.sent_messages) >= 1
            )

            session_update = fake_openai.sent_messages[0]

            self.assertEqual(
                session_update["type"],
                "session.update",
            )

            session = session_update["session"]

            self.assertEqual(
                session["modalities"],
                ["audio", "text"],
            )

            self.assertEqual(
                session["voice"],
                "marin",
            )

            self.assertEqual(
                session["input_audio_format"],
                "pcm16",
            )

            self.assertEqual(
                session["output_audio_format"],
                "pcm16",
            )

            self.assertEqual(
                session["tool_choice"],
                "auto",
            )

            self.assertIn(
                "Test Fishing Nets",
                session["instructions"],
            )

            await communicator.disconnect()

            self.assertTrue(
                fake_openai.closed
            )

    # ------------------------------------------------------------------
    # Audio forwarding
    # ------------------------------------------------------------------

    async def test_binary_audio_is_forwarded_to_openai(self):
        fake_openai = FakeOpenAIWebSocket()

        consumer = RealtimeVoiceCRMConsumer()
        consumer.user = self.user
        consumer.business = self.business
        consumer.openai_ws = fake_openai

        audio = b"test microphone audio"

        await consumer.receive(
            bytes_data=audio,
        )

        expected_base64 = base64.b64encode(
            audio
        ).decode("ascii")

        self.assertEqual(
            len(fake_openai.sent_messages),
            1,
        )

        self.assertEqual(
            fake_openai.sent_messages[0],
            {
                "type": "input_audio_buffer.append",
                "audio": expected_base64,
            },
        )

    async def test_oversized_audio_is_rejected(self):
        fake_openai = FakeOpenAIWebSocket()

        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "test-key"},
        ), patch(
            "apps.inventory.consumers.websockets.connect",
            new=AsyncMock(return_value=fake_openai),
        ), patch(
            "apps.inventory.consumers.get_inventory_tools",
            return_value=[],
        ):

            communicator = self.communicator()

            connected, _ = await communicator.connect()

            self.assertTrue(connected)

            oversized_audio = (
                b"x"
                * (
                    RealtimeVoiceCRMConsumer.MAX_AUDIO_CHUNK_SIZE
                    + 1
                )
            )

            await communicator.send_to(
                bytes_data=oversized_audio,
            )

            audio_events = [
                event
                for event in fake_openai.sent_messages
                if event.get("type")
                == "input_audio_buffer.append"
            ]

            self.assertEqual(
                len(audio_events),
                0,
            )

            await communicator.disconnect()

    # ------------------------------------------------------------------
    # Invalid JSON
    # ------------------------------------------------------------------

    async def test_invalid_json_returns_error(self):
        fake_openai = FakeOpenAIWebSocket()

        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "test-key"},
        ), patch(
            "apps.inventory.consumers.websockets.connect",
            new=AsyncMock(return_value=fake_openai),
        ), patch(
            "apps.inventory.consumers.get_inventory_tools",
            return_value=[],
        ):

            communicator = self.communicator()

            connected, _ = await communicator.connect()

            self.assertTrue(connected)

            await communicator.send_to(
                text_data="this is not json",
            )

            response = await communicator.receive_json_from()

            self.assertEqual(
                response["type"],
                "error",
            )

            self.assertEqual(
                response["code"],
                "invalid_json",
            )

            await communicator.disconnect()

    # ------------------------------------------------------------------
    # Client control messages
    # ------------------------------------------------------------------

    async def test_response_create_is_forwarded(self):
        fake_openai = FakeOpenAIWebSocket()

        consumer = RealtimeVoiceCRMConsumer()
        consumer.user = self.user
        consumer.business = self.business
        consumer.openai_ws = fake_openai

        await consumer.receive(
            text_data=json.dumps(
                {
                    "type": "response.create",
                }
            )
        )

        self.assertEqual(
            fake_openai.sent_messages,
            [
                {
                    "type": "response.create",
                }
            ],
        )

    async def test_audio_commit_is_forwarded(self):
        fake_openai = FakeOpenAIWebSocket()

        consumer = RealtimeVoiceCRMConsumer()
        consumer.user = self.user
        consumer.business = self.business
        consumer.openai_ws = fake_openai

        await consumer.receive(
            text_data=json.dumps(
                {
                    "type": "input_audio_buffer.commit",
                }
            )
        )

        self.assertEqual(
            fake_openai.sent_messages,
            [
                {
                    "type": "input_audio_buffer.commit",
                }
            ],
        )

    async def test_response_cancel_is_forwarded(self):
        fake_openai = FakeOpenAIWebSocket()

        consumer = RealtimeVoiceCRMConsumer()
        consumer.user = self.user
        consumer.business = self.business
        consumer.openai_ws = fake_openai

        await consumer.receive(
            text_data=json.dumps(
                {
                    "type": "response.cancel",
                }
            )
        )

        self.assertEqual(
            fake_openai.sent_messages,
            [
                {
                    "type": "response.cancel",
                }
            ],
        )

    # ------------------------------------------------------------------
    # Direct event handling
    # ------------------------------------------------------------------

    async def test_openai_error_is_forwarded_safely(self):
        consumer = RealtimeVoiceCRMConsumer()

        consumer.user = self.user
        consumer.business = self.business
        consumer.send = AsyncMock()

        event = {
            "type": "error",
            "error": {
                "message": "Internal OpenAI error",
            },
        }

        await consumer._handle_openai_event(event)

        consumer.send.assert_awaited_once()

        sent_payload = json.loads(
            consumer.send.await_args.kwargs["text_data"]
        )

        self.assertEqual(
            sent_payload["type"],
            "error",
        )

        self.assertEqual(
            sent_payload["code"],
            "realtime_api_error",
        )

        # Internal OpenAI error details must not leak.
        self.assertNotIn(
            "Internal OpenAI error",
            sent_payload["message"],
        )

    # ------------------------------------------------------------------
    # Tool argument validation
    # ------------------------------------------------------------------

    async def test_invalid_tool_arguments_return_error(self):
        fake_openai = FakeOpenAIWebSocket()

        consumer = RealtimeVoiceCRMConsumer()

        consumer.user = self.user
        consumer.business = self.business
        consumer.openai_ws = fake_openai

        event = {
            "type": "response.function_call_arguments.done",
            "name": "check_inventory",
            "call_id": "call_123",
            "arguments": "{invalid json",
        }

        await consumer._handle_function_call(event)

        self.assertEqual(
            len(fake_openai.sent_messages),
            1,
        )

        output_event = fake_openai.sent_messages[0]

        self.assertEqual(
            output_event["type"],
            "conversation.item.create",
        )

        output = json.loads(
            output_event["item"]["output"]
        )

        self.assertEqual(
            output["status"],
            "error",
        )

        self.assertEqual(
            output["error_code"],
            "INVALID_TOOL_ARGUMENTS",
        )

    async def test_non_object_tool_arguments_return_error(self):
        fake_openai = FakeOpenAIWebSocket()

        consumer = RealtimeVoiceCRMConsumer()

        consumer.user = self.user
        consumer.business = self.business
        consumer.openai_ws = fake_openai

        event = {
            "type": "response.function_call_arguments.done",
            "name": "check_inventory",
            "call_id": "call_456",
            "arguments": json.dumps(["not", "an", "object"]),
        }

        await consumer._handle_function_call(event)

        self.assertEqual(
            len(fake_openai.sent_messages),
            1,
        )

        output_event = fake_openai.sent_messages[0]

        output = json.loads(
            output_event["item"]["output"]
        )

        self.assertEqual(
            output["status"],
            "error",
        )

        self.assertEqual(
            output["error_code"],
            "INVALID_TOOL_ARGUMENTS",
        )

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    async def test_valid_tool_call_is_sent_to_router(self):
        fake_openai = FakeOpenAIWebSocket()

        consumer = RealtimeVoiceCRMConsumer()

        consumer.user = self.user
        consumer.business = self.business
        consumer.openai_ws = fake_openai

        arguments = {
            "product_name": "Nylon Net",
            "location": "WAREHOUSE",
        }

        router_instance = MagicMock()

        router_instance.execute.return_value = json.dumps(
            {
                "status": "success",
                "quantity": 50,
            }
        )

        with patch(
            "apps.inventory.consumers.AIToolRouter",
            return_value=router_instance,
        ):

            event = {
                "type": "response.function_call_arguments.done",
                "name": "check_inventory",
                "call_id": "call_789",
                "arguments": json.dumps(arguments),
            }

            await consumer._handle_function_call(event)

        router_instance.execute.assert_called_once_with(
            "check_inventory",
            arguments,
        )

        self.assertEqual(
            fake_openai.sent_messages[0]["type"],
            "conversation.item.create",
        )

        self.assertEqual(
            fake_openai.sent_messages[0]["item"]["call_id"],
            "call_789",
        )

        self.assertEqual(
            fake_openai.sent_messages[1]["type"],
            "response.create",
        )

    # ------------------------------------------------------------------
    # Missing function call data
    # ------------------------------------------------------------------

    async def test_malformed_function_call_is_ignored(self):
        fake_openai = FakeOpenAIWebSocket()

        consumer = RealtimeVoiceCRMConsumer()

        consumer.user = self.user
        consumer.business = self.business
        consumer.openai_ws = fake_openai

        event = {
            "type": "response.function_call_arguments.done",
            "name": "check_inventory",
        }

        await consumer._handle_function_call(event)

        self.assertEqual(
            fake_openai.sent_messages,
            [],
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def test_close_openai_connection(self):
        fake_openai = FakeOpenAIWebSocket()

        consumer = RealtimeVoiceCRMConsumer()

        consumer.openai_ws = fake_openai

        await consumer._close_openai_connection()

        self.assertTrue(
            fake_openai.closed
        )

        self.assertIsNone(
            consumer.openai_ws
        )
