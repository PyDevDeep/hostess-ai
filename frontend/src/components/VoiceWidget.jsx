import { useVoiceSession } from "../hooks/useVoiceSession";
import AudioWaveform from "./AudioWaveform";

export default function VoiceWidget() {
  const { status, startSession, stopSession, analyser } = useVoiceSession();

  return (
    <div className="w-full max-w-md p-6 bg-white border rounded-xl shadow-sm text-center">
      <h2 className="text-xl font-bold mb-6">Table Reservation</h2>

      <div className="mb-8">
        <div className="mb-4">
          <AudioWaveform analyser={analyser} />
        </div>
        <p className="mt-4 text-sm font-medium text-gray-600">
          {status === "IDLE" && "Ready to assist"}
          {status === "PROCESSING" && "Connecting to AI..."}
          {status === "RECORDING" && "Listening..."}
        </p>
      </div>

      <button
        onClick={status === "IDLE" ? startSession : stopSession}
        className={`w-full py-3 px-4 rounded-lg font-bold text-white transition-colors ${
          status === "IDLE"
            ? "bg-blue-600 hover:bg-blue-700"
            : "bg-red-600 hover:bg-red-700"
        }`}
      >
        {status === "IDLE" ? "Start Call" : "End Call"}
      </button>
    </div>
  );
}
