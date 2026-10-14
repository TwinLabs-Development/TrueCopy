import { MdOutlineUpload } from "react-icons/md";
import { useState, useRef } from "react";

type Page = "register" | "verify";

type BodyProps = {
  page: Page;
  isUploading: boolean;
  setIsUploading: (value: boolean) => void;
};

type Alteration = {
  detected: boolean;
  details: string;
  flagged_timestamps?: string[];
};

type Frame = {
  timestamp_sec: number;
  distance: number;
  matched: boolean;
  frame_url: string;
};

type ApiResult = {
  status?: string;
  record_id?: string;
  exact_match?: boolean;
  verdict?: "authentic" | "altered" | "not_registered";
  overall_similarity?: number;
  avg_distance?: number;
  is_authentic?: boolean;
  message?: string;
  total_frames_sampled?: number;
  alterations?: {
    visually_altered?: Alteration;
    time_altered?: Alteration;
    quality_altered?: Alteration;
    audio_altered?: Alteration;
  };
  frames?: Frame[];
};

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex min-w-0 flex-col items-center rounded-lg bg-beige1 p-4">
      <span className="text-xs text-beige5/80">{label}</span>
      <span className="break-all text-center text-xl font-bold text-beige5 sm:text-2xl">{value}</span>
    </div>
  );
}

function getHeadline(r: ApiResult): { text: string; color: string } {
  if (r.status) return { text: r.status, color: "text-beige5" };
  if (r.exact_match) return { text: "Exact match", color: "text-green-700" };
  switch (r.verdict) {
    case "authentic":
      return { text: "Authentic", color: "text-green-700" };
    case "altered":
      return { text: "Altered", color: "text-red-700" };
    case "not_registered":
      return { text: "Not registered", color: "text-beige5" };
    default:
      return { text: "Result", color: "text-beige5" };
  }
}

function AlterationRow({
  label,
  item,
  notChecked = false,
}: {
  label: string;
  item?: Alteration;
  notChecked?: boolean;
}) {
  if (!item) return null;

  const badge = notChecked
    ? { text: "Not checked", color: "text-beige5/60" }
    : item.detected
      ? { text: "Detected", color: "text-red-700" }
      : { text: "Clear", color: "text-green-700" };

  return (
    <div className="flex flex-col gap-1 rounded-lg bg-beige1 p-4 text-left">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-beige5">{label}</span>
        <span className={`text-sm font-semibold ${badge.color}`}>{badge.text}</span>
      </div>
      <p className="text-sm text-beige5/80">{item.details}</p>
    </div>
  );
}

function ResultCard({ result }: { result: ApiResult }) {
  const headline = getHeadline(result);
  const frames = result.frames ?? [];
  const matchedCount = frames.filter((f) => f.matched).length;

  return (
    <div className="flex flex-col gap-4 rounded-xl bg-gray1 border-[0.3rem] border-gray2 border-dashed p-6">
      <h3 className={`text-3xl font-semibold italic ${headline.color}`}>
        {headline.text}
      </h3>

      {result.message && <p className="text-beige5">{result.message}</p>}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {result.overall_similarity !== undefined && (
          <Stat label="Similarity" value={`${result.overall_similarity}%`} />
        )}
        {result.avg_distance !== undefined && (
          <Stat label="Avg distance" value={result.avg_distance.toFixed(2)} />
        )}
        {result.total_frames_sampled !== undefined && (
          <Stat label="Frames sampled" value={String(result.total_frames_sampled)} />
        )}
        {frames.length > 0 && (
          <Stat label="Frames matched" value={`${matchedCount} / ${frames.length}`} />
        )}
        {result.record_id && <Stat label="Record ID" value={result.record_id} />}
      </div>

      {result.alterations && (
        <div className="flex flex-col gap-2">
          <h4 className="text-lg font-semibold text-beige5">Alterations</h4>
          <AlterationRow label="Visual" item={result.alterations.visually_altered} />
          <AlterationRow label="Timing" item={result.alterations.time_altered} />
          <AlterationRow label="Quality" item={result.alterations.quality_altered} />
          <AlterationRow label="Audio" item={result.alterations.audio_altered} notChecked />
        </div>
      )}

      {frames.length > 0 && (
        <div className="flex flex-col gap-2">
          <h4 className="text-lg font-semibold text-beige5">Frame results</h4>
          <div className="max-h-64 overflow-y-auto rounded-lg bg-beige1">
            {frames.map((f, i) => (
              <div
                key={i}
                className="flex items-center justify-between border-b border-gray2 px-4 py-2 text-sm text-beige5 last:border-b-0"
              >
                <span>{f.timestamp_sec}s</span>
                <span>distance {f.distance}</span>
                <span className={f.matched ? "text-green-700" : "text-red-700"}>
                  {f.matched ? "Matched" : "Changed"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Body({ page, isUploading, setIsUploading }: BodyProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState("");

  const [result, setResult] = useState<ApiResult | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setUploadStatus("");
      setUploadProgress(0);
      setResult(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);

    if (!selectedFile) {
      setUploadStatus("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus("Uploading...");

    const endpoint = page === "register" ? "/register" : "/verify";
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `http://localhost:8000${endpoint}`);

    // Tracks actual network bytes sent
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        setUploadProgress(percent);
        if (percent === 100) {
          setUploadStatus("Processing frames on server...");
        }
      }
    };

    xhr.onload = () => {
      setIsUploading(false);
      if (xhr.status >= 200 && xhr.status < 300) {
        const result = JSON.parse(xhr.responseText);
        setResult(result);
        setUploadStatus(page === "register"
          ? `Success! Sampled ${result.total_frames_sampled} frames. (ID: ${result.record_id})`
          : "Verification complete."
        );
      } else if (xhr.status === 409) {
        const err = JSON.parse(xhr.responseText);
        setUploadStatus(err.detail || "This file has already been uploaded.");
      } else {
        setUploadStatus(`Upload failed with status: ${xhr.status}`);
      }
      setSelectedFile(null);
    };

    xhr.onerror = () => {
      setIsUploading(false);
      setUploadStatus("Upload failed. Check backend terminal for details.");
    };

    xhr.send(formData);
  };

  return (
    <section className="flex flex-col min-h-screen w-full max-w-7xl mx-auto">
      {/* MAIN CONTAINER */}
      <div className="drop-shadow-glow flex flex-col flex-1 bg-beige1 px-[clamp(1rem,4vw,5rem)] pb-16 gap-12 md:gap-20">
        {/* SECTION 1 */}
        <div className="flex flex-col items-center justify-center text-center">
          <h1 className="py-6 sm:py-10 text-[clamp(3rem,16vw,8rem)] font-extrabold tracking-tight">
            TrueCopy
          </h1>
          <p className="max-w-xl text-sm leading-relaxed text-beige5 sm:text-base">
            Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage
          </p>
        </div>

        {/* SECTION 2 */}
        <div className="flex flex-col w-full px-0 sm:px-10 lg:px-40 gap-6">
          <h2 className="text-3xl sm:text-5xl font-semibold italic">
            {page === "register" ? "Register" : "Verify"}
          </h2>
          <p>
            {page === "register"
              ? "Upload the original video to put into the database"
              : "Upload a video to check against the database"}
          </p>

          <form onSubmit={handleSubmit} className="flex w-full flex-col rounded-xl border-[0.3rem] border-dashed border-gray2 bg-gray1 gap-4 p-4 sm:p-6 text-center transition hover:border-gray2/25">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="video/*"
              className="hidden"
            />

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="bg-beige5 mx-auto flex flex-row gap-4 max-w-xs cursor-pointer items-center justify-center rounded-lg py-3 px-6 text-sm font-medium text-white shadow-sm hover:bg-beige5/20 hover:text-beige5 transition disabled:cursor-not-allowed disabled:bg-gray2 disabled:text-beige5 disabled:shadow-none disabled:hover:bg-gray2 disabled:hover:text-beige5"
            >
              <MdOutlineUpload className="text-lg" /> Choose File
            </button>

            {selectedFile && (
              <>
                <p className="text-xs text-beige5 font-medium">{selectedFile.name} ({(selectedFile.size / 1000000).toFixed(2)}MB)</p>
                <button
                  type="submit"
                  disabled={isUploading}
                  className="mx-auto max-w-xs cursor-pointer rounded-lg bg-green-700 py-2 px-5 text-xs font-semibold text-white hover:bg-green-800 disabled:opacity-50"
                >
                  Upload Video
                </button>
              </>
            )}

            {isUploading && (
              <div className="relative overflow-hidden rounded-lg bg-beige1 py-2.5">
                <div
                  className="absolute inset-y-0 left-0 bg-green-600 transition-[width] duration-200 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
                <span className="relative z-10 flex items-center justify-center text-xs font-semibold text-white pointer-events-none sm:text-sm">
                  {uploadProgress < 100
                    ? `Uploading... ${uploadProgress}%`
                    : `${uploadStatus}`}
                </span>
              </div>
            )}

            {(!isUploading && uploadStatus) && (
              <p className="text-xs text-beige5/80">{uploadStatus}</p>
            )}
          </form>

        {result && <ResultCard result={result} />}
        </div>
      </div>
    </section>
  );
}
