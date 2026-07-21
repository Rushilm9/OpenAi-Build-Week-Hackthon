import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  Server,
  WifiOff,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { apiService } from "../services/api";
import logo from "../assets/arthvest-logo.png";

const JUDGE_EMAIL = "judge@arthavest.ai";
const JUDGE_PASSWORD = "OpenAIHack2026!";

type ApiStatus = "checking" | "connected" | "offline";
type SubmitAction = "regular" | "judge" | null;

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitAction, setSubmitAction] = useState<SubmitAction>(null);
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");

  const checkApi = useCallback(async () => {
    setApiStatus("checking");
    try {
      await apiService.healthCheck();
      setApiStatus("connected");
    } catch {
      setApiStatus("offline");
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    apiService.healthCheck().then(
      () => {
        if (isMounted) setApiStatus("connected");
      },
      () => {
        if (isMounted) setApiStatus("offline");
      },
    );
    return () => {
      isMounted = false;
    };
  }, []);

  const signIn = async (loginEmail: string, loginPassword: string, action: Exclude<SubmitAction, null>) => {
    setError("");
    setSubmitAction(action);
    try {
      await login(loginEmail, loginPassword);
      navigate("/", { replace: true });
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(
        errorObj?.response?.data?.detail ||
          errorObj?.message ||
          "We could not reach the ArthVest API. Check the backend and try again.",
      );
    } finally {
      setSubmitAction(null);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("Enter both your email and password.");
      return;
    }
    await signIn(email.trim(), password, "regular");
  };

  const handleJudgeLogin = async () => {
    setEmail(JUDGE_EMAIL);
    setPassword(JUDGE_PASSWORD);
    await signIn(JUDGE_EMAIL, JUDGE_PASSWORD, "judge");
  };

  const isSubmitting = submitAction !== null;

  return (
    <main className="relative min-h-[100dvh] overflow-hidden bg-cream px-4 py-8 sm:py-12">
      <div className="pointer-events-none fixed inset-0 select-none" aria-hidden="true">
        <div className="absolute -right-32 -top-40 h-96 w-96 rounded-full bg-accent/10 blur-3xl" />
        <div className="absolute -bottom-40 -left-32 h-96 w-96 rounded-full bg-accent/10 blur-3xl" />
      </div>

      <div className="relative mx-auto grid w-full max-w-5xl items-stretch overflow-hidden rounded-3xl border border-border bg-white shadow-2xl lg:grid-cols-[0.9fr_1.1fr]">
        <section className="flex flex-col justify-between bg-primary p-7 text-white sm:p-10">
          <div>
            <img src={logo} alt="ArthVest" className="h-20 w-auto rounded-xl bg-white object-contain px-3" />
            <div className="mt-10 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-bold uppercase tracking-wider">
              <KeyRound size={14} /> OpenAI Hackathon Demo
            </div>
            <h1 className="mt-5 max-w-md text-3xl font-bold leading-tight sm:text-4xl">
              Evidence-first market discovery, powered by a live backend.
            </h1>
            <p className="mt-4 max-w-md text-sm leading-6 text-white/70">
              Use the public judge account to experience the complete discovery and analysis workflow.
            </p>
          </div>

          <div className="mt-10 rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Server size={16} /> Backend API
              </div>
              {apiStatus === "checking" && (
                <span className="flex items-center gap-1.5 text-xs text-white/70">
                  <Loader2 size={13} className="animate-spin" /> Checking
                </span>
              )}
              {apiStatus === "connected" && (
                <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-300">
                  <CheckCircle2 size={14} /> Connected
                </span>
              )}
              {apiStatus === "offline" && (
                <button type="button" onClick={() => void checkApi()} className="flex items-center gap-1.5 text-xs font-bold text-amber-300 hover:text-amber-200">
                  <WifiOff size={14} /> Offline · Retry
                </button>
              )}
            </div>
            <p className="mt-2 text-xs leading-5 text-white/60">
              Authentication and market workflows run through the ArthVest API—not a browser-only mock.
            </p>
          </div>
        </section>

        <section className="flex flex-col justify-center p-6 sm:p-10">
          <div className="mb-6">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-accent">Judge access</p>
            <h2 className="mt-2 text-2xl font-bold text-primary">Welcome to ArthVest</h2>
            <p className="mt-2 text-sm text-muted">Sign in instantly with the public hackathon account.</p>
          </div>

          <div className="mb-6 rounded-2xl border border-accent/20 bg-accent/5 p-4">
            <div className="grid gap-3 text-xs sm:grid-cols-2">
              <div>
                <p className="font-bold uppercase tracking-wider text-muted">Email</p>
                <p className="mt-1 break-all font-mono font-semibold text-primary">{JUDGE_EMAIL}</p>
              </div>
              <div>
                <p className="font-bold uppercase tracking-wider text-muted">Password</p>
                <p className="mt-1 font-mono font-semibold text-primary">{JUDGE_PASSWORD}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => void handleJudgeLogin()}
              disabled={isSubmitting || apiStatus === "offline"}
              className="mt-4 flex w-full items-center justify-center gap-2.5 rounded-xl bg-accent px-5 py-3.5 text-sm font-bold text-white shadow-lg shadow-accent/25 transition-all hover:bg-accent-dark disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitAction === "judge" ? <Loader2 size={16} className="animate-spin" /> : <KeyRound size={16} />}
              <span>{submitAction === "judge" ? "Connecting to live demo..." : "Enter live hackathon demo"}</span>
              {submitAction !== "judge" && <ArrowRight size={16} />}
            </button>
          </div>

          <div className="mb-5 flex items-center gap-3" aria-hidden="true">
            <div className="h-px flex-1 bg-border" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted">or use your account</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          {error && (
            <div role="alert" className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-xs font-semibold text-red-800">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="login-email" className="text-xs font-bold uppercase tracking-wider text-muted">Email address</label>
              <input id="login-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" autoComplete="email" className="w-full rounded-xl border border-border px-4 py-3 text-sm font-medium text-primary transition-all placeholder:text-neutral-300 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20" />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="login-password" className="text-xs font-bold uppercase tracking-wider text-muted">Password</label>
              <div className="relative">
                <input id="login-password" type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="••••••••" autoComplete="current-password" className="w-full rounded-xl border border-border px-4 py-3 pr-12 text-sm font-medium text-primary transition-all placeholder:text-neutral-300 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20" />
                <button type="button" onClick={() => setShowPassword((visible) => !visible)} className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-muted transition-colors hover:text-primary" aria-label={showPassword ? "Hide password" : "Show password"}>
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={isSubmitting} className="flex w-full items-center justify-center gap-2 rounded-xl border border-accent px-5 py-3 text-sm font-bold text-accent transition-all hover:bg-accent/5 disabled:cursor-not-allowed disabled:opacity-60">
              {submitAction === "regular" && <Loader2 size={16} className="animate-spin" />}
              <span>{submitAction === "regular" ? "Signing in..." : "Sign in"}</span>
            </button>
          </form>

          <p className="mt-6 text-center text-[10px] font-medium leading-4 text-muted/70">
            Research assistance only. Verify sources before making financial decisions.
          </p>
        </section>
      </div>
    </main>
  );
}
