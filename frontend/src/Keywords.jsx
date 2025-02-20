import { useMemo, useLayoutEffect, useEffect, useCallback, useState, useRef } from 'react'
import nonTopics from './nonTopics'
function getFrequentWords(posts, minFrequency = 2) {
    const wordCounts = {};
    const wordEmotion = {};
    
    posts.slice(2000).forEach((post, idx)=> {
        const words = post.words
        if (words) {
            words.forEach(word => {
               wordEmotion[word] = (0.99*wordEmotion[word] || 0) + 0.01 * Math.abs(post.eScore[0] - 0.5) **2 ;
            });
        }
    });
    
  return Object.entries(wordEmotion)
    .filter(([w, _])=>!nonTopics.has(w))
    .sort((a, b) => b[1] - a[1]).slice(0, 100)
    .map(([word, count]) => ({ word, count }));
}

export default function Keywords({posts}){
  const keywords = useMemo(()=>{
    let res = getFrequentWords(posts)
    return res
  }, [posts])

  return <div style={{display:"flex", flexWrap:"wrap", gap:"4px 8px"}}>
  {
    keywords.map((w)=><div key={w.word} title={w.count}>{w.word}</div>)
  }
</div>

}
