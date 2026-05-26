"use client";

import Link from "next/link";
import Image from "next/image";
import { useState, useRef, useEffect } from "react";
import { Menu, X, ChevronDown, LogOut, LayoutGrid, User } from "lucide-react";
import { useAuth } from "@/auth/AuthProvider";
import { useRouter } from "next/navigation";

const LINKS = [
  { href: "/about", label: "About" },
  { href: "/products", label: "Products" },
  { href: "/technology", label: "Technology" },
  { href: "/pricing", label: "Pricing" },
  { href: "/blog", label: "Blog" },
  { href: "/careers", label: "Career" },
];

export default function Nav() {
  const [open, setOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const { user, logout } = useAuth();
  const router = useRouter();
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  async function handleLogout() {
    await logout();
    setProfileOpen(false);
    setOpen(false);
    router.replace("/");
  }

  const initials = (user?.displayName || user?.email || "U")
    .split(/[\s@]+/)
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[var(--color-bg)]/95 backdrop-blur border-b border-[var(--color-bd)]">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-5 md:px-12 h-20">
        <Link href="/" className="flex items-center" onClick={() => setOpen(false)}>
          <Image
            src="/logo.png"
            alt="Gaara AI"
            width={180}
            height={60}
            priority
            className="h-14 w-auto invert"
          />
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="px-3 py-2 text-sm font-medium text-[var(--color-muted)] hover:text-white transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </nav>

        {/* Desktop right side */}
        <div className="hidden md:flex items-center gap-2">
          {user ? (
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-2 pl-1.5 pr-3 py-1.5 bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-full hover:border-[var(--color-bd-2)] transition-colors"
              >
                <span className="w-7 h-7 rounded-full bg-[var(--color-yoga)] text-[var(--color-bg)] flex items-center justify-center text-xs font-bold">
                  {initials}
                </span>
                <span className="text-sm font-semibold max-w-[100px] truncate">
                  {user.displayName?.split(" ")[0] ?? user.email?.split("@")[0]}
                </span>
                <ChevronDown
                  size={14}
                  className={`text-[var(--color-muted)] transition-transform ${profileOpen ? "rotate-180" : ""}`}
                />
              </button>
              {profileOpen && (
                <div className="absolute top-full right-0 mt-2 w-60 bg-[var(--color-bg-2)] border border-[var(--color-bd-2)] rounded-lg overflow-hidden shadow-2xl">
                  <div className="px-4 py-3 border-b border-[var(--color-bd)]">
                    <div className="text-sm font-bold truncate">
                      {user.displayName ?? user.email?.split("@")[0]}
                    </div>
                    <div className="text-xs text-[var(--color-muted)] truncate">{user.email}</div>
                  </div>
                  <Link
                    href="/select-service"
                    onClick={() => setProfileOpen(false)}
                    className="flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--color-muted)] hover:bg-[var(--color-bg-3)] hover:text-white"
                  >
                    <LayoutGrid size={16} /> My Services
                  </Link>
                  <Link
                    href="/about"
                    onClick={() => setProfileOpen(false)}
                    className="flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--color-muted)] hover:bg-[var(--color-bg-3)] hover:text-white"
                  >
                    <User size={16} /> Account
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10 border-t border-[var(--color-bd)]"
                  >
                    <LogOut size={16} /> Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link
                href="/login"
                className="px-4 py-2 text-sm font-semibold text-white border border-[var(--color-bd-2)] rounded hover:bg-[var(--color-bg-2)] transition-colors"
              >
                Login
              </Link>
              <Link
                href="/contact"
                className="px-4 py-2 text-sm font-bold text-[var(--color-bg)] bg-white rounded hover:opacity-90 transition-opacity"
              >
                Contact
              </Link>
            </>
          )}
        </div>

        <button
          className="md:hidden p-2 -mr-2 text-white"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-[var(--color-bd)] bg-[var(--color-bg-1)]">
          <nav className="flex flex-col px-5 py-3">
            {LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="py-3 text-base font-medium text-[var(--color-muted)] hover:text-white"
              >
                {l.label}
              </Link>
            ))}
            <div className="pt-3 mt-2 flex flex-col gap-2 border-t border-[var(--color-bd)]">
              {user ? (
                <>
                  <div className="px-1 py-2">
                    <div className="text-sm font-bold truncate">
                      {user.displayName ?? user.email?.split("@")[0]}
                    </div>
                    <div className="text-xs text-[var(--color-muted)] truncate">{user.email}</div>
                  </div>
                  <Link
                    href="/select-service"
                    onClick={() => setOpen(false)}
                    className="py-2.5 text-center text-sm font-bold text-[var(--color-bg)] bg-white rounded"
                  >
                    My Services
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="py-2.5 text-sm font-semibold text-red-400 border border-red-500/30 rounded"
                  >
                    Sign out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    onClick={() => setOpen(false)}
                    className="py-2.5 text-center text-sm font-semibold text-white border border-[var(--color-bd-2)] rounded"
                  >
                    Login
                  </Link>
                  <Link
                    href="/contact"
                    onClick={() => setOpen(false)}
                    className="py-2.5 text-center text-sm font-bold text-[var(--color-bg)] bg-white rounded"
                  >
                    Contact
                  </Link>
                </>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
