# app.py – Complete Image tools for Government Job Applications
import os, io, tempfile, uuid, traceback
from flask import Flask, render_template_string, request, send_file
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key')

ALLOWED_EXT = {'png','jpg','jpeg','webp','bmp','gif'}

def allowed_filename(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def pil_open_validate(file_stream):
    try:
        img = Image.open(file_stream)
        img.verify()
        file_stream.seek(0)
        return True
    except:
        return False

def save_temp_bytes(b: bytes, suffix=''):
    name = f"{uuid.uuid4().hex}{suffix}"
    path = os.path.join(tempfile.gettempdir(), name)
    with open(path, 'wb') as f:
        f.write(b)
    return path

# Complete HTML with all JavaScript
HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ImageMaster Pro - Government Job Tools</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
<style>
.tab{display:none}.tab.active{display:block}
.preview-container{border:2px dashed #cbd5e1;border-radius:0.5rem;padding:2rem;text-align:center;background:#f8fafc;transition:all 0.3s}
.preview-container:hover{border-color:#667eea;background:#f1f5f9}
.preview-image{max-width:100%;max-height:400px;margin:1rem auto;border-radius:0.5rem;box-shadow:0 4px 6px rgba(0,0,0,0.1)}
.comparison-container{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem}
@media (max-width:768px){.comparison-container{grid-template-columns:1fr}}
.comparison-item{text-align:center;padding:1rem;background:#f8fafc;border-radius:0.5rem}
.btn-primary{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);transition:all 0.3s}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 10px 20px rgba(0,0,0,0.2)}
.tab-button{transition:all 0.3s;border-bottom:3px solid transparent}
.tab-button.active{border-bottom-color:#667eea;color:#667eea;font-weight:600}
.pdf-image-item{position:relative;cursor:move;border:2px solid #e2e8f0;border-radius:0.5rem;padding:0.5rem;background:white;transition:all 0.2s}
.pdf-image-item:hover{border-color:#667eea;box-shadow:0 4px 6px rgba(0,0,0,0.1)}
.pdf-image-item img{width:100%;height:150px;object-fit:cover;border-radius:0.25rem}
.remove-btn{position:absolute;top:0.5rem;right:0.5rem;background:#ef4444;color:white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;cursor:pointer}
.loader{border:3px solid #f3f4f6;border-top:3px solid #667eea;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:0 auto}
@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
.preset-btn{padding:0.5rem 1rem;border:2px solid #e2e8f0;border-radius:0.5rem;cursor:pointer;transition:all 0.2s}
.preset-btn:hover{border-color:#667eea;background:#f0f4ff}
.preset-btn.active{border-color:#667eea;background:#667eea;color:white}
canvas{max-width:100%;height:auto;border-radius:0.5rem}
</style>
</head>
<body class="bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 min-h-screen p-4">
<div class="max-w-6xl mx-auto">

<!-- Header -->
<div class="bg-white p-6 rounded-2xl shadow-lg mb-6">
<h1 class="text-3xl font-bold mb-2" style="background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent">
<i class="fas fa-briefcase mr-2"></i>ImageMaster Pro</h1>
<p class="text-gray-600">Perfect Tools for Government Job Applications</p>
</div>

<!-- Alert -->
<div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded-lg">
<p class="text-sm"><i class="fas fa-info-circle text-blue-500"></i> <strong>For Government Job Applicants:</strong> Meet exact photo requirements for UPSC, SSC, Railway, Banking exams</p>
</div>

<!-- Tabs -->
<div class="bg-white p-4 rounded-2xl shadow-lg mb-6 overflow-x-auto">
<div class="flex gap-2 flex-wrap">
<button onclick="showTab('passport')" class="tab-button active px-6 py-3 rounded-lg"><i class="fas fa-id-card"></i> Passport</button>
<button onclick="showTab('compress')" class="tab-button px-6 py-3 rounded-lg"><i class="fas fa-compress"></i> Compress</button>
<button onclick="showTab('crop')" class="tab-button px-6 py-3 rounded-lg"><i class="fas fa-crop"></i> Crop</button>
<button onclick="showTab('rotate')" class="tab-button px-6 py-3 rounded-lg"><i class="fas fa-sync"></i> Rotate</button>
<button onclick="showTab('filter')" class="tab-button px-6 py-3 rounded-lg"><i class="fas fa-palette"></i> Filters</button>
<button onclick="showTab('pdf')" class="tab-button px-6 py-3 rounded-lg"><i class="fas fa-file-pdf"></i> PDF</button>
<button onclick="showTab('signature')" class="tab-button px-6 py-3 rounded-lg"><i class="fas fa-signature"></i> Signature</button>
</div>
</div>

<!-- Content -->
<div class="bg-white p-6 rounded-2xl shadow-lg">

<!-- Passport Photo -->
<div id="passport" class="tab active">
<h2 class="text-2xl font-bold mb-4"><i class="fas fa-id-card text-purple-600"></i> Passport Size Photo</h2>
<form id="form-passport" onsubmit="handlePassport(event)">
<div class="preview-container mb-4">
<input type="file" id="passport-input" name="image" accept="image/*" required onchange="previewImage(this,'passport-preview')" class="hidden">
<label for="passport-input" class="cursor-pointer inline-block">
<i class="fas fa-cloud-upload-alt text-6xl text-gray-400"></i>
<p class="text-lg font-medium mt-2">Upload Photo</p>
</label>
<div id="passport-preview"></div>
</div>
<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
<button type="button" class="preset-btn active" onclick="selectPreset(this,200,230)"><div class="font-bold">Standard</div><div class="text-xs">200×230px</div></button>
<button type="button" class="preset-btn" onclick="selectPreset(this,300,350)"><div class="font-bold">UPSC</div><div class="text-xs">300×350px</div></button>
<button type="button" class="preset-btn" onclick="selectPreset(this,240,320)"><div class="font-bold">SSC</div><div class="text-xs">240×320px</div></button>
<button type="button" class="preset-btn" onclick="selectPreset(this,160,200)"><div class="font-bold">Banking</div><div class="text-xs">160×200px</div></button>
</div>
<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
<div><label class="block text-sm font-medium mb-2">Width:</label>
<input id="passport-width" name="width" type="number" value="200" min="50" required class="w-full px-4 py-2 border rounded-lg"></div>
<div><label class="block text-sm font-medium mb-2">Height:</label>
<input id="passport-height" name="height" type="number" value="230" min="50" required class="w-full px-4 py-2 border rounded-lg"></div>
<div><label class="block text-sm font-medium mb-2">Max Size:</label>
<select name="maxsize" class="w-full px-4 py-2 border rounded-lg">
<option value="50">50 KB</option><option value="100" selected>100 KB</option><option value="200">200 KB</option></select></div>
</div>
<button type="submit" class="btn-primary text-white px-8 py-3 rounded-lg w-full"><i class="fas fa-magic mr-2"></i>Create Passport Photo</button>
</form>
<div id="passport-result" class="mt-6"></div>
</div>

<!-- Compress -->
<div id="compress" class="tab">
<h2 class="text-2xl font-bold mb-4"><i class="fas fa-compress text-purple-600"></i> Compress to Size</h2>
<form id="form-compress" onsubmit="handleCompress(event)">
<div class="preview-container mb-4">
<input type="file" id="compress-input" name="image" accept="image/*" required onchange="previewImage(this,'compress-preview')" class="hidden">
<label for="compress-input" class="cursor-pointer inline-block">
<i class="fas fa-cloud-upload-alt text-6xl text-gray-400"></i>
<p class="text-lg font-medium mt-2">Upload Image</p>
</label>
<div id="compress-preview"></div>
</div>
<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
<button type="button" class="preset-btn" onclick="setTarget(20)">20 KB</button>
<button type="button" class="preset-btn active" onclick="setTarget(50)">50 KB</button>
<button type="button" class="preset-btn" onclick="setTarget(100)">100 KB</button>
<button type="button" class="preset-btn" onclick="setTarget(200)">200 KB</button>
</div>
<div class="mb-4">
<label class="block text-sm font-medium mb-2">Target: <span id="target-val" class="text-purple-600 font-bold">50</span> KB</label>
<input name="targetsize" id="target-slider" type="range" value="50" min="10" max="500" step="10" oninput="document.getElementById('target-val').textContent=this.value" class="w-full">
</div>
<button type="submit" class="btn-primary text-white px-8 py-3 rounded-lg w-full"><i class="fas fa-compress mr-2"></i>Compress</button>
</form>
<div id="compress-result" class="mt-6"></div>
</div>

<!-- Crop -->
<div id="crop" class="tab">
<h2 class="text-2xl font-bold mb-4"><i class="fas fa-crop text-purple-600"></i> Crop Image</h2>
<div class="preview-container mb-4">
<input type="file" id="crop-input" accept="image/*" onchange="loadCrop(this)" class="hidden">
<label for="crop-input" class="cursor-pointer inline-block">
<i class="fas fa-cloud-upload-alt text-6xl text-gray-400"></i>
<p class="text-lg font-medium mt-2">Upload Image</p>
</label>
</div>
<div id="crop-container" style="display:none">
<div class="grid grid-cols-3 md:grid-cols-6 gap-2 mb-4">
<button type="button" class="preset-btn active" onclick="setCropRatio('1:1')">1:1</button>
<button type="button" class="preset-btn" onclick="setCropRatio('4:3')">4:3</button>
<button type="button" class="preset-btn" onclick="setCropRatio('16:9')">16:9</button>
<button type="button" class="preset-btn" onclick="setCropRatio('3:4')">3:4</button>
<button type="button" class="preset-btn" onclick="setCropRatio('9:16')">9:16</button>
<button type="button" class="preset-btn" onclick="setCropRatio('free')">Free</button>
</div>
<div class="text-center mb-4"><canvas id="crop-canvas" class="mx-auto"></canvas></div>
<div class="flex gap-2">
<button onclick="resetCrop()" class="flex-1 bg-gray-500 text-white px-6 py-3 rounded-lg"><i class="fas fa-undo mr-2"></i>Reset</button>
<button onclick="downloadCrop()" class="flex-1 btn-primary text-white px-6 py-3 rounded-lg"><i class="fas fa-download mr-2"></i>Download</button>
</div>
</div>
</div>

<!-- Rotate -->
<div id="rotate" class="tab">
<h2 class="text-2xl font-bold mb-4"><i class="fas fa-sync text-purple-600"></i> Rotate & Flip</h2>
<div class="preview-container mb-4">
<input type="file" id="rotate-input" accept="image/*" onchange="loadRotate(this)" class="hidden">
<label for="rotate-input" class="cursor-pointer inline-block">
<i class="fas fa-cloud-upload-alt text-6xl text-gray-400"></i>
<p class="text-lg font-medium mt-2">Upload Image</p>
</label>
</div>
<div id="rotate-container" style="display:none">
<div class="text-center mb-4"><canvas id="rotate-canvas" class="mx-auto"></canvas></div>
<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
<button onclick="doRotate(90)" class="preset-btn"><i class="fas fa-redo"></i> 90°</button>
<button onclick="doRotate(180)" class="preset-btn"><i class="fas fa-redo"></i> 180°</button>
<button onclick="doFlip('h')" class="preset-btn"><i class="fas fa-arrows-alt-h"></i> Flip H</button>
<button onclick="doFlip('v')" class="preset-btn"><i class="fas fa-arrows-alt-v"></i> Flip V</button>
</div>
<div class="flex gap-2">
<button onclick="resetRotate()" class="flex-1 bg-gray-500 text-white px-6 py-3 rounded-lg"><i class="fas fa-undo mr-2"></i>Reset</button>
<button onclick="downloadRotate()" class="flex-1 btn-primary text-white px-6 py-3 rounded-lg"><i class="fas fa-download mr-2"></i>Download</button>
</div>
</div>
</div>

<!-- Filter -->
<div id="filter" class="tab">
<h2 class="text-2xl font-bold mb-4"><i class="fas fa-palette text-purple-600"></i> Filters</h2>
<div class="preview-container mb-4">
<input type="file" id="filter-input" accept="image/*" onchange="loadFilter(this)" class="hidden">
<label for="filter-input" class="cursor-pointer inline-block">
<i class="fas fa-cloud-upload-alt text-6xl text-gray-400"></i>
<p class="text-lg font-medium mt-2">Upload Image</p>
</label>
</div>
<div id="filter-container" style="display:none">
<div class="text-center mb-4"><canvas id="filter-canvas" class="mx-auto"></canvas></div>
<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
<button onclick="applyFilter('none')" class="preset-btn active">Original</button>
<button onclick="applyFilter('grayscale')" class="preset-btn">Grayscale</button>
<button onclick="applyFilter('sepia')" class="preset-btn">Sepia</button>
<button onclick="applyFilter('blur')" class="preset-btn">Blur</button>
<button onclick="applyFilter('brightness')" class="preset-btn">Bright</button>
<button onclick="applyFilter('contrast')" class="preset-btn">Contrast</button>
<button onclick="applyFilter('saturate')" class="preset-btn">Vibrant</button>
<button onclick="applyFilter('invert')" class="preset-btn">Invert</button>
</div>
<div class="flex gap-2">
<button onclick="resetFilter()" class="flex-1 bg-gray-500 text-white px-6 py-3 rounded-lg"><i class="fas fa-undo mr-2"></i>Reset</button>
<button onclick="downloadFilter()" class="flex-1 btn-primary text-white px-6 py-3 rounded-lg"><i class="fas fa-download mr-2"></i>Download</button>
</div>
</div>
</div>

<!-- PDF -->
<div id="pdf" class="tab">
<h2 class="text-2xl font-bold mb-4"><i class="fas fa-file-pdf text-purple-600"></i> Images to PDF</h2>
<form id="form-pdf" onsubmit="handlePDF(event)">
<div class="preview-container mb-4">
<input type="file" id="pdf-input" name="files" accept="image/*" multiple required onchange="handlePDFImages(this)" class="hidden">
<label for="pdf-input" class="cursor-pointer inline-block">
<i class="fas fa-cloud-upload-alt text-6xl text-gray-400"></i>
<p class="text-lg font-medium mt-2">Upload Multiple Images</p>
</label>
</div>
<div id="pdf-preview" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4"></div>
<button type="submit" class="btn-primary text-white px-8 py-3 rounded-lg w-full"><i class="fas fa-file-pdf mr-2"></i>Create PDF</button>
</form>
<div id="pdf-result" class="mt-6"></div>
</div>

<!-- Signature -->
<div id="signature" class="tab">
<h2 class="text-2xl font-bold mb-4"><i class="fas fa-signature text-purple-600"></i> Signature Tool</h2>
<form id="form-signature" onsubmit="handleSignature(event)">
<div class="preview-container mb-4">
<input type="file" id="signature-input" name="image" accept="image/*" required onchange="previewImage(this,'signature-preview')" class="hidden">
<label for="signature-input" class="cursor-pointer inline-block">
<i class="fas fa-cloud-upload-alt text-6xl text-gray-400"></i>
<p class="text-lg font-medium mt-2">Upload Signature</p>
</label>
<div id="signature-preview"></div>
</div>
<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
<div><label class="block text-sm font-medium mb-2">Width:</label>
<input name="width" type="number" value="140" min="50" required class="w-full px-4 py-2 border rounded-lg"></div>
<div><label class="block text-sm font-medium mb-2">Height:</label>
<input name="height" type="number" value="60" min="30" required class="w-full px-4 py-2 border rounded-lg"></div>
<div><label class="block text-sm font-medium mb-2">Max Size:</label>
<select name="maxsize" class="w-full px-4 py-2 border rounded-lg">
<option value="20">20 KB</option><option value="50" selected>50 KB</option><option value="100">100 KB</option></select></div>
</div>
<button type="submit" class="btn-primary text-white px-8 py-3 rounded-lg w-full"><i class="fas fa-magic mr-2"></i>Process Signature</button>
</form>
<div id="signature-result" class="mt-6"></div>
</div>

</div>

<!-- Footer -->
<div class="mt-8 text-center text-sm text-gray-600">
<p>© 2024 ImageMaster Pro • Perfect for Government Job Applications</p>
</div>

</div>

<script>
let pdfImages=[],sortable=null;
let cropCanvas,cropCtx,cropImg,cropRatio='1:1';
let rotateCanvas,rotateCtx,rotateImg,rotation=0,flippedH=false,flippedV=false;
let filterCanvas,filterCtx,filterImg,currentFilter='none';

function showTab(id){
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
document.querySelectorAll('.tab-button').forEach(b=>b.classList.remove('active'));
document.getElementById(id).classList.add('active');
event.target.classList.add('active');
['passport-result','compress-result','pdf-result','signature-result'].forEach(r=>{
const el=document.getElementById(r);if(el)el.innerHTML='';
});
}

function previewImage(input,previewId){
const preview=document.getElementById(previewId);
if(input.files&&input.files[0]){
const reader=new FileReader();
reader.onload=function(e){
const img=new Image();
img.onload=function(){
const size=(input.files[0].size/1024).toFixed(1);
preview.innerHTML=`<img src="${e.target.result}" class="preview-image"><p class="text-sm text-gray-600 mt-2"><i class="fas fa-info-circle"></i> ${img.width}×${img.height}px • ${size}KB</p>`;
};
img.src=e.target.result;
};
reader.readAsDataURL(input.files[0]);
}
}

function selectPreset(btn,w,h){
document.querySelectorAll('#passport .preset-btn').forEach(b=>b.classList.remove('active'));
btn.classList.add('active');
document.getElementById('passport-width').value=w;
document.getElementById('passport-height').value=h;
}

function setTarget(kb){
document.querySelectorAll('#compress .preset-btn').forEach(b=>b.classList.remove('active'));
event.target.classList.add('active');
document.getElementById('target-slider').value=kb;
document.getElementById('target-val').textContent=kb;
}

// Crop
function loadCrop(input){
if(input.files&&input.files[0]){
const reader=new FileReader();
reader.onload=function(e){
cropImg=new Image();
cropImg.onload=function(){
cropCanvas=document.getElementById('crop-canvas');
cropCtx=cropCanvas.getContext('2d');
cropCanvas.width=cropImg.width;
cropCanvas.height=cropImg.height;
document.getElementById('crop-container').style.display='block';
drawCrop();
};
cropImg.src=e.target.result;
};
reader.readAsDataURL(input.files[0]);
}
}

function setCropRatio(ratio){
document.querySelectorAll('#crop .preset-btn').forEach(b=>b.classList.remove('active'));
event.target.classList.add('active');
cropRatio=ratio;
drawCrop();
}

function drawCrop(){
if(!cropImg||!cropCanvas)return;
cropCtx.clearRect(0,0,cropCanvas.width,cropCanvas.height);
cropCtx.drawImage(cropImg,0,0);
if(cropRatio!=='free'){
const [w,h]=cropRatio.split(':').map(Number);
const ratio=w/h;
let cropW,cropH;
if(cropCanvas.width/cropCanvas.height>ratio){
cropH=cropCanvas.height;cropW=cropH*ratio;
}else{
cropW=cropCanvas.width;cropH=cropW/ratio;
}
const x=(cropCanvas.width-cropW)/2;
const y=(cropCanvas.height-cropH)/2;
cropCtx.strokeStyle='#667eea';
cropCtx.lineWidth=3;
cropCtx.setLineDash([10,5]);
cropCtx.strokeRect(x,y,cropW,cropH);
}
}

function resetCrop(){drawCrop();}

function downloadCrop(){
if(!cropCanvas)return;
const temp=document.createElement('canvas');
const tempCtx=temp.getContext('2d');
if(cropRatio==='free'){
temp.width=cropCanvas.width;
temp.height=cropCanvas.height;
tempCtx.drawImage(cropCanvas,0,0);
}else{
const [w,h]=cropRatio.split(':').map(Number);
const ratio=w/h;
let cropW,cropH,x,y;
if(cropCanvas.width/cropCanvas.height>ratio){
cropH=cropCanvas.height;cropW=cropH*ratio;
}else{
cropW=cropCanvas.width;cropH=cropW/ratio;
}
x=(cropCanvas.width-cropW)/2;
y=(cropCanvas.height-cropH)/2;
temp.width=cropW;
temp.height=cropH;
tempCtx.drawImage(cropCanvas,x,y,cropW,cropH,0,0,cropW,cropH);
}
downloadCanvas(temp,'cropped');
}

// Rotate
function loadRotate(input){
if(input.files&&input.files[0]){
const reader=new FileReader();
reader.onload=function(e){
rotateImg=new Image();
rotateImg.onload=function(){
rotateCanvas=document.getElementById('rotate-canvas');
rotateCtx=rotateCanvas.getContext('2d');
rotateCanvas.width=rotateImg.width;
rotateCanvas.height=rotateImg.height;
document.getElementById('rotate-container').style.display='block';
rotation=0;flippedH=false;flippedV=false;
drawRotate();
};
rotateImg.src=e.target.result;
};
reader.readAsDataURL(input.files[0]);
}
}

function doRotate(deg){
rotation=(rotation+deg)%360;
drawRotate();
}

function doFlip(dir){
if(dir==='h')flippedH=!flippedH;
if(dir==='v')flippedV=!flippedV;
drawRotate();
}

function drawRotate(){
if(!rotateImg||!rotateCanvas)return;
const rad=rotation*Math.PI/180;
let w=rotateImg.width,h=rotateImg.height;
if(rotation%180!==0){
rotateCanvas.width=h;rotateCanvas.height=w;
}else{
rotateCanvas.width=w;rotateCanvas.height=h;
}
rotateCtx.clearRect(0,0,rotateCanvas.width,rotateCanvas.height);
rotateCtx.save();
rotateCtx.translate(rotateCanvas.width/2,rotateCanvas.height/2);
rotateCtx.rotate(rad);
rotateCtx.scale(flippedH?-1:1,flippedV?-1:1);
if(rotation%180!==0){
rotateCtx.drawImage(rotateImg,-h/2,-w/2,h,w);
}else{
rotateCtx.drawImage(rotateImg,-w/2,-h/2,w,h);
}
rotateCtx.restore();
}

function resetRotate(){
rotation=0;flippedH=false;flippedV=false;
rotateCanvas.width=rotateImg.width;
rotateCanvas.height=rotateImg.height;
drawRotate();
}

function downloadRotate(){
if(!rotateCanvas)return;
downloadCanvas(rotateCanvas,'rotated');
}

// Filter
function loadFilter(input){
if(input.files&&input.files[0]){
const reader=new FileReader();
reader.onload=function(e){
filterImg=new Image();
filterImg.onload=function(){
filterCanvas=document.getElementById('filter-canvas');
filterCtx=filterCanvas.getContext('2d');
filterCanvas.width=filterImg.width;
filterCanvas.height=filterImg.height;
document.getElementById('filter-container').style.display='block';
currentFilter='none';
drawFilter();
};
filterImg.src=e.target.result;
};
reader.readAsDataURL(input.files[0]);
}
}

function applyFilter(filter){
document.querySelectorAll('#filter .preset-btn').forEach(b=>b.classList.remove('active'));
event.target.classList.add('active');
currentFilter=filter;
drawFilter();
}

function drawFilter(){
if(!filterImg||!filterCanvas)return;
filterCtx.clearRect(0,0,filterCanvas.width,filterCanvas.height);
const filters={'none':'none','grayscale':'grayscale(100%)','sepia':'sepia(100%)','blur':'blur(3px)','brightness':'brightness(1.3)','contrast':'contrast(1.3)','saturate':'saturate(1.5)','invert':'invert(100%)'};
filterCtx.filter=filters[currentFilter]||'none';
filterCtx.drawImage(filterImg,0,0);
filterCtx.filter='none';
}

function resetFilter(){
currentFilter='none';
document.querySelectorAll('#filter .preset-btn').forEach((b,i)=>{
b.classList.remove('active');
if(i===0)b.classList.add('active');
});
drawFilter();
}

function downloadFilter(){
if(!filterCanvas)return;
downloadCanvas(filterCanvas,'filtered');
}

// PDF
function handlePDFImages(input){
const preview=document.getElementById('pdf-preview');
pdfImages=Array.from(input.files);
renderPDF();
if(sortable)sortable.destroy();
sortable=Sortable.create(preview,{
animation:150,
onEnd:function(evt){
const moved=pdfImages.splice(evt.oldIndex,1)[0];
pdfImages.splice(evt.newIndex,0,moved);
}
});
}

function renderPDF(){
const preview=document.getElementById('pdf-preview');
preview.innerHTML='';
pdfImages.forEach((file,idx)=>{
const reader=new FileReader();
reader.onload=function(e){
const div=document.createElement('div');
div.className='pdf-image-item';
div.innerHTML=`<img src="${e.target.result}"><div class="remove-btn" onclick="removePDF(${idx})">×</div><p class="text-xs text-gray-600 mt-1 text-center">${idx+1}</p>`;
preview.appendChild(div);
};
reader.readAsDataURL(file);
});
}

function removePDF(idx){
pdfImages.splice(idx,1);
renderPDF();
if(sortable)sortable.destroy();
if(pdfImages.length>0){
sortable=Sortable.create(document.getElementById('pdf-preview'),{
animation:150,
onEnd:function(evt){
const moved=pdfImages.splice(evt.oldIndex,1)[0];
pdfImages.splice(evt.newIndex,0,moved);
}
});
}
}

function downloadCanvas(canvas,name){
canvas.toBlob(function(blob){
const url=URL.createObjectURL(blob);
const a=document.createElement('a');
a.href=url;
a.download=name+'.png';
document.body.appendChild(a);
a.click();
document.body.removeChild(a);
URL.revokeObjectURL(url);
},'image/png');
}

// Server handlers
async function handlePassport(e){
e.preventDefault();
const form=e.target;
const formData=new FormData(form);
const resultDiv=document.getElementById('passport-result');
resultDiv.innerHTML='<div class="loader"></div><p class="text-center mt-2">Creating passport photo...</p>';
try{
const response=await fetch('/passport',{method:'POST',body:formData});
if(response.ok){
const blob=await response.blob();
const url=URL.createObjectURL(blob);
const size=(blob.size/1024).toFixed(1);
resultDiv.innerHTML=`<div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4"><i class="fas fa-check-circle text-green-600"></i> <span class="font-bold text-green-700">Success!</span> ${size}KB</div><div class="text-center"><img src="${url}" class="preview-image mx-auto mb-4"><button onclick="downloadFile('${url}','passport_photo.jpg')" class="bg-green-500 text-white px-8 py-3 rounded-lg hover:bg-green-600"><i class="fas fa-download mr-2"></i>Download</button></div>`;
}else{
resultDiv.innerHTML=`<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"><i class="fas fa-exclamation-circle"></i> Error: ${await response.text()}</div>`;
}
}catch(err){
resultDiv.innerHTML=`<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"><i class="fas fa-exclamation-circle"></i> Error: ${err.message}</div>`;
}
}

async function handleCompress(e){
e.preventDefault();
const form=e.target;
const formData=new FormData(form);
const resultDiv=document.getElementById('compress-result');
resultDiv.innerHTML='<div class="loader"></div><p class="text-center mt-2">Compressing...</p>';
try{
const response=await fetch('/compress',{method:'POST',body:formData});
if(response.ok){
const blob=await response.blob();
const url=URL.createObjectURL(blob);
const size=(blob.size/1024).toFixed(1);
resultDiv.innerHTML=`<div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4"><i class="fas fa-check-circle text-green-600"></i> <span class="font-bold text-green-700">Success!</span> ${size}KB</div><div class="text-center"><img src="${url}" class="preview-image mx-auto mb-4"><button onclick="downloadFile('${url}','compressed.jpg')" class="bg-green-500 text-white px-8 py-3 rounded-lg hover:bg-green-600"><i class="fas fa-download mr-2"></i>Download</button></div>`;
}else{
resultDiv.innerHTML=`<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"><i class="fas fa-exclamation-circle"></i> Error: ${await response.text()}</div>`;
}
}catch(err){
resultDiv.innerHTML=`<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"><i class="fas fa-exclamation-circle"></i> Error: ${err.message}</div>`;
}
}

async function handlePDF(e){
e.preventDefault();
const form=e.target;
const formData=new FormData(form);
formData.delete('files');
pdfImages.forEach(file=>formData.append('files',file));
const resultDiv=document.getElementById('pdf-result');
resultDiv.innerHTML='<div class="loader"></div><p class="text-center mt-2">Creating PDF...</p>';
try{
const response=await fetch('/to_pdf',{method:'POST',body:formData});
if(response.ok){
const blob=await response.blob();
const url=URL.createObjectURL(blob);
resultDiv.innerHTML=`<div class="text-center bg-gradient-to-r from-purple-50 to-blue-50 p-8 rounded-lg"><i class="fas fa-file-pdf text-6xl text-red-500 mb-4"></i><h3 class="font-bold text-xl mb-2">PDF Created!</h3><p class="text-gray-600 mb-4">${pdfImages.length} images</p><button onclick="downloadFile('${url}','document.pdf')" class="bg-green-500 text-white px-8 py-3 rounded-lg hover:bg-green-600"><i class="fas fa-download mr-2"></i>Download PDF</button></div>`;
}else{
resultDiv.innerHTML=`<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"><i class="fas fa-exclamation-circle"></i> Error: ${await response.text()}</div>`;
}
}catch(err){
resultDiv.innerHTML=`<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"><i class="fas fa-exclamation-circle"></i> Error: ${err.message}</div>`;
}
}

async function handleSignature(e){
e.preventDefault();
const form=e.target;
const formData=new FormData(form);
const resultDiv=document.getElementById('signature-result');
resultDiv.innerHTML='<div class="loader"></div><p class="text-center mt-2">Processing...</p>';
try{
const response=await fetch('/signature',{method:'POST',body:formData});
if(response.ok){
const blob=await response.blob();
const url=URL.createObjectURL(blob);
const size=(blob.size/1024).toFixed(1);
resultDiv.innerHTML=`<div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4"><i class="fas fa-check-circle text-green-600"></i> <span class="font-bold text-green-700">Success!</span> ${size}KB</div><div class="text-center"><div class="bg-white p-4 inline-block mb-4"><img src="${url}" class="preview-image mx-auto" style="max-height:150px"></div><br><button onclick="downloadFile('${url}','signature.jpg')" class="bg-green-500 text-white px-8 py-3 rounded-lg hover:bg-green-600"><i class="fas fa-download mr-2"></i>Download</button></div>`;
}else{
resultDiv.innerHTML=`<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"><i class="fas fa-exclamation-circle"></i> Error: ${await response.text()}</div>`;
}
}catch(err){
resultDiv.innerHTML=`<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"><i class="fas fa-exclamation-circle"></i> Error: ${err.message}</div>`;
}
}

function downloadFile(url,filename){
const a=document.createElement('a');
a.href=url;
a.download=filename;
document.body.appendChild(a);
a.click();
document.body.removeChild(a);
}
</script>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/passport', methods=['POST'])
def passport():
    try:
        f = request.files.get('image')
        if not f: return "No file", 400
        if not allowed_filename(f.filename): return "Invalid type", 400
        if not pil_open_validate(f.stream): return "Invalid image", 400
        
        width = int(request.form.get('width', 200))
        height = int(request.form.get('height', 230))
        maxsize = int(request.form.get('maxsize', 100)) * 1024
        
        f.stream.seek(0)
        img = Image.open(f.stream)
        img = ImageOps.exif_transpose(img)
        img = img.resize((width, height), Image.LANCZOS)
        img = img.convert('RGB')
        
        quality = 95
        while quality > 10:
            out = io.BytesIO()
            img.save(out, format='JPEG', quality=quality, optimize=True)
            if out.tell() <= maxsize:
                break
            quality -= 5
        
        out.seek(0)
        tmp = save_temp_bytes(out.read(), '.jpg')
        return send_file(tmp, as_attachment=True, download_name='passport_photo.jpg')
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/compress', methods=['POST'])
def compress():
    try:
        f = request.files.get('image')
        if not f: return "No file", 400
        if not allowed_filename(f.filename): return "Invalid type", 400
        if not pil_open_validate(f.stream): return "Invalid image", 400
        
        targetsize = int(request.form.get('targetsize', 50)) * 1024
        
        f.stream.seek(0)
        img = Image.open(f.stream)
        img = ImageOps.exif_transpose(img)
        img = img.convert('RGB')
        
        quality = 95
        while quality > 10:
            out = io.BytesIO()
            img.save(out, format='JPEG', quality=quality, optimize=True)
            if out.tell() <= targetsize:
                break
            quality -= 5
        
        out.seek(0)
        tmp = save_temp_bytes(out.read(), '.jpg')
        return send_file(tmp, as_attachment=True, download_name='compressed.jpg')
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/to_pdf', methods=['POST'])
def to_pdf():
    try:
        files = request.files.getlist('files')
        if not files: return "No files", 400
        
        imgs = []
        for f in files:
            if not allowed_filename(f.filename): continue
            if not pil_open_validate(f.stream): continue
            f.stream.seek(0)
            img = Image.open(f.stream)
            img = ImageOps.exif_transpose(img)
            if img.mode in ('RGBA','LA','P'):
                bg = Image.new('RGB', img.size, (255,255,255))
                if img.mode == 'RGBA':
                    bg.paste(img, mask=img.split()[-1])
                else:
                    bg.paste(img)
                img = bg
            else:
                img = img.convert('RGB')
            imgs.append(img)
        
        if not imgs: return "No valid images", 400
        
        out = io.BytesIO()
        imgs[0].save(out, format='PDF', save_all=True, append_images=imgs[1:], quality=85)
        out.seek(0)
        tmp = save_temp_bytes(out.read(), '.pdf')
        return send_file(tmp, as_attachment=True, download_name='document.pdf')
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/signature', methods=['POST'])
def signature():
    try:
        f = request.files.get('image')
        if not f: return "No file", 400
        if not allowed_filename(f.filename): return "Invalid type", 400
        if not pil_open_validate(f.stream): return "Invalid image", 400
        
        width = int(request.form.get('width', 140))
        height = int(request.form.get('height', 60))
        maxsize = int(request.form.get('maxsize', 50)) * 1024
        
        f.stream.seek(0)
        img = Image.open(f.stream)
        img = ImageOps.exif_transpose(img)
        
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                bg.paste(img, mask=img.split()[-1])
            else:
                bg.paste(img)
            img = bg
        else:
            img = img.convert('RGB')
        
        img = img.resize((width, height), Image.LANCZOS)
        
        quality = 95
        while quality > 10:
            out = io.BytesIO()
            img.save(out, format='JPEG', quality=quality, optimize=True)
            if out.tell() <= maxsize:
                break
            quality -= 5
        
        out.seek(0)
        tmp = save_temp_bytes(out.read(), '.jpg')
        return send_file(tmp, as_attachment=True, download_name='signature.jpg')
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("📋 ImageMaster Pro - Government Job Tools")
    print("="*60)
    print(f"🚀 Server: http://localhost:{port}")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)
