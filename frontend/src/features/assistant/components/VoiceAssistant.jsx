import { useRealtimeAssistant } from "../hooks/useRealtimeAssistant";
import { useBusiness } from "../../business/BusinessContext";

function VoiceAssistant() {
    const { currentBusiness } = useBusiness();

    const businessId = currentBusiness?.id;

    const {
        connectionState,
        connect,
        disconnect,
    } = useRealtimeAssistant(businessId);

    const isConnected = connectionState === "connected";
    const isConnecting = connectionState === "connecting";

    return (
        <section className="rounded-2xl border border-slate-200 bg-slate-50 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                        AI Voice Assistant
                    </h2>

                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                        Manage your business using voice.
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <span
                        className={[
                            "h-3 w-3 rounded-full",
                            isConnected
                                ? "bg-green-500"
                                : isConnecting
                                  ? "bg-yellow-500"
                                  : "bg-slate-400 dark:bg-slate-600",
                        ].join(" ")}
                    />

                    <span className="text-sm text-slate-500 dark:text-slate-400">
                        {connectionState}
                    </span>
                </div>
            </div>

            <div className="mt-6 flex gap-3">
                {!isConnected ? (
                    <button
                        type="button"
                        onClick={connect}
                        disabled={isConnecting || !businessId}
                        className="rounded-xl bg-purple-600 px-5 py-3 font-medium text-white transition hover:bg-purple-500 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        {isConnecting
                            ? "Connecting..."
                            : "Connect Assistant"}
                    </button>
                ) : (
                    <button
                        type="button"
                        onClick={disconnect}
                        className="rounded-xl bg-red-600 px-5 py-3 font-medium text-white transition hover:bg-red-500"
                    >
                        Disconnect
                    </button>
                )}
            </div>
        </section>
    );
}

export default VoiceAssistant;