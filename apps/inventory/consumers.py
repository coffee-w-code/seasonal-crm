from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from typing import Any

import websockets
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import PermissionDenied

from apps.accounts.context import get_business_membership
from apps.tenants.models import Business

from .ai.tool_router import AIToolRouter
from .ai.tools import get_inventory_tools


logger = logging.getLogger(__name__)


class RealtimeVoiceCRMConsumer(AsyncWebsocketConsumer):
    """
    WebSocket gateway between the CRM frontend and OpenAI Realtime API.

    Responsibilities:
        1. Authenticate the Django user.
        2. Resolve the user's business.
        3. Establish the OpenAI Realtime connection.
        4. Forward microphone audio to OpenAI.
        5. Forward generated audio back to the frontend.
        6. Route AI tool calls into application services.

    Business logic must NOT live here.
    """

    OPENAI_REALTIME_MODEL = os.getenv(
        "OPENAI_REALTIME_MODEL",
        "gpt-realtime",
    )

    OPENAI_REALTIME_URL = (
        "wss://api.openai.com/v1/realtime"
        f"?model={OPENAI_REALTIME_MODEL}"
    )

    MAX_AUDIO_CHUNK_SIZE = 1024 * 1024

    async def connect(self):
        """
        Authenticate the user, resolve the requested business, verify
        active membership, and establish the OpenAI Realtime session.
        """

        self.user = self.scope.get("user")

        self.openai_ws = None
        self.openai_task = None

        # ------------------------------------------------------------------
        # Authentication
        # ------------------------------------------------------------------

        if not self.user or self.user.is_anonymous:
            logger.warning(
                "AI Websocket rejected: unauthenticated user."
            )
            await self.close(code=4001)
            return

        # ------------------------------------------------------------------
        # Resolve business from WebSocket URL
        # ------------------------------------------------------------------

        business_id = (
            self.scope
            .get("url_route", {})
            .get("kwargs", {})
            .get("business_id")
        )

        if not business_id:
            logger.warning(
                "AI WebSocket rejected: missing business_id."
                "user_id=%s",
                self.user.id,
            )

            await self.close(code=4002)
            return

        # ------------------------------------------------------------------
        # Verify tenant membership
        # ------------------------------------------------------------------

        try:
            self.business = await self._get_authorized_business(
            business_id=business_id,
        )
        except Exception:
            logger.exception(
                "Unable to resolve authorized business. "
                "user_id=%s business_id=%s",
                self.user.id,
                business_id,
            )
            await self.close(code=4500)
            return

        if self.business is None:
            logger.warning(
                "AI WebSocket rejected: unauthorized business access. "
                "user_id=%s business_id=%s",
                self.user.id,
                business_id,
            )
            await self.close(code=4003)
            return

        self.business_id = self.business.id

        # ------------------------------------------------------------------
        # OpenAI configuration
        # ------------------------------------------------------------------

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            logger.error(
                "OPENAI_API_KEY is not configured."
                )
            await self.close(code=4500)
            return

        # ------------------------------------------------------------------
        # Connect to OpenAI Realtime API
        # ------------------------------------------------------------------

        try:
            self.openai_ws = await websockets.connect(
                self.OPENAI_REALTIME_URL,
                additional_headers={
                    "Authorization": f"Bearer {api_key}",
                },
                max_size=None,
                ping_interval=20,
                ping_timeout=20,
            )
        except Exception:
            logger.exception(
                "Failed to connect to OpenAI Realtime API. "
                "user_id=%s business_id=%s",
                self.user.id,
                self.business.id,
            )
            await self.close(code=4501)
            return

        # ------------------------------------------------------------------
        # Accept frontend WebSocket
        # ------------------------------------------------------------------

        await self.accept()

        try:
            await self.configure_ai_session()

            self.openai_task = asyncio.create_task(
                self.stream_from_openai()
            )

            logger.info(
                "Realtime CRM session established. "
                "user_id=%s business_id=%s",
                self.user.id,
                self.business.id,
            )

        except Exception:
            logger.exception(
                "Failed to initialize Realtime session. "
                "user_id=%s business_id=%s",
                self.user.id,
                self.business.id,
            )

            await self._close_openai_connection()
            await self.close(code=4502)

    async def disconnect(self, close_code):
        """
        Cleanly terminate the AI session and release resources.
        """

        task = self.openai_task

        if task is not None:
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception(
                    "Error while stopping OpenAI event stream."
                )

            self.openai_task = None

        await self._close_openai_connection()

        logger.info(
            "Realtime CRM session closed. "
            "user_id=%s business_id=%s close_code=%s",
            getattr(self.user, "id", None),
            getattr(
                getattr(self, "business", None),
                "id",
                None,
            ),
            close_code,
        )
    async def receive(self, text_data=None, bytes_data=None):
        """
        Receive messages from the CRM frontend.

        Supported messages:

            Binary:
                raw microphone audio

            JSON:
                control messages
        """

        if bytes_data is not None:
            await self._handle_audio(bytes_data)
            return

        if text_data:
            await self._handle_client_message(text_data)

    async def _handle_audio(self, audio_bytes: bytes):
        """
        Forward microphone audio to OpenAI.

        The frontend should send audio in the format configured for
        the Realtime session.
        """

        if self.openai_ws is None:
            return

        if not audio_bytes:
            return

        if len(audio_bytes) > self.MAX_AUDIO_CHUNK_SIZE:
            logger.warning(
                "Rejected oversized audio chunk. size=%s",
                len(audio_bytes),
            )
            return

        audio_base64 = base64.b64encode(
            audio_bytes
        ).decode("ascii")

        event = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64,
        }

        await self._send_openai_event(event)

    async def _handle_client_message(
        self,
        text_data: str,
    ):

        """
        Handle JSON control messages from the frontend.
        """

        try:
            message = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "code": "invalid_json",
                        "message": "Invalid JSON message.",
                    }
                )
            )
            return

        if not isinstance(message, dict):
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "code": "invalid_message",
                        "message": "Message must be a JSON object.",
                    }
                )
            )
            return

        message_type = message.get("type")

        if message_type in {
            "response.create",
            "input_audio_buffer.commit",
            "response.cancel",
        }:
            await self._send_openai_event(
                {
                    "type": message_type,
                }
            )
            return

        logger.debug(
            "Ignoring unsupported frontend message type: %s",
            message_type,
        )

    # ------------------------------------------------------------------
    # OpenAI session
    # ------------------------------------------------------------------

    async def configure_ai_session(self):
        """
        Configure the OpenAI Realtime session.

        The session defines:
        - AI behavior and instructions
        - Voice output
        - Audio input/output formats
        - Available backend tools
        - Automatic tool selection
        """

        tools = get_inventory_tools()

        instructions = f"""
    You are the voice business assistant for a fishing-net wholesale
    business.

    Business name:
    {self.business.name}

    You help the authenticated business user manage their CRM.

    IMPORTANT RULES:

    1. Keep spoken responses concise and natural.
    2. Understand English, Hindi, and Hinglish.
    3. Respond in the same language the user is using whenever practical.
    4. Never claim that an operation succeeded unless the backend tool
    returned a successful result.
    5. Never invent inventory quantities.
    6. Never invent customers, products, balances, orders, or transactions.
    7. Use backend tools whenever the user asks for real business data.
    8. If a product or business entity is ambiguous, ask for clarification.
    9. If inventory is insufficient, clearly explain the situation.
    10. Never expose internal database IDs unless necessary.
    11. Do not claim a WhatsApp, SMS, order, transfer, dispatch, or other
        business operation was completed unless the backend confirms it.
    12. Treat the authenticated business context as authoritative.
    13. Never attempt to access another business.
    14. Never ask the user to provide or reveal internal database IDs when
        a normal business name or product name is sufficient.

    Examples:

    "Warehouse mein nylon net kitna hai?"
    -> check_inventory

    "Warehouse se shop mein 20 nylon net bhej do."
    -> transfer_inventory

    "Warehouse se Ramesh ko 30 nylon net dispatch kar do."
    -> dispatch_inventory

    "Factory se 100 nylon net warehouse mein aaye hain."
    -> receive_inventory
    """

        session_update = {
            "type": "session.update",
            "session": {
                "modalities": [
                    "audio",
                    "text",
                ],

                "voice": "marin",

                "input_audio_format": "pcm16",

                "output_audio_format": "pcm16",

                "instructions": instructions,

                "tools": tools,

                "tool_choice": "auto",
            },
        }

        await self._send_openai_event(session_update)

        logger.info(
            "OpenAI Realtime session configured. "
            "user_id=%s business_id=%s model=%s",
            self.user.id,
            self.business.id,
            self.OPENAI_REALTIME_MODEL,
        )

    # ------------------------------------------------------------------
    # OpenAI event stream
    # ------------------------------------------------------------------

    async def stream_from_openai(self):
        """
        Consume events from OpenAI Realtime API.
        """

        try:
            async for raw_message in self.openai_ws:
                try:
                    event = json.loads(raw_message)
                except json.JSONDecodeError:
                    logger.warning(
                        "Received invalid JSON from OpenAI."
                    )
                    continue

                await self._handle_openai_event(event)

        except asyncio.CancelledError:
            raise

        except websockets.ConnectionClosed:
            logger.info(
                "OpenAI Realtime connection closed."
            )

        except Exception:
            logger.exception(
                "Unexpected OpenAI streaming error."
            )

    async def _handle_openai_event(
        self,
        event: dict[str, Any],
    ):
        """
        Dispatch OpenAI events to the appropriate handler.
        """

        event_type = event.get("type")

        if event_type == "response.audio.delta":
            await self._forward_audio_to_client(
                event
            )
            return

        if event_type == "response.function_call_arguments.done":
            await self._handle_function_call(
                event
            )
            return

        if event_type == "error":
            await self._handle_openai_error(
                event
            )
            return

        # Forward useful realtime events to frontend.
        if event_type in {
            "response.created",
            "response.done",
            "response.audio.done",
            "conversation.item.created",
            "input_audio_buffer.committed",
            "input_audio_buffer.speech_started",
            "input_audio_buffer.speech_stopped",
        }:
            await self.send(
                text_data=json.dumps(event)
            )

    async def _forward_audio_to_client(
        self,
        event: dict[str, Any],
    ):
        """
        Forward model-generated audio to the browser.
        """

        delta = event.get("delta")

        if not delta:
            return

        try:
            audio_bytes = base64.b64decode(
                delta
            )
        except Exception:
            logger.exception(
                "Failed to decode OpenAI audio delta."
            )
            return

        await self.send(
            bytes_data=audio_bytes
        )

    # ------------------------------------------------------------------
    # AI tools
    # ------------------------------------------------------------------

    async def _handle_function_call(
        self,
        event: dict[str, Any],
    ):
        """
        Execute an AI function through the backend tool router.
        """

        tool_name = event.get("name")
        call_id = event.get("call_id")
        raw_arguments = event.get(
            "arguments",
            "{}",
        )

        if not tool_name or not call_id:
            logger.warning(
                "Malformed AI function call."
            )
            return

        try:
            arguments = json.loads(
                raw_arguments
            )
        except json.JSONDecodeError:
            output = json.dumps(
                {
                    "status": "error",
                    "error_code": "INVALID_TOOL_ARGUMENTS",
                    "message": (
                        "The AI generated invalid tool arguments."
                    ),
                }
            )

            await self._send_function_output(
                call_id,
                output,
            )

            return

        if not isinstance(arguments, dict):
            output = json.dumps(
                {
                    "status": "error",
                    "error_code": "INVALID_TOOL_ARGUMENTS",
                    "message": (
                        "Tool arguments must be a JSON object."
                    ),
                }
            )

            await self._send_function_output(
                call_id,
                output,
            )

            return

        logger.info(
            "Executing AI tool. "
            "tool=%s business_id=%s",
            tool_name,
            self.business.id,
        )

        router = AIToolRouter(
            business=self.business
        )

        output = await sync_to_async(
            router.execute,
            thread_sensitive=True,
        )(
            tool_name,
            arguments,
        )

        await self._send_function_output(
            call_id,
            output,
        )

        await self._send_openai_event(
            {
                "type": "response.create",
            }
        )

    async def _send_function_output(
        self,
        call_id: str,
        output: str,
    ):
        """
        Send backend tool result back into the AI conversation.
        """

        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": output,
            },
        }

        await self._send_openai_event(
            event
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @sync_to_async
    def _get_authorized_business(
        self,
        *,
        business_id: int | str,
    ) -> Business | None:
        """
        Resolve a business only when the authenticated user has
        an active membership in that business.

        The business_id comes from the WebSocket route, so this is
        intentionally a specific-business authorization check.

        Authorization is delegated to the central business-context
        helper. The realtime consumer must not maintain its own
        membership rules.
        """

        try:
            membership = get_business_membership(
                user=self.user,
                business_id=business_id,
            )
        except PermissionDenied:
            return None

        return membership.business

    async def _send_openai_event(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Send an event to the OpenAI Realtime WebSocket.

        Raises RuntimeError when the OpenAI connection is unavailable
        so callers can handle the failure explicitly.
        """

        websocket = getattr(self, "openai_ws", None)

        if websocket is None:
            raise RuntimeError(
                "OpenAI Realtime connection is not available."
            )

        try:
            await websocket.send(json.dumps(event))

        except websockets.ConnectionClosed as exc:
            logger.error(
                "OpenAI WebSocket closed while sending event. "
                "user_id=%s business_id=%s event_type=%s",
                getattr(self.user, "id", None),
                getattr(self.business, "id", None),
                event.get("type"),
            )

            raise RuntimeError(
                "OpenAI Realtime connection was closed."
            ) from exc


    async def _handle_openai_error(
        self,
        event: dict[str, Any],
    ):
        """
        Log OpenAI errors server-side and send a safe error to frontend.
        """

        logger.error(
            "OpenAI Realtime error: %s",
            event,
        )

        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "code": "realtime_api_error",
                    "message": (
                        "The voice assistant encountered "
                        "a temporary error."
                    ),
                }
            )
        )

    async def _close_openai_connection(self):
        """
        Close the OpenAI connection safely.
        """

        websocket = getattr(
            self,
            "openai_ws",
            None,
        )

        if websocket is None:
            return

        try:
            await websocket.close()
        except Exception:
            logger.exception(
                "Error while closing OpenAI WebSocket."
            )
        finally:
            self.openai_ws = None
