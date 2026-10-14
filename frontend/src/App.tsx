import './index.css';
import { useState } from 'react';
import Header from './assets/Header';
import Body from './assets/Body';
import Footer from './assets/Footer';

function App() {
  

  return (
    <div className="flex flex-col min-h-screen">
    <Header />
    
    {/* The main tag wraps the body and stretches to fill empty space */}
    <main className="grow">
      <Body />
    </main>
    
    <Footer />
  </div>
  );

  // yo wtf is this? vvvvv -diego

  //   <div className="flex flex-col justify-center items-center min-h-screen gap-4 p-4">
  //     <header className="text-center">
  //       <h1 className="font-bold text-4xl">TrueCopy</h1>
  //       <p className="mt-2 text-gray-500">Motto in progress idk ginagawa palang</p>
  //     </header>

  //     <div>
  //       <form className="flex flex-row items-center gap-4" onSubmit={handleSubmit}>
  //         <label className="cursor-pointer rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition">
  //           <span>Browse File</span>
  //           <input
  //             type="file"
  //             name="file"
  //             accept="video/*"
  //             className="hidden"
  //             onChange={handleFileChange}
  //           />
  //         </label>

  //         <p className="text-sm text-gray-600">
  //           {selectedFile
  //             ? `${selectedFile.name} (${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)`
  //             : 'No file selected'}
  //         </p>

  //         <button
  //           type="submit"
  //           className="rounded-lg bg-blue-500 px-6 py-2 text-white hover:bg-blue-600 disabled:opacity-50 transition"
  //           disabled={isUploading}
  //         >
  //           {isUploading ? 'Processing...' : 'Upload File'}
  //         </button>

  //         {uploadStatus && (
  //           <p className="text-xs text-gray-600 mt-1">{uploadStatus}</p>
  //         )}
  //       </form>
  //     </div>

  //     {frames.length > 0 && (
  //       <div className="grid grid-cols-3 gap-3 max-w-2xl mt-4">
  //         {frames.map((framePath, i) => (
  //           <img
  //             key={i}
  //             src={`http://localhost:8000${framePath}`}
  //             alt={`Frame ${i}`}
  //             className="rounded border shadow-sm w-full object-cover"
  //           />
  //         ))}
  //       </div>
  //     )}
  //   </div>
  // );
}

export default App;
