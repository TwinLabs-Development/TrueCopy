import { FaHeart } from "react-icons/fa"

export default function Footer() {
    return (
        <footer className="w-full bg-gray-50 py-4 text-center text-sm text-gray-600 border-t border-gray-100 flex items-center justify-center gap-1.5">
            <span>Made with</span> 
            <FaHeart className="text-red-500" /> 
            <span>by thingy, diogress (TwinLabs)</span>
        </footer>
    )
}