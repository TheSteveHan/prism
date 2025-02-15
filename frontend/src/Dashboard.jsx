import React, { useCallback, useRef, useState, useEffect } from "react";
import { Line } from 'react-chartjs-2';
import SocialMediaEmbed from './SocialMediaEmbed'
import axios from 'axios'
import LabelWidget from './LabelWidget'
import "./Dashboard.css"
import 'chartjs-adapter-moment';
import {Chart, TimeScale,LinearScale, PointElement, LineElement, Tooltip, Legend} from "chart.js";
Chart.register(LinearScale, PointElement, LineElement, Tooltip, Legend, TimeScale);
import OpsNav from './OpsNav'


const SOCIAL_DOMAINS = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com", "facebook.com", "linkedin.com"];
let USER_TOKEN = localStorage.getItem('user-token')
axios.defaults.headers.common['Authorization'] = `JWT ${USER_TOKEN}`;

const E_SCALE_COLOR = "rgba(255,64,64,1)"
const I_SCALE_COLOR = "rgba(255,128,64,1)"
const A_SCALE_COLOR = "rgba(128,128,255,1)"

const LABEL_TYPES = {
  0: 1, // aggregate emotion score
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

function toCap(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}
function generateVideoStats(videoData) {
    let stats = {
        totalVideos: videoData.length,
        averageAScore: 0,
        averageEScore: 0,
        averageIScore: 0,
        platformDistribution: { TikTok: 0, Instagram: 0, Youtube:0, Other: 0 },
        scoreDistribution: { a: Array(7).fill(0), e: Array(7).fill(0), i: Array(7).fill(0) },
        timeSeries: []
    };

    let aScores = [], eScores = [], iScores = [];
    let cumulativeCount = 0;
    let timeSeriesMap = {};

    function categorizeScore(score) {
        return Math.min(6, Math.floor(score * 7));
    }
    videoData.sort((a, b) => new Date(a.indexed_at) - new Date(b.indexed_at));

    videoData.forEach(video => {
        let uri = video.uri || "";
        if (uri.includes("tiktok.com")) {
            stats.platformDistribution.TikTok++;
        } else if (uri.includes("instagram.com")) {
            stats.platformDistribution.Instagram++;
        } else if (uri.includes("youtu")) {
            stats.platformDistribution.Youtube++;
        } else {
            stats.platformDistribution.Other++;
        }

        if (video.a_score !== null && video.a_score !== undefined) {
            aScores.push(video.a_score);
            stats.scoreDistribution.a[categorizeScore(video.a_score)]++;
        }
        if (video.e_score !== null && video.e_score !== undefined) {
            eScores.push(video.e_score);
            stats.scoreDistribution.e[categorizeScore(video.e_score)]++;
        }
        if (video.i_score !== null && video.i_score !== undefined) {
            iScores.push(video.i_score);
            stats.scoreDistribution.i[categorizeScore(video.i_score)]++;
        }
        let date = new Date(video.indexed_at+"Z").toISOString().split(':')[0]+":00:00Z";
        cumulativeCount++;
        timeSeriesMap[date] = cumulativeCount;
    });

    stats.averageAScore = aScores.length ? aScores.reduce((a, b) => a + b, 0) / aScores.length : null;
    stats.averageEScore = eScores.length ? eScores.reduce((a, b) => a + b, 0) / eScores.length : null;
    stats.averageIScore = iScores.length ? iScores.reduce((a, b) => a + b, 0) / iScores.length : null;
    stats.timeSeries = Object.entries(timeSeriesMap).map(([date, count]) => ({ date, count }));

    const maxScoreCount = Math.max(...stats.scoreDistribution.a, ...stats.scoreDistribution.e, ...stats.scoreDistribution.i, 1);

    stats.scoreDistribution.a = stats.scoreDistribution.a.map(v => v / maxScoreCount);
    stats.scoreDistribution.e = stats.scoreDistribution.e.map(v => v / maxScoreCount);
    stats.scoreDistribution.i = stats.scoreDistribution.i.map(v => v / maxScoreCount);
    stats.maxScoreCount = maxScoreCount 


    return stats;
}

const DIMS = ['Uplifting', 'Mind-Expanding', 'Empowering']
export default function Review() {
  const [posts, setPosts] = useState([])
  const [labelValues, setLabelValues] = useState([0.5,0.5,0.5])
  const [stats, setStats] = useState(null)

  const onFilterChange = useCallback((v, idx) => {
    setLabelValues(l=>{
      let newL = [...l]
      newL[idx] = v
      return newL
    })
  }, [])

  useEffect(() => {
      axios.get("/api/posts/all-videos").then(({data})=>{
        setPosts(data)
        setStats(generateVideoStats(data))
      })
  }, [])
  const timeSeriesData = stats?{
    labels: stats.timeSeries.map(entry => entry.date),
    datasets: [
      {
        label: "Cumulative Videos",
        data: stats.timeSeries.map(entry => entry.count),
        borderColor: "#4CAF50",
        backgroundColor: "rgba(76, 175, 80, 0.2)",
        fill: true,
      }
    ]
  }:null;
  const timeSeriesOptions = {
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'day'
        }
      },
      y: {
        beginAtZero: true
      }
    }
  };


  return (
    <div style={{
      display:"flex",
      flexDirection:"column",
      justifyContent:"flex-start",
      height:"100%"
    }}>
      <OpsNav/>
      <div style={{
        justifyContent:"flex-start", gap: 16, textAlign:"left", 
        alignItems:"flex-start",
        display:"flex", flexDirection:"row", flexWrap:"wrap",
        overflowY:"auto", padding:16,
      }}>
        {false&&posts.map(p=>
        <a href={p.uri} style={{
          cursor:"pointer", color:"white", textDecoration:"none", 
          }}><div key={p.id} style={{
          height:600, width:320, overflow:"hidden", textWrap:"wrap", backgroundColor:"#333", 
          borderRadius:8, justifyContent:"center", alignItems:"center", display:"flex"
        }}>
          View on {toCap(p.uri?.split(".")[1])}
</div></a>)}
  {stats&& <div style={{ fontFamily: 'Arial, sans-serif', margin: '20px' ,margin:"auto"}}>
    <h1 style={{ color: '#EEE' }}>Bloom Feed Stats</h1>
    <div style={{display:"flex", gap:16, marginBottom:16}}>
      <div className="statsTile">
        <div>
        {stats.totalVideos}
        </div>
        <div>
        Total
        </div>
      </div>
      <div className="statsTile">
        <div>
        {stats.platformDistribution.TikTok}
        </div>
        <div>
          Tiktok
        </div>
      </div>
      <div className="statsTile">
        <div>
        {stats.platformDistribution.Instagram}
        </div>
        <div>
          Instagram
        </div>
      </div>
      <div className="statsTile">
        <div>
        {stats.platformDistribution.Youtube}
        </div>
        <div>
          Youtube
        </div>
      </div>
    </div>
    <div style={{display:"flex", gap:16}}>
    {['e', 'i', 'a'].map((key, index) => (
      <div key={index} style={{
        backgroundColor:"#333", padding: "16px 32px 16px",  borderRadius:8,fontSize:10, 
        fontWeight:900,
        display:"flex", flexDirection:"column", justifyContent:'center', alignItems:"center"}}>
                    <div style={{ position: 'relative', display: 'flex', gap: '5px', alignItems: 'flex-end', height: '100px' }}>
                        {stats.scoreDistribution[key].map((val, idx) => (
                            <div key={idx} style={{
                                width: '30px',
                                height: `${val* 100}%`,
                                backgroundColor: '#FFFFff33',
                                borderRadius:3,
                                textAlign: 'center',
                                color: 'white',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center', fontSize:8, position:"relative",
                            }}>
                              {val>0? val*stats.maxScoreCount:""}
                                <div style={{position:"absolute", bottom: -16, opacity:0.6}}>{idx+1}</div>
                            </div>
                        ))}
                    </div>
                    <div style={{marginTop:24}}>{DIMS[index]}</div>
                </div>
            ))}
    </div>
            {timeSeriesData &&
            <Line data={timeSeriesData} options={timeSeriesOptions}/>
            }
  </div>
  }
      
    </div>
    <div style={{
      flexShrink:0,
      width:"100%",
      paddingBottom:16,
      justifyContent:"center", 
      backgroundColor:"#111",
      display:"none"
    }}>
    <div style={{maxWidth: 600, justifyContent:"center", alignItems:"center", 
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
    </div>
    </div>
  );
}


