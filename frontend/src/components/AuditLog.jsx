import React, { useState, useEffect } from "react";
import { getEvents } from "../services/events";
import { FileText, Clock } from "lucide-react";

function AuditLog() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const data = await getEvents();
      setEvents(data.events);
    } catch (err) {
      console.error("Failed to load events");
    } finally {
      setLoading(false);
    }
  };

  const getEventColor = (type) => {
    const colors = {
      visitor_created: "bg-blue-100 text-blue-800",
      visitor_approved: "bg-green-100 text-green-800",
      visitor_denied: "bg-red-100 text-red-800",
      visitor_checked_in: "bg-purple-100 text-purple-800",
      visitor_checked_out: "bg-gray-100 text-gray-800",
    };
    return colors[type] || "bg-gray-100 text-gray-800";
  };

  if (loading) {
    return <div className="text-center py-12">Loading audit log...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Audit Log</h2>
        <button
          onClick={loadEvents}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Refresh
        </button>
      </div>

      {events.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <FileText size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500">No events found</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="divide-y divide-gray-200">
            {events.map((event) => (
              <div key={event.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${getEventColor(
                          event.type
                        )}`}
                      >
                        {event.type.replace(/_/g, " ").toUpperCase()}
                      </span>
                      <span className="text-sm text-gray-500 flex items-center gap-1">
                        <Clock size={14} />
                        {new Date(event.timestamp).toLocaleString()}
                      </span>
                    </div>
                    {event.payload && (
                      <div className="text-sm text-gray-600 mt-2">
                        {Object.entries(event.payload).map(([key, value]) => (
                          <div key={key}>
                            <span className="font-medium">{key}:</span> {value}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default AuditLog;
