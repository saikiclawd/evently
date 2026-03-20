import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Zap } from "lucide-react";
import useAuthStore from "@/store/authStore";
import toast from "react-hot-toast";

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", company_name: "" });
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isRegister) {
        await register(form);
        toast.success("Account created!");
      } else {
        await login(form.email, form.password);
        toast.success("Welcome back!");
      }
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.error || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent to-purple-500 flex items-center justify-center">
            <Zap size={24} className="text-white" />
          </div>
          <div>
            <div className="text-2xl font-extrabold text-gray-100 tracking-tight">Evently</div>
            <div className="text-xs font-semibold text-gray-500 tracking-[0.2em]">PRO</div>
          </div>
        </div>

        {/* Card */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-8">
          <h2 className="text-xl font-bold text-gray-100 mb-1">
            {isRegister ? "Create your account" : "Welcome back"}
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            {isRegister ? "Start your 14-day free trial" : "Sign in to your account"}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <>
                <input
                  type="text" placeholder="Your name" value={form.name} onChange={update("name")}
                  className="w-full px-4 py-3 rounded-lg bg-dark-bg border border-dark-border text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent transition-colors"
                  required
                />
                <input
                  type="text" placeholder="Company name" value={form.company_name} onChange={update("company_name")}
                  className="w-full px-4 py-3 rounded-lg bg-dark-bg border border-dark-border text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent transition-colors"
                />
              </>
            )}
            <input
              type="email" placeholder="Email" value={form.email} onChange={update("email")}
              className="w-full px-4 py-3 rounded-lg bg-dark-bg border border-dark-border text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent transition-colors"
              required
            />
            <input
              type="password" placeholder="Password" value={form.password} onChange={update("password")}
              className="w-full px-4 py-3 rounded-lg bg-dark-bg border border-dark-border text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent transition-colors"
              required minLength={8}
            />
            <button
              type="submit" disabled={loading}
              className="w-full py-3 rounded-lg bg-accent text-white text-sm font-semibold hover:bg-accent/90 transition-colors disabled:opacity-50"
            >
              {loading ? "Loading..." : isRegister ? "Create Account" : "Sign In"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
            <button onClick={() => setIsRegister(!isRegister)} className="text-accent font-semibold hover:underline">
              {isRegister ? "Sign in" : "Start free trial"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
