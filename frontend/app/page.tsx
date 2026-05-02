"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Stats = {
  total_requests: number;
  average_latency_ms: number;
  total_tokens_saved: number;
  tier_blurs_total: number;
  tokens_saved_percent: number;
};

type RecentRequest = {
  id: number;
  prompt: string;
  label: string;
  model_used: string;
  latency_ms: number;
  toon_token_count: number;
  json_token_count: number;
  confidence: number;
  tier_blurred: number;
  fallback_used: number;
  timestamp: string;
};

const API_BASE = "http://localhost:8000";

const defaultStats: Stats = {
  total_requests: 0,
  average_latency_ms: 0,
  total_tokens_saved: 0,
  tier_blurs_total: 0,
  tokens_saved_percent: 0,
};

const formatNumber = (value: number, digits = 0) =>
  value.toLocaleString("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });

const formatLatency = (value: number) => `${Math.round(value)} ms`;

const truncate = (value: string, max = 40) =>
  value.length <= max ? value : `${value.slice(0, max - 1)}…`;

const modelShort = (model: string) => {
  const lower = model.toLowerCase();
  if (lower.includes("gemini")) return "gemini";
  if (lower.includes("8b")) return "8b";
  if (lower.includes("70b")) return "70b";
  return model.split("/").pop() ?? model;
};

export default function Home() {
  const [stats, setStats] = useState<Stats>(defaultStats);
  const [recent, setRecent] = useState<RecentRequest[]>([]);
  const [animatedSavings, setAnimatedSavings] = useState(0);
  const savingsRef = useRef(0);

  useEffect(() => {
    let mounted = true;

    const fetchAll = async () => {
      try {
        const [statsRes, recentRes] = await Promise.all([
          fetch(`${API_BASE}/stats`, { cache: "no-store" }),
          fetch(`${API_BASE}/recent-requests`, { cache: "no-store" }),
        ]);

        if (!statsRes.ok || !recentRes.ok) {
          return;
        }

        const statsData = (await statsRes.json()) as Stats;
        const recentData = (await recentRes.json()) as RecentRequest[];

        if (!mounted) return;
        setStats(statsData);
        setRecent(recentData);
      } catch (error) {
        console.error("Failed to fetch dashboard data", error);
      }
    };

    fetchAll();
    const interval = setInterval(fetchAll, 3000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const lastRequest = recent[0];
  const toonTokens = lastRequest?.toon_token_count ?? 0;
  const jsonTokens = lastRequest?.json_token_count ?? 0;
  const savedTokens = Math.max(jsonTokens - toonTokens, 0);

  const avgJsonTokens = useMemo(() => {
    if (!recent.length) return 0;
    const total = recent.reduce((acc, item) => acc + item.json_token_count, 0);
    return total / recent.length;
  }, [recent]);

  const projectedSavings = useMemo(() => {
    const percent = stats.tokens_saved_percent / 100;
    return Math.max(0, percent * avgJsonTokens * 1_000_000);
  }, [stats.tokens_saved_percent, avgJsonTokens]);

  useEffect(() => {
    const start = savingsRef.current;
    const end = savedTokens;
    if (start === end) return;
    const duration = 700;
    const startTime = performance.now();

    const tick = (now: number) => {
      const progress = Math.min((now - startTime) / duration, 1);
      const value = Math.round(start + (end - start) * progress);
      setAnimatedSavings(value);
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        savingsRef.current = end;
      }
    };

    requestAnimationFrame(tick);
  }, [savedTokens]);

  const cards = [
    {
      label: "Total Requests",
      value: formatNumber(stats.total_requests),
      accent: "border-[#00ff88] text-[#00ff88]",
    },
    {
      label: "Avg Latency",
      value: formatLatency(stats.average_latency_ms),
      accent: "border-[#0088ff] text-[#0088ff]",
    },
    {
      label: "Tokens Saved",
      value: formatNumber(stats.total_tokens_saved),
      accent: "border-[#ff6600] text-[#ff6600]",
    },
    {
      label: "Token Savings %",
      value: `${formatNumber(stats.tokens_saved_percent, 1)}%`,
      accent: "border-[#9d7bff] text-[#9d7bff]",
    },
    {
      label: "Tier Blurs Applied",
      value: formatNumber(stats.tier_blurs_total),
      accent: "border-[#00c2ff] text-[#00c2ff]",
    },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-zinc-100">
      <div className="relative isolate overflow-hidden px-6 pb-16 pt-14 sm:px-10">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(0,136,255,0.15),_transparent_55%)]" />
        <div className="pointer-events-none absolute right-[-15%] top-10 h-72 w-72 rounded-full bg-[radial-gradient(circle,_rgba(0,255,136,0.18),_transparent_70%)]" />

        <header className="relative z-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-zinc-400">
              OmniRoute
            </p>
            <h1 className="text-4xl font-semibold text-white sm:text-5xl">
              OmniRoute AI
            </h1>
            <p className="mt-2 text-lg text-zinc-400">
              Intelligent LLM Routing
            </p>
          </div>
          <div className="flex items-center gap-3 rounded-full border border-[#222222] bg-[#111111] px-4 py-2 text-sm">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#00ff88] opacity-70" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-[#00ff88]" />
            </span>
            <span className="text-[#00ff88]">Live</span>
          </div>
        </header>

        <section className="relative z-10 mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {cards.map((card, index) => (
            <div
              key={card.label}
              className={`animate-fade-in rounded-2xl border border-[#222222] bg-[#111111] px-4 py-5 transition-all duration-300 ${card.accent}`}
              style={{ animationDelay: `${index * 80}ms` }}
            >
              <div className="text-2xl font-semibold text-white font-mono">
                {card.value}
              </div>
              <div className="mt-2 text-xs uppercase tracking-[0.2em] text-zinc-500">
                {card.label}
              </div>
            </div>
          ))}
        </section>

        <section className="relative z-10 mt-10 rounded-3xl border border-[#00ff88]/40 bg-[#0f0f0f] px-6 py-8 shadow-[0_0_40px_rgba(0,255,136,0.15)] animate-glow">
          <div className="grid gap-6 lg:grid-cols-[1fr_2fr_1fr]">
            <div className="rounded-2xl border border-[#222222] bg-[#111111] px-5 py-4">
              <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">OmniRoute</p>
              <p className="mt-4 text-3xl font-semibold text-white font-mono">
                {toonTokens}
              </p>
              <p className="mt-2 text-sm text-zinc-400">TOON Tokens Used</p>
            </div>

            <div className="flex flex-col items-center justify-center gap-4 text-center">
              <p className="text-sm uppercase tracking-[0.4em] text-zinc-500">
                Tokens Saved This Request
              </p>
              <p className="text-6xl font-semibold text-white font-mono sm:text-7xl">
                {animatedSavings}
              </p>
              <p className="text-sm text-zinc-400">
                At 1M requests/day → {formatNumber(projectedSavings)} tokens saved/day
              </p>
            </div>

            <div className="rounded-2xl border border-[#222222] bg-[#111111] px-5 py-4">
              <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">Naive Routing</p>
              <p className="mt-4 text-3xl font-semibold text-white font-mono">
                {jsonTokens}
              </p>
              <p className="mt-2 text-sm text-zinc-400">JSON Tokens (no optimization)</p>
            </div>
          </div>
        </section>

        <section className="relative z-10 mt-10 rounded-3xl border border-[#222222] bg-[#111111] p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">Request Feed</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Live routing decisions</h2>
            </div>
            <p className="text-xs text-zinc-500">Last 10 requests</p>
          </div>

          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                <tr>
                  <th className="pb-3">Time</th>
                  <th className="pb-3">Prompt</th>
                  <th className="pb-3">Label</th>
                  <th className="pb-3">Model</th>
                  <th className="pb-3">Latency</th>
                  <th className="pb-3">Tokens Saved</th>
                  <th className="pb-3">Tier Blurred</th>
                </tr>
              </thead>
              <tbody className="text-zinc-200">
                {recent.map((item) => {
                  const saved = item.json_token_count - item.toon_token_count;
                  const labelColor =
                    item.label === "SIMPLE"
                      ? "bg-[#00ff88]/20 text-[#00ff88]"
                      : item.label === "MODERATE"
                        ? "bg-[#ff6600]/20 text-[#ff6600]"
                        : "bg-[#ff3366]/20 text-[#ff3366]";

                  return (
                    <tr key={item.id} className="border-t border-[#222222]">
                      <td className="py-3 text-zinc-400">
                        {new Date(item.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-3 max-w-[280px] text-zinc-100">
                        {truncate(item.prompt || "(empty)")}
                      </td>
                      <td className="py-3">
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${labelColor}`}>
                          {item.label}
                        </span>
                      </td>
                      <td className="py-3 font-mono text-zinc-200">
                        {modelShort(item.model_used)}
                      </td>
                      <td className="py-3 text-zinc-300">
                        {Math.round(item.latency_ms)} ms
                      </td>
                      <td className="py-3 font-mono text-zinc-100">
                        {saved}
                      </td>
                      <td className="py-3 text-center">
                        {item.tier_blurred ? "✓" : ""}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
