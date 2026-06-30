export default function BookingTable({ bookings }) {
  return (
    <table className="w-full text-left text-sm min-w-max">
      <thead className="bg-gray-50 border-b">
        <tr>
          <th className="p-4 font-medium text-gray-500">Event Type</th>
          <th className="p-4 font-medium text-gray-500">Booking ID</th>
          <th className="p-4 font-medium text-gray-500">Status</th>
          <th className="p-4 font-medium text-gray-500">Raw Data</th>
        </tr>
      </thead>
      <tbody className="divide-y">
        {bookings.length === 0 ? (
          <tr>
            <td colSpan="4" className="p-8 text-center text-gray-400">
              No recent activity
            </td>
          </tr>
        ) : (
          bookings.map((ev, i) => (
            <tr key={i} className="hover:bg-gray-50 transition-colors">
              <td className="p-4 font-semibold text-gray-800">
                {ev.event || "system_event"}
              </td>
              <td className="p-4 font-mono text-gray-500">
                {ev.booking_id || "-"}
              </td>
              <td className="p-4">
                <span
                  className={`px-2 py-1 rounded text-xs font-bold ${
                    ev.status === "Confirmed"
                      ? "bg-green-100 text-green-700"
                      : ev.status === "On Hold"
                        ? "bg-yellow-100 text-yellow-700"
                        : ev.status === "Cancelled"
                          ? "bg-gray-200 text-gray-700"
                          : "bg-blue-50 text-blue-700"
                  }`}
                >
                  {ev.status || "INFO"}
                </span>
              </td>
              <td className="p-4">
                <pre className="text-[10px] text-gray-400 w-64 overflow-hidden text-ellipsis whitespace-nowrap">
                  {JSON.stringify(ev)}
                </pre>
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
