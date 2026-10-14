import { MdOutlineUpload } from "react-icons/md";
import { useState, useRef } from "react";

type Page = "register" | "verify";

type BodyProps = {
  page: Page;
  isUploading: boolean;
  setIsUploading: (value: boolean) => void;
};

export default function Body({ page, isUploading, setIsUploading }: BodyProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setUploadStatus("");
      setUploadProgress(0);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

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
        setUploadStatus(`Success! Sampled ${result.total_frames_sampled} frames. (ID: ${result.record_id})`);
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
      <div className="drop-shadow-glow flex flex-col flex-1 bg-beige1 px-[clamp(1rem,4vw,5rem)] gap-20">
        {/* SECTION 1 */}
        <div className="flex flex-col items-center justify-center text-center">
          <h1 className="py-10 text-[8rem] font-extrabold tracking-tight">
            TrueCopy
          </h1>
          <p className="max-w-xl text-sm leading-relaxed text-beige5 sm:text-base">
            Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage
          </p>
        </div>

        {/* SECTION 2 */}
        <div className="flex flex-col px-40 gap-6">
          <h2 className="text-5xl font-semibold italic">
            {page === "register" ? "Register" : "Verify"}
          </h2>
          <p>
            {page === "register"
              ? "Upload the original video to put into the database"
              : "Upload a video to check against the database"}
          </p>

          <form onSubmit={handleSubmit} className="relative left-1/2 -translate-x-1/2 flex w-[max(30rem,100%)] flex flex-col rounded-xl border-[0.3rem] border-dashed border-gray2 bg-gray1 gap-4 p-6 text-center transition hover:border-gray2/25">
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
        </div>
      </div>
    </section>
  );
}
