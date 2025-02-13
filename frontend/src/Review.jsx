import React, { useCallback, useRef, useState, useEffect } from "react";
import SocialMediaEmbed from './SocialMediaEmbed'
import axios from 'axios'
import LabelWidget from './LabelWidget'

const SOCIAL_DOMAINS = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com", "facebook.com", "linkedin.com"];
let USER_TOKEN = localStorage.getItem('user-token')
axios.defaults.headers.common['Authorization'] = `JWT ${USER_TOKEN}`;

const E_SCALE_COLOR = "rgba(255,64,64,1)"
const I_SCALE_COLOR = "rgba(255,128,64,1)"
const A_SCALE_COLOR = "rgba(128,128,255,1)"

const LABEL_TYPES = {
  0: 0,
  1: 2,
  2: 3,
}

const submitLabel = (sid, labelValues, approved, comment) => {
  const newLabels = []
  for(let i = 0;i < 3 ;i++){
    if(labelValues[i]!==null){
      let newLabel = {
        value: labelValues[i], 
        label_type: LABEL_TYPES[i]
      }
      newLabels.push(newLabel)
    }
  }
  newLabels.push({
    value: approved?1:0,
    label_type: 4
  })
  axios.post(`/api/posts/submissions/review/${sid}`, newLabels).catch(e=>{console.error(e)})
}
export default function Review() {
  const [posts, setPosts] = useState([])
  const [postIdx, setPostIdx] = useState(0)
  const [labelValues, setLabelValues] = useState([0.5,0.5,0.5])
  const [comment, setComment] = useState("")
  const viewedPostsRef = useRef(new Set())
  const onFilterChange = useCallback((v, idx) => {
    setLabelValues(l=>{
      let newL = [...l]
      newL[idx] = v
      return newL
    })
  }, [])

  useEffect(() => {
    if(postIdx>=posts.length){
      axios.get("/api/posts/submissions").then(({data})=>{
        setPosts(data.filter(p=>!viewedPostsRef.current.has(p.id)))
        setPostIdx(0)
      })
    }
  }, [postIdx, posts])

  const onAccept = useCallback(() => {
    viewedPostsRef.current.add(posts[[postIdx]].id)
    submitLabel(posts[postIdx].id, labelValues, comment, true)
    setPostIdx(p=>p+1)
    setLabelValues([0.5, 0.5, 0.5])
    setComment("")
  }, [posts, postIdx, labelValues, comment])

  const onReject = useCallback(() => {
    viewedPostsRef.current.add(posts[[postIdx]].id)
    submitLabel(posts[postIdx].id, labelValues, comment, true)
    setPostIdx(p=>p+1)
    setLabelValues([0.5, 0.5, 0.5])
    setComment("")
  }, [posts, postIdx, labelValues, comment])

  return (
    <div style={{
      display:"flex",
      flexDirection:"column",
      justifyContent:"space-between",
      height:"100%"
    }}>
      <div style={{
        justifyContent:"center", gap: 16, textAlign:"left", 
        alignItems:"center",
        display:"flex", flexDirection:"column",
        overflowY:"auto"
      }}>
        {posts[postIdx] && 
        <>
              <div style={{width:320, height: 500}}>
                <div style={{overflowY:"hidden", height:"100%"}}>
                <SocialMediaEmbed post={posts[postIdx]}/>
                </div>
            </div>
            <div style={{maxWidth:320, fontSize: 10}}>
        {posts[postIdx].text}
            </div>
          </>
          }
    </div>
    <div style={{
      flexShrink:0,
      width:"100%",
      paddingBottom:16,
      justifyContent:"center", 
      backgroundColor:"#111"
    }}>
    <div style={{maxWidth: 320, justifyContent:"center", alignItems:"center", 
      display:"flex",  gap:16, margin:"auto", paddingBottom:24
    }}>
    <LabelWidget defaultValue={null} value={labelValues[0]} 
      barHeight={8} color={E_SCALE_COLOR} 
      title="Uplifting" onChange={onFilterChange} idx={0}/>
    <LabelWidget defaultValue={null} value={labelValues[1]} 
      barHeight={8} color={I_SCALE_COLOR} 
      title="Mind-Expanding" onChange={onFilterChange} idx={1}/>
    <LabelWidget defaultValue={null} value={labelValues[2]} 
      barHeight={8} color={A_SCALE_COLOR} 
      title="Empowering" onChange={onFilterChange} idx={2}/>
    </div>
    <div>
      <textarea style={{
        backgroundColor:"#333", borderRadius:4, padding:8, width:"100%", 
        maxWidth: 320, height: 80, fontSize:10,
        }} value={comment} 
        placeholder="Why would you recommend or reject?"
        onChange={e=>setComment(e.target.value)}/>
    </div>
    <div style={{display:"flex", gap:16, marginTop:8, justifyContent:"center"}}>
    <button style={{
      padding: "8px 12px", 
      border: "none",
      borderRadius:4,
      backgroundColor:"#666666"
    }} onClick={onAccept}>Reject</button>
    <button style={{
      padding: "8px 12px",
      border: "none",
      borderRadius:4,
      backgroundColor:"#6666ff"
    }} onClick={onReject}>Accept</button>
    </div>
    </div>
    </div>
  );
}

