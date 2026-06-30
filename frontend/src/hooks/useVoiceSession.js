import { useState, useRef, useCallback } from "react";
import { getWsUrl } from "../services/websocket";

export function useVoiceSession() {
  const [status, setStatus] = useState("IDLE");
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const streamRef = useRef(null);
  const processorRef = useRef(null);
  const analyserRef = useRef(null);

  const startSession = useCallback(async () => {
    try {
      setStatus("PROCESSING");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const ws = new WebSocket(getWsUrl("/ws/voice"));
      wsRef.current = ws;
      ws.binaryType = "arraybuffer";

      ws.onopen = () => {
        setStatus("RECORDING");
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)(
          { sampleRate: 24000 },
        );
        audioContextRef.current = audioCtx;

        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 2048;
        analyserRef.current = analyser;

        const source = audioCtx.createMediaStreamSource(stream);
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);
        processorRef.current = processor;

        processor.onaudioprocess = (e) => {
          if (ws.readyState === WebSocket.OPEN) {
            const inputData = e.inputBuffer.getChannelData(0);
            const pcm16 = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
              const s = Math.max(-1, Math.min(1, inputData[i]));
              pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
            }
            ws.send(pcm16.buffer);
          }
        };

        source.connect(analyser);
        analyser.connect(processor);
        processor.connect(audioCtx.destination);
      };

      ws.onmessage = async (event) => {
        if (typeof event.data === "string") {
          const msg = JSON.parse(event.data);
          if (msg.type === "session_end") {
            stopSession();
          }
        } else {
          const view = new Int16Array(event.data);
          const audioCtx = audioContextRef.current;
          if (audioCtx) {
            const buffer = audioCtx.createBuffer(1, view.length, 24000);
            const channelData = buffer.getChannelData(0);
            for (let i = 0; i < view.length; i++) {
              channelData[i] = view[i] / 32768;
            }
            const source = audioCtx.createBufferSource();
            source.buffer = buffer;
            source.connect(audioCtx.destination);
            source.start(0);
          }
        }
      };

      ws.onclose = () => stopSession();
      ws.onerror = () => stopSession();
    } catch (error) {
      console.error("Microphone error:", error);
      setStatus("IDLE");
    }
  }, []);

  const stopSession = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    analyserRef.current = null;
    setStatus("IDLE");
  }, []);

  return { status, startSession, stopSession, analyser: analyserRef.current };
}
