import noteIcon from "./note.svg";

export default function Body() {
  return (
    <main className="flex flex-col min-h-screen w-full max-w-7xl mx-auto">
      {/* MAIN CONTAINER */}
      <div className="drop-shadow-glow flex flex-col flex-1 bg-beige1 px-20 gap-20">
        {/* SECTION 1 */}
        <div className="flex flex-col items-center justify-center text-center">
          <h1 className="py-10 text-[8rem] font-extrabold tracking-tight">
            TrueCopy
          </h1>

          <p className="text-justify">
            Lorem ipsum dolor sit amet consectetur adipisicing elit. Explicabo
            id veniam beatae quod non optio tempore aliquam, ullam reprehenderit
            a quisquam quos consectetur accusantium voluptatum distinctio rem
            libero quaerat perspiciatis. Lorem ipsum dolor, sit amet consectetur
            adipisicing elit. Illo accusamus enim ipsa ullam numquam
            voluptatibus incidunt temporibus ducimus minima. Dolorum rem
            quibusdam omnis perspiciatis accusamus ipsam non dignissimos?
            Fugiat, adipisci. Lorem ipsum dolor sit amet consectetur adipisicing
            elit. Quidem deserunt dolore hic error. Debitis ratione saepe
            tempore? Quam sequi, similique nobis excepturi adipisci saepe.
            Sapiente saepe deserunt beatae magni at.
          </p>
        </div>

        {/* SECTION 2 */}
        <div className="flex flex-col px-40 gap-6">
          <h2 className="text-5xl font-semibold italic">Register</h2>
          <p>Upload the original video to put into the database</p>

          {/* FILE UPLOAD CONTAINER */}
          <div className="rounded-xl border-[0.3rem] border-dashed border-gray2 bg-gray1 text-center py-30 transition-all">
            <div className="drop-shadow-lg grid grid-cols-[auto_1fr_auto] items-center mx-auto max-w-xs cursor-pointer rounded-lg bg-beige5 text-beige1 py-3 px-4 text-sm font-medium transition-all duration-300 ease-out hover:opacity-80">
              <img className="w-6 h-6" src={noteIcon} alt="" />
              <p className="justify-self-center">Choose File</p>
              <div className="w-6" />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
