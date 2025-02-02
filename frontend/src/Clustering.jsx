import axios from 'axios'
import { useEffect, useState, useRef } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import tSNE from './tsne'

function splitText(text, maxLength) {
    const words = text.split(' ');
    const lines = [];
    let currentLine = '';

    for (const word of words) {
        if ((currentLine + word).length <= maxLength) {
            currentLine += (currentLine ? ' ' : '') + word;
        } else {
            lines.push(currentLine);
            currentLine = word;
        }
    }

    if (currentLine) {
        lines.push(currentLine);
    }

    return lines;
}

function App() {
  const [count, setCount] = useState(0)
  const tsneRef = useRef(null)
  const canvasRef = useRef(null)
  const solutionRef = useRef([])
  const embeddingsRef = useRef([])
  useEffect(() => {
    if(tsneRef.current){
      return
    }
    const canvas = canvasRef.current
    var ctx = canvas.getContext('2d');
    canvas.width = canvas.clientWidth
    canvas.height = canvas.clientHeight
		trackTransforms(ctx);
    const redraw = () => {
      const solution = solutionRef.current
      // Clear the entire canvas
			const p1 = ctx.transformedPoint(0,0);
			const p2 = ctx.transformedPoint(canvas.width,canvas.height);
			ctx.clearRect(p1.x,p1.y,p2.x-p1.x,p2.y-p1.y);
      const w = canvas.width
      const h = canvas.height
      solution.map(([x, y], idx)=>{
        const p = ctx.transformedPoint(x, y)
        const scale = 200.0
        ctx.fillStyle="#fff"
        const lines = splitText(embeddingsRef.current[idx].text, 45)
        for(let i = 0;i < lines.length;i++){
          ctx.fillText(lines[i], x*scale+w/2, y*scale+h/2+12*i);
        }
      })
    }
    var lastX=canvas.width/2, lastY=canvas.height/2;
		var dragStart,dragged;
		canvas.addEventListener('mousedown',function(evt){
			document.body.style.mozUserSelect = document.body.style.webkitUserSelect = document.body.style.userSelect = 'none';
			lastX = evt.offsetX || (evt.pageX - canvas.offsetLeft);
			lastY = evt.offsetY || (evt.pageY - canvas.offsetTop);
			dragStart = ctx.transformedPoint(lastX,lastY);
			dragged = false;
		},false);
		canvas.addEventListener('mousemove',function(evt){
			lastX = evt.offsetX || (evt.pageX - canvas.offsetLeft);
			lastY = evt.offsetY || (evt.pageY - canvas.offsetTop);
			dragged = true;
			if (dragStart){
				var pt = ctx.transformedPoint(lastX,lastY);
				ctx.translate(pt.x-dragStart.x,pt.y-dragStart.y);
				redraw();
			}
		},false);
		canvas.addEventListener('mouseup',function(evt){
			dragStart = null;
			if (!dragged) zoom(evt.shiftKey ? -1 : 1 );
		},false);

		var scaleFactor = 1.1;
		var zoom = function(clicks){
			var pt = ctx.transformedPoint(lastX,lastY);
			ctx.translate(pt.x,pt.y);
			var factor = Math.pow(scaleFactor,clicks);
			ctx.scale(factor,factor);
			ctx.translate(-pt.x,-pt.y);
			redraw();
		}

		var handleScroll = function(evt){
			var delta = evt.wheelDelta ? evt.wheelDelta/40 : evt.detail ? -evt.detail : 0;
			if (delta) zoom(delta);
			return evt.preventDefault() && false;
		};
		canvas.addEventListener('DOMMouseScroll',handleScroll,false);
		canvas.addEventListener('mousewheel',handleScroll,false);
    function trackTransforms(ctx){
      var svg = document.createElementNS("http://www.w3.org/2000/svg",'svg');
      var xform = svg.createSVGMatrix();
      ctx.getTransform = function(){ return xform; };

      var savedTransforms = [];
      var save = ctx.save;
      ctx.save = function(){
        savedTransforms.push(xform.translate(0,0));
        return save.call(ctx);
        };
      var restore = ctx.restore;
      ctx.restore = function(){
        xform = savedTransforms.pop();
        return restore.call(ctx);
        };

      var scale = ctx.scale;
      ctx.scale = function(sx,sy){
        xform = xform.scaleNonUniform(sx,sy);
        return scale.call(ctx,sx,sy);
        };
      var rotate = ctx.rotate;
      ctx.rotate = function(radians){
        xform = xform.rotate(radians*180/Math.PI);
        return rotate.call(ctx,radians);
        };
      var translate = ctx.translate;
      ctx.translate = function(dx,dy){
        xform = xform.translate(dx,dy);
        return translate.call(ctx,dx,dy);
        };
      var transform = ctx.transform;
      ctx.transform = function(a,b,c,d,e,f){
        var m2 = svg.createSVGMatrix();
        m2.a=a; m2.b=b; m2.c=c; m2.d=d; m2.e=e; m2.f=f;
        xform = xform.multiply(m2);
        return transform.call(ctx,a,b,c,d,e,f);
        };
      var setTransform = ctx.setTransform;
      ctx.setTransform = function(a,b,c,d,e,f){
        xform.a = a;
        xform.b = b;
        xform.c = c;
        xform.d = d;
        xform.e = e;
        xform.f = f;
        return setTransform.call(ctx,a,b,c,d,e,f);
        };
      var pt  = svg.createSVGPoint();
      ctx.transformedPoint = function(x,y){
        pt.x=x; pt.y=y;
        return pt.matrixTransform(xform.inverse());
        }
      }

    tsneRef.current = true
    axios.get('/embeddings_0.json').then(({data})=>{
      const newEmbeddings = Object.keys(data).filter(k=>k.length>90).map(k=>
        ({
          text:k,
          vec:data[k].map(v=>(v+10.0)/30.0)
        })
        ).slice(0, 5000)
      embeddingsRef.current = newEmbeddings
      const tsne = new tSNE({
        epsilon: 200,  // learning rate
        perplexity: 20, // how many beighbors each point influences
        dim: 2, // dimensionality 
      })
      let vecs = newEmbeddings.map(k=>k.vec)
      //debugger
      //tsne.initDataDist(dists);
      tsne.initDataRaw(vecs);
      //tsne.initDataDist()
      let stepCount = 0 
      const runTSNE = () => {
        if(stepCount==1000){
          return
        }
        for(let i = 0;i < 4;i++){
          tsne.step(); // every time you call this, solution gets better
          stepCount++
          console.log(stepCount)
        }
        redraw()
        const newSolution = tsne.getSolution()
        solutionRef.current = newSolution
        window.requestAnimationFrame(runTSNE)
      }
      window.requestAnimationFrame(runTSNE)
    })
  }, [])

  return (
    <> 
      <canvas ref={canvasRef} style={{width:"100%", height:"100%"}}/>
    </>
  )
}

export default App
