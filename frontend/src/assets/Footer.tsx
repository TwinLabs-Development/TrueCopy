import { FaHeart } from "react-icons/fa"

export default function Footer() {
    return (
        <footer className="z-1 w-full bg-beige5 py-4 text-center text-sm text-beige1 flex items-center justify-center gap-1.5">
            <span>Made with</span> 
            <FaHeart className="text-red-500" /> 
            <span>by thingy, diogress (TwinLabs)</span>
        </footer>
    )
}