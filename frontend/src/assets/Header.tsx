import logo from "./book.svg";

export default function Header() {
  return (
    <>
      <header className="drop-shadow-lg bg-beige5 text-beige1 p-6">
        <div className="mx-auto grid grid-cols-[auto_1fr_auto] items-center px-12">
          {/* LEFT SIDE*/}
          <div className="flex flex-row items-center gap-4">
            <img src={logo} className="h-8 w-auto object-contain" />
            <h1 className="text-2xl font-black italic leading-none">
              TrueCopy
            </h1>
          </div>

          {/* RIGHT SIDE */}
          <div className="justify-end flex flex-row text-xl items-center gap-12 font-medium">
            <button
              type="button"
              className="cursor-pointer transition-all duration-300 ease-out hover:scale-110 hover:opacity-80 active:scale-95"
            >
              {/* placeholders, idk why i put an anchor tag, just incase it switches tabs? */}
              <a href="#">Verify</a>
            </button>
            <button
              type="button"
              className="cursor-pointer transition-all duration-300 ease-out hover:scale-110 hover:opacity-80 active:scale-95"
            >
              <a href="#">Register</a>
            </button>
          </div>
        </div>
      </header>
    </>
  );
}
