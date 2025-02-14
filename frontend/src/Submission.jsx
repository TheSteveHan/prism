import React, { useState, useEffect } from "react";
import SocialMediaEmbed from './SocialMediaEmbed'
import axios from 'axios'
import aesjs from 'aes-js'

const VIDEO_PATTERNS = [
  /https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
  /https?:\/\/(www\.)?youtu\.be\/[\w-]+/,
  /https?:\/\/(www\.)?tiktok\.com\/.*\/video\/\d+/,
  /https?:\/\/(www\.)?instagram\.com\/reel\/[\w-]+/,
  /https?:\/\/(www\.)?facebook\.com\/watch\/\?v=\d+/,
  /https?:\/\/(www\.)?linkedin\.com\/feed\/update\/urn:li:activity:\d+/
];

function isCSV(text) {
  if(text[0]=="<"){
    return false
  }
    if (typeof text !== "string") return false;

    // Split into lines, handling different line endings
    const lines = text.trim().split(/\r?\n/);
    if (lines.length < 2) return false; // Must have at least a header and one row

    // Detect delimiter (comma, semicolon, or tab) based on the first line
    const delimiters = [','];
    let detectedDelimiter = null;
    let headerColumns = [];

    for (let delimiter of delimiters) {
        const columns = parseCSVLine(lines[0], delimiter);
        if (columns.length > 1) {
            detectedDelimiter = delimiter;
            headerColumns = columns;
            break;
        }
    }

    if (!detectedDelimiter) return false; // No valid delimiter found

    // Check if all rows have the same number of columns
    for (let i = 1; i < lines.length; i++) {
        if (parseCSVLine(lines[i], detectedDelimiter).length !== headerColumns.length) {
            return false;
        }
    }

    return true;
}

// Function to parse a CSV line correctly considering quoted fields
function parseCSVLine(line, delimiter) {
    const regex = new RegExp(
        `(?:^|${delimiter})("([^"]*(?:""[^"]*)*)"|[^${delimiter}]*)`,
        'g'
    );
    let matches = [];
    let match;

    while ((match = regex.exec(line)) !== null) {
        let value = match[2] !== undefined ? match[2].replace(/""/g, '"') : match[1];
        matches.push(value);
      if(matches.length>5){
        return []
      }
    }

    return matches;
}

function parseCSV(csvText) {
    if (typeof csvText !== "string") return [];

    const lines = csvText.trim().split(/\r?\n/);
    if (lines.length < 2) return [];

    // Parse header
    const headers = lines[0].split(/,(?=(?:[^"]*"[^"]*")*[^"]*$)/); // Handles quoted fields
    const dataRows = lines.slice(1);

    let urlIndex = -1, titleIndex = -1, descriptionIndex = -1;
    let rowData = [];

    // Determine column types based on content
    let sampleRow = dataRows[0].split(/,(?=(?:[^"]*"[^"]*")*[^"]*$)/);
    let lengths = sampleRow.map(field => field.replace(/"/g, '').length);

    urlIndex = sampleRow.findIndex(field => field.startsWith('"http') || field.startsWith('http'));
    if (urlIndex === -1) return []; // No URL found, invalid CSV

    let nonUrlIndexes = [...Array(sampleRow.length).keys()].filter(i => i !== urlIndex);
    nonUrlIndexes.sort((a, b) => lengths[a] - lengths[b]); // Sort by field length

    titleIndex = nonUrlIndexes[0]; // Shortest non-URL field
    descriptionIndex = nonUrlIndexes[1]; // Longest non-URL field

    // Convert rows into structured objects
    for (let row of dataRows) {
        let fields = row.split(/,(?=(?:[^"]*"[^"]*")*[^"]*$)/).map(field => field.replace(/^"|"$/g, '')); // Remove surrounding quotes
        if (fields.length !== headers.length) continue;

        rowData.push({
            url: fields[urlIndex],
            title: fields[titleIndex],
            description: fields[descriptionIndex]
        });
    }

    return rowData;
}

async function extractPreview(url, text){
  // return {title, desc}
  if(url.indexOf("tiktok.com")!==-1){
    let match = text.match(/"shareMeta":(\{.*?\})/s);
    if(!match){
      return null
    }
    match = JSON.parse(match[1])
    match.desc = decodeHtmlEntities(match.desc)
    return match
  }
  if(url.indexOf("instagram.com")!==-1){
    //const videos = await extractIGVideoVersions(url)
    const res = extractInstagramMeta(text)
    if(!res){
      return null
    }
    //res['videos'] = videos 
    return res
  }
  if(url.indexOf("youtu")!==-1){
    console.log(text)
    return extractYTMeta(text)
  }
}

async function extractIGVideoVersions(url){
  /*
              let s = r().utils.utf8.toBytes("qwertyuioplkjhgf")
              , n = r().utils.utf8.toBytes(e)
              , t = r().padding.pkcs7.pad(n)
              , a = new (r()).ModeOfOperation.ecb(s)
              , l = a.encrypt(t)
              , i = r().utils.hex.fromBytes(l);
              */
  let s = aesjs.utils.utf8.toBytes("qwertyuioplkjhgf")
  let n = aesjs.utils.utf8.toBytes(url)
  let t = aesjs.padding.pkcs7.pad(n)
  let a = new aesjs.ModeOfOperation.ecb(s)
  let l = a.encrypt(t) 
  let i = aesjs.utils.hex.fromBytes(l)
  return await axios.get('https://api.videodropper.app/allinone', {
    headers:{
      Url:i,
      Authorization:null,
    }
  }).then(({data})=>{
    // {video: [{video, thumbnail}]}
    return data.video || null
  })
}

function extractYTMeta(html) {
    const metaTags = {
        title: /<meta\s+property=["']og:title["']\s+content=["']([^"']+)["']/i,
        desc: /<meta\s+property=["']og:description["']\s+content=["']([^"']+)["']/i,
        keywords: /<meta\s+name=["']keywords["']\s+content=["']([^"']+)["']/i
    };

    const result = {};
    
    for (const [key, regex] of Object.entries(metaTags)) {
        const match = html.match(regex);
        result[key] = match ? decodeHtmlEntities(match[1]) : null;
    }

    if (!result.desc) {
      return null
    }
    return result;
}
function extractInstagramMeta(html) {
    const metaTags = {
        title: /<meta\s+property=["']og:title["']\s+content=["']([^"']+)["']/i,
        desc: /<meta\s+property=["']og:description["']\s+content=["']([^"']+)["']/i
    };

    const result = {};
    
    for (const [key, regex] of Object.entries(metaTags)) {
        const match = html.match(regex);
        result[key] = match ? decodeHtmlEntities(match[1]) : null;
    }

    if (!result.desc) {
      return null
    }

    const likeCommentRegex = /([\d,.]+[KMB]?) likes, ([\d,.]+) comments - ([^-\n]+) on (\w+ \d{1,2}, \d{4})/;
    const descMatch = result.desc.match(likeCommentRegex);
    result.desc = result.desc.split('"')
    result.desc = result.desc.slice(1, result.desc.length-1).join('"')
    
    if (descMatch) {
        result.likes = convertToNumber(descMatch[1]);
        result.comments = convertToNumber(descMatch[2]);
        result.username = descMatch[3].trim();
        result.time = descMatch[4];
    }

    return result;
}

function decodeHtmlEntities(text) {
    const doc = new DOMParser().parseFromString(text, "text/html");
    return doc.documentElement.textContent;
}

function convertToNumber(str) {
    if (str.includes('K')) {
        return parseFloat(str.replace(',', '')) * 1_000;
    } else if (str.includes('M')) {
        return parseFloat(str.replace(',', '')) * 1_000_000;
    } else if (str.includes('B')) {
        return parseFloat(str.replace(',', '')) * 1_000_000_000;
    }
    return parseInt(str.replace(',', ''), 10);
}
async function fetchOEmbedData(url) {
    const providers = [
        { name: "YouTube", match: /youtube\.com|youtu\.be/, endpoint: "https://www.youtube.com/oembed?url=" },
        { name: "Instagram", match: /instagram\.com/, endpoint: "https://graph.facebook.com/v12.0/instagram_oembed?url=" },
        { name: "TikTok", match: /tiktok\.com/, endpoint: "https://www.tiktok.com/oembed?url=" }
    ];

    const provider = providers.find(p => p.match.test(url));
    if (!provider) {
        throw new Error("Unsupported URL");
    }

    try {
      const response = await fetch(`/${provider.endpoint}${encodeURIComponent(url)}`);
        if (!response.ok) {
            throw new Error("Failed to fetch oEmbed data");
        }

        const data = await response.json();
      if(!data.title){
        return null

      } 
      return {
          title: data.title || null,
          thumbnail: data.thumbnail_url || null,
          provider: provider.name
      };
    } catch (error) {
        console.error("Error fetching oEmbed data:", error);
        return null;
    }
}

function CandidateLink({link}){
  const [isValid, setIsValid] = useState(true)
  const [checking, setChecking] = useState(true)
  const [desc, setDesc] = useState("")
  const url = link.url
  useEffect(() => {
    if(url.includes('instagram')){
      axios.get(`/${url}`).then(async ({data})=>{
        //
        const preview = await extractPreview(url, data)
        if(!preview){
          setIsValid(false)
          return
        }
        setDesc(preview.title)
        link.title = preview.title
      }).finally(() => {
        setChecking(false)
      })
    }else {
      fetchOEmbedData(url).then(data=>{
        if(!data){
          setIsValid(false)
          return 
        }
        setIsValid(true)
        setDesc(data.title)
        link.title = data.title
      }).finally(() => {
        setChecking(false)
      })
    }
  }, [])
  return <div>
  <a href={url} target="_blank" rel="noopener noreferrer" style={{ 
    textDecoration: "underline", color: isValid?"#8888ff":"#ff8888", opacity: checking? 0.3:1}} >
    {url} 
  </a>
  <div style={{color:"#999"}}>
    {desc}
  </div>
</div>
}
let USER_TOKEN = localStorage.getItem('user-token')
export default function ExtractLinks() {
  const [richText, setRichText] = useState("");
  const [csvMode, setCsvMode] = useState(false)
  const [loading, setLoading] = useState(false)
  const [links, setLinks] = useState([
    {
      url: "https://www.tiktok.com/@codingmermaid.ai/video/7297607356190575878",
    }
  ]);

  useEffect(() => {
    if(!USER_TOKEN){
      axios.post("/api/auth/stateless-user").then(({data:{token}})=>{
        localStorage.setItem('user-token', token)
        USER_TOKEN = token
        axios.defaults.headers.common['Authorization'] = `JWT ${USER_TOKEN}`;
      })
    } else {
        axios.defaults.headers.common['Authorization'] = `JWT ${USER_TOKEN}`;
    }
  }, [])

  useEffect(() => {
    const extractLinks = () => {
      const tempElement = document.createElement("div");
      tempElement.innerHTML = richText;
      const anchorTags = tempElement.getElementsByTagName("a");
      let foundLinks = [];

      const urlRegex = /https?:\/\/[a-zA-Z0-9\/_\-@.?=]*/g;
      let urls = new Set([
        ...Array.from(anchorTags).map(
          a=>a.href.substr(0, (a.href.indexOf("#")+1||a.href.length+1)-1)
        ),
        ...(tempElement.textContent.match(urlRegex) || [])
      ])
      urls.forEach(url=>{
        if (VIDEO_PATTERNS.some(pattern => pattern.test(url))) {
          foundLinks.push(url)
        }
      })
      setLinks(foundLinks.map(l=>({url:l})));
    };
    if(csvMode){
      setLinks(parseCSV(richText.replace("<br/>", "\n")))
    } else {
      extractLinks();
    }
  }, [richText, csvMode]);

  const handlePaste = async (event) => {
    event.preventDefault();
    const clipboardData = event.clipboardData || window.clipboardData;
    if (!clipboardData) return;

    if (clipboardData.types.includes("text/html")) {
      const htmlData = await navigator.clipboard.read();
      for (const item of htmlData) {
        if (item.types.includes("text/html")) {
          const blob = await item.getType("text/html");
          const plainBlob = await item.getType("text/plain");
          const htmlText = await blob.text();
          const plainText = await plainBlob.text();
          if(isCSV(plainText)){
            setRichText(plainText.replace("\n", "<br/>"));
            setCsvMode(true)
          } else {
            setCsvMode(false)
            setRichText(htmlText);
          }
          return;
        }
      }
    } else {
      const txtData = await navigator.clipboard.read();
      console.log(txtData)
      for (const item of txtData) {
          const plainBlob = await item.getType("text/plain");
          const plainText = await plainBlob.text();
          setRichText(plainText.replace("\n", "<br/>"));
          if(isCSV(plainText)){
            setCsvMode(true)
          } else {
            setCsvMode(false)
          }
          return;
      }
    }
  };

  const onSubmit = () => {
    if(loading){
      return
    }
    setLoading(true)
    console.log(links)
    axios.post('/api/posts/submit', links.filter(l=>l.desc).map(l=>({
      uri: l.url, text: l.desc
    }))).then(({data}) => {
      setRichText("")
    }).finally(() => {
      setLoading(false)
    })
  }

  return (
    <div style={{ height: "100%", backgroundColor: "#121212", color: "white", display: "flex", 
      flexDirection: "row", alignItems: "stretch", textAlign:"left"}}>
      <div style={{ width: "100%", maxWidth: "600px", backgroundColor: "#1e1e1e", 
        boxShadow: "0px 4px 6px rgba(0,0,0,0.1)",
        display:"flex", 
        flexDirection:"column", justifyContent:"flex-start", alignItems:"stretch", height:"100%",
      }}>
        <div style={{display:"flex",justifyContent:"space-between"}}>
        <h2 style={{ margin:16, fontSize: "20px", fontWeight: "bold", marginBottom: "16px" }}>Paste Text Below</h2>
        <button style={{ marginTop: "16px", backgroundColor: "#3b82f6", color: "white",  opacity:((!richText)||loading)?0.3:1,
          fontWeight: "bold", padding: "10px 20px", borderRadius: "8px", margin: 16,
          border: "none", cursor: "pointer" }} onClick={onSubmit} disabled={(!richText)||loading}>
          Submit
        </button>
        </div>
        <div
          className="gptTxtContainer"
          style={{ textAlign:"left", minWidth: "90%", margin:16,  flex:1, minHeight: "200px", 
        backgroundColor: "#333", color: "white", 
            padding: "8px", borderRadius: "8px", border: "none", overflowY: "auto" }}
          contentEditable
          onPaste={handlePaste}
          dangerouslySetInnerHTML={{ __html: richText }}
        />
      </div>
      <div style={{display:"flex", flexDirection:"row", flexWrap:"wrap"}}>
        {links.length > 0 && (
          <div style={{ 
            textAlign:"left", margin: "0px 16px",maxHeight:"100vh",
            display:"flex", flexDirection:"column", flexWrap:"wrap", gap: "0px 16px"
          }}>
        <div style={{ fontSize: "18px", fontWeight: "bold"}}>
          Extracted {links.length} Videos:</div>
              {links.map((link, index) => (
                <div key={link.url} style={{width:420, fontSize:11, overview:"hidden"}}>
                  <CandidateLink link={link}/>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
