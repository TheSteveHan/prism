import { useEffect, useCallback, useState, useRef } from 'react'


function Spritz({text, wpm}) {
  const wordsRef = useRef([])
  const wordIdxRef = useRef(0)
  const [wordParts, setWordParts] = useState(["", "", ""])

  useEffect(() => {
    wordsRef.current = text.replace("\n", " ").split(" ")
    wordIdxRef.current = 0
  }, [text])


  useEffect(() => {
    const interVal = setInterval(
      () => {
        const word = wordsRef.current[wordIdxRef.current++]
        const stop = Math.round((word.length+1)*0.4)-1;
        setWordParts([word.slice(0, stop), word[stop], word.slice(stop + 1)])
        wordIdxRef.current = wordIdxRef.current%wordsRef.current.length
      }, 60000/wpm
    )
    return () => {
      clearInterval(interVal)
    }
  }, [wpm])

  return (
    <div style={{
      display:"flex", flexDirection:"row", borderTop:"1px solid white", height: 25, 
      borderBottom: "1px solid white", position:'relative'}}>
      <div style={{width: 2, height:4, position: "absolute", left: "38.2%", marginLeft:3, top:0, backgroundColor:"white"}}>
      </div>
      <div style={{width: 2, height:4, position: "absolute", left: "38.2%", marginLeft:3, bottom:0, backgroundColor:"white"}}>
      </div>
      <div style={{width: "38.2%", overflow:"hidden", textAlign:"right", textWrap:"nowrap"}}>
      {wordParts[0]}
      </div>
      <div style={{color:"red",overflow:"hidden"}}>
      {wordParts[1]}
      </div>
      <div>
      {wordParts[2]}
      </div>
    </div>
  )
}

export default Spritz
