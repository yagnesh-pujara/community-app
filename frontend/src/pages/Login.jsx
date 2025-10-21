import React, { useState } from "react";
import { login } from "../services/auth";
import { LogIn } from "lucide-react";

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
      onLogin();
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = async (userType) => {
    const credentials = {
      resident: { email: "john@example.com", password: "password123" },
      guard: { email: "guard.mike@example.com", password: "guard123" },
      admin: { email: "admin.sara@example.com", password: "admin123" },
    };

    const cred = credentials[userType];
    setEmail(cred.email);
    setPassword(cred.password);

    try {
      await login(cred.email, cred.password);
      onLogin();
    } catch (err) {
      setError("Quick login failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600">
      <div className="bg-white p-8 rounded-lg shadow-2xl w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Community Management
          </h1>
          <p className="text-gray-600">Sign in to your account</p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="your@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-200 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <LogIn size={20} />
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="mt-6">
          <p className="text-sm text-gray-600 text-center mb-3">
            Quick Login (Demo)
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => quickLogin("resident")}
              className="bg-green-100 text-green-700 py-2 px-3 rounded text-sm hover:bg-green-200 transition"
            >
              Resident
            </button>
            <button
              onClick={() => quickLogin("guard")}
              className="bg-blue-100 text-blue-700 py-2 px-3 rounded text-sm hover:bg-blue-200 transition"
            >
              Guard
            </button>
            <button
              onClick={() => quickLogin("admin")}
              className="bg-purple-100 text-purple-700 py-2 px-3 rounded text-sm hover:bg-purple-200 transition"
            >
              Admin
            </button>
          </div>
        </div>

        <div className="mt-6 text-center text-xs text-gray-500">
          <p>Demo Credentials:</p>
          <p>resident@example.com / password123</p>
        </div>
      </div>
    </div>
  );
}

export default Login;
