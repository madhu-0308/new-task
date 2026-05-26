"use client";

import { useState, FormEvent, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
} from "firebase/auth";
import { auth, googleProvider, isFirebaseConfigured } from "@/firebaseConfig";
import { useAuth } from "@/auth/AuthProvider";

export default function LoginPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/select-service");
  }, [user, loading, router]);

  async function handleEmailAuth(e: FormEvent) {
    e.preventDefault();
    if (!auth) {
      setError("Sign-in is not configured. Add Firebase keys to .env.local and restart the dev server.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      if (mode === "signin") {
        await signInWithEmailAndPassword(auth, email, password);
      } else {
        await createUserWithEmailAndPassword(auth, email, password);
      }
      router.replace("/select-service");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleGoogle() {
    if (!auth || !googleProvider) {
      setError("Sign-in is not configured. Add Firebase keys to .env.local and restart the dev server.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      await signInWithPopup(auth, googleProvider);
      router.replace("/select-service");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sign-in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="px-5 md:px-12 pt-28 md:pt-32 pb-16 min-h-screen flex flex-col items-center justify-center">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-block mb-4">
            <Image
              src="/logo.png"
              alt="Gaara AI"
              width={240}
              height={84}
              priority
              className="h-20 w-auto invert mx-auto"
            />
          </Link>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-2">
            {mode === "signin" ? "Welcome back" : "Create your account"}
          </h1>
          <p className="text-sm text-[var(--color-muted)]">
            {mode === "signin" ? "Sign in to continue" : "Get started with Gaara AI"}
          </p>
        </div>

        <div className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6 md:p-8">
          {!isFirebaseConfigured && (
            <div className="text-xs text-amber-200 bg-amber-500/10 border border-amber-500/30 rounded px-3 py-2 mb-5">
              Firebase is not configured. Copy <code className="text-white">.env.example</code> to{" "}
              <code className="text-white">.env.local</code>, add your project keys from the Firebase
              console, then restart <code className="text-white">npm run dev</code>.
            </div>
          )}
          <button
            onClick={handleGoogle}
            disabled={busy || !isFirebaseConfigured}
            className="w-full flex items-center justify-center gap-2.5 py-3 bg-white text-[var(--color-bg)] font-semibold rounded text-sm hover:opacity-90 transition-opacity disabled:opacity-60"
          >
            <GoogleIcon />
            Continue with Google
          </button>

          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-[var(--color-bd)]" />
            <span className="text-xs text-[var(--color-dim)]">OR</span>
            <div className="flex-1 h-px bg-[var(--color-bd)]" />
          </div>

          <form onSubmit={handleEmailAuth} className="space-y-4">
            <div>
              <label className="block text-xs font-bold tracking-widest uppercase text-[var(--color-dim)] mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-[var(--color-bg-3)] border border-[var(--color-bd)] rounded px-3.5 py-2.5 text-sm text-white outline-none focus:border-[var(--color-bd-2)]"
              />
            </div>
            <div>
              <label className="block text-xs font-bold tracking-widest uppercase text-[var(--color-dim)] mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full bg-[var(--color-bg-3)] border border-[var(--color-bd)] rounded px-3.5 py-2.5 text-sm text-white outline-none focus:border-[var(--color-bd-2)]"
              />
            </div>
            {error && (
              <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded px-3 py-2">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={busy || !isFirebaseConfigured}
              className="w-full py-3 bg-[var(--color-yoga)] text-[var(--color-bg)] font-bold rounded text-sm hover:opacity-90 transition-opacity disabled:opacity-60"
            >
              {busy ? "Please wait…" : mode === "signin" ? "Sign in" : "Create account"}
            </button>
          </form>

          <div className="text-center text-xs text-[var(--color-muted)] mt-5">
            {mode === "signin" ? "Don't have an account? " : "Already registered? "}
            <button
              onClick={() => {
                setMode(mode === "signin" ? "signup" : "signin");
                setError("");
              }}
              className="text-white font-semibold hover:underline"
            >
              {mode === "signin" ? "Sign up" : "Sign in"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18">
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"
      />
    </svg>
  );
}
