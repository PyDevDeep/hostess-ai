import { useAdminSocket } from "../hooks/useAdminSocket";
import BookingTable from "./BookingTable";

export default function AdminDashboard() {
  const { events, status } = useAdminSocket();

  return (
    <div className="w-full max-w-4xl bg-white border rounded-xl shadow-sm overflow-hidden">
      <div className="p-4 border-b bg-gray-50 flex justify-between items-center">
        <h2 className="text-lg font-bold">Live Admin Dashboard</h2>
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${
            status === "CONNECTED"
              ? "bg-green-100 text-green-800"
              : status === "ERROR"
                ? "bg-red-100 text-red-800"
                : "bg-yellow-100 text-yellow-800"
          }`}
        >
          {status === "ERROR" ? "Server unavailable, refresh the page" : status}
        </span>
      </div>
      <div className="p-0 overflow-x-auto">
        <BookingTable bookings={events} />
      </div>
    </div>
  );
}
