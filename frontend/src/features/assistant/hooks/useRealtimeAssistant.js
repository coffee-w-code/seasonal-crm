import { useCallback, useEffect, useRef, useState } from "react";

import { RealtimeSocket } from "../services/realtimeSocket";


export function useRealtimeAssistant(businessId) {
    const socketRef = useRef(null);
    const connectedBusinessIdRef = useRef(null);

    const [connectionState, setConnectionState] = useState(
        "disconnected",
    );

    const [lastEvent, setLastEvent] = useState(null);

    const connect = useCallback(() => {
        if (!businessId) {
            console.error(
                "Cannot connect realtime assistant without businessId.",
            );

            return;
        }

        if (socketRef.current) {
            return;
        }

        const socket = new RealtimeSocket({
            businessId,

            onOpen: () => {
                connectedBusinessIdRef.current = businessId;
                setConnectionState("connected");
            },

            onMessage: (data) => {
                setLastEvent(data);
            },

            onClose: () => {
                socketRef.current = null;
                connectedBusinessIdRef.current = null;

                setConnectionState("disconnected");
            },

            onError: (error) => {
                console.error(
                    "Realtime WebSocket error:",
                    error,
                );

                setConnectionState("error");
            },
        });

        socketRef.current = socket;

        setConnectionState("connecting");

        socket.connect();
    }, [businessId]);

    const disconnect = useCallback(() => {
        const socket = socketRef.current;

        if (!socket) {
            return;
        }

        socket.disconnect();

        socketRef.current = null;
        connectedBusinessIdRef.current = null;

        setConnectionState("disconnected");
    }, []);

    const sendAudio = useCallback((audioBuffer) => {
        socketRef.current?.sendAudio(audioBuffer);
    }, []);

    const sendMessage = useCallback((message) => {
        socketRef.current?.sendMessage(message);
    }, []);

    useEffect(() => {
        const connectedBusinessId =
            connectedBusinessIdRef.current;

        if (
            connectedBusinessId &&
            businessId &&
            connectedBusinessId !== businessId
        ) {
            socketRef.current?.disconnect();

            socketRef.current = null;
            connectedBusinessIdRef.current = null;

            setConnectionState("disconnected");
            setLastEvent(null);
        }
    }, [businessId]);

    useEffect(() => {
        return () => {
            socketRef.current?.disconnect();

            socketRef.current = null;
            connectedBusinessIdRef.current = null;
        };
    }, []);

    return {
        connectionState,
        lastEvent,
        connect,
        disconnect,
        sendAudio,
        sendMessage,
    };
}