import './index.css'

function App() {
  
  return (
    <>
      <div className='flex flex-col justify-center items-center min-h-screen'>
        <div className="text-center">
          <h1 className="font-bold text-4xl">TrueCopy</h1>
          <p className="mt-2 text-gray-500">Motto in progress idk ginagawa palang</p>
        </div>
        <div>
          <form className="flex flex-col items-center gap-4">
            <input type='file' name="file" />
            <button type="submit" className="rounded-lg bg-blue-500 px-6 py-2 text-white">Upload File</button>
          </form>
        </div>
      </div>
    </>
  )
}

export default App
