// Camera and image capture handling for MangoSmart-Sorter

let mediaStream = null;
let isCapturing = false;
let wsConnection = null;

function initCameraStation(lotCode) {
    console.log("Inicializando estación de cámara para lote:", lotCode);
    
    const video = document.getElementById('camera-stream');
    const startBtn = document.getElementById('btn-start-camera');
    const captureBtn = document.getElementById('btn-manual-shot');
    
    startBtn.addEventListener('click', async function() {
        startBtn.disabled = true;
        showAlert('Solicitando acceso a la cámara...', 'info');
        
        // Validación de contexto seguro (HTTPS) para el celular
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showAlert('🔒 Error: Acceso bloqueado por el navegador. Debes ingresar usando obligatoriamente HTTPS (la URL en tu celular debe comenzar estrictamente con "https://" y no con "http://").', 'danger');
            startBtn.disabled = false;
            return;
        }

        try {
            if (mediaStream) {
                stopCamera();
            }
            
            const constraints = {
                video: {
                    facingMode: 'environment', // Usar cámara trasera
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            };
            
            mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = mediaStream;
            
            video.onloadedmetadata = () => {
                video.play();
                captureBtn.disabled = false;
                startBtn.innerText = "🔄 Reiniciar Cámara";
                startBtn.disabled = false;
                showAlert('Cámara iniciada con éxito. Listo para capturas.', 'success');
            };
        } catch (err) {
            console.error('Error al acceder a la cámara:', err);
            let errorMsg = 'No se pudo acceder a la cámara. ';
            if (err.name === 'NotAllowedError') {
                errorMsg += 'Permiso denegado por el usuario.';
            } else if (err.name === 'NotFoundError') {
                errorMsg += 'No se encontró una cámara trasera compatible.';
            } else {
                errorMsg += err.message;
            }
            showAlert(errorMsg, 'danger');
            startBtn.disabled = false;
            captureBtn.disabled = true;
        }
    });

    // Capturar foto manualmente
    captureBtn.addEventListener('click', function() {
        if (!mediaStream || isCapturing) return;
        captureAndUpload(lotCode);
    });

    // Conectar WebSocket para recibir peticiones automáticas de captura
    wsConnection = new MangoWebSocket(
        lotCode,
        'mobile',
        handleWebSocketMessage,
        handleServerConnectionStatus
    );
    wsConnection.connect();
}

function handleServerConnectionStatus(connected) {
    const dot = document.getElementById('conn-server');
    const text = document.getElementById('conn-server-text');
    if (dot && text) {
        if (connected) {
            dot.className = "status-dot status-connected";
            text.innerText = "Online";
        } else {
            dot.className = "status-dot status-disconnected";
            text.innerText = "Offline";
        }
    }
}

function handleWebSocketMessage(data) {
    console.log("Mensaje recibido en Móvil:", data);

    if (data.type === 'capture_request') {
        console.log("Solicitud de captura recibida del servidor. ID:", data.classification_id);
        if (mediaStream && !isCapturing) {
            // Disparar captura automática
            captureAndUpload(data.lot_code, data.classification_id);
        } else {
            console.warn("No se pudo auto-capturar: la cámara no está activa o ya está procesando una captura.");
        }
    }
}

function stopCamera() {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
}

function showAlert(message, type) {
    const alertBox = document.getElementById('camera-alert');
    if (alertBox) {
        alertBox.className = `alert alert-${type}`;
        alertBox.innerText = message;
        alertBox.classList.remove('d-none');
    }
}

/**
 * Captura un fotograma actual del stream de video y lo sube al backend.
 */
function captureAndUpload(lotCode, classificationId = null) {
    const video = document.getElementById('camera-stream');
    const canvas = document.getElementById('photo-canvas');
    const captureBtn = document.getElementById('btn-manual-shot');
    const previewImg = document.getElementById('last-shot-preview');
    const previewPlaceholder = document.getElementById('preview-placeholder');
    const indicator = document.getElementById('capture-indicator');
    
    if (isCapturing) return;
    isCapturing = true;
    
    // Deshabilitar captura para prevenir dobles clics
    captureBtn.disabled = true;
    if (indicator) indicator.classList.remove('d-none');
    showAlert('Capturando imagen...', 'info');

    // Configurar dimensiones de canvas iguales a la resolución del video real
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    
    // Dibujar el fotograma del video en el canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convertir canvas a JPEG Blob
    canvas.toBlob(function(blob) {
        if (!blob) {
            showAlert('Error al procesar la imagen.', 'danger');
            isCapturing = false;
            captureBtn.disabled = false;
            if (indicator) indicator.classList.add('d-none');
            return;
        }

        // Mostrar previsualización local inmediata
        const objectURL = URL.createObjectURL(blob);
        previewImg.src = objectURL;
        previewImg.classList.remove('d-none');
        if (previewPlaceholder) previewPlaceholder.classList.add('d-none');

        // Preparar datos multipart/form-data
        const formData = new FormData();
        formData.append('imagen', blob, 'capture.jpg');
        formData.append('lot_code', lotCode);
        if (classificationId) {
            formData.append('classification_id', classificationId);
        }

        showAlert('Enviando imagen al servidor de clasificación...', 'warning');

        // Enviar al backend vía API Fetch
        fetch('/api/classifications/capture/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(err => { throw err; });
            }
            return res.json();
        })
        .then(data => {
            showAlert('Imagen procesada con éxito por el servidor.', 'success');
            
            // Actualizar UI del último resultado
            const resultClass = document.getElementById('result-class');
            const resultConf = document.getElementById('result-conf');
            
            if (resultClass) {
                resultClass.innerText = data.clase_predicha;
                resultClass.className = `badge ${data.clase_predicha === 'MADURO' ? 'mango-badge-mature' : (data.clase_predicha === 'INMADURO' ? 'mango-badge-immature' : 'mango-badge-review')}`;
            }
            if (resultConf) {
                resultConf.innerText = `${(data.confianza * 100).toFixed(1)}%`;
            }
            
            isCapturing = false;
            captureBtn.disabled = false;
            if (indicator) indicator.classList.add('d-none');
        })
        .catch(err => {
            console.error('Error al subir imagen:', err);
            showAlert('Error al procesar la imagen: ' + (err.error || JSON.stringify(err)), 'danger');
            isCapturing = false;
            captureBtn.disabled = false;
            if (indicator) indicator.classList.add('d-none');
        });

    }, 'image/jpeg', 0.85);
}

// Helper para obtener cookies (CSRF Token)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
