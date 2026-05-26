"use client";

import React, { useRef, useState } from "react";
import Link from "next/link";

export default function CoachUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0] ?? null;
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  }

  function onDragOver(e: React.DragEvent) {
    e.preventDefault();
  }

  function upload() {
    if (!file) return alert("Choose a video first");
    setLoading(true);
    setProgress(0);
    const fd = new FormData();
    fd.append("video", file, file.name);

    const xhr = new XMLHttpRequest();
    const api = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000") + "/predict";
    xhr.open("POST", api);
    xhr.upload.onprogress = (ev) => {
      if (ev.lengthComputable) setProgress(Math.round((ev.loaded / ev.total) * 100));
    };
    xhr.onload = () => {
      setLoading(false);
      try {
        const json = JSON.parse(xhr.responseText);
        setResult(json);
      } catch (e) {
        alert("Failed to parse server response");
      }
    };
    xhr.onerror = () => {
      setLoading(false);
      alert("Upload failed");
    };
    xhr.send(fd);
  }

  return (
    <div className="px-5 md:px-12 py-16">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold">Batting Coach — Upload Video</h1>
            <p className="text-sm text-[var(--color-muted)] mt-2">
              Upload a short clip (~2s around the shot) and receive instant coaching feedback.
            </p>
          </div>
          <div>
            <Link href="/products" className="text-sm text-[var(--color-muted)]">
              ← Back to products
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6">
            <div
              className="border-2 border-dashed rounded-md p-6 text-center text-[var(--color-muted)] cursor-pointer"
              onDrop={onDrop}
              onDragOver={onDragOver}
              onClick={() => fileRef.current?.click()}
            >
              <input ref={fileRef} type="file" accept="video/*" hidden onChange={onFileChange} />
              <div className="mb-3">Drag & drop a video, or click to choose</div>
              <div className="text-xs">Recommended: 1–4 seconds centered on the shot</div>
            </div>

            <div className="mt-4">
              {preview ? (
                <video src={preview} controls className="w-full rounded-md" />
              ) : (
                <div className="h-48 bg-white/5 rounded-md flex items-center justify-center text-[var(--color-muted)]">
                  No preview
                </div>
              )}
            </div>

            <div className="mt-4 flex items-center gap-3">
              <button onClick={upload} className="btn primary px-4 py-2" disabled={loading}>
                {loading ? `Analyzing ${progress}%` : "Analyze"}
              </button>
              <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-[var(--color-cricket)]" style={{ width: `${progress}%` }} />
              </div>
            </div>
          </div>

          <div className="bg-[var(--color-bg-2)] border border-[var(--color-bd)] rounded-lg p-6">
            <h3 className="text-lg font-bold mb-3">Coach Feedback</h3>
            {!result && <div className="text-[var(--color-muted)]">No results yet. Upload a clip to analyze.</div>}
            {result && (
              <div>
                    {result.predictions && (
                  <div className="mb-3">
                    <strong>Top prediction:</strong>
                    <div className="mt-2 text-2xl">{result.predictions[0].name} <span className="text-sm text-[var(--color-muted)]">({(result.predictions[0].prob*100).toFixed(1)}%)</span></div>
                  </div>
                )}

                {result.feedback && (
                  <div>
                    <div className="mb-2">
                      <strong>Issue:</strong>
                      <div className="text-sm text-[var(--color-muted)]">{result.feedback.issue}</div>
                    </div>
                    <div className="mb-2">
                      <strong>Advice:</strong>
                      <div className="text-sm text-[var(--color-muted)]">{result.feedback.advice}</div>
                    </div>
                    <div className="mb-2">
                      <strong>Corrections:</strong>
                      <div className="text-sm text-[var(--color-muted)]">{result.feedback.corrections}</div>
                    </div>
                    <div className="mt-3 text-xs text-[var(--color-muted)]">
                      Visible ratio: {result.feedback.visible_ratio?.toFixed(2)} · Avg conf: {result.feedback.avg_confidence?.toFixed(2)}
                    </div>
                  </div>
                )}
                    {result.objects && result.objects.summary && (
                      <div className="mt-4">
                        <h4 className="text-sm font-semibold mb-2">Detected objects</h4>
                        <div className="text-sm text-[var(--color-muted)]">Ball detections: {result.objects.summary.ball_count}</div>
                        <div className="text-sm text-[var(--color-muted)]">Bat detections: {result.objects.summary.bat_count}</div>
                      </div>
                    )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
