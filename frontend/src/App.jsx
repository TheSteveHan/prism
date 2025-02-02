import axios from 'axios'
import { useEffect, useCallback, useState, useRef } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import tSNE from './tsne'
import KDTree from './KDTree'
import Spritz from './Spritz'

function normalize2DArray(array) {
    // Initialize min and max values
    let min = Infinity;
    let max = -Infinity;

    // Find the global min and max using nested loops
    for (let i = 0; i < array.length; i++) {
        for (let j = 0; j < array[i].length; j++) {
            const value = array[i][j];
            if (value < min) min = value;
            if (value > max) max = value;
        }
    }

    // Normalize the array in place
    for (let i = 0; i < array.length; i++) {
        for (let j = 0; j < array[i].length; j++) {
            array[i][j] = (array[i][j] - min) / (max - min);
        }
    }

    return array; // The array is modified in place but also returned for convenience
}

function computeHistograms(array, bins = 10) {
    // Transpose the 2D array to get dimensions as separate arrays
    const dimensions = array[0].map((_, colIndex) => array.map(row => row[colIndex]));

    // Find global min and max for each dimension
    const histograms = dimensions.map(dimension => {
        const min = Math.min(...dimension);
        const max = Math.max(...dimension);

        // Initialize bins
        const binWidth = (max - min) / bins;
        const histogram = new Array(bins).fill(0);

        // Compute histogram
        dimension.forEach(value => {
            const binIndex = Math.min(
                bins - 1,
                Math.floor((value - min) / binWidth)
            );
            histogram[binIndex]++;
        });

        return {
            min,
            max,
            bins: histogram
        };
    });

    // Find the global max bin value across all histograms
    const globalMax = Math.max(...histograms.flatMap(h => h.bins));

    // Normalize histograms so the largest bin value is 1
    const normalizedHistograms = histograms.map(histogram => ({
        min: histogram.min,
        max: histogram.max,
        bins: histogram.bins.map(bin => bin / globalMax)
    }));

    return normalizedHistograms;
}

function App() {
  const [count, setCount] = useState(0)
  const [dims, setDims] = useState(0)
  const [targetVec, setTargetVec] = useState([])
  const [kdTree, setKdTree] = useState(null)
  const [results, setResults] = useState([])
  const [embeddings, setEmbeddings] = useState([])
  const [histograms, setHistograms] = useState([])
  const tsneRef = useRef(null)
  const canvasRef = useRef(null)
  const solutionRef = useRef([])
  const embeddingsRef = useRef([])

  useEffect(() => {
    if(tsneRef.current){
      return
    }

    axios.get('/embeddings_0.json').then(({data})=>{
      const newEmbeddings = Object.keys(data).filter(k=>k.length>90).map(k=>
        ({
          text:k,
          vec:data[k]
        })
        )
      let newDims = newEmbeddings[0].vec.length
      setDims(newDims)
      setTargetVec(Array.from({length:newDims}).fill(0.5))
      const vecs = normalize2DArray(newEmbeddings.map(e=>e.vec))
      const newHistograms = computeHistograms(vecs)
      setHistograms(newHistograms)
      const indices = (new Array(newDims)).fill(0).map((_, idx)=>idx)
      const newTree = new KDTree(vecs, indices);
      setKdTree(newTree)
      setEmbeddings(newEmbeddings)
    })
  }, [])

  useEffect(() => {
    if(kdTree==null){
      return
    }
    const res = kdTree.nearest_k(targetVec, 600)
    console.log(res)
    setResults(res)

  }, [targetVec, kdTree])

  const handleKnobChange = useCallback((e) => {
    const idx = e.target.dataset.idx
    setTargetVec(v=>{
      const tgt = [...v]
      tgt[idx] = parseFloat(e.target.value)
      console.log(tgt)
      return tgt
    })
     
  }, [])

  return (
    <div style={{display:"flex", flexDirection:"column",flex:1,  padding:32, overflow:"hidden"}}> 
      <div style={{flex:1, display:"flex", flexWrap:"wrap", gap:16, justifyContent:"center", alignItems:"center",
      overflowY:"auto", overflowX:"hidden"}}>
      {
        results.map(r=><div style={{height:"18ch", width:"35ch", textAlign:"left", 
          backgroundColor:"rgba(255,255,255,0.1)", padding:"12px 16px", borderRadius: 8}}>
          {embeddings[r.point.idx].text}
          {false&&
          <Spritz text={embeddings[r.point.idx].text} wpm={800}/>
          }
        </div>)
      }
      </div>
      <div style={{flex:0, maxHeight: "38.2vh"}}>
        <div style={{display: "flex", flexDirection:"row", gap: 16, justifyContent:"space-between", flexWrap:"wrap"}}>
          {histograms.map((ent,idx)=><div>
            <div style={{display:"flex", height: 80, alignItems:"flex-end"}}>
            {ent.bins.map(val=><div style={{height: `${val*100}%`, flex:1, backgroundColor: "rgba(255,255,255,0.3)"}}></div>)}
            </div>
            <div style={{display:"flex", justifyContent:"space-between", fontSize:8, width:"100%"}}>
              <div>
                {ent.min.toFixed(2)} 
              </div>
              <div>
                {ent.max.toFixed(2)}
              </div>
            </div>
            <input type="range"  min="0" max="1" value={targetVec[idx]} 
              style={{width:"100%"}}
              data-idx={idx} step={0.0001} onChange={handleKnobChange}/>
          </div>)}
        </div>
      </div>
    </div>
  )
}

export default App
