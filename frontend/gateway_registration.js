/**
 * Gateway Registration - JavaScript
 */

// Global variables
let currentFloor = 5;
let selectedPosition = null;
let floorPlanImages = {};
let gateways = [];

// Canvas
const canvas = document.getElementById('mapCanvas');
const ctx = canvas.getContext('2d');

// Map dimensions (เมตร)
const MAP_WIDTH = 80;  // 80 เมตร
const MAP_HEIGHT = 60; // 60 เมตร

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeFloorButtons();
    loadFloorPlans();
    loadGateways();
    setupCanvasEvents();
    setupFormEvents();
    updateStats();
});

// ==================== Floor Selection ====================

function initializeFloorButtons() {
    const floorButtons = document.querySelectorAll('.floor-btn');
    
    floorButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            floorButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update current floor
            currentFloor = parseInt(btn.dataset.floor);
            document.getElementById('floor').value = currentFloor;
            
            // Reload data
            drawMap();
            loadGateways();
        });
    });
}

// ==================== Floor Plan Loading ====================

function loadFloorPlans() {
    for (let i = 1; i <= 5; i++) {
        const img = new Image();
        img.onload = () => {
            floorPlanImages[i] = img;
            if (i === currentFloor) {
                drawMap();
            }
        };
        img.onerror = () => {
            console.warn(`Failed to load floor${i}.png`);
        };
        img.src = `images/floor${i}.png`;
    }
}

// ==================== Canvas Drawing ====================

function drawMap() {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw floor plan image
    const img = floorPlanImages[currentFloor];
    if (img) {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        // Draw semi-transparent overlay
        ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    } else {
        // Draw grid if no image
        drawGrid();
    }
    
    // Draw gateways
    drawGateways();
    
    // Draw selected position
    if (selectedPosition) {
        drawSelectedPosition();
    }
}

function drawGrid() {
    ctx.strokeStyle = '#ddd';
    ctx.lineWidth = 1;
    
    // Vertical lines (every 10 meters)
    for (let x = 0; x <= MAP_WIDTH; x += 10) {
        const canvasX = (x / MAP_WIDTH) * canvas.width;
        ctx.beginPath();
        ctx.moveTo(canvasX, 0);
        ctx.lineTo(canvasX, canvas.height);
        ctx.stroke();
    }
    
    // Horizontal lines (every 10 meters)
    for (let y = 0; y <= MAP_HEIGHT; y += 10) {
        const canvasY = (y / MAP_HEIGHT) * canvas.height;
        ctx.beginPath();
        ctx.moveTo(0, canvasY);
        ctx.lineTo(canvas.width, canvasY);
        ctx.stroke();
    }
}

function drawGateways() {
    const floorGateways = gateways.filter(gw => gw.floor === currentFloor);
    
    floorGateways.forEach(gw => {
        const canvasX = (gw.x / MAP_WIDTH) * canvas.width;
        const canvasY = (gw.y / MAP_HEIGHT) * canvas.height;
        
        // Draw gateway marker
        ctx.fillStyle = '#667eea';
        ctx.beginPath();
        ctx.arc(canvasX, canvasY, 8, 0, 2 * Math.PI);
        ctx.fill();
        
        // Draw border
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw label
        ctx.fillStyle = '#333';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(gw.name || gw.mac_address.slice(-8), canvasX, canvasY - 12);
    });
}

function drawSelectedPosition() {
    const canvasX = (selectedPosition.x / MAP_WIDTH) * canvas.width;
    const canvasY = (selectedPosition.y / MAP_HEIGHT) * canvas.height;
    
    // Draw crosshair
    ctx.strokeStyle = '#e74c3c';
    ctx.lineWidth = 2;
    
    // Horizontal line
    ctx.beginPath();
    ctx.moveTo(canvasX - 20, canvasY);
    ctx.lineTo(canvasX + 20, canvasY);
    ctx.stroke();
    
    // Vertical line
    ctx.beginPath();
    ctx.moveTo(canvasX, canvasY - 20);
    ctx.lineTo(canvasX, canvasY + 20);
    ctx.stroke();
    
    // Draw circle
    ctx.beginPath();
    ctx.arc(canvasX, canvasY, 10, 0, 2 * Math.PI);
    ctx.stroke();
}

// ==================== Canvas Events ====================

function setupCanvasEvents() {
    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;
        
        // Convert to map coordinates
        const x = (canvasX / canvas.width) * MAP_WIDTH;
        const y = (canvasY / canvas.height) * MAP_HEIGHT;
        
        // Update selected position
        selectedPosition = { x: x.toFixed(1), y: y.toFixed(1) };
        
        // Update form
        document.getElementById('xCoord').value = selectedPosition.x;
        document.getElementById('yCoord').value = selectedPosition.y;
        
        // Redraw
        drawMap();
    });
    
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;
        
        // Convert to map coordinates
        const x = (canvasX / canvas.width) * MAP_WIDTH;
        const y = (canvasY / canvas.height) * MAP_HEIGHT;
        
        // Update coordinates display
        document.getElementById('coordsDisplay').textContent = 
            `X: ${x.toFixed(1)}, Y: ${y.toFixed(1)}`;
    });
}

// ==================== Form Events ====================

function setupFormEvents() {
    const form = document.getElementById('gatewayForm');
    const clearBtn = document.getElementById('clearBtn');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveGateway();
    });
    
    clearBtn.addEventListener('click', () => {
        form.reset();
        selectedPosition = null;
        document.getElementById('floor').value = currentFloor;
        drawMap();
    });
}

// ==================== API Calls ====================

async function loadGateways() {
    try {
        const response = await fetch(`/api/gateways?floor=${currentFloor}`);
        const data = await response.json();
        
        if (data.success) {
            gateways = data.gateways;
            updateGatewayList();
            updateStats();
            drawMap();
        }
    } catch (error) {
        console.error('Error loading gateways:', error);
        showMessage('เกิดข้อผิดพลาดในการโหลดข้อมูล Gateway', 'error');
    }
}

async function saveGateway() {
    const macAddress = document.getElementById('macAddress').value.trim();
    const floor = parseInt(document.getElementById('floor').value);
    const x = parseFloat(document.getElementById('xCoord').value);
    const y = parseFloat(document.getElementById('yCoord').value);
    const name = document.getElementById('gatewayName').value.trim();
    const description = document.getElementById('gatewayDescription').value.trim();
    
    if (!macAddress) {
        showMessage('กรุณาระบุ MAC Address', 'error');
        return;
    }
    
    if (!selectedPosition) {
        showMessage('กรุณาคลิกบนแผนที่เพื่อเลือกตำแหน่ง', 'error');
        return;
    }
    
    try {
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ กำลังบันทึก...';
        
        const response = await fetch('/api/gateways', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mac_address: macAddress,
                floor: floor,
                x: x,
                y: y,
                name: name || null,
                description: description || null
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('✅ บันทึก Gateway สำเร็จ!', 'success');
            
            // Clear form
            document.getElementById('gatewayForm').reset();
            selectedPosition = null;
            document.getElementById('floor').value = currentFloor;
            
            // Reload data
            await loadGateways();
        } else {
            showMessage(`❌ ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error saving gateway:', error);
        showMessage('เกิดข้อผิดพลาดในการบันทึก', 'error');
    } finally {
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = false;
        submitBtn.textContent = '💾 บันทึก Gateway';
    }
}

async function deleteGateway(macAddress) {
    if (!confirm(`ต้องการลบ Gateway ${macAddress} หรือไม่?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/gateways/${macAddress}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('✅ ลบ Gateway สำเร็จ!', 'success');
            await loadGateways();
        } else {
            showMessage(`❌ ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error deleting gateway:', error);
        showMessage('เกิดข้อผิดพลาดในการลบ', 'error');
    }
}

async function updateStats() {
    try {
        const response = await fetch('/api/gateways/count');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalGateways').textContent = data.count;
        }
        
        // Update floor gateways count
        const floorGateways = gateways.filter(gw => gw.floor === currentFloor);
        document.getElementById('floorGateways').textContent = floorGateways.length;
        
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// ==================== UI Updates ====================

function updateGatewayList() {
    const container = document.getElementById('gatewayListContainer');
    const floorGateways = gateways.filter(gw => gw.floor === currentFloor);
    
    document.getElementById('gatewayCount').textContent = floorGateways.length;
    
    if (floorGateways.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999;">ยังไม่มี Gateway ในชั้นนี้</p>';
        return;
    }
    
    container.innerHTML = floorGateways.map(gw => `
        <div class="gateway-item">
            <button class="delete-btn" onclick="deleteGateway('${gw.mac_address}')">🗑️ ลบ</button>
            <strong>${gw.name || 'Gateway'}</strong>
            <small>MAC: ${gw.mac_address}</small>
            <small>Position: (${gw.x}, ${gw.y})</small>
            ${gw.description ? `<small>${gw.description}</small>` : ''}
        </div>
    `).join('');
}

function showMessage(message, type) {
    const messageEl = document.getElementById('statusMessage');
    messageEl.textContent = message;
    messageEl.className = `status-message ${type}`;
    messageEl.style.display = 'block';
    
    setTimeout(() => {
        messageEl.style.display = 'none';
    }, 5000);
}

