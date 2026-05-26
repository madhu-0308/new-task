(() => {
  const fileInput = document.getElementById('file-input');
  const dropArea = document.getElementById('drop-area');
  const preview = document.getElementById('preview');
  const uploadBtn = document.getElementById('upload-btn');
  const progressBar = document.getElementById('progress-bar');
  const resultsEl = document.getElementById('results');
  const emptyEl = document.getElementById('result-empty');
  const shotName = document.getElementById('shot-name');
  const shotProb = document.getElementById('shot-prob');
  const shotBar = document.getElementById('shot-bar');
  const predList = document.getElementById('pred-list');
  const notesEl = document.getElementById('notes');
  const adviceEl = document.getElementById('advice');
  const corrEl = document.getElementById('corrections');
  const metaEl = document.getElementById('meta');

  function prevent(e){ e.preventDefault(); e.stopPropagation(); }
  ['dragenter','dragover','dragleave','drop'].forEach(ev => dropArea.addEventListener(ev, prevent));
  dropArea.addEventListener('drop', (e)=>{
    const f = e.dataTransfer.files[0]; if(!f) return; fileInput.files = e.dataTransfer.files; setPreview(f);
  });

  fileInput.addEventListener('change', (e)=>{ const f = e.target.files[0]; if(!f) return; setPreview(f); });

  function setPreview(file){
    try{ preview.src = URL.createObjectURL(file); preview.load(); }catch(e){}
    emptyEl.classList.add('hidden'); resultsEl.classList.add('hidden');
  }

  uploadBtn.addEventListener('click', ()=>{
    const f = fileInput.files[0]; if(!f) return alert('Choose a video first');
    uploadBtn.disabled = true; progressBar.style.width = '0%';
    const xhr = new XMLHttpRequest();
    const fd = new FormData(); fd.append('video', f);
    xhr.open('POST','/predict');
    xhr.upload.onprogress = (ev)=>{ if(ev.lengthComputable){ const pct = Math.round(ev.loaded/ev.total*100); progressBar.style.width = pct+'%'; }};
    xhr.onreadystatechange = ()=>{
      if(xhr.readyState===4){ uploadBtn.disabled=false; if(xhr.status>=400){ alert('Server error'); return;} try{ const j=JSON.parse(xhr.responseText); showResults(j); }catch(e){ alert('Invalid server response'); } }
    };
    xhr.send(fd);
  });

  function showResults(data){
    if(data.error){ alert(data.error); return; }
    const preds = data.predictions || [];
    const fb = data.feedback || {};
    const top = preds[0] || {name:'—',prob:0};
    shotName.textContent = top.name;
    shotProb.textContent = (top.prob*100).toFixed(1)+'%';
    shotBar.style.width = Math.min(100,Math.round(top.prob*100))+'%';

    predList.innerHTML = '';
    preds.forEach(p=>{
      const li = document.createElement('li');
      li.textContent = `${p.name}`;
      const span = document.createElement('span'); span.textContent = `${(p.prob*100).toFixed(1)}%`;
      li.appendChild(span);
      predList.appendChild(li);
    });

    notesEl.textContent = fb.notes || fb.issue || 'No notes.';
    adviceEl.textContent = fb.advice || '—';
    corrEl.textContent = fb.corrections || '—';
    metaEl.textContent = `visible_ratio=${(fb.visible_ratio||0).toFixed(2)} avg_conf=${(fb.avg_confidence||0).toFixed(2)}`;

    resultsEl.classList.remove('hidden');
    emptyEl.classList.add('hidden');
  }

})();
