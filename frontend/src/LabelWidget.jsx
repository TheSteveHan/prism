import { useLayoutEffect, useEffect, useCallback, useState, useRef } from 'react'

function LabelWidget({
  barHeight, title, color, defaultValue=0.5, value=null,
  onChange, idx
}){
  const adjustmentSteps = 6
  const [newVal, setNewVal] = useState(defaultValue==null? value: defaultValue)
  const containerRef = useRef(null)
  const draggingRef = useRef(false)
  const onClick = useCallback((e) => {
    // Get bounding box of the div
    const rect = containerRef.current.getBoundingClientRect();

    // Calculate click position relative to the div
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    let v = Math.round(x/e.target.clientWidth*adjustmentSteps)/adjustmentSteps
    setNewVal(v)
  }, [])

  const updateValue = useCallback((e) => {
    const rect = containerRef.current.getBoundingClientRect();

    // Calculate click position relative to the div
    let x, y;
    if(event.clientX!==undefined){
      x = event.clientX
      y = event.clientY
    } else {
      x = event.changedTouches[0].clientX;
      y = event.changedTouches[0].clientY;
    }
    x -= rect.left;
    y -= rect.top;
    let v = Math.max(Math.min(Math.round(x/e.target.clientWidth*adjustmentSteps)/adjustmentSteps, 1.0), 0)
    setNewVal(oldV =>{
      if(oldV!=v && window.navigator?.vibrate){
        window.navigator.vibrate(50)
      }
      if(oldV!=v){
        setTimeout(
          () => {
            onChange && onChange(v, idx)
          }, 0
        )
      }
      return v
    })
    e.stopPropagation()
  }, [onChange])

  const onDragStart = useCallback((e) => {
    draggingRef.current = true
    updateValue(e)
  }, [updateValue])

  const onDrag = useCallback((e) => {
    if(!draggingRef.current){
      return
    }
    updateValue(e)
  }, [updateValue])

  const onDragEnd = useCallback((e) => {
    draggingRef.current = false
    //updateValue(e)
  }, [updateValue])

  return <div 
    key={idx}
    ref={containerRef}
    onMouseMove={onDrag}
    onMouseDown={onDragStart}
    onMouseUp={onDragEnd}
    onMouseLeave={onDragEnd}
    onTouchStart={onDragStart}
    onTouchMove={onDrag}
    onTouchEnd={onDragEnd}
    style={{
    top:8,
    width:"calc(33% - 8px)", height:48, position:"relative"}} onClick={onClick}
  >
    <div style={{position:"absolute", 
      pinterEvent:"none",
      boxShadow:"inset 0px 3px 3px #000e, inset 0px -1px 2px rgba(255,255,255,0.1)",
      height:barHeight, bottom:8+barHeight, 
      background: `
      linear-gradient(to left, ${color} 38.2%, ${color.replace(",1)", ", 0.5)")})
      `,
      width:"100%", borderRadius:barHeight, 
      opacity:1
    }}>
      {/*Bar*/}
    </div>
    {new Array(adjustmentSteps+1).fill(0).map((_, i)=>
    <div key={i} style={{
      pointerEvents:"none",
      position:"absolute",bottom:8+barHeight * 2.382,
      left: `calc(${i*100/adjustmentSteps}% + ${(i==0?barHeight/2:((i==adjustmentSteps)?-barHeight/2:0))-1}px)`,
      width:2,height:6, backgroundColor: color, opacity:0.2
    }}>
    </div>
    )}
    {defaultValue!==null&& <div style={{
      pointerEvents:"none",
      position:"absolute", 
      boxShadow:"inset 0px 3px 3px #000e, inset 0px -1px 2px rgba(255,255,255,0.1)",
      left: `calc(${defaultValue*100}% - ${defaultValue==0?0:(defaultValue==1?barHeight:barHeight/2)}px)`,
      height:barHeight+2,width:barHeight+2,bottom:8+barHeight * 2.382, backgroundColor:color, borderRadius:barHeight, opacity:defaultValue==newVal? 1: 0.2, 
    }}>
      {/*default dot*/}
    </div>
    }
    
    <div style={{
      pointerEvents:"none",
      visibility:defaultValue==newVal? "hidden": "visible", 
      position:"absolute", 
      boxShadow:"inset 0px 3px 3px #000e, inset 0px -1px 2px rgba(255,255,255,0.1)",
      left: `calc(${newVal*100}% - ${newVal==0?0:(newVal==1?barHeight+1:barHeight/2+1)}px)`,
      height:barHeight+2, bottom:8+barHeight* 2.382, backgroundColor:color,width:barHeight+2, borderRadius:barHeight, 
      opacity:1
    }}>
      {/*new dot*/}
    </div>
    {title&& <div 
      style={{
        pointerEvents:"none",
        position:"absolute",
        bottom:-0,
        textAlign:"center",
        width:"100%",
        color:color,
        fontSize: 8,
        textTransform:"uppercase",
        letterSpacing: 0,
        fontWeight: 900,
        textShadow: "0px 2px 4px black",
      }}
    >&nbsp;{title}</div>
    }
  </div>
}

export default LabelWidget
