# app.py — Enhanced single-file Flask app with improved background removal and color replacement
import os, io, tempfile, uuid, traceback
from flask import Flask, render_template_string, request, send_file, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, UnidentifiedImageError
import time, base64

# Optional: OpenCV for background removal
try:
    import cv2, numpy as np
    OPENCV_AVAILABLE = True
except Exception:
    OPENCV_AVAILABLE = False

# Optional: rembg for better background removal
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except Exception:
    REMBG_AVAILABLE = False

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25 MB max upload
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key-in-production')

ALLOWED_EXT = {'png','jpg','jpeg','webp','bmp','gif'}

# ---------- Helpers ----------
def allowed_filename(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def pil_open_validate(file_stream):
    try:
        img = Image.open(file_stream)
        img.verify()
        file_stream.seek(0)
        return True
    except Exception:
        return False

def save_temp_bytes(b: bytes, suffix=''):
    name = f"{uuid.uuid4().hex}{suffix}"
    path = os.path.join(tempfile.gettempdir(), name)
    with open(path, 'wb') as f:
        f.write(b)
    return path

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# ---------- Enhanced HTML Template ----------
INDEX_HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ImageMaster Pro - All-in-One Image Tools</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
  <style>
    .tab{display:none}
    .tab.active{display:block}
    .preview-container{
      border: 2px dashed #cbd5e1;
      border-radius: 0.5rem;
      padding: 2rem;
      text-align: center;
      background: #f8fafc;
      transition: all 0.3s;
    }
    .preview-container:hover{
      border-color: #667eea;
      background: #f1f5f9;
    }
    .preview-image{
      max-width: 100%;
      max-height: 400px;
      margin: 1rem auto;
      border-radius: 0.5rem;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .comparison-container{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      margin-top: 1rem;
    }
    @media (max-width: 768px) {
      .comparison-container{
        grid-template-columns: 1fr;
      }
    }
    .comparison-item{
      text-align: center;
      padding: 1rem;
      background: #f8fafc;
      border-radius: 0.5rem;
    }
    .btn-primary{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      transition: all 0.3s;
    }
    .btn-primary:hover{
      transform: translateY(-2px);
      box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .btn-secondary{
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      transition: all 0.3s;
    }
    .btn-secondary:hover{
      transform: translateY(-2px);
      box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .tab-button{
      transition: all 0.3s;
      border-bottom: 3px solid transparent;
    }
    .tab-button.active{
      border-bottom-color: #667eea;
      color: #667eea;
      font-weight: 600;
    }
    .pdf-image-item{
      position: relative;
      cursor: move;
      border: 2px solid #e2e8f0;
      border-radius: 0.5rem;
      padding: 0.5rem;
      background: white;
      transition: all 0.2s;
    }
    .pdf-image-item:hover{
      border-color: #667eea;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      transform: scale(1.02);
    }
    .pdf-image-item.sortable-ghost{
      opacity: 0.4;
    }
    .pdf-image-item img{
      width: 100%;
      height: 150px;
      object-fit: cover;
      border-radius: 0.25rem;
    }
    .remove-btn{
      position: absolute;
      top: 0.5rem;
      right: 0.5rem;
      background: #ef4444;
      color: white;
      border-radius: 50%;
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 16px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
      transition: all 0.2s;
    }
    .remove-btn:hover{
      background: #dc2626;
      transform: scale(1.1);
    }
    .loader{
      border: 3px solid #f3f4f6;
      border-top: 3px solid #667eea;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 0 auto;
    }
    @keyframes spin{
      0%{transform: rotate(0deg);}
      100%{transform: rotate(360deg);}
    }
    .color-swatch{
      width: 50px;
      height: 50px;
      border-radius: 0.5rem;
      cursor: pointer;
      border: 3px solid transparent;
      transition: all 0.2s;
      display: inline-block;
    }
    .color-swatch:hover{
      transform: scale(1.1);
      box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .color-swatch.selected{
      border-color: #667eea;
      box-shadow: 0 0 0 2px white, 0 0 0 4px #667eea;
    }
    .checkerboard{
      background-image: 
        linear-gradient(45deg, #ccc 25%, transparent 25%), 
        linear-gradient(-45deg, #ccc 25%, transparent 25%), 
        linear-gradient(45deg, transparent 75%, #ccc 75%), 
        linear-gradient(-45deg, transparent 75%, #ccc 75%);
      background-size: 20px 20px;
      background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
    }
    .feature-card{
      background: white;
      padding: 1.5rem;
      border-radius: 1rem;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
      transition: all 0.3s;
    }
    .feature-card:hover{
      transform: translateY(-4px);
      box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    .gradient-text{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  </style>
</head>
<body class="bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 min-h-screen p-4 md:p-6">
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="bg-white p-6 md:p-8 rounded-2xl shadow-lg mb-6">
      <div class="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 class="text-3xl md:text-4xl font-bold gradient-text mb-2">
            <i class="fas fa-magic mr-2"></i>ImageMaster Pro
          </h1>
          <p class="text-gray-600">Professional image tools at your fingertips</p>
        </div>
        <div class="text-sm text-gray-500">
          <i class="fas fa-shield-alt text-green-500"></i> Free • No Sign-up • Privacy First
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="bg-white p-4 rounded-2xl shadow-lg mb-6 overflow-x-auto">
      <div class="flex gap-2 min-w-max">
        <button onclick="showTab('compress')" class="tab-button active px-4 md:px-6 py-3 rounded-lg flex items-center gap-2 whitespace-nowrap">
          <i class="fas fa-compress"></i> <span class="hidden sm:inline">Compress</span>
        </button>
        <button onclick="showTab('convert')" class="tab-button px-4 md:px-6 py-3 rounded-lg flex items-center gap-2 whitespace-nowrap">
          <i class="fas fa-exchange-alt"></i> <span class="hidden sm:inline">Resize/Convert</span>
        </button>
        <button onclick="showTab('pdf')" class="tab-button px-4 md:px-6 py-3 rounded-lg flex items-center gap-2 whitespace-nowrap">
          <i class="fas fa-file-pdf"></i> <span class="hidden sm:inline">Images → PDF</span>
        </button>
        <button onclick="showTab('bg')" class="tab-button px-4 md:px-6 py-3 rounded-lg flex items-center gap-2 whitespace-nowrap">
          <i class="fas fa-cut"></i> <span class="hidden sm:inline">Background</span>
        </button>
        <button onclick="showTab('enhance')" class="tab-button px-4 md:px-6 py-3 rounded-lg flex items-center gap-2 whitespace-nowrap">
          <i class="fas fa-wand-magic-sparkles"></i> <span class="hidden sm:inline">Enhance</span>
        </button>
      </div>
    </div>

    <!-- Content Area -->
    <div class="bg-white p-6 md:p-8 rounded-2xl shadow-lg">
      <!-- Compress Tab -->
      <div id="compress" class="tab active">
        <h2 class="text-2xl font-bold mb-4 flex items-center gap-2">
          <i class="fas fa-compress text-purple-600"></i> Compress Image
        </h2>
        <p class="text-gray-600 mb-6">Reduce file size while maintaining quality</p>
        <form id="form-compress" onsubmit="handleCompress(event)">
          <div class="preview-container mb-4">
            <input type="file" id="compress-input" name="image" accept="image/*" required 
              onchange="previewImage(this, 'compress-preview')" class="hidden">
            <label for="compress-input" class="cursor-pointer inline-block">
              <div class="text-gray-400 mb-2">
                <i class="fas fa-cloud-upload-alt text-6xl"></i>
              </div>
              <p class="text-lg font-medium text-gray-700">Click to upload image</p>
              <p class="text-sm text-gray-500">PNG, JPG, WEBP, BMP, GIF (Max 25MB)</p>
            </label>
            <div id="compress-preview"></div>
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Quality: <span id="quality-value" class="text-purple-600 font-bold">85</span>%
            </label>
            <input name="quality" type="range" value="85" min="10" max="95" 
              oninput="document.getElementById('quality-value').textContent=this.value"
              class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
            <div class="flex justify-between text-xs text-gray-500 mt-1">
              <span>Smaller file</span>
              <span>Better quality</span>
            </div>
          </div>
          <button type="submit" class="btn-primary text-white px-8 py-3 rounded-lg font-medium w-full">
            <i class="fas fa-compress mr-2"></i>Compress & Download
          </button>
        </form>
        <div id="compress-result" class="mt-6"></div>
      </div>

      <!-- Convert / Resize Tab -->
      <div id="convert" class="tab">
        <h2 class="text-2xl font-bold mb-4 flex items-center gap-2">
          <i class="fas fa-exchange-alt text-purple-600"></i> Resize / Convert Image
        </h2>
        <p class="text-gray-600 mb-6">Change dimensions and file format</p>
        <form id="form-convert" onsubmit="handleConvert(event)">
          <div class="preview-container mb-4">
            <input type="file" id="convert-input" name="image" accept="image/*" required
              onchange="previewImage(this, 'convert-preview')" class="hidden">
            <label for="convert-input" class="cursor-pointer inline-block">
              <div class="text-gray-400 mb-2">
                <i class="fas fa-cloud-upload-alt text-6xl"></i>
              </div>
              <p class="text-lg font-medium text-gray-700">Click to upload image</p>
            </label>
            <div id="convert-preview"></div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Output Format:</label>
              <select name="outfmt" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                <option value="JPEG">JPG</option>
                <option value="PNG">PNG</option>
                <option value="WEBP">WEBP</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Width (px):</label>
              <input name="width" type="number" min="1" placeholder="Auto"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Height (px):</label>
              <input name="height" type="number" min="1" placeholder="Auto"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
            </div>
          </div>
          <button type="submit" class="btn-primary text-white px-8 py-3 rounded-lg font-medium w-full">
            <i class="fas fa-exchange-alt mr-2"></i>Convert & Download
          </button>
        </form>
        <div id="convert-result" class="mt-6"></div>
      </div>

      <!-- PDF Tab -->
      <div id="pdf" class="tab">
        <h2 class="text-2xl font-bold mb-4 flex items-center gap-2">
          <i class="fas fa-file-pdf text-purple-600"></i> Images to PDF
        </h2>
        <p class="text-gray-600 mb-6">Combine multiple images into a single PDF</p>
        <form id="form-pdf" onsubmit="handlePDF(event)">
          <div class="preview-container mb-4">
            <input type="file" id="pdf-input" name="files" accept="image/*" multiple required
              onchange="handlePDFImages(this)" class="hidden">
            <label for="pdf-input" class="cursor-pointer inline-block">
              <div class="text-gray-400 mb-2">
                <i class="fas fa-cloud-upload-alt text-6xl"></i>
              </div>
              <p class="text-lg font-medium text-gray-700">Click to upload multiple images</p>
              <p class="text-sm text-gray-500"><i class="fas fa-arrows-alt mr-1"></i>Drag to reorder • <i class="fas fa-times-circle mr-1"></i>Click X to remove</p>
            </label>
          </div>
          <div id="pdf-preview" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4"></div>
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Quality: <span id="pdf-quality-value" class="text-purple-600 font-bold">85</span>%
            </label>
            <input name="quality" type="range" value="85" min="10" max="95"
              oninput="document.getElementById('pdf-quality-value').textContent=this.value"
              class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
          </div>
          <button type="submit" class="btn-primary text-white px-8 py-3 rounded-lg font-medium w-full">
            <i class="fas fa-file-pdf mr-2"></i>Create PDF
          </button>
        </form>
        <div id="pdf-result" class="mt-6"></div>
      </div>

      <!-- Background Remove Tab -->
      <div id="bg" class="tab">
        <h2 class="text-2xl font-bold mb-4 flex items-center gap-2">
          <i class="fas fa-cut text-purple-600"></i> Remove & Replace Background
        </h2>
        <p class="text-gray-600 mb-6">Remove background or replace with any color</p>
        <form id="form-bg" onsubmit="handleBGRemove(event)">
          <div class="preview-container mb-4">
            <input type="file" id="bg-input" name="image" accept="image/*" required
              onchange="previewImage(this, 'bg-preview')" class="hidden">
            <label for="bg-input" class="cursor-pointer inline-block">
              <div class="text-gray-400 mb-2">
                <i class="fas fa-cloud-upload-alt text-6xl"></i>
              </div>
              <p class="text-lg font-medium text-gray-700">Click to upload image</p>
            </label>
            <div id="bg-preview"></div>
          </div>
          
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-3">Background Color:</label>
            <div class="flex flex-wrap gap-3 mb-3">
              <div class="color-swatch selected" style="background: transparent; background-image: linear-gradient(45deg, #ccc 25%, transparent 25%), linear-gradient(-45deg, #ccc 25%, transparent 25%); background-size: 10px 10px; background-position: 0 0, 5px 5px;" 
                   onclick="selectColor('transparent', this)" data-color="transparent" title="Transparent"></div>
              <div class="color-swatch" style="background: #ffffff;" onclick="selectColor('#ffffff', this)" title="White"></div>
              <div class="color-swatch" style="background: #000000;" onclick="selectColor('#000000', this)" title="Black"></div>
              <div class="color-swatch" style="background: #ef4444;" onclick="selectColor('#ef4444', this)" title="Red"></div>
              <div class="color-swatch" style="background: #3b82f6;" onclick="selectColor('#3b82f6', this)" title="Blue"></div>
              <div class="color-swatch" style="background: #10b981;" onclick="selectColor('#10b981', this)" title="Green"></div>
              <div class="color-swatch" style="background: #f59e0b;" onclick="selectColor('#f59e0b', this)" title="Orange"></div>
              <div class="color-swatch" style="background: #8b5cf6;" onclick="selectColor('#8b5cf6', this)" title="Purple"></div>
              <div class="color-swatch" style="background: #ec4899;" onclick="selectColor('#ec4899', this)" title="Pink"></div>
              <div class="color-swatch" style="background: #06b6d4;" onclick="selectColor('#06b6d4', this)" title="Cyan"></div>
            </div>
            <div class="flex gap-2 items-center">
              <label class="text-sm text-gray-600">Custom Color:</label>
              <input type="color" id="custom-color" value="#667eea" 
                onchange="selectColor(this.value, null)" 
                class="w-16 h-10 rounded cursor-pointer border-2 border-gray-300">
              <button type="button" onclick="selectColor(document.getElementById('custom-color').value, null)" 
                class="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 text-sm">Apply Custom</button>
            </div>
            <input type="hidden" name="bg_color" id="bg-color-input" value="transparent">
          </div>
          
          <button type="submit" class="btn-primary text-white px-8 py-3 rounded-lg font-medium w-full">
            <i class="fas fa-cut mr-2"></i>Process Background
          </button>
        </form>
        <div id="bg-result" class="mt-6"></div>
      </div>

      <!-- Enhance Tab -->
      <div id="enhance" class="tab">
        <h2 class="text-2xl font-bold mb-4 flex items-center gap-2">
          <i class="fas fa-wand-magic-sparkles text-purple-600"></i> Enhance Image
        </h2>
        <p class="text-gray-600 mb-6">Improve brightness, contrast, sharpness and more with real-time preview</p>
        
        <div class="preview-container mb-4">
          <input type="file" id="enhance-input" name="image" accept="image/*" required
            onchange="loadEnhanceImage(this)" class="hidden">
          <label for="enhance-input" class="cursor-pointer inline-block">
            <div class="text-gray-400 mb-2">
              <i class="fas fa-cloud-upload-alt text-6xl"></i>
            </div>
            <p class="text-lg font-medium text-gray-700">Click to upload image</p>
          </label>
        </div>
        
        <div id="enhance-canvas-container" style="display:none;">
          <div class="mb-4 text-center">
            <canvas id="enhance-canvas" class="preview-image mx-auto" style="max-width: 100%; height: auto; border-radius: 0.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></canvas>
          </div>
          
          <div class="space-y-4 mb-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Brightness: <span id="brightness-value" class="text-purple-600 font-bold">1.0</span>
              </label>
              <input id="brightness-slider" type="range" value="1.0" min="0.5" max="2.0" step="0.05"
                oninput="updateEnhancement()"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Contrast: <span id="contrast-value" class="text-purple-600 font-bold">1.0</span>
              </label>
              <input id="contrast-slider" type="range" value="1.0" min="0.5" max="2.0" step="0.05"
                oninput="updateEnhancement()"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Saturation: <span id="saturation-value" class="text-purple-600 font-bold">1.0</span>
              </label>
              <input id="saturation-slider" type="range" value="1.0" min="0" max="2.0" step="0.05"
                oninput="updateEnhancement()"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Blur/Sharpen: <span id="blur-value" class="text-purple-600 font-bold">0</span>
              </label>
              <input id="blur-slider" type="range" value="0" min="-5" max="5" step="1"
                oninput="updateEnhancement()"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
              <div class="flex justify-between text-xs text-gray-500 mt-1">
                <span>Blur</span>
                <span>Normal</span>
                <span>Sharpen</span>
              </div>
            </div>

            <div class="flex gap-2">
              <button type="button" onclick="resetEnhancement()" 
                class="flex-1 bg-gray-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-600 transition">
                <i class="fas fa-undo mr-2"></i>Reset
              </button>
              <button type="button" onclick="downloadEnhancedImage()" 
                class="flex-1 btn-primary text-white px-6 py-3 rounded-lg font-medium">
                <i class="fas fa-download mr-2"></i>Download
              </button>
            </div>
          </div>
        </div>
      </div>

      <div id="msg" class="mt-4 text-sm"></div>
    </div>

    <!-- Features Section -->
    <div class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="feature-card">
        <i class="fas fa-lock text-3xl text-purple-600 mb-3"></i>
        <h3 class="font-bold mb-2">100% Privacy</h3>
        <p class="text-sm text-gray-600">Your images are processed securely and never stored</p>
      </div>
      <div class="feature-card">
        <i class="fas fa-bolt text-3xl text-purple-600 mb-3"></i>
        <h3 class="font-bold mb-2">Lightning Fast</h3>
        <p class="text-sm text-gray-600">Process images in seconds with our optimized algorithms</p>
      </div>
      <div class="feature-card">
        <i class="fas fa-star text-3xl text-purple-600 mb-3"></i>
        <h3 class="font-bold mb-2">Professional Quality</h3>
        <p class="text-sm text-gray-600">Industry-standard tools for perfect results every time</p>
      </div>
    </div>

    <!-- Footer -->
    <div class="mt-8 text-center text-sm text-gray-600">
      <p>© 2024 ImageMaster Pro • Made with <i class="fas fa-heart text-red-500"></i></p>
    </div>
  </div>

<script>
let pdfImages = [];
let sortable = null;
let selectedBgColor = 'transparent';

// Real-time enhancement variables
let originalImage = null;
let enhanceCanvas = null;
let enhanceCtx = null;

function showTab(id){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab-button').forEach(b=>b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
  document.getElementById('msg').textContent = '';
  
  // Clear results
  ['compress-result','convert-result','pdf-result','bg-result'].forEach(rid => {
    const el = document.getElementById(rid);
    if(el) el.innerHTML = '';
  });
  
  // Reset enhance tab
  if(id === 'enhance'){
    document.getElementById('enhance-canvas-container').style.display = 'none';
    originalImage = null;
    enhanceCanvas = null;
    enhanceCtx = null;
  }
}

function selectColor(color, element){
  selectedBgColor = color;
  document.getElementById('bg-color-input').value = color;
  
  // Update visual selection
  document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('selected'));
  if(element){
    element.classList.add('selected');
  }
}

function previewImage(input, previewId){
  const preview = document.getElementById(previewId);
  if(input.files && input.files[0]){
    const reader = new FileReader();
    reader.onload = function(e){
      const img = new Image();
      img.onload = function(){
        const fileSize = (input.files[0].size / 1024 / 1024).toFixed(2);
        preview.innerHTML = `
          <img src="${e.target.result}" class="preview-image" alt="Preview">
          <p class="text-sm text-gray-600 mt-2">
            <i class="fas fa-info-circle"></i> ${img.width} × ${img.height}px • ${fileSize}MB
          </p>
        `;
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(input.files[0]);
  }
}

// Real-time enhancement functions
function loadEnhanceImage(input){
  if(input.files && input.files[0]){
    const reader = new FileReader();
    reader.onload = function(e){
      originalImage = new Image();
      originalImage.onload = function(){
        // Setup canvas
        enhanceCanvas = document.getElementById('enhance-canvas');
        enhanceCtx = enhanceCanvas.getContext('2d', { willReadFrequently: true });
        
        // Set canvas size to match image
        enhanceCanvas.width = originalImage.width;
        enhanceCanvas.height = originalImage.height;
        
        // Show canvas container
        document.getElementById('enhance-canvas-container').style.display = 'block';
        
        // Reset sliders
        resetEnhancement();
        
        // Initial draw
        updateEnhancement();
      };
      originalImage.src = e.target.result;
    };
    reader.readAsDataURL(input.files[0]);
  }
}

function updateEnhancement(){
  if(!originalImage || !enhanceCanvas) return;
  
  // Get slider values
  const brightness = parseFloat(document.getElementById('brightness-slider').value);
  const contrast = parseFloat(document.getElementById('contrast-slider').value);
  const saturation = parseFloat(document.getElementById('saturation-slider').value);
  const blur = parseInt(document.getElementById('blur-slider').value);
  
  // Update labels
  document.getElementById('brightness-value').textContent = brightness.toFixed(2);
  document.getElementById('contrast-value').textContent = contrast.toFixed(2);
  document.getElementById('saturation-value').textContent = saturation.toFixed(2);
  document.getElementById('blur-value').textContent = blur;
  
  // Build filter string
  let filters = [];
  filters.push(`brightness(${brightness})`);
  filters.push(`contrast(${contrast})`);
  filters.push(`saturate(${saturation})`);
  if(blur > 0){
    filters.push(`blur(${blur}px)`);
  } else if(blur < 0){
    // For sharpening effect
    filters.push(`contrast(${1 + Math.abs(blur) * 0.1})`);
  }
  
  // Apply filters and redraw
  enhanceCtx.filter = filters.join(' ');
  enhanceCtx.clearRect(0, 0, enhanceCanvas.width, enhanceCanvas.height);
  enhanceCtx.drawImage(originalImage, 0, 0);
  enhanceCtx.filter = 'none';
}

function resetEnhancement(){
  document.getElementById('brightness-slider').value = 1.0;
  document.getElementById('contrast-slider').value = 1.0;
  document.getElementById('saturation-slider').value = 1.0;
  document.getElementById('blur-slider').value = 0;
  updateEnhancement();
}

function downloadEnhancedImage(){
  if(!enhanceCanvas) return;
  
  // Show custom filename dialog
  const filename = prompt('Enter filename (without extension):', 'enhanced_image');
  if(!filename) return; // User cancelled
  
  // Convert canvas to blob and download
  enhanceCanvas.toBlob(function(blob){
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 'image/png');
}

function handlePDFImages(input){
  const preview = document.getElementById('pdf-preview');
  pdfImages = Array.from(input.files);
  renderPDFPreview();
  
  // Initialize sortable
  if(sortable) sortable.destroy();
  sortable = Sortable.create(preview, {
    animation: 150,
    onEnd: function(evt){
      const movedItem = pdfImages.splice(evt.oldIndex, 1)[0];
      pdfImages.splice(evt.newIndex, 0, movedItem);
    }
  });
}

function renderPDFPreview(){
  const preview = document.getElementById('pdf-preview');
  preview.innerHTML = '';
  pdfImages.forEach((file, idx) => {
    const reader = new FileReader();
    reader.onload = function(e){
      const div = document.createElement('div');
      div.className = 'pdf-image-item';
      div.innerHTML = `
        <img src="${e.target.result}" alt="Image ${idx+1}">
        <div class="remove-btn" onclick="removePDFImage(${idx})" title="Remove">×</div>
        <p class="text-xs text-gray-600 mt-1 text-center font-medium">${idx+1}. ${file.name.substring(0, 20)}${file.name.length > 20 ? '...' : ''}</p>
      `;
      preview.appendChild(div);
    };
    reader.readAsDataURL(file);
  });
}

function removePDFImage(idx){
  pdfImages.splice(idx, 1);
  renderPDFPreview();
  if(sortable) sortable.destroy();
  if(pdfImages.length > 0){
    sortable = Sortable.create(document.getElementById('pdf-preview'), {
      animation: 150,
      onEnd: function(evt){
        const movedItem = pdfImages.splice(evt.oldIndex, 1)[0];
        pdfImages.splice(evt.newIndex, 0, movedItem);
      }
    });
  }
}

async function handleCompress(e){
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const resultDiv = document.getElementById('compress-result');
  
  resultDiv.innerHTML = '<div class="loader"></div><p class="text-center mt-2 text-gray-600">Compressing image...</p>';
  
  try{
    const response = await fetch('/compress', {method: 'POST', body: formData});
    if(response.ok){
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const originalSrc = document.querySelector('#compress-preview img').src;
      const originalSize = (form.image.files[0].size / 1024 / 1024).toFixed(2);
      const newSize = (blob.size / 1024 / 1024).toFixed(2);
      const savings = ((1 - blob.size / form.image.files[0].size) * 100).toFixed(1);
      
      resultDiv.innerHTML = `
        <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
          <i class="fas fa-check-circle text-green-600"></i> 
          <span class="font-bold text-green-700">Success!</span> Reduced by ${savings}% (${originalSize}MB → ${newSize}MB)
        </div>
        <div class="comparison-container">
          <div class="comparison-item">
            <h3 class="font-bold text-lg mb-2">Original</h3>
            <img src="${originalSrc}" class="preview-image">
            <p class="text-sm text-gray-600">${originalSize}MB</p>
          </div>
          <div class="comparison-item">
            <h3 class="font-bold text-lg mb-2">Compressed</h3>
            <img src="${url}" class="preview-image">
            <p class="text-sm text-gray-600">${newSize}MB</p>
            <button onclick="downloadWithCustomName('${url}', 'compressed', 'jpg')" 
              class="inline-block mt-4 bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition">
              <i class="fas fa-download mr-2"></i>Download
            </button>
          </div>
        </div>
      `;
    } else {
      resultDiv.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <i class="fas fa-exclamation-circle"></i> Error: ${await response.text()}
      </div>`;
    }
  } catch(err){
    resultDiv.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
      <i class="fas fa-exclamation-circle"></i> Error: ${err.message}
    </div>`;
  }
}

async function handleConvert(e){
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const resultDiv = document.getElementById('convert-result');
  
  resultDiv.innerHTML = '<div class="loader"></div><p class="text-center mt-2 text-gray-600">Converting image...</p>';
  
  try{
    const response = await fetch('/convert', {method: 'POST', body: formData});
    if(response.ok){
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const originalSrc = document.querySelector('#convert-preview img').src;
      const format = form.outfmt.value.toLowerCase();
      
      resultDiv.innerHTML = `
        <div class="comparison-container">
          <div class="comparison-item">
            <h3 class="font-bold text-lg mb-2">Original</h3>
            <img src="${originalSrc}" class="preview-image">
          </div>
          <div class="comparison-item">
            <h3 class="font-bold text-lg mb-2">Converted</h3>
            <img src="${url}" class="preview-image">
            <button onclick="downloadWithCustomName('${url}', 'converted', '${format}')" 
              class="inline-block mt-4 bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition">
              <i class="fas fa-download mr-2"></i>Download
            </button>
          </div>
        </div>
      `;
    } else {
      resultDiv.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <i class="fas fa-exclamation-circle"></i> Error: ${await response.text()}
      </div>`;
    }
  } catch(err){
    resultDiv.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
      <i class="fas fa-exclamation-circle"></i> Error: ${err.message}
    </div>`;
  }
}

async function handlePDF(e){
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  
  // Clear existing files and add reordered ones
  formData.delete('files');
  pdfImages.forEach(file => formData.append('files', file));
  
  const resultDiv = document.getElementById('pdf-result');
  resultDiv.innerHTML = '<div class="loader"></div><p class="text-center mt-2 text-gray-600">Creating PDF...</p>';
  
  try{
    const response = await fetch('/to_pdf', {method: 'POST', body: formData});
    if(response.ok){
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      resultDiv.innerHTML = `
        <div class="text-center bg-gradient-to-r from-purple-50 to-blue-50 p-8 rounded-lg">
          <i class="fas fa-file-pdf text-6xl text-red-500 mb-4"></i>
          <h3 class="font-bold text-xl mb-2">PDF Created Successfully!</h3>
          <p class="text-gray-600 mb-4">${pdfImages.length} images combined</p>
          <button onclick="downloadWithCustomName('${url}', 'images', 'pdf')" 
            class="inline-block bg-green-500 text-white px-8 py-3 rounded-lg hover:bg-green-600 transition text-lg font-medium">
            <i class="fas fa-download mr-2"></i>Download PDF
          </button>
        </div>
      `;
    } else {
      resultDiv.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <i class="fas fa-exclamation-circle"></i> Error: ${await response.text()}
      </div>`;
    }
  } catch(err){
    resultDiv.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
      <i class="fas fa-exclamation-circle"></i> Error: ${err.message}
    </div>`;
  }
}

async function handleBGRemove(e){
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const resultDiv = document.getElementById('bg-result');
  
  resultDiv.innerHTML = '<div class="loader"></div><p class="text-center mt-2 text-gray-600">Processing background... This may take a moment.</p>';
  
  try{
    const response = await fetch('/bg_remove', {method: 'POST', body: formData});
    if(response.ok){
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const originalSrc = document.querySelector('#bg-preview img').src;
      const bgColor = selectedBgColor;
      const isTransparent = bgColor === 'transparent';
      const ext = isTransparent ? 'png' : 'jpg';
      
      resultDiv.innerHTML = `
        <div class="comparison-container">
          <div class="comparison-item">
            <h3 class="font-bold text-lg mb-2">Original</h3>
            <img src="${originalSrc}" class="preview-image">
          </div>
          <div class="comparison-item">
            <h3 class="font-bold text-lg mb-2">Processed</h3>
            <div class="${isTransparent ? 'checkerboard' : ''}" style="${!isTransparent ? 'background-color: ' + bgColor : ''}; padding: 1rem; border-radius: 0.5rem;">
              <img src="${url}" class="preview-image">
            </div>
            <button onclick="downloadWithCustomName('${url}', 'no_background', '${ext}')" 
              class="inline-block mt-4 bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition">
              <i class="fas fa-download mr-2"></i>Download
            </button>
          </div>
        </div>
      `;
    } else {
      const errorText = await response.text();
      resultDiv.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <i class="fas fa-exclamation-circle"></i> ${errorText}
      </div>`;
    }
  } catch(err){
    resultDiv.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
      <i class="fas fa-exclamation-circle"></i> Error: ${err.message}
    </div>`;
  }
}

// Custom filename download function
function downloadWithCustomName(url, defaultName, extension){
  const filename = prompt('Enter filename (without extension):', defaultName);
  if(!filename) return; // User cancelled
  
  const a = document.createElement('a');
  a.href = url;
  a.download = `${filename}.${extension}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
</script>
</body>
</html>
"""

# ---------- Image endpoints ----------

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/compress', methods=['POST'])
def compress():
    try:
        f = request.files.get('image')
        if not f or f.filename == '':
            return "No file uploaded", 400
        if not allowed_filename(f.filename):
            return "Unsupported file type", 400
        if not pil_open_validate(f.stream):
            return "Invalid or corrupted image", 400
        f.stream.seek(0)
        quality = int(request.form.get('quality', 85))
        quality = max(10, min(95, quality))

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

        out = io.BytesIO()
        img.save(out, format='JPEG', quality=quality, optimize=True)
        out.seek(0)
        filename = secure_filename(f.filename)
        base = os.path.splitext(filename)[0]
        tmp = save_temp_bytes(out.read(), suffix='.jpg')
        return send_file(tmp, as_attachment=True, download_name=f'{base}_compressed.jpg')
    except Exception as e:
        traceback.print_exc()
        return f"Processing error: {str(e)}", 500

@app.route('/convert', methods=['POST'])
def convert():
    try:
        f = request.files.get('image')
        if not f: return "No file uploaded", 400
        if not allowed_filename(f.filename): return "Unsupported file type", 400
        if not pil_open_validate(f.stream): return "Invalid or corrupted image", 400
        outfmt = request.form.get('outfmt','JPEG')
        width = request.form.get('width')
        height = request.form.get('height')

        f.stream.seek(0)
        img = Image.open(f.stream)
        img = ImageOps.exif_transpose(img)
        if width or height:
            w = int(width) if width else None
            h = int(height) if height else None
            if w and not h:
                ratio = w / img.width
                h = int(img.height * ratio)
            if h and not w:
                ratio = h / img.height
                w = int(img.width * ratio)
            img = img.resize((w,h), Image.LANCZOS)
        buf = io.BytesIO()
        save_kwargs = {}
        if outfmt.upper() == 'JPEG':
            save_kwargs['quality'] = 90
            img = img.convert('RGB')
        if outfmt.upper() == 'WEBP':
            save_kwargs['quality'] = 90
        img.save(buf, format=outfmt.upper(), **save_kwargs)
        buf.seek(0)
        ext = outfmt.lower()
        tmp = save_temp_bytes(buf.read(), suffix='.'+ext)
        return send_file(tmp, as_attachment=True, download_name=f"{secure_filename(f.filename).rsplit('.',1)[0]}.{ext}")
    except Exception as e:
        traceback.print_exc()
        return f"Processing error: {str(e)}", 500

@app.route('/to_pdf', methods=['POST'])
def to_pdf():
    try:
        files = request.files.getlist('files')
        if not files: return "No files uploaded", 400
        quality = int(request.form.get('quality',85))
        imgs = []
        for f in files:
            if not allowed_filename(f.filename):
                continue
            if not pil_open_validate(f.stream):
                continue
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
            img.thumbnail((2000,2000))
            imgs.append(img)
        if not imgs:
            return "No valid images found", 400
        outbuf = io.BytesIO()
        imgs[0].save(outbuf, format='PDF', save_all=True, append_images=imgs[1:], quality=quality)
        outbuf.seek(0)
        tmp = save_temp_bytes(outbuf.read(), suffix='.pdf')
        return send_file(tmp, as_attachment=True, download_name=f'images_{int(time.time())}.pdf')
    except Exception as e:
        traceback.print_exc()
        return f"Processing error: {str(e)}", 500

# ---------- Background removal with color replacement ----------
def remove_background_with_color(image_bytes, bg_color='transparent'):
    """Advanced background removal with color replacement"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)
        
        # Try using rembg if available (best quality)
        if REMBG_AVAILABLE:
            img_no_bg = remove(img)
            
            if bg_color == 'transparent':
                out = io.BytesIO()
                img_no_bg.save(out, format='PNG')
                return out.getvalue()
            
            if img_no_bg.mode != 'RGBA':
                img_no_bg = img_no_bg.convert('RGBA')
            
            rgb = hex_to_rgb(bg_color)
            bg_image = Image.new('RGB', img_no_bg.size, rgb)
            bg_image.paste(img_no_bg, (0, 0), img_no_bg)
            
            out = io.BytesIO()
            bg_image.save(out, format='JPEG', quality=95)
            return out.getvalue()
        
        elif OPENCV_AVAILABLE:
            return remove_background_opencv_improved(image_bytes, bg_color)
        
        else:
            return remove_background_simple(image_bytes, bg_color)
            
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"Background removal failed: {str(e)}")

def remove_background_opencv_improved(image_bytes, bg_color='transparent'):
    """Improved OpenCV background removal"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("Could not decode image")
    
    mask = np.zeros(img.shape[:2], np.uint8)
    h, w = img.shape[:2]
    
    margin_h = max(5, int(h * 0.02))
    margin_w = max(5, int(w * 0.02))
    rect = (margin_w, margin_h, w - 2*margin_w, h - 2*margin_h)
    
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    
    try:
        cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    except:
        mask2 = np.ones(img.shape[:2], dtype='uint8')
    
    if bg_color == 'transparent':
        img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        img_rgba[:, :, 3] = mask2 * 255
        pil_img = Image.fromarray(img_rgba)
    else:
        rgb = hex_to_rgb(bg_color)
        bgr = (rgb[2], rgb[1], rgb[0])
        background = np.full(img.shape, bgr, dtype=np.uint8)
        foreground = img * mask2[:, :, np.newaxis]
        background = background * (1 - mask2[:, :, np.newaxis])
        result = foreground + background
        pil_img = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    
    out = io.BytesIO()
    pil_img.save(out, format='PNG' if bg_color == 'transparent' else 'JPEG', quality=95)
    return out.getvalue()

def remove_background_simple(image_bytes, bg_color='transparent'):
    """Simple threshold-based background removal"""
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert('RGBA')
    
    data = img.getdata()
    new_data = []
    
    for px in data:
        r, g, b, a = px
        brightness = (r + g + b) / 3
        if brightness > 230:
            if bg_color == 'transparent':
                new_data.append((255, 255, 255, 0))
            else:
                rgb = hex_to_rgb(bg_color)
                new_data.append(rgb + (255,))
        else:
            new_data.append((r, g, b, a))
    
    img.putdata(new_data)
    
    if bg_color != 'transparent':
        rgb_img = Image.new('RGB', img.size, hex_to_rgb(bg_color))
        rgb_img.paste(img, mask=img.split()[3])
        img = rgb_img
    
    out = io.BytesIO()
    img.save(out, format='PNG' if bg_color == 'transparent' else 'JPEG', quality=95)
    return out.getvalue()

@app.route('/bg_remove', methods=['POST'])
def bg_remove():
    try:
        f = request.files.get('image')
        if not f: 
            return "No file uploaded", 400
        if not allowed_filename(f.filename): 
            return "Unsupported file type", 400
        if not pil_open_validate(f.stream): 
            return "Invalid or corrupted image", 400
        
        bg_color = request.form.get('bg_color', 'transparent')
        f.stream.seek(0)
        data = f.read()
        
        processed = remove_background_with_color(data, bg_color)
        
        tmp = save_temp_bytes(processed, suffix='.png' if bg_color == 'transparent' else '.jpg')
        filename = secure_filename(f.filename)
        base = os.path.splitext(filename)[0]
        ext = 'png' if bg_color == 'transparent' else 'jpg'
        return send_file(tmp, as_attachment=True, download_name=f'{base}_processed.{ext}')
    except Exception as e:
        traceback.print_exc()
        error_msg = str(e)
        if 'rembg' in error_msg.lower():
            error_msg = "AI background removal not available. Please install rembg: pip install rembg"
        return f"Processing error: {error_msg}", 500

# ---------- Run ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("🎨 ImageMaster Pro - Professional Image Tools")
    print("="*60)
    print(f"🚀 Server: http://localhost:{port}")
    print(f"📦 OpenCV: {'✅ Available' if OPENCV_AVAILABLE else '❌ Not installed'}")
    print(f"🤖 rembg (AI): {'✅ Available' if REMBG_AVAILABLE else '❌ Not installed'}")
    if not REMBG_AVAILABLE:
        print("💡 Tip: Install rembg for best background removal:")
        print("   pip install rembg")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=port, debug=True)