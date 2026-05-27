"use client";

import React, { useCallback, useRef, useState } from "react";
import Link from "next/link";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface FrameResult {
  frame: number;
  ball_pos: [number, number] | null;
  ball_track_id: number | null;
  bat_bbox: [number, number, number, number] | null;
  contact: boolean;
  is_wide: boolean;
  wide_conf: number;
  is_noball: boolean;
  noball_conf: number;
  wide_decision: string;
  noball_decision: string;
}

interface Summary {
  wide_count: number;
  noball_count: number;
  contact_count: number;
  ball_detected_frames: number;
}

interface AnalysisResult {
  status: string;
  request_id: string;
  total_frames: number;
  summary: Summary;
  frames: FrameResult[];
  output_video: string;
}

type Stage = "idle" | "uploading" | "processing" | "done" | "error";

const CV_API = process.env.NEXT_PUBLIC_CV_API_URL ?? "http://localhost:5001";

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  color,
  sub,
}: {
  label: string;
  value: string | number;
  color: string;
  sub?: string;
}) {
  return (
    <div className="bg-[var(--color-bg-3)] border border-[var(--color-bd)] rounded-xl p-4 flex flex-col gap-1">
      <div className="text-xs text-[var(--color-muted)] uppercase tracking-wider">{label}</div>
      <div className={`text-3xl font-black ${color}`}>{value}</div>
      {sub && <div className="text-xs text-[var(--color-muted)]">{sub}</div>}
    </div>
  );
}

function FrameTimeline({ frames, total }: { frames: FrameResult[]; total: number }) {
  if (!frames.length) return null;
  const events = frames.filter(
    (f) => f.is_wide || f.is_noball || f.contact || f.ball_pos !== null
  );

  return (
    <div className="mt-6">
      <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-2">
        Frame Timeline
      </h3>
      {/* progress-bar style timeline */}
      <div className="relative h-8 bg-white/5 rounded-full overflow-hidden w-full">
        {frames.map((f) => {
          const pct = ((f.frame - 1) / Math.max(total - 1, 1)) * 100;
          let color = "";
          if (f.is_wide) color = "bg-red-500";
          else if (f.is_noball) color = "bg-orange-400";
          else if (f.contact) color = "bg-yellow-400";
          else if (f.ball_pos) color = "bg-[var(--color-cricket)]";
          if (!color) return null;
          return (
            <div
              key={f.frame}
              title={`Frame ${f.frame}: ${f.is_wide ? "WIDE" : f.is_noball ? "NO BALL" : f.contact ? "CONTACT" : "Ball"}`}
              className={`absolute top-0 h-full w-1 ${color} opacity-80`}
              style={{ left: `${pct}%` }}
            />
          );
        })}
      </div>
      <div className="flex gap-4 mt-2 text-xs text-[var(--color-muted)]">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> Wide</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-400 inline-block" /> No-Ball</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400 inline-block" /> Contact</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[var(--color-cricket)] inline-block" /> Ball</span>
      </div>
    </div>
  );
}

function EventTable({ frames }: { frames: FrameResult[] }) {
  const events = frames
    .filter((f) => f.is_wide || f.is_noball || f.contact)
    .slice(0, 40);

  if (!events.length) return (
    <p className="text-xs text-[var(--color-muted)] mt-4">No wide / no-ball / contact events detected.</p>
  );

  return (
    <div className="mt-6 overflow-x-auto">
      <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-2">
        Key Events
      </h3>
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="text-[var(--color-muted)] border-b border-[var(--color-bd)]">
            <th className="text-left py-2 pr-4">Frame</th>
            <th className="text-left py-2 pr-4">Event</th>
            <th className="text-left py-2 pr-4">Confidence</th>
            <th className="text-left py-2 pr-4">Ball Position</th>
          </tr>
        </thead>
        <tbody>
          {events.map((f) => (
            <tr key={f.frame} className="border-b border-[var(--color-bd)] hover:bg-white/3">
              <td className="py-1.5 pr-4 font-mono text-[var(--color-muted)]">#{f.frame}</td>
              <td className="py-1.5 pr-4">
                {f.is_wide && (
                  <span className="bg-red-500/20 text-red-400 px-2 py-0.5 rounded text-[10px] font-bold">
                    WIDE
                  </span>
                )}
                {f.is_noball && (
                  <span className="bg-orange-400/20 text-orange-400 px-2 py-0.5 rounded text-[10px] font-bold ml-1">
                    NO BALL
                  </span>
                )}
                {f.contact && (
                  <span className="bg-yellow-400/20 text-yellow-400 px-2 py-0.5 rounded text-[10px] font-bold ml-1">
                    CONTACT
                  </span>
                )}
              </td>
              <td className="py-1.5 pr-4 text-[var(--color-muted)]">
                {f.is_wide ? `${(f.wide_conf * 100).toFixed(0)}%` :
                 f.is_noball ? `${(f.noball_conf * 100).toFixed(0)}%` : "—"}
              </td>
              <td className="py-1.5 font-mono text-[var(--color-muted)]">
                {f.ball_pos ? `(${f.ball_pos[0].toFixed(0)}, ${f.ball_pos[1].toFixed(0)})` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

export default function CricketAnalyzePage() {
  const [file, setFile]           = useState<File | null>(null);
  const [previewUrl, setPreview]  = useState<string | null>(null);
  const [stage, setStage]         = useState<Stage>("idle");
  const [uploadPct, setUploadPct] = useState(0);
  const [result, setResult]       = useState<AnalysisResult | null>(null);
  const [errorMsg, setErrorMsg]   = useState("");
  const [outputVideoUrl, setOutputVideoUrl] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // ── File selection ─────────────────────────────────────────────────────────
  const pickFile = useCallback((f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setOutputVideoUrl(null);
    setStage("idle");
    setErrorMsg("");
  }, []);

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) pickFile(f);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) pickFile(f);
  }

  // ── Upload & analyze ───────────────────────────────────────────────────────
  async function analyze() {
    if (!file) return;
    setStage("uploading");
    setUploadPct(0);
    setResult(null);
    setOutputVideoUrl(null);
    setErrorMsg("");

    const fd = new FormData();
    fd.append("video", file, file.name);

    // Use XHR for upload progress, then fetch for response
    const uploadRes = await new Promise<string>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${CV_API}/analyze`);
      xhr.upload.onprogress = (ev) => {
        if (ev.lengthComputable) {
          setUploadPct(Math.round((ev.loaded / ev.total) * 100));
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          setStage("processing");
          resolve(xhr.responseText);
        } else {
          reject(new Error(`Server error ${xhr.status}: ${xhr.responseText}`));
        }
      };
      xhr.onerror = () => reject(new Error("Network error — is the CV API running on port 5001?"));
      xhr.send(fd);
    }).catch((err) => {
      setStage("error");
      setErrorMsg(err.message);
      return null;
    });

    if (!uploadRes) return;

    try {
      const json: AnalysisResult = JSON.parse(uploadRes);
      setResult(json);

      // Build URL to download the annotated output video
      if (json.output_video) {
        setOutputVideoUrl(`${CV_API}${json.output_video}`);
      }
      setStage("done");
    } catch {
      setStage("error");
      setErrorMsg("Failed to parse server response.");
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  const isLoading = stage === "uploading" || stage === "processing";

  return (
    <div className="min-h-screen bg-[var(--color-bg)] px-4 md:px-10 py-10">
      <div className="max-w-7xl mx-auto">

        {/* ── Header ── */}
        <div className="flex items-start justify-between mb-8 gap-4 flex-wrap">
          <div>
            <div className="text-xs text-[var(--color-cricket)] uppercase tracking-widest mb-1 font-semibold">
              Cricket CV System
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold leading-tight">
              Ball &amp; Delivery Analyzer
            </h1>
            <p className="text-[var(--color-muted)] mt-2 max-w-xl text-sm">
              Upload a cricket video to detect the ball trajectory, bat contact,
              wide balls, and no-balls — all annotated live on the output video.
            </p>
          </div>
          <Link
            href="/products/cricket"
            className="text-sm text-[var(--color-muted)] hover:text-white transition-colors shrink-0"
          >
            ← Cricket Products
          </Link>
        </div>

        {/* ── Main grid ── */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

          {/* ── LEFT: Upload panel ── */}
          <div className="flex flex-col gap-4">

            {/* Drop zone */}
            <div
              onDrop={onDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileRef.current?.click()}
              className={`
                relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer
                transition-all duration-200 select-none
                ${file
                  ? "border-[var(--color-cricket)]/50 bg-[var(--color-cricket)]/5"
                  : "border-[var(--color-bd-2)] bg-[var(--color-bg-2)] hover:border-[var(--color-cricket)]/40 hover:bg-[var(--color-cricket)]/5"
                }
              `}
            >
              <input
                ref={fileRef}
                type="file"
                accept="video/*"
                hidden
                onChange={onFileChange}
              />
              {file ? (
                <div>
                  <div className="text-[var(--color-cricket)] text-2xl mb-1">✓</div>
                  <div className="font-semibold text-white truncate max-w-xs mx-auto">{file.name}</div>
                  <div className="text-xs text-[var(--color-muted)] mt-1">
                    {(file.size / 1024 / 1024).toFixed(1)} MB · Click to change
                  </div>
                </div>
              ) : (
                <div>
                  <div className="text-4xl mb-3 opacity-40">🎬</div>
                  <div className="font-semibold">Drop your cricket video here</div>
                  <div className="text-xs text-[var(--color-muted)] mt-1">
                    or click to browse — MP4, MOV, AVI supported
                  </div>
                </div>
              )}
            </div>

            {/* Original video preview */}
            {previewUrl && (
              <div className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-xl overflow-hidden">
                <div className="px-4 py-2 border-b border-[var(--color-bd)] text-xs text-[var(--color-muted)] font-semibold uppercase tracking-wider">
                  Original Upload
                </div>
                <video
                  src={previewUrl}
                  controls
                  className="w-full max-h-72 object-contain bg-black"
                />
              </div>
            )}

            {/* Analyze button */}
            <button
              onClick={analyze}
              disabled={!file || isLoading}
              className={`
                w-full py-3 rounded-xl font-bold text-sm transition-all duration-200
                ${!file || isLoading
                  ? "bg-white/5 text-[var(--color-muted)] cursor-not-allowed"
                  : "bg-[var(--color-cricket)] text-black hover:brightness-110 active:scale-95"
                }
              `}
            >
              {stage === "uploading"
                ? `Uploading… ${uploadPct}%`
                : stage === "processing"
                ? "Processing video…"
                : "▶  Analyze Video"}
            </button>

            {/* Progress bar */}
            {isLoading && (
              <div className="space-y-2">
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[var(--color-cricket)] transition-all duration-300 rounded-full"
                    style={{
                      width: stage === "uploading" ? `${uploadPct}%` : "100%",
                      animation: stage === "processing" ? "pulse 1.5s ease-in-out infinite" : "none",
                    }}
                  />
                </div>
                <p className="text-xs text-[var(--color-muted)] text-center">
                  {stage === "uploading"
                    ? `Uploading ${uploadPct}% — please wait…`
                    : "Running ball / bat / wide / no-ball detection…"}
                </p>
              </div>
            )}

            {/* Error */}
            {stage === "error" && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-sm text-red-400">
                <strong>Error:</strong> {errorMsg}
                <div className="text-xs mt-1 text-red-400/70">
                  Make sure the Cricket CV API is running:
                  <code className="ml-1 bg-red-500/10 px-1 rounded">
                    python api.py --port 5001
                  </code>
                </div>
              </div>
            )}
          </div>

          {/* ── RIGHT: Results panel ── */}
          <div className="flex flex-col gap-4">

            {!result && !isLoading && (
              <div className="flex-1 flex flex-col items-center justify-center bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-2xl p-10 text-center min-h-64">
                <div className="text-5xl mb-4 opacity-20">📊</div>
                <div className="text-[var(--color-muted)] text-sm">
                  Results will appear here after analysis.
                </div>
                <div className="text-xs text-[var(--color-muted)] mt-2 opacity-60">
                  Ball tracking · Wide detection · No-ball detection · Contact events
                </div>
              </div>
            )}

            {isLoading && (
              <div className="flex-1 flex flex-col items-center justify-center bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-2xl p-10 min-h-64">
                <div className="relative w-14 h-14 mb-5">
                  <div className="absolute inset-0 rounded-full border-2 border-[var(--color-cricket)]/20" />
                  <div
                    className="absolute inset-0 rounded-full border-2 border-transparent border-t-[var(--color-cricket)]"
                    style={{ animation: "spin 0.9s linear infinite" }}
                  />
                </div>
                <div className="text-white font-semibold">
                  {stage === "uploading" ? "Uploading video…" : "Analyzing…"}
                </div>
                <div className="text-xs text-[var(--color-muted)] mt-2">
                  {stage === "processing"
                    ? "Running YOLOv8 · SORT tracker · Wide & No-ball detection"
                    : `${uploadPct}% uploaded`}
                </div>
              </div>
            )}

            {result && stage === "done" && (
              <div className="flex flex-col gap-4">

                {/* Annotated output video */}
                {outputVideoUrl && (
                  <div className="bg-[var(--color-bg-2)] border border-[var(--color-cricket)]/30 rounded-xl overflow-hidden">
                    <div className="px-4 py-2 bg-[var(--color-cricket)]/10 border-b border-[var(--color-cricket)]/20 flex items-center justify-between">
                      <span className="text-xs font-bold text-[var(--color-cricket)] uppercase tracking-wider">
                        ✓ Annotated Output
                      </span>
                      <a
                        href={outputVideoUrl}
                        download
                        className="text-xs text-[var(--color-muted)] hover:text-white transition-colors"
                      >
                        ↓ Download
                      </a>
                    </div>
                    <video
                      src={outputVideoUrl}
                      controls
                      autoPlay
                      loop
                      className="w-full max-h-80 object-contain bg-black"
                    />
                    <div className="px-4 py-2 text-xs text-[var(--color-muted)] flex gap-4 flex-wrap border-t border-[var(--color-bd)]">
                      <span>🟢 Green = Ball + Trail</span>
                      <span>🔵 Blue = Bat</span>
                      <span>🟡 Yellow = Crease lines</span>
                      <span>🔴 Red = Wide / No-ball</span>
                    </div>
                  </div>
                )}

                {/* Summary stats */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <StatCard
                    label="Ball Detected"
                    value={result.summary.ball_detected_frames}
                    color="text-[var(--color-cricket)]"
                    sub={`of ${result.total_frames} frames`}
                  />
                  <StatCard
                    label="Contact Events"
                    value={result.summary.contact_count}
                    color="text-yellow-400"
                    sub="bat-ball hits"
                  />
                  <StatCard
                    label="Wides"
                    value={result.summary.wide_count}
                    color={result.summary.wide_count > 0 ? "text-red-400" : "text-[var(--color-muted)]"}
                    sub="wide balls"
                  />
                  <StatCard
                    label="No Balls"
                    value={result.summary.noball_count}
                    color={result.summary.noball_count > 0 ? "text-orange-400" : "text-[var(--color-muted)]"}
                    sub="foot faults"
                  />
                </div>

                {/* Frame timeline */}
                <div className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-xl p-4">
                  <FrameTimeline frames={result.frames} total={result.total_frames} />
                  <EventTable frames={result.frames} />
                </div>

              </div>
            )}
          </div>
        </div>

        {/* ── How it works ── */}
        <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: "🟢", title: "Ball Tracking", desc: "YOLOv8 + SORT Kalman filter tracks the ball across frames with trajectory trail" },
            { icon: "🔵", title: "Bat Detection", desc: "Detects bat position and alerts on bat-ball contact events" },
            { icon: "🟡", title: "Wide Detection", desc: "Hough crease detection + ICC 89cm boundary rule flags wide deliveries" },
            { icon: "🔴", title: "No-Ball", desc: "MediaPipe pose tracks bowler's front foot against the popping crease" },
          ].map((item) => (
            <div
              key={item.title}
              className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-xl p-4"
            >
              <div className="text-2xl mb-2">{item.icon}</div>
              <div className="font-semibold text-sm mb-1">{item.title}</div>
              <div className="text-xs text-[var(--color-muted)]">{item.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
