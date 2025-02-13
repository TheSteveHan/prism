import axios from 'axios'
import { useLayoutEffect, useEffect, useCallback, useState, useRef } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import tSNE from './tsne'
import KDTree from './KDTree'
import Spritz from './Spritz'
import VisibilitySensor from 'react-visibility-sensor'
import useWindowDimensions from './useWindowDimensions'
import Keywords from './Keywords'
import Fuse from 'fuse.js'
import {get, entries, set} from 'idb-keyval'
import LabelWidget from './LabelWidget'

const E_SCALE_COLOR = "rgba(255,64,64,1)"
const I_SCALE_COLOR = "rgba(255,128,64,1)"
const A_SCALE_COLOR = "rgba(128,128,255,1)"

const e28Classes = [
    "admiration",
    "amusement",
    "anger",
    "annoyance",
    "approval",
    "caring",
    "confusion",
    "curiosity",
    "desire",
    "disappointment",
    "disapproval",
    "disgust",
    "embarrassment",
    "excitement",
    "fear",
    "gratitude",
    "grief",
    "joy",
    "love",
    "nervousness",
    "optimism",
    "pride",
    "realization",
    "relief",
    "remorse",
    "sadness",
    "surprise",
    "neutral"
]
const e28NameToE21 = {
    "admiration": 0,  // Joy, Empowerment/Knowledge, Love, Freedom
    "amusement": 2,  // Enthusiasm
    "anger": 16,  // Anger
    "annoyance": 9,  // Frustration/Irritation/Impatience
    "approval": 4,  // Optimism
    "caring": 0,  // Empowerment/Knowledge, Love, Freedom
    "confusion": 12,  // Doubt
    "curiosity": 2,  // Enthusiasm
    "desire": 1,  // Passion
    "disappointment": 11,  // Disappointment
    "disapproval": 14,  // Blame
    "disgust": 14,  // Blame
    "embarrassment": 15,  // Discouragement
    "excitement": 2,  // Enthusiasm
    "fear": 21,  // Fear/Grief/Depression/Powerlessness/Victim
    "gratitude": 5,  // Hopefulness
    "grief": 21,  // Grief
    "joy": 0,  // Joy
    "love": 0,  // Joy, Empowerment/Knowledge, Love, Freedom
    "nervousness": 13,  // Worry
    "optimism": 4,  // Optimism
    "pride": 4,  // Optimism
    "realization": 3,  // Positive expectation/belief
    "relief": 6,  // Contentment
    "remorse": 14,  // Blame
    "sadness": 21, // Fear/Grief/Depression/Powerlessness/Victim
    "surprise": 2,  // Enthusiasm
    "neutral": 6,  // Contentment
}
const e28ToEScale = {}
e28Classes.forEach((name, idx)=>{
  e28ToEScale[idx] = e28NameToE21[name]
})

const computeEScale = (labels) =>{
  let sum = -1
  let uncertainty = 0
  for(var i=0;i < labels.length;i++){
    const v = e28ToEScale[labels[i][0]] 
    const c = labels[i][1];
    if(sum==-1){
      sum = v 
      uncertainty = 1-c
    } else {
      sum = (1-c)*sum +  c * v
    }
    uncertainty *= (1-c)
  }
  return  [1-sum/21.0, uncertainty]
}


const LABEL_TYPES = {
  0: 0,
  1: 2,
  2: 3,
}
function PostCard({p, idx, onShow}){
  const [baseFontSize, setBaseFontSize] = useState(16)
  const { width: wWidth, height: wHeight } = useWindowDimensions()
  const elmRef = useRef(null)
  const newLabelsRef = useRef([null, null, null])

  const onFilterChange = useCallback((v, idx) => {
    newLabelsRef.current[idx] = v
  }, [])

  const onVisibilityChange = useCallback((isVisible) => {
    if(isVisible){
      onShow(idx)
    } else {
      console.log(isVisible)
      const newLabels = []
      for(let i = 0;i < 3 ;i++){
        if(newLabelsRef.current[i]!==null){
          let newLabel = {
            confidence:0.8,
            value: newLabelsRef.current[i], 
            post_id:p.i,
            src: "STV",
            label_type: LABEL_TYPES[i]
          }
          newLabels.push(newLabel)
          set(`pl_${p.i}_${LABEL_TYPES[i]}`, [newLabel.value, newLabel.confidence, Date.now()])
        }
      }
      if(newLabels.length){
        console.log(newLabels)
        axios.post('/api/labels/', newLabels).catch(e=>{console.error(e)})
      }
      // reset new labels
      newLabelsRef.current=[null, null, null]
    }
  }, [idx, p])

  useLayoutEffect(() => {
    if(elmRef.current){
      const cWidth = elmRef.current.parentNode.clientWidth
      const baseFontSize = Math.min(Math.max(cWidth/70, 16), 32);
      setBaseFontSize(baseFontSize)
    }
  }, [wWidth])

  

  return p&&<VisibilitySensor onChange={onVisibilityChange}>
        <div ref={elmRef} key={p.i} 
        style={
          {
            width:"100%",
            height:"100%",  flexShrink:0,  display:"flex",
            scrollSnapAlign:"start", justifyContent:"center", alignItems:"center",
          }
        }>
          <div style={{
            boxShadow:"0px 8px 12px rgba(0,0,0,0.6)", 
            borderTop: "1px solid rgba(255,255,255,0.1)",
            minHeight: baseFontSize*20*0.618, 
            background: "linear-gradient(#FFF1, #FFF0)", 
          maxWidth:baseFontSize*20, width:"100%", textAlign:"left", 
          padding:`${baseFontSize*1.618}px ${baseFontSize}px`, borderRadius: baseFontSize/1.618, 
          fontSize: baseFontSize,
          position:"relative", overflow:"visible"
          }}>
          {p.t}
          <div style={{
position:"absolute", bottom:0, left: 0, height:15,right:0,display:"flex", alignItems:"flex-end", justifyContent:"space-evenly"
          }}>
            <LabelWidget defaultValue={p.eScore[0]} onChange={onFilterChange} idx={0} barHeight={baseFontSize/2} color="rgba(255,64,64,1)"/>
            <LabelWidget defaultValue={p.iScore[0]} onChange={onFilterChange} idx={1} barHeight={baseFontSize/2} color="rgba(255,128,64,1)"/>
            <LabelWidget defaultValue={p.aScore[0]} onChange={onFilterChange} idx={2} barHeight={baseFontSize/2} color="rgba(128,128,255,1)"/>
          </div>
        </div>
      </div>
    </VisibilitySensor>
}

function FeedControl({value, setValue}){
  const barsTop = 0//64
  const canvasRef = useRef(null)
  const valueRef = useRef(null)
  const ctxRef = useRef(null)
  const { width: wWidth, height: wHeight } = useWindowDimensions()
  valueRef.current = value
  const redraw = useCallback(() => {
    const ctx = ctxRef.current
    if(!ctx){
      return 
    }
    const canvas = canvasRef.current
    const pr = window.devicePixelRatio || 1.0
    const w = canvasRef.current.width
    const h = canvasRef.current.height
    ctx.clearRect(0, 0, w, h)
    const colors = [
      "rgba(255,64,64,AAA)",
      "rgba(255,128,64,AAA)",
      "rgba(128,128,255,AAA)",
      "rgba(128,255,255,AAA)",
      "rgba(128,255,128,AAA)",
      "rgba(255,255,128,AAA)",
    ]
    const labels = [
      {
        start:"Vibe",
        end:"Love & joy"
      },
      {
        start:"Learning",
        end:"Learning"
      },
      {
        start:"Actionable",
        end:"Action"
      },
      {
        start:"Stable",
        end:"Adaptive"
      },
      {
        start:"Comfort",
        end:"Expansion"
      },
      {
        start:"Adventerous",
        end:"Adventerous"
      },
    ]
    ctx.textBaseline = "middle";
    ctx.textAlign = "center";
    ctx.font = "20px Arial";
    const barsBottom = h - 48
    const barsPersToggle = Math.floor(w/120)
    const barWidth = w/6/barsPersToggle
    for(let i = 0;i< 6;i++){
      ctx.fillStyle = colors[i].replace("AAA", 1.0)
      ctx.fillText(labels[i].start, i * w/6 + w/12, h - 23);
      //ctx.fillText(labels[i].end, i * w/6 + w/12, 23);
      const gradient = ctx.createLinearGradient(0, barsBottom, 0, barsTop);
      const knobVal = Math.max(0.01,valueRef.current[i] )
      for (let j =0; j< barsPersToggle;j++){
        const heightFactor = knobVal// Math.max(0,knobVal * (1+(Math.random()-0.5)*0.1))
        gradient.addColorStop(0.0, colors[i].replace("AAA", 1.0));
        gradient.addColorStop(Math.min(.382*heightFactor, 1), colors[i].replace("AAA", 0.618));
        gradient.addColorStop(Math.min(1*heightFactor, 1), colors[i].replace("AAA", 0));
        ctx.fillStyle = gradient
        ctx.fillRect(
          i*w/6 + j * w/6/barsPersToggle + barWidth*0.618, barsBottom, 
          w/6/barsPersToggle- barWidth*0.618*2, 
          (barsTop - barsBottom) * heightFactor
        ); // Add a rectangle to the current path
      }
    }
  }, [value])
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d')
    ctxRef.current = ctx
    const pr = window.devicePixelRatio || 1.0
    canvas.width = canvas.clientWidth * pr
    canvas.height = canvas.clientHeight * pr

    redraw()

    const handleWheel = (e) => {
      const w = canvasRef.current.width
      const h = canvasRef.current.height
      e.preventDefault()
      const x = e.offsetX / e.target.clientWidth 
      const y = 1 - e.offsetY / e.target.clientHeight 
      const labelIdx = Math.floor(x*6)
      setValue(v=>{
        const newV = ([ ...v ])
        newV[labelIdx] -= e.deltaY/200.0
        newV[labelIdx] =  Math.min(1, newV[labelIdx])
        newV[labelIdx] =  Math.max(0, newV[labelIdx])
        return newV
      })
    };
    let isAdjusting = false
    const updateNewVToPos = (e) => {
      if(!isAdjusting){
        return
      }
      const pr = window.devicePixelRatio || 1.0
      const w = canvasRef.current.width
      const h = canvasRef.current.height
      const barsBottom = h - 48
      e.preventDefault()
      let x = 0
      let y = 0
      if(e.offsetX!==undefined){
        x = e.offsetX
        y = e.offsetY
      } else {
        // touch events
        x = Math.max(e.changedTouches[0].clientX - canvas.offsetLeft, 0)
        y = Math.max(e.changedTouches[0].clientY - canvas.offsetTop, 0)
      }
      x = x / e.target.clientWidth
      y = (barsBottom/pr - y) / (barsBottom/pr - barsTop/pr) 

      const labelIdx = Math.floor(x*6)
      setValue(v=>{
        const newV = ([ ...v ])
        newV[labelIdx] = y
        return newV
      })
    }
    const handleClick = updateNewVToPos;
    canvas.addEventListener('mousedown', (e)=>{
      isAdjusting = true
      updateNewVToPos(e)
    })
    canvas.addEventListener('mouseup', (e)=>{
      isAdjusting = false
      updateNewVToPos(e)
    })
    canvas.addEventListener('mouseleave', (e)=>{
      isAdjusting = false
      updateNewVToPos(e)
    })
    canvas.addEventListener('mousemove', updateNewVToPos)
    canvas.addEventListener('touchstart', (e)=>{
      isAdjusting = true
      updateNewVToPos(e)
    })
    canvas.addEventListener('touchend', (e)=>{
      isAdjusting = false 
      updateNewVToPos(e)
    })
    canvas.addEventListener('touchmove', updateNewVToPos)
    canvas.addEventListener('wheel', handleWheel);
    canvas.addEventListener('click', updateNewVToPos);
    return () => {
        canvas.removeEventListener('wheel', handleWheel);
        canvas.addEventListener('click', handleClick);
    }
  }, [])

  useLayoutEffect(() => {
    redraw()
  }, [redraw, value, wWidth])
  return <canvas ref={canvasRef} style={{width:"100%", height:"100%"}}/>
}

function App() {
  const [filteredPosts, setFilteredPosts] = useState([])
  const [sortedPosts, setSortedPosts] = useState([])
  const [allPosts, setAllPosts] = useState([])
  const [displayedPosts, setDisplayedPosts] = useState([])
  const [confLvl, setConfLvl] = useState(0.5)
  const [itemIdx, setItemIdx] = useState(0)
  const intersectionObserverRef = useRef(null)
  const lastShownItemIdxRef = useRef(null)
  const containerRef = useRef(null)
  const [displayMode, setDisplayMode] = useState(0)
  const [searchTerm, setSearchTerm] = useState("")
  const [searchOptions, setSearchOptions] = useState([])
  const [fcValues, setFcValues] = useState([
    0.6,Math.random(),Math.random(),Math.random(),Math.random(),0
  ])
 

  useEffect(() => {
    const postsWithLabels = {}
    Promise.all([
      entries(),
      axios.get('/api/posts/recent')
    ]).then(([entries, {data}])=>{
      for(let i = 0; i < entries.length; i++){
        const [name, values] = entries[i]
        if(name.indexOf("_")===-1){
          continue
        }
        let [_, pid, labelType] = name.split("_")
        const [val, conf, t] = values
        pid = parseInt(pid)
        labelType = parseInt(labelType)
        if(!postsWithLabels[pid]){
          postsWithLabels[pid] = {}
        }
        postsWithLabels[pid][labelType] = val 
      }
      for(let i = 0;i < data.length;i++){
        if(postsWithLabels[data[i].i]){
          console.log(data[i])
          // refuse to serve this
         continue 
        }
        data[i].eScore = computeEScale(data[i].l[1])
        data[i].iScore = computeEScale(data[i].l[1])
        data[i].aScore = computeEScale(data[i].l[1])
        data[i].words = new Set(data[i].t.toLowerCase().match(/\b[a-z]+\b/g))
      }
      setAllPosts(data.filter(x=>x.eScore!==undefined))
    })
  }, [])

  useEffect(() => {
    const eLvl = fcValues[0]
    const noise = fcValues[5]
    const sorted = allPosts.sort((a,b)=>{
      const v = Math.abs(a.eScore[0]-eLvl) *(1.0+Math.random()*noise*20) - Math.abs(b.eScore[0]-eLvl)*(1.0+Math.random()*noise*20)
      return v
    })
    setSortedPosts([...sorted])
    setItemIdx(0)
    containerRef.current.scrollTop = 0
  }, [allPosts, confLvl, fcValues])

  useEffect(() => {
    setDisplayedPosts(
      filteredPosts.slice(0, itemIdx+3)
    )
  }, [itemIdx, filteredPosts])

  useEffect(() => {
    setFilteredPosts(sortedPosts.filter(p=>{
      if(!searchTerm){
        return true
      }
      const words = searchTerm.toLowerCase().split(" ")
      let matchCount = 0 
      for(let i = 0; i< words.length; i++){
        if(p.words.has(words[i])){
          matchCount +=1
        }
      }
      if(matchCount==words.length){
        return true
      }
    }))

  }, [searchTerm, sortedPosts])

  const onChangeELvl = useCallback((e) => {
    const newVal = e.target.value
    setELvl(newVal)
  }, [])

  const onShow = useCallback((postIdx)=>{
    setItemIdx(postIdx)
    lastShownItemIdxRef.current = postIdx
  }, [])
  const onScorll =  useCallback((e)=>{
    return
    console.log(e.target.scrollTop, lastShownItemIdxRef.current)
    if(e.target.scrollTop>e.target.clientHeight && lastShownItemIdxRef.current>0){
      setItemIdx(lastShownItemIdxRef.current)
      lastShownItemIdxRef.current = -1
      e.target.scrollTop - e.target.clientHeight
    }
  }, [])
  const onSearch = useCallback((e) => {
     setSearchTerm(e.target.value)
  }, [])
  const onFilterChange = useCallback((v, idx) => {
    setFcValues(old=>{
      const newV = [...old]
      newV[idx] = v
      return newV
    })
  }, [])
  return (
    <div className="no-scrollbar" style={{
      display:"flex", flexDirection:"column", flex:1,  padding:16, overflow:"hidden", justifyContent:"center", alignItems:"center"}}> 
      <div style={{position:"relative", maxWidth:400, flexShrink:0, width:"100%"}}>
        <input spellCheck="false" placeholder="Search..." value={searchTerm} onChange={onSearch} style={{
          width:"calc(100% - 32px)",
          padding:"12px 16px", 
          outline:"none",
          borderRadius:32,
          border: "none",
        }}/>
        <div style={{position:"absolute", top:0, right:12, 
          fontSize:32, fontWeight:100,color:"#555", lineHeight:"38px"}}>
          ⌕
        </div>
        <div style={{position:"absolute", maxHeight: "38.2vh"}}>
        </div>
      </div>
      <div ref={containerRef} className="no-scrollbar" style={{
        marginLeft: -16, marginRight:-16, 
        flex:1, display:"flex", flexDirection:"column",gap:16, justifyContent:"flex-start", alignItems:"center", 
        overflowY:"auto", overflowX:"hidden", scrollSnapType:"y mandatory", scrollSnapStop:"always", 
        maskImage: "linear-gradient(to bottom, rgba(0, 0, 0, 0), black 20%, black 80%, rgba(0, 0, 0, 0))"
      }} onScroll={onScorll}>
      {

      displayedPosts.map(
        (p,idx)=><PostCard p={p} idx={idx} onShow={onShow}/>)
      }
      </div>
      <div style={{overflowX:"visible",marginBottom: 8, width:"100%", display:"flex", justifyContent:"space-between"}}>
        <LabelWidget defaultValue={null} value={fcValues[0]} barHeight={8} color={E_SCALE_COLOR} title="Vibe" onChange={onFilterChange} idx={0}/>
        <LabelWidget defaultValue={null} value={fcValues[1]} barHeight={8} color={I_SCALE_COLOR} title="Learning" onChange={onFilterChange} idx={1}/>
        <LabelWidget defaultValue={null} value={fcValues[2]} barHeight={8} color={A_SCALE_COLOR} title="Action" onChange={onFilterChange} idx={2}/>
      </div>
    </div>
  )
}

export default App
