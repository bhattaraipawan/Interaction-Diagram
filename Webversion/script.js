(function(){
  const EPS_CU=0.003, ES=29000;
  const BAR_AREA={4:0.20,5:0.31,6:0.44,7:0.60,8:0.79,9:1.00,10:1.27,11:1.56};
  const $=id=>document.getElementById(id);
  const sec=$("sec"), sx=sec.getContext("2d");
  const chart=$("chart"), cx=chart.getContext("2d");

  // teal site palette (capacity = teal, demand/steel = warm orange)
  const PAL={'--grid':'#e4ecec','--grid-strong':'#cdd8d8','--muted':'#8a9296','--ink':'#2c3135',
    '--mono':'ui-monospace,monospace','--sans':'system-ui,sans-serif',
    '--concrete':'#167685','--design':'#5aa0aa','--steel':'#d6602e','--safe':'#1f9d61'};
  const getCss=v=>PAL[v]||v;
  // read a typed value safely: fall back to default if blank/NaN, clamp to [min,max] if given
  function num(id,def,min,max){
    let v=parseFloat($(id).value);
    if(!isFinite(v)) v=def;
    if(min!==undefined) v=Math.max(min,v);
    if(max!==undefined) v=Math.min(max,v);
    return v;
  }

  let demand={M:120, P:300};
  let dragging=false;

  function beta1(fc){ if(fc<=4)return .85; if(fc>=8)return .65; return .85-.05*(fc-4);}

  function buildLayers(b,h,nFace,Abar,cover){
    const layers=[];
    layers.push({As:nFace*Abar, d:cover});
    layers.push({As:nFace*Abar, d:h-cover});
    const side=Math.max(0,nFace-2);
    if(side>0){ for(let i=1;i<=side;i++){ const d=cover+(h-2*cover)*i/(side+1); layers.push({As:2*Abar, d}); } }
    return layers;
  }

  function point(c,b,h,fc,fy,layers){
    const a=Math.min(beta1(fc)*c,h);
    const Cc=0.85*fc*b*a;
    let P=Cc, M=Cc*(h/2-a/2), dt=0;
    for(const L of layers){
      let es=EPS_CU*(c-L.d)/c;
      let fs=Math.max(-fy,Math.min(fy,ES*es));
      if(L.d<=a) fs-=0.85*fc;            // displaced concrete
      const F=fs*L.As; P+=F; M+=F*(h/2-L.d);
      if(L.d>dt) dt=L.d;
    }
    const et=EPS_CU*(dt-c)/c, ey=fy/ES;
    let phi;
    if(et>=ey+0.003) phi=0.9; else if(et<=ey) phi=0.65; else phi=0.65+0.25*(et-ey)/0.003;
    return {P,M:Math.abs(M),phi};
  }

  function compute(){
    const b=num("b",16,1), h=num("h",16,1), fc=num("fc",4,1), fy=num("fy",60,1);
    const barNo=Math.round(num("bar",8,4,11)), nFace=Math.round(num("n",3,2,5)), cover=2.5;
    const Abar=BAR_AREA[barNo];
    const layers=buildLayers(b,h,nFace,Abar,cover);
    const Ast=layers.reduce((s,L)=>s+L.As,0);
    const Ag=b*h, rho=Ast/Ag;
    const P0=0.85*fc*(Ag-Ast)+fy*Ast;
    const PnMax=0.80*P0, phiPnMax=0.65*PnMax;     // tied column
    const nom=[], des=[];
    for(let c=0.30;c<=h*4;c*=1.03){
      const pt=point(c,b,h,fc,fy,layers);
      nom.push({M:pt.M/12, P:Math.min(pt.P,PnMax)});                 // kip-ft
      des.push({M:pt.phi*pt.M/12, P:Math.min(pt.phi*pt.P, phiPnMax)});
    }
    const Pt=-fy*Ast;
    nom.push({M:0,P:Pt}); des.push({M:0,P:0.9*Pt});
    return {b,h,fc,fy,Ast,rho,P0,PnMax,phiPnMax,layers,nom,des,barNo,nFace,Abar};
  }

  let scale={};
  function drawChart(d){
    const W=chart.width,H=chart.height; cx.clearRect(0,0,W,H);
    const padL=58,padR=18,padT=18,padB=44, plotW=W-padL-padR, plotH=H-padT-padB;
    const maxM=Math.max(...d.nom.map(p=>p.M))*1.18;
    const maxP=d.PnMax*1.12, minP=Math.min(...d.nom.map(p=>p.P))*1.15;
    scale={padL,padT,plotW,plotH,maxM,maxP,minP};
    const X=m=>padL+(m/maxM)*plotW, Y=p=>padT+(maxP-p)/(maxP-minP)*plotH;

    cx.strokeStyle=getCss('--grid'); cx.lineWidth=1;
    cx.font="10px "+getCss('--mono'); cx.fillStyle=getCss('--muted');
    const mStep=niceStep(maxM,6);
    for(let m=0;m<=maxM;m+=mStep){ cx.beginPath();cx.moveTo(X(m),padT);cx.lineTo(X(m),padT+plotH);cx.stroke();
      cx.textAlign="center";cx.fillText(Math.round(m),X(m),padT+plotH+15); }
    const pStep=niceStep(maxP-minP,7);
    for(let p=Math.ceil(minP/pStep)*pStep;p<=maxP;p+=pStep){ cx.beginPath();cx.moveTo(padL,Y(p));cx.lineTo(padL+plotW,Y(p));cx.stroke();
      cx.textAlign="right";cx.fillText(Math.round(p),padL-6,Y(p)+3); }
    if(minP<0){cx.strokeStyle=getCss('--grid-strong');cx.lineWidth=1.2;cx.beginPath();cx.moveTo(padL,Y(0));cx.lineTo(padL+plotW,Y(0));cx.stroke();}

    cx.fillStyle=getCss('--ink');cx.font="11px "+getCss('--sans');
    cx.textAlign="center";cx.fillText("\u03c6Mn  (kip\u00b7ft)",padL+plotW/2,H-8);
    cx.save();cx.translate(14,padT+plotH/2);cx.rotate(-Math.PI/2);cx.fillText("\u03c6Pn  (kip)",0,0);cx.restore();

    plotCurve(d.nom,X,Y,getCss('--concrete'),2);
    cx.beginPath();
    d.des.forEach((p,i)=>{const xx=X(Math.max(0,p.M)),yy=Y(p.P); i?cx.lineTo(xx,yy):cx.moveTo(xx,yy);});
    cx.lineTo(X(0),Y(d.des[d.des.length-1].P)); cx.closePath();
    cx.fillStyle="rgba(90,160,170,.15)";cx.fill();
    plotCurve(d.des,X,Y,getCss('--design'),2);

    const dx=X(demand.M), dy=Y(demand.P), safe=isInside(demand,d.des);
    cx.strokeStyle=getCss('--steel');cx.lineWidth=2.2;
    cx.beginPath();cx.moveTo(dx-7,dy-7);cx.lineTo(dx+7,dy+7);cx.moveTo(dx+7,dy-7);cx.lineTo(dx-7,dy+7);cx.stroke();
    cx.fillStyle=safe?getCss('--safe'):getCss('--steel');
    cx.beginPath();cx.arc(dx,dy,4,0,7);cx.fill();

    $("rho").textContent=(d.rho*100).toFixed(2)+"%";
    $("pmax").textContent=Math.round(d.phiPnMax)+" k";
    $("du").textContent=Math.round(demand.P)+" k";
    $("dm").textContent=Math.round(demand.M)+" k\u00b7ft";
    const v=$("verdict"), dot=v.querySelector('.dot'), txt=v.querySelector('span:last-child');
    if(safe){dot.style.background=getCss('--safe');txt.textContent="Demand inside envelope \u2014 section is adequate.";txt.style.color=getCss('--safe');}
    else{dot.style.background=getCss('--steel');txt.textContent="Demand outside envelope \u2014 increase section or steel.";txt.style.color=getCss('--steel');}
  }

  function plotCurve(arr,X,Y,color,w){
    cx.strokeStyle=color;cx.lineWidth=w;cx.beginPath();
    arr.forEach((p,i)=>{const xx=X(Math.max(0,p.M)),yy=Y(p.P);i?cx.lineTo(xx,yy):cx.moveTo(xx,yy);});
    cx.stroke();
  }

  function isInside(pt,des){
    const poly=des.map(p=>[Math.max(0,p.M),p.P]);
    poly.push([0,des[des.length-1].P]); poly.push([0,des[0].P]);
    let inside=false;
    for(let i=0,j=poly.length-1;i<poly.length;j=i++){
      const xi=poly[i][0],yi=poly[i][1],xj=poly[j][0],yj=poly[j][1];
      const hit=((yi>pt.P)!==(yj>pt.P)) && (pt.M < (xj-xi)*(pt.P-yi)/(yj-yi)+xi);
      if(hit) inside=!inside;
    }
    return inside && pt.M>=0;
  }

  function niceStep(range,target){
    const raw=range/target, mag=Math.pow(10,Math.floor(Math.log10(raw))), n=raw/mag;
    return (n<1.5?1:n<3?2:n<7?5:10)*mag;
  }

  function drawSection(d){
    const W=sec.width,H=sec.height,pad=34; sx.clearRect(0,0,W,H);
    const s=Math.min((W-2*pad)/d.b,(H-2*pad)/d.h), w=d.b*s, h=d.h*s, ox=(W-w)/2, oy=(H-h)/2;
    sx.fillStyle="#eef1f6";sx.strokeStyle=getCss('--ink');sx.lineWidth=2;
    sx.fillRect(ox,oy,w,h);sx.strokeRect(ox,oy,w,h);
    sx.strokeStyle=getCss('--muted');sx.lineWidth=1;sx.strokeRect(ox+8,oy+8,w-16,h-16);
    const cover=2.5, r=Math.max(3,Math.sqrt(d.Abar)*4.5);
    sx.fillStyle=getCss('--steel');
    const xs=[ox+cover*s, ox+w-cover*s];
    const drawRow=(yy,count)=>{ for(let i=0;i<count;i++){ const t=count===1?0.5:i/(count-1);
      const px=ox+cover*s+t*(w-2*cover*s); sx.beginPath();sx.arc(px,yy,r,0,7);sx.fill(); } };
    drawRow(oy+cover*s,d.nFace); drawRow(oy+h-cover*s,d.nFace);
    const side=Math.max(0,d.nFace-2);
    for(let i=1;i<=side;i++){ const yy=oy+cover*s+(h-2*cover*s)*i/(side+1);
      sx.beginPath();sx.arc(xs[0],yy,r,0,7);sx.fill(); sx.beginPath();sx.arc(xs[1],yy,r,0,7);sx.fill(); }
    sx.fillStyle=getCss('--muted');sx.font="11px "+getCss('--mono');sx.textAlign="center";
    sx.fillText(d.b+'"',ox+w/2,oy+h+22);
    sx.save();sx.translate(ox-14,oy+h/2);sx.rotate(-Math.PI/2);sx.fillText(d.h+'"',0,0);sx.restore();
    sx.fillText("#"+d.barNo+" bars",W/2,18);
  }

  function chartToData(ev){
    const rect=chart.getBoundingClientRect();
    const px=(ev.clientX-rect.left)*(chart.width/rect.width);
    const py=(ev.clientY-rect.top)*(chart.height/rect.height);
    const {padL,padT,plotW,plotH,maxM,maxP,minP}=scale;
    return {M:Math.max(0,(px-padL)/plotW*maxM), P:maxP-(py-padT)/plotH*(maxP-minP)};
  }
  const setDemand=ev=>{demand=chartToData(ev);render();};
  chart.addEventListener("pointerdown",e=>{dragging=true;chart.setPointerCapture(e.pointerId);setDemand(e);});
  chart.addEventListener("pointermove",e=>{if(dragging)setDemand(e);});
  chart.addEventListener("pointerup",()=>dragging=false);
  chart.addEventListener("pointercancel",()=>dragging=false);

  function render(){ const d=compute(); drawSection(d); drawChart(d); }
  ["b","h","fc","fy","bar","n"].forEach(id=>$(id).addEventListener("input",render));
  render();
})();
