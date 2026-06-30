import { useState, useEffect, useRef } from "react";
import { getWsUrl } from "../services/websocket";

export function useAdminSocket() {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("CONNECTING"); // CONNECTING, CONNECTED, DISCONNECTED, ERROR
  const retryCount = useRef(0);
  const maxRetries = 5;

  useEffect(() => {
    let ws = null;
    let timeoutId = null;
    let isMounted = true;

    const connect = () => {
      ws = new WebSocket(getWsUrl("/ws/admin"));

      ws.onopen = () => {
        if (!isMounted) return;
        setStatus("CONNECTED");
        retryCount.current = 0;
      };

      ws.onmessage = (event) => {
        if (!isMounted) return;
        const data = JSON.parse(event.data);
        setEvents((prev) => [data, ...prev].slice(0, 50));
      };

      ws.onclose = () => {
        if (!isMounted) return;
        setStatus("DISCONNECTED");
        if (retryCount.current < maxRetries) {
          const delay = Math.min(3000 * Math.pow(2, retryCount.current), 60000);
          retryCount.current += 1;
          timeoutId = setTimeout(connect, delay);
        } else {
          setStatus("ERROR");
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
      if (ws) ws.close();
    };
  }, []);

  return { events, status };
}
