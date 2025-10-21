import React, { useState, useEffect } from "react";
import {
  getVisitors,
  approveVisitor,
  denyVisitor,
  checkinVisitor,
  checkoutVisitor,
} from "../services/visitors";
import {
  CheckCircle,
  XCircle,
  LogIn,
  LogOut,
  Clock,
  User,
  Phone,
  MapPin,
} from "lucide-react";

function VisitorsList({ user, onRefresh }) {
  const [visitors, setVisitors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    loadVisitors();
  }, []);

  const loadVisitors = async () => {
    try {
      setLoading(true);
      const data = await getVisitors();
      setVisitors(data);
    } catch (err) {
      setError("Failed to load visitors");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (visitorId) => {
    try {
      setActionLoading(visitorId);
      await approveVisitor(visitorId);
      await loadVisitors();
      onRefresh();
    } catch (err) {
      alert("Failed to approve visitor");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeny = async (visitorId) => {
    const reason = prompt("Enter reason for denial (optional):");
    try {
      setActionLoading(visitorId);
      await denyVisitor(visitorId, reason || "No reason provided");
      await loadVisitors();
      onRefresh();
    } catch (err) {
      alert("Failed to deny visitor");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCheckin = async (visitorId) => {
    try {
      setActionLoading(visitorId);
      await checkinVisitor(visitorId);
      await loadVisitors();
      onRefresh();
    } catch (err) {
      alert("Failed to check in visitor");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCheckout = async (visitorId) => {
    try {
      setActionLoading(visitorId);
      await checkoutVisitor(visitorId);
      await loadVisitors();
      onRefresh();
    } catch (err) {
      alert("Failed to check out visitor");
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: "bg-yellow-100 text-yellow-800",
      approved: "bg-green-100 text-green-800",
      denied: "bg-red-100 text-red-800",
      checked_in: "bg-blue-100 text-blue-800",
      checked_out: "bg-gray-100 text-gray-800",
    };
    return (
      <span
        className={`px-3 py-1 rounded-full text-xs font-medium ${styles[status]}`}
      >
        {status.replace("_", " ").toUpperCase()}
      </span>
    );
  };

  const canApprove = (visitor) => {
    return (
      visitor.status === "pending" &&
      (user.roles?.includes("admin") ||
        user.household_id === visitor.host_household_id)
    );
  };

  const canCheckin = (visitor) => {
    return (
      visitor.status === "approved" &&
      (user.roles?.includes("guard") || user.roles?.includes("admin"))
    );
  };

  const canCheckout = (visitor) => {
    return (
      visitor.status === "checked_in" &&
      (user.roles?.includes("guard") || user.roles?.includes("admin"))
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Loading visitors...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Visitors</h2>
        <button
          onClick={loadVisitors}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Refresh
        </button>
      </div>

      {visitors.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <User size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500">No visitors found</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {visitors.map((visitor) => (
            <div key={visitor.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <User className="text-gray-400" size={20} />
                    <h3 className="text-xl font-semibold text-gray-900">
                      {visitor.name}
                    </h3>
                    {getStatusBadge(visitor.status)}
                  </div>

                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <Phone size={16} />
                      <span>{visitor.phone}</span>
                    </div>
                    {visitor.purpose && (
                      <div className="flex items-center gap-2">
                        <MapPin size={16} />
                        <span>{visitor.purpose}</span>
                      </div>
                    )}
                    {visitor.scheduled_time && (
                      <div className="flex items-center gap-2">
                        <Clock size={16} />
                        <span>
                          Scheduled:{" "}
                          {new Date(visitor.scheduled_time).toLocaleString()}
                        </span>
                      </div>
                    )}
                    {visitor.checked_in_at && (
                      <div className="text-green-600">
                        Checked in:{" "}
                        {new Date(visitor.checked_in_at).toLocaleString()}
                      </div>
                    )}
                    {visitor.checked_out_at && (
                      <div className="text-gray-600">
                        Checked out:{" "}
                        {new Date(visitor.checked_out_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex gap-2 ml-4">
                  {canApprove(visitor) && (
                    <>
                      <button
                        onClick={() => handleApprove(visitor.id)}
                        disabled={actionLoading === visitor.id}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50"
                      >
                        <CheckCircle size={18} />
                        Approve
                      </button>
                      <button
                        onClick={() => handleDeny(visitor.id)}
                        disabled={actionLoading === visitor.id}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50"
                      >
                        <XCircle size={18} />
                        Deny
                      </button>
                    </>
                  )}

                  {canCheckin(visitor) && (
                    <button
                      onClick={() => handleCheckin(visitor.id)}
                      disabled={actionLoading === visitor.id}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                    >
                      <LogIn size={18} />
                      Check In
                    </button>
                  )}

                  {canCheckout(visitor) && (
                    <button
                      onClick={() => handleCheckout(visitor.id)}
                      disabled={actionLoading === visitor.id}
                      className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition disabled:opacity-50"
                    >
                      <LogOut size={18} />
                      Check Out
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default VisitorsList;
