import logo from './suisei.png'


export default function Header() {
    return <>
        <header className="bg-speed p-4">
            <div className="max-w-5xl mx-auto flex flex-row items-center justify-between">
                <div className="flex flex-row items-center gap-4">
                    <img src={logo} className='rounded-lg h-8 w-auto object-contain' />
                    <h1 className="text-2xl font-bold text-wallahi leading-none">TrueCopy</h1>
                </div>

                <div className="flex flex-row items-center gap-6 text-[#ececec] text-sm font-medium">
                    <button type="button" className="text-wallahi">Verify</button>
                    <button type="button" className="text-wallahi">Register</button>
                </div>
            </div>
            
        </header>
    </>
}