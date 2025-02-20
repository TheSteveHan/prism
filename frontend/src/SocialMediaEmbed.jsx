import React, {useState, useEffect} from "react";
import { TikTokEmbed, InstagramEmbed, YouTubeEmbed } from 'react-social-media-embed';


const VIDEO_PATTERNS = [
  /https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
  /https?:\/\/(www\.)?youtu\.be\/[\w-]+/,
  /https?:\/\/(www\.)?tiktok\.com\/.*\/video\/\d+/,
  /https?:\/\/(www\.)?instagram\.com\/reel\/[\w-]+/,
  /https?:\/\/(www\.)?facebook\.com\/watch\/\?v=\d+/,
  /https?:\/\/(www\.)?linkedin\.com\/feed\/update\/urn:li:activity:\d+/
];

const SocialMediaEmbed = ({ post }) => {
  const {uri, videos} = post
  const [elm, setElm] = useState(null)
  useEffect(() => {
    if(!uri){
      console.log(post)
      return
    }
    let EmbedElm = null
    if(uri.includes("tiktok.com")){
      EmbedElm = TikTokEmbed
    } else if(uri.includes('instagram.com')){
      EmbedElm = InstagramEmbed
    } else if(uri.includes("youtu")){
      EmbedElm = YouTubeEmbed
    }
    setTimeout(() => {
      setElm(<EmbedElm url={uri} width={320}/>)
    }, 1000)
    setElm(null)
  }, [post, uri])

  return elm? (
    <div>
      {elm}
    </div>

  ): <div></div>
};

export default SocialMediaEmbed;
