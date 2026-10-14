import { MdOutlineUpload } from "react-icons/md";

export default function Body() {
  return (
    <main className="w-full px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl overflow-hidden rounded-2xl bg-white shadow-lg shadow-speed/10">
        <div className="flex flex-col items-center justify-center gap-3 px-6 pt-8 pb-4 text-center sm:px-10 sm:pt-10">
          <h1 className="text-3xl font-black tracking-tight text-speed sm:text-5xl md:text-6xl">
            TrueCopy
          </h1>
          <p className="max-w-xl text-sm leading-relaxed text-speed sm:text-base">
            Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage Lorem ipsum garbage 
          </p>
        </div>

        <div className="flex flex-col gap-6 px-4 py-6 sm:px-10 sm:pb-10">
          <div>
            <h2 className="text-xl font-bold text-speed sm:text-2xl">Register</h2>
            <p className="text-xs text-speed/75 sm:text-sm">
              Upload the original video to put into the database
            </p>
          </div>

          <div className="rounded-xl border-2 border-dashed border-speed/30 bg-gray-200 p-6 text-center transition hover:border-[#5b4837]/40 sm:p-10">
            <div className="mx-auto flex flex-row gap-4 max-w-xs cursor-pointer items-center justify-center rounded-lg bg-speed py-3 px-4 text-sm font-medium text-white shadow-sm hover:bg-speed/20 hover:text-speed transition">
              <MdOutlineUpload className="text-lg" /> Choose File
            </div>
          </div>
        </div>

      </div>
    </main>
  );
}