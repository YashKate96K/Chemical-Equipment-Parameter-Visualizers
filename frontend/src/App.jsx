import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Beaker } from "lucide-react";
import UploadForm from "./components/UploadForm";
import DatasetList from "./components/DatasetList";
import ChartPanel from "./components/ChartPanel";
import TablePreview from "./components/TablePreview";
import { clearAuthToken } from "./api/client";
import { toast } from "sonner";

function App() {
  const [summary, setSummary] = useState(null);
  const [preview, setPreview] = useState("");
  const [datasetsChanged, setDatasetsChanged] = useState(0);
  const [lastDatasetId, setLastDatasetId] = useState(null);

  useEffect(() => {
    try {
      localStorage.removeItem("last_summary");
      localStorage.removeItem("last_preview");
      localStorage.removeItem("last_dataset_id");
    } catch {}
  }, []);

  const isAuthed = true; // TEMPORARY BYPASS: Always consider authenticated
  const onSignOut = () => {
    clearAuthToken();
    try { sessionStorage.removeItem('session_authed') } catch {}
    toast.success("Signed out");
    window.location.assign("/signin");
  };

  useEffect(() => {
    // TEMPORARY BYPASS: Don't redirect to signin
    // if (!isAuthed) window.location.replace("/signin");
  }, [isAuthed]);

  return (
    <div className="relative min-h-screen text-gray-900 overflow-hidden">

      {/* BACKGROUND — TEAL/AQUA ABSTRACT WAVES */}
      <div className="absolute -top-40 -left-40 w-[900px] h-[900px] bg-teal-300/30 rounded-full blur-3xl animate-pulse-slow"></div>
      <div className="absolute top-20 right-0 w-[800px] h-[800px] bg-cyan-300/30 rounded-full blur-[180px] animate-pulse-delay"></div>
      <div className="absolute bottom-10 left-1/3 w-[500px] h-[500px] bg-emerald-200/30 rounded-full blur-[150px] animate-pulse-slower"></div>

      {/* CUSTOM ANIMATIONS */}
      <style>{`
        @keyframes pulseSlow {
          0%, 100% { transform: translateY(0px) scale(1); }
          50% { transform: translateY(30px) scale(1.06); }
        }
        @keyframes pulseDelay {
          0%, 100% { transform: translateY(0px) scale(1); }
          50% { transform: translateY(-25px) scale(1.04); }
        }
        @keyframes pulseSlower {
          0%, 100% { transform: translateY(0px) scale(1); }
          50% { transform: translateY(20px) scale(1.05); }
        }
        .animate-pulse-slow { animation: pulseSlow 8s ease-in-out infinite; }
        .animate-pulse-delay { animation: pulseDelay 10s ease-in-out infinite; }
        .animate-pulse-slower { animation: pulseSlower 12s ease-in-out infinite; }
      `}</style>

      {/* HEADER */}
      <header className="sticky top-0 backdrop-blur-2xl bg-white/10 shadow-lg z-20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">

          {/* Branding */}
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-500 text-white grid place-items-center shadow-xl shadow-teal-500/40 border border-white/20">
              <Beaker size={20} />
            </div>
            <div>
              <h1 className="text-3xl font-semibold tracking-tight drop-shadow">
                Chemical Equipment Visualizer
              </h1>
              <p className="text-xs text-gray-100/70">
                Upload → Analyze → Generate Dashboards
              </p>
            </div>
          </div>

          {/* Right side buttons */}
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="px-4 py-2 rounded-full bg-white/15 hover:bg-white/30 text-sm font-semibold text-black border border-white/30 shadow-sm transition"
            >
              Home
            </Link>

            {lastDatasetId && (
              <Link
                to={`/dashboard/${lastDatasetId}`}
                className="px-5 py-2 rounded-full bg-gradient-to-r from-teal-500 to-cyan-500 hover:opacity-90 text-white shadow-lg shadow-teal-300/40 transition"
              >
                Resume Dashboard →
              </Link>
            )}

            {isAuthed ? (
              <button
                onClick={onSignOut}
                className="px-4 py-2 rounded-full border border-white/30 text-sm font-semibold hover:text-black hover:bg-white/20 shadow-sm transition

"
              >
                Sign out
              </button>
            ) : (
              <div className="flex items-center gap-3 text-sm">
                <Link to="/signin" className="text-white/90 hover:underline">
                  Sign in
                </Link>
                <Link to="/signup" className="text-white/90 hover:underline">
                  Sign up
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">

          {/* LEFT — Big section */}
          <div className="lg:col-span-2 space-y-10">

            {/* Upload Form Card */}
            <div className="p-8 rounded-3xl bg-white/10 backdrop-blur-xl border border-white/20 shadow-xl shadow-teal-400/20 hover:bg-white/20 transition">
              <UploadForm
                onUploaded={(res) => {
                  setSummary(res.summary_json);
                  setPreview(res.preview_csv);
                  setDatasetsChanged((x) => x + 1);
                  setLastDatasetId(res.id);

                  try {
                    localStorage.setItem("last_summary", JSON.stringify(res.summary_json));
                    localStorage.setItem("last_preview", res.preview_csv || "");
                    localStorage.setItem("last_dataset_id", String(res.id));
                  } catch {}
                }}
              />
            </div>

            <div className="flex items-center justify-between mt-6 relative z-10">
  <h2 className="text-2xl font-semibold text-black drop-shadow-lg tracking-tight">
    Quick Summary
  </h2>

  {lastDatasetId && (
    <Link
      to={`/dashboard/${lastDatasetId}`}
      className="text-teal-200 hover:text-white underline font-medium"
    >
      Open Dashboard →
    </Link>
  )}
</div>


            {/* Summary Chart Panel */}
            <div className="rounded-3xl bg-white/10 backdrop-blur-xl border border-white/20 shadow-xl p-8 hover:bg-white/20 transition">
              <ChartPanel summary={summary} />
            </div>

            {/* Table Preview */}
            <div className="rounded-3xl bg-white/10 backdrop-blur-xl border border-white/20 shadow-xl p-8 hover:bg-white/20 transition">
              <TablePreview csvText={preview} />
            </div>
          </div>

          {/* RIGHT — Dataset List */}
          <div className="rounded-3xl bg-white/10 backdrop-blur-xl border border-white/20 shadow-xl p-8 hover:bg-white/20 transition">
            <DatasetList changed={datasetsChanged} />
          </div>

        </div>
      </main>
    </div>
  );
}

export default App;

