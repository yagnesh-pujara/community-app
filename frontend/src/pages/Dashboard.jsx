import React, { useState, useEffect } from "react";
import { getUser } from "../services/auth";
import {
  LogOut,
  UserPlus,
  Users,
  MessageSquare,
  CheckCircle,
  XCircle,
  LogIn as LogInIcon,
  LogOut as LogOutIcon,
  Clock,
  FileText,
} from "lucide-react";
import VisitorsList from "../components/VisitorsList";
import CreateVisitor from "../components/CreateVisitor";
import ChatInterface from "../components/ChatInterface";
import AuditLog from "../components/AuditLog";

function Dashboard({ onLogout }) {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("visitors");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const userData = getUser();
    setUser(userData);
  }, []);

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading...
      </div>
    );
  }

  const isResident = user.roles?.includes("resident");
  const isGuard = user.roles?.includes("guard");
  const isAdmin = user.roles?.includes("admin");

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Community Management
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Welcome, {user.display_name}
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                  {user.roles?.join(", ")}
                </span>
              </p>
            </div>
            <button
              onClick={onLogout}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
            >
              <LogOut size={18} />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab("visitors")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "visitors"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <Users className="inline mr-2" size={18} />
              Visitors
            </button>

            {!isGuard && (
              <button
                onClick={() => setActiveTab("create")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "create"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <UserPlus className="inline mr-2" size={18} />
                Create Visitor
              </button>
            )}

            <button
              onClick={() => setActiveTab("chat")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "chat"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <MessageSquare className="inline mr-2" size={18} />
              AI Copilot
            </button>

            <button
              onClick={() => setActiveTab("audit")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "audit"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <FileText className="inline mr-2" size={18} />
              Audit Log
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "visitors" && (
          <VisitorsList
            key={refreshKey}
            user={user}
            onRefresh={handleRefresh}
          />
        )}
        {activeTab === "create" && isResident && (
          <CreateVisitor
            user={user}
            onSuccess={() => {
              setActiveTab("visitors");
              handleRefresh();
            }}
          />
        )}
        {activeTab === "chat" && (
          <ChatInterface user={user} onActionComplete={handleRefresh} />
        )}
        {activeTab === "audit" && <AuditLog />}
      </div>
    </div>
  );
}

export default Dashboard;
