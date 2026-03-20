import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Zap } from "lucide-react";
import useAuthStore from "@/store/authStore";
import { auth as authApi } from "@/lib/api";
import toast from "react-hot-toast";

function GoogleButton({ onSuccess }) {
  const btnRef = useRef(null);
  const [clientId, setClientId] = useState(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    authApi.googleConfig().then(({ data }) => {
      if (data.enabled) setClientId(data.client_id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!clientId) return;

    // Load Google Identity Services script
    if (document.getElementById("google-gsi")) {
      setLoaded(true);
      return;
    }
    const script = document.createElement("script");
    script.id = "google-gsi";
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => setLoaded(true);
    document.head.appendChild(script);
  }, [clientId]);

  useEffect(() => {
    if (!loaded || !clientId || !btnRef.current) return;

    // Initialize Google Sign-In
    window.google?.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        if (response.credential) {
          onSuccess(response.credential);
        }
      },
    });

    window.google?.accounts.id.renderButton(btnRef.current, {
      type: "standard",
      theme: "filled_black",
      size: "large",
      width: "100%",
      text: "continue_with",
      shape: "rectangular",
      logo_alignment: "center",
    });
  }, [loaded, clientId, onSuccess]);

  if (!clientId) return null;

  return (
    <div>
      <div className="flex items-center gap-3 my-5">
        <div className="flex-1 h-px bg-gray-700" />
        <span className="text-xs text-gray-500">or</span>
        <div className="flex-1 h-px bg-gray-700" />
      </div>
      <div ref={btnRef} className="flex justify-center [&>div]:w-full" />
    </div>
  );
}

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", company_name: "" });
  const [loading, setLoading] = useState(false);
  const { login, register, googleLogin } = useAuthStore();
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

  const handleGoogleSuccess = useCallback(async (credential) => {
    setLoading(true);
    try {
      await googleLogin(credential);
      toast.success("Signed in with Google!");
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.error || "Google sign-in failed");
    } finally {
      setLoading(false);
    }
  }, [googleLogin, navigate]);

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

          {/* Google Sign-In */}
          <GoogleButton onSuccess={handleGoogleSuccess} />

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
