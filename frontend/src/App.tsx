import './index.css';
import { useState } from 'react';

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [frames, setFrames] = useState<string[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setUploadStatus('');
      setFrames([]);
    }
  };

  const handleSubmit = async (e : React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      setUploadStatus('Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setUploadStatus('Uploading and extracting frames...');
      setIsUploading(true);

      const response = await fetch('http://localhost:8000/video', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed with status: ${response.status}`);
      }

      const result = await response.json();
      setUploadStatus(`Success! Extracted ${result.frames.length} frames.`);
      setFrames(result.frames);
      console.log('Result: ', result);
    } catch (error) {
      console.error(error);
      setUploadStatus('Upload failed. Check backend terminal for details.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col justify-center items-center min-h-screen gap-4 p-4">
      <div className="text-center">
        <h1 className="font-bold text-4xl">TrueCopy</h1>
        <p className="mt-2 text-gray-500">Motto in progress idk ginagawa palang</p>
      </div>

      <div>
        <form className="flex flex-col items-center gap-4" onSubmit={handleSubmit}>
          <label className="cursor-pointer rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition">
            <span>Browse File</span>
            <input 
              type="file" 
              name="file" 
              accept="video/*" 
              className="hidden" 
              onChange={handleFileChange}
            />
          </label>

          <p className="text-sm text-gray-600">
            {selectedFile 
              ? `${selectedFile.name} (${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)` 
              : 'No file selected'}
          </p>

          <button 
            type="submit" 
            className="rounded-lg bg-blue-500 px-6 py-2 text-white hover:bg-blue-600 disabled:opacity-50 transition" 
            disabled={isUploading}
          >
            {isUploading ? 'Processing...' : 'Upload File'}
          </button>

          {uploadStatus && (
            <p className="text-xs text-gray-600 mt-1">{uploadStatus}</p>
          )}
        </form>
      </div>

      {frames.length > 0 && (
        <div className="grid grid-cols-3 gap-3 max-w-2xl mt-4">
          {frames.map((framePath, i) => (
            <img 
              key={i} 
              src={`http://localhost:8000${framePath}`} 
              alt={`Frame ${i}`} 
              className="rounded border shadow-sm w-full object-cover" 
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default App;