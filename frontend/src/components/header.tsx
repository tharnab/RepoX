"use client";

import { useAuth } from "@/lib/auth-context";
import { LogOut, ExternalLink, ChevronDown } from "lucide-react";
import { useState } from "react";

export function Header() {
  const { user, loading, login, logout } = useAuth();
  const [showOptions, setShowOptions] = useState(false);

  return (
    <header className="border-b border-zinc-800/50 bg-zinc-950/60 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-900/30">
            <span className="text-black font-bold text-xs">RX</span>
          </div>
          <span className="font-bold text-base tracking-tight">RepoX</span>
        </div>

        <div>
          {loading ? (
            <div className="w-20 h-8 bg-zinc-800/50 rounded-lg animate-pulse" />
          ) : user ? (
            <div className="relative">
              <button
                onClick={() => setShowOptions(!showOptions)}
                className="flex items-center gap-2 hover:bg-zinc-800/50 px-3 py-1.5 rounded-lg transition-all border border-transparent hover:border-zinc-700/50"
              >
                <img
                  src={user.avatar_url}
                  alt={user.login}
                  className="w-6 h-6 rounded-full ring-2 ring-zinc-700/50"
                />
                <span className="text-sm font-medium text-zinc-200 hidden sm:block">
                  {user.login}
                </span>
                <ChevronDown className="w-3.5 h-3.5 text-zinc-500" />
              </button>

              {showOptions && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowOptions(false)} />
                  <div className="absolute right-0 top-full mt-2 w-60 bg-zinc-800 border border-zinc-700 rounded-xl shadow-2xl z-20 py-2 overflow-hidden">
                    <div className="px-3 py-2 border-b border-zinc-700/50">
                      <p className="text-xs font-medium text-zinc-400">Signed in as</p>
                      <p className="text-sm font-semibold text-white">{user.login}</p>
                    </div>
                    <a
                      href="https://github.com/logout"
                      target="_blank"
                      className="flex items-center gap-2 w-full px-3 py-2.5 text-sm hover:bg-zinc-700/50 transition-colors text-zinc-300"
                    >
                      <ExternalLink className="w-4 h-4" />
                      Sign out of GitHub
                    </a>
                    <button
                      onClick={() => {
                        setShowOptions(false);
                        logout();
                      }}
                      className="flex items-center gap-2 w-full px-3 py-2.5 text-sm hover:bg-zinc-700/50 transition-colors text-red-400"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign out of RepoX
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <button
              onClick={login}
              className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-sm font-medium transition-all border border-zinc-700 hover:border-zinc-600 shadow-lg"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              Sign in
            </button>
          )}
        </div>
      </div>
    </header>
  );
}