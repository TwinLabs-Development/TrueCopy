import logo from "./book.svg";

type Page = "register" | "verify";

type HeaderProps = {
  page: Page;
  setPage: (page: Page) => void;
  canRegister: boolean;
  isUploading: boolean;
};

export default function Header({page, setPage, canRegister, isUploading}: HeaderProps) {
  const buttonBase =
    "cursor-pointer transition-all duration-300 ease-out hover:scale-110 hover:opacity-80 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:scale-100 disabled:hover:opacity-40";
  
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
            onClick={() => setPage("verify")}
            disabled={isUploading}
            className={`${buttonBase} ${page === "verify" ? "underline underline-offset-8" : ""}`}>
              Verify
            </button>
          <button
            type="button"
            onClick={() => setPage("register")}
            disabled={!canRegister || isUploading}
            className={`${buttonBase} ${page === "register" ? "underline underline-offset-8" : ""}`}>
              Register
            </button>
          </div>
        </div>
      </header>
    </>
  );
}
