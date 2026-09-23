// Dashboard interface updates and manual commands for MangoSmart-Sorter

let wsConnection = null;

function initDashboard(lotCode) {
    console.log("Iniciando Dashboard para lote:", lotCode);

    // Cargar datos y estadísticas iniciales desde la API REST
    loadInitialData(lotCode);

    // Configurar WebSocket
    wsConnection = new MangoWebSocket(
        lotCode, 
        'dashboard',
        handleWebSocketMessage,
        handleServerConnectionStatus
    );
    wsConnection.connect();

    // Configurar escuchadores de botones de control manual
    setupControlButtons(lotCode);

    // Configurar enlace celular y código QR dinámico
    setupCellLinkQR(lotCode);
}

function setupCellLinkQR(lotCode) {
    const input = document.getElementById('input-base-url');
    const saveBtn = document.getElementById('btn-save-url');
    
    // Cargar del localStorage si ya existe
    let storedUrl = localStorage.getItem('mango_base_url');
    
    // Fallback inicial: si no hay URL guardada, sugerir el protocolo y host actual de la barra
    if (!storedUrl) {
        const protocol = window.location.protocol;
        const host = window.location.host;
        storedUrl = `${protocol}//${host}`;
    }

    if (storedUrl) {
        input.value = storedUrl;
        updateQR(lotCode, storedUrl);
    }

    saveBtn.addEventListener('click', function() {
        let value = input.value.trim();
        // Quitar barra diagonal final si el usuario la puso
        if (value.endsWith('/')) {
            value = value.substring(0, value.length - 1);
        }
        if (value) {
            localStorage.setItem('mango_base_url', value);
            updateQR(lotCode, value);
        }
    });
}

function updateQR(lotCode, baseUrl) {
    const qrImg = document.getElementById('qr-image');
    const qrPlaceholder = document.getElementById('qr-placeholder');
    const link = document.getElementById('link-camera-view');

    // Forzar de forma segura https si es un enlace de ngrok para cumplir con las políticas de cámara del navegador móvil
    let secureUrl = baseUrl;
    if (secureUrl.includes('ngrok-free.dev')) {
        if (secureUrl.startsWith('http://')) {
            secureUrl = secureUrl.replace('http://', 'https://');
        } else if (!secureUrl.startsWith('https://')) {
            secureUrl = 'https://' + secureUrl;
        }
    } else {
        // Enlace IP local ordinario, mantener http si no se especifica protocolo
        if (!secureUrl.startsWith('http://') && !secureUrl.startsWith('https://')) {
            secureUrl = 'http://' + secureUrl;
        }
    }

    const cameraUrl = `${secureUrl}/camera/${lotCode}/`;
    
    // Actualizar enlace de texto
    link.href = cameraUrl;
    link.innerText = cameraUrl;

    // Generar código QR usando la API gratuita qrserver.com
    const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(cameraUrl)}`;
    
    qrImg.src = qrApiUrl;
    qrImg.classList.remove('d-none');
    if (qrPlaceholder) {
        qrPlaceholder.classList.add('d-none');
    }
}



function handleServerConnectionStatus(connected) {
    const dot = document.getElementById('conn-server');
    const text = document.getElementById('conn-server-text');
    if (connected) {
        dot.className = "status-dot status-connected";
        text.innerText = "Online";
    } else {
        dot.className = "status-dot status-disconnected";
        text.innerText = "Offline";
    }
}

function handleWebSocketMessage(data) {
    console.log("Mensaje recibido en Dashboard:", data);

    switch(data.type) {
        case 'device_status':
            updateDeviceIndicator(data.device, data.connected);
            break;
            
        case 'classification_result':
            renderClassificationResult(data);
            break;
            
        case 'hardware_status':
            updateGateIndicator(data.command);
            break;
            
        case 'conveyor_status':
            updateConveyorIndicator(data.status);
            break;
    }
}

function updateDeviceIndicator(device, connected) {
    let dotId, textId, deviceName;
    if (device === 'mobile' || device === 'celular') {
        dotId = 'conn-mobile';
        textId = 'conn-mobile-text';
        deviceName = 'Celular';
    } else if (device === 'arduino') {
        dotId = 'conn-arduino';
        textId = 'conn-arduino-text';
        deviceName = 'Arduino';
    } else {
        return;
    }

    const dot = document.getElementById(dotId);
    const text = document.getElementById(textId);
    const alerts = document.getElementById('connection-alerts');

    if (dot && text) {
        if (connected) {
            dot.className = "status-dot status-connected";
            text.innerText = "Online";
            // Quitar alerta si existía
            if (alerts) alerts.classList.add('d-none');
        } else {
            dot.className = "status-dot status-disconnected";
            text.innerText = "Offline";
            // Mostrar banner de alerta
            if (alerts) {
                alerts.className = "alert alert-warning border-0 shadow-sm";
                alerts.innerHTML = `⚠️ <strong>Alerta:</strong> El dispositivo <strong>${deviceName}</strong> se ha desconectado. Verifique la conexión.`;
                alerts.classList.remove('d-none');
            }
        }
    }
}

function renderClassificationResult(data) {
    // 1. Actualizar contadores
    document.getElementById('count-mature').innerText = data.total_mature;
    document.getElementById('count-immature').innerText = data.total_immature;
    document.getElementById('count-review').innerText = data.total_review;
    document.getElementById('count-total').innerText = data.total_processed;

    // 2. Actualizar el panel central de último mango
    const img = document.getElementById('last-image');
    const placeholder = document.getElementById('image-placeholder');
    
    if (img && placeholder) {
        img.src = data.image_url;
        img.classList.remove('d-none');
        placeholder.classList.add('d-none');
    }

    document.getElementById('inference-seq').innerText = `#${data.sequence}`;
    
    const badge = document.getElementById('inference-class');
    badge.innerText = data.class_name;
    badge.className = `badge float-end ${data.class_name === 'MADURO' ? 'mango-badge-mature' : (data.class_name === 'INMADURO' ? 'mango-badge-immature' : 'mango-badge-review')}`;
    
    document.getElementById('inference-conf').innerText = `${(data.confidence * 100).toFixed(1)}%`;

    // Actualizar barra de probabilidad de madurez
    const matureProbPercent = (data.probabilities.Maduro * 100).toFixed(0);
    const bar = document.getElementById('prob-bar-mature');
    bar.style.width = `${matureProbPercent}%`;
    bar.setAttribute('aria-valuenow', matureProbPercent);

    // Actualizar latencias
    document.getElementById('time-preprocess').innerText = `${data.preprocess_ms} ms`;
    document.getElementById('time-inference').innerText = `${data.inference_ms} ms`;
    document.getElementById('time-total').innerText = `${data.total_ms} ms`;

    // 3. Insertar fila en la tabla de clasificaciones recientes
    const tbody = document.getElementById('history-table-body');
    // Quitar placeholder de "No hay clasificaciones" si está presente
    if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
        tbody.innerHTML = '';
    }

    const row = document.createElement('tr');
    
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    
    const classBadge = `<span class="badge ${data.class_name === 'MADURO' ? 'mango-badge-mature' : (data.class_name === 'INMADURO' ? 'mango-badge-immature' : 'mango-badge-review')}">${data.class_name}</span>`;
    
    row.innerHTML = `
        <td><strong>#${data.sequence}</strong></td>
        <td>${timeStr}</td>
        <td>${classBadge}</td>
        <td>${(data.confidence * 100).toFixed(1)}%</td>
        <td>${(data.probabilities.Maduro * 100).toFixed(1)}%</td>
        <td>${data.inference_ms} ms</td>
        <td><span class="badge bg-success">Completado</span></td>
    `;
    
    tbody.insertBefore(row, tbody.firstChild);

    // Limitar filas a 5
    if (tbody.children.length > 5) {
        tbody.removeChild(tbody.lastChild);
    }
}

function updateGateIndicator(command) {
    const badge = document.getElementById('status-gate');
    if (command.startsWith("SORT:")) {
        badge.innerText = command.split(":")[1];
        badge.className = "badge bg-warning text-dark float-end";
        // Regresa a NEUTRAL después del tiempo de espera simulado
        setTimeout(() => {
            badge.innerText = "NEUTRAL";
            badge.className = "badge bg-secondary float-end";
        }, 2000);
    }
}

function updateConveyorIndicator(status) {
    const badge = document.getElementById('status-conveyor');
    const pauseBtn = document.getElementById('btn-pause');
    const resumeBtn = document.getElementById('btn-resume');

    if (status === 'ACTIVE') {
        badge.innerText = "Activa";
        badge.className = "badge bg-success float-end";
        pauseBtn.classList.remove('d-none');
        resumeBtn.classList.add('d-none');
    } else {
        badge.innerText = "Detenida";
        badge.className = "badge bg-danger float-end";
        pauseBtn.classList.add('d-none');
        resumeBtn.classList.remove('d-none');
    }
}

function setupControlButtons(lotCode) {
    // Solicitud de captura manual
    document.getElementById('btn-manual-capture').addEventListener('click', function() {
        if (wsConnection) {
            wsConnection.send({ action: 'request_manual_capture' });
        }
    });

    // Test de ángulos de servomotor
    document.getElementById('btn-servo-mature').addEventListener('click', function() {
        sendServoTest('mature');
    });
    document.getElementById('btn-servo-immature').addEventListener('click', function() {
        sendServoTest('immature');
    });
    document.getElementById('btn-servo-neutral').addEventListener('click', function() {
        sendServoTest('neutral');
    });

    // Control de cinta
    document.getElementById('btn-pause').addEventListener('click', function() {
        if (wsConnection) wsConnection.send({ action: 'pause_conveyor' });
    });
    document.getElementById('btn-resume').addEventListener('click', function() {
        if (wsConnection) wsConnection.send({ action: 'resume_conveyor' });
    });

    // Botón de emergencia
    document.getElementById('btn-emergency').addEventListener('click', function() {
        if (wsConnection) {
            wsConnection.send({ action: 'pause_conveyor' });
            alert("🚨 PARADA DE EMERGENCIA ACTIVA. La cinta transportadora ha sido detenida.");
        }
    });
}

function sendServoTest(target) {
    // Usar API REST para comando manual
    fetch('/api/hardware/test-command/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            action: 'test_servo',
            target: target
        })
    })
    .then(res => res.json())
    .then(data => {
        console.log(`Prueba de servo ${target} enviada. Evento ID:`, data.event_id);
    })
    .catch(err => {
        console.error("Error al testear servomotor:", err);
    });
}

function loadInitialData(lotCode) {
    // Obtener estadísticas iniciales
    fetch(`/api/lots/${lotCode}/statistics/`)
    .then(res => res.json())
    .then(data => {
        document.getElementById('count-mature').innerText = data.total_mature;
        document.getElementById('count-immature').innerText = data.total_immature;
        document.getElementById('count-review').innerText = data.total_review;
        document.getElementById('count-total').innerText = data.total_processed;
    })
    .catch(err => console.error("Error cargando estadísticas iniciales:", err));

    // Obtener clasificaciones iniciales para rellenar la tabla
    fetch(`/api/lots/${lotCode}/`)
    .then(res => res.json())
    .then(data => {
        const tbody = document.getElementById('history-table-body');
        if (data.clasificaciones_recientes && data.clasificaciones_recientes.length > 0) {
            tbody.innerHTML = '';
            
            // Mostrar últimos 5
            data.clasificaciones_recientes.slice(0, 5).forEach(item => {
                const row = document.createElement('tr');
                const timeStr = new Date(item.fecha_hora).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
                const classBadge = `<span class="badge ${item.clase_predicha === 'MADURO' ? 'mango-badge-mature' : (item.clase_predicha === 'INMADURO' ? 'mango-badge-immature' : 'mango-badge-review')}">${item.clase_predicha}</span>`;
                
                row.innerHTML = `
                    <td><strong>#${item.secuencia}</strong></td>
                    <td>${timeStr}</td>
                    <td>${classBadge}</td>
                    <td>${(item.confianza * 100).toFixed(1)}%</td>
                    <td>${(item.probabilidad_maduro * 100).toFixed(1)}%</td>
                    <td>${item.tiempo_inferencia_ms.toFixed(0)} ms</td>
                    <td><span class="badge bg-success">Completado</span></td>
                `;
                tbody.appendChild(row);
            });
            
            // Rellenar panel de último mango con el más reciente
            const last = data.clasificaciones_recientes[0];
            if (last.imagen_original) {
                const img = document.getElementById('last-image');
                const placeholder = document.getElementById('image-placeholder');
                img.src = last.imagen_original;
                img.classList.remove('d-none');
                placeholder.classList.add('d-none');
                
                document.getElementById('inference-seq').innerText = `#${last.secuencia}`;
                const badge = document.getElementById('inference-class');
                badge.innerText = last.clase_predicha;
                badge.className = `badge float-end ${last.clase_predicha === 'MADURO' ? 'mango-badge-mature' : (last.clase_predicha === 'INMADURO' ? 'mango-badge-immature' : 'mango-badge-review')}`;
                document.getElementById('inference-conf').innerText = `${(last.confianza * 100).toFixed(1)}%`;
                
                const matureProbPercent = (last.probabilidad_maduro * 100).toFixed(0);
                const bar = document.getElementById('prob-bar-mature');
                bar.style.width = `${matureProbPercent}%`;
                bar.setAttribute('aria-valuenow', matureProbPercent);
                
                document.getElementById('time-preprocess').innerText = `${last.tiempo_preprocesamiento_ms.toFixed(1)} ms`;
                document.getElementById('time-inference').innerText = `${last.tiempo_inferencia_ms.toFixed(1)} ms`;
                document.getElementById('time-total').innerText = `${last.latencia_total_ms.toFixed(1)} ms`;
            }
        }
    })
    .catch(err => console.error("Error cargando clasificaciones recientes:", err));
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
