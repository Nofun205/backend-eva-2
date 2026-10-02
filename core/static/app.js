const API_URL = 'http://localhost:8000/api';

// Estado de la app
let token = localStorage.getItem('access_token');
let username = localStorage.getItem('username');

document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();
    loadCourses();
    if(token) loadCart();
});

// UI Functions
function toggleCart() {
    if(!token) {
        openLoginModal();
        return;
    }
    document.getElementById('cart-sidebar').classList.toggle('open');
    document.getElementById('overlay').classList.toggle('show');
}

function openLoginModal() {
    document.getElementById('login-modal').classList.add('show');
}

function closeLoginModal() {
    document.getElementById('login-modal').classList.remove('show');
}

function updateAuthUI() {
    const authSection = document.getElementById('auth-section');
    if (token) {
        authSection.innerHTML = `
            <button class="logout-btn" style="background: var(--surface); color: var(--primary); border: 1px solid var(--primary);" onclick="openMisCursosModal()">Mis Cursos</button>
            <span class="user-greeting" style="margin-left:10px;">Hola, ${username}</span>
            <button class="logout-btn" onclick="logout()">Salir</button>
        `;
    } else {
        authSection.innerHTML = `
            <button class="login-btn" onclick="openLoginModal()">Iniciar Sesión</button>
        `;
        document.getElementById('cart-count').innerText = '0';
    }
}

// API Calls
async function login(e) {
    e.preventDefault();
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const errorEl = document.getElementById('login-error');
    
    try {
        const res = await fetch(`${API_URL}/auth/login/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: user, password: pass})
        });
        
        if (!res.ok) throw new Error('Credenciales incorrectas');
        
        const data = await res.json();
        token = data.access;
        // Parsear JWT para sacar el nombre
        const payload = JSON.parse(atob(token.split('.')[1]));
        username = payload.username;
        
        localStorage.setItem('access_token', token);
        localStorage.setItem('username', username);
        
        closeLoginModal();
        updateAuthUI();
        loadCart();
    } catch (err) {
        errorEl.innerText = err.message;
    }
}

document.getElementById('login-form').addEventListener('submit', login);

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    token = null;
    username = null;
    updateAuthUI();
    document.getElementById('cart-sidebar').classList.remove('open');
    document.getElementById('overlay').classList.remove('show');
}

async function loadCourses(query = '') {
    try {
        const url = query ? `${API_URL}/cursos/?search=${encodeURIComponent(query)}` : `${API_URL}/cursos/`;
        const res = await fetch(url);
        const courses = await res.json();
        const grid = document.getElementById('course-grid');
        
        if(courses.length === 0) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center;">No hay cursos disponibles por el momento.</p>';
            return;
        }

        grid.innerHTML = courses.map(course => `
            <div class="course-card">
                <div class="card-img"></div>
                <div class="card-content">
                    <p class="card-area">${course.area_nombre || 'Tecnología'}</p>
                    <h4 class="card-title">${course.titulo}</h4>
                    <p class="card-desc">${course.descripcion}</p>
                    <div class="card-footer">
                        <span class="price">$${course.costo_matricula}</span>
                        <button class="add-cart-btn" onclick="addToCart(${course.id})">Agregar</button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error(err);
        document.getElementById('course-grid').innerHTML = '<p>Error al cargar el catálogo.</p>';
    }
}

async function loadCart() {
    if(!token) return;
    try {
        const res = await fetch(`${API_URL}/carro-matricula/`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        const cartData = await res.json();
        
        const cart = Array.isArray(cartData) ? cartData[0] : cartData;
        if(!cart) return;

        document.getElementById('cart-count').innerText = cart.items ? cart.items.length : 0;
        document.getElementById('cart-total-price').innerText = `$${cart.total_a_pagar || '0.00'}`;
        
        const itemsContainer = document.getElementById('cart-items');
        if(!cart.items || cart.items.length === 0) {
            itemsContainer.innerHTML = '<p>Tu carrito está vacío.</p>';
            return;
        }

        itemsContainer.innerHTML = cart.items.map(item => `
            <div class="cart-item">
                <div class="item-info">
                    <h4>${item.curso_titulo}</h4>
                    <p>$${item.costo}</p>
                </div>
                <button class="remove-item" onclick="removeFromCart(${item.curso})"><i class="ri-delete-bin-line"></i></button>
            </div>
        `).join('');
        
    } catch (err) {
        console.error(err);
    }
}

async function addToCart(cursoId) {
    if(!token) {
        openLoginModal();
        return;
    }
    
    try {
        const res = await fetch(`${API_URL}/carro-matricula/agregar_curso/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({curso_id: cursoId})
        });
        
        const data = await res.json();
        if(!res.ok) {
            alert(data.error || 'Error al agregar');
            return;
        }
        
        loadCart();
        toggleCart();
    } catch (err) {
        console.error(err);
    }
}

async function emptyCart() {
    try {
        await fetch(`${API_URL}/carro-matricula/vaciar/`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${token}`}
        });
        loadCart();
    } catch(err) {}
}

async function removeFromCart(cursoId) {
    if(!token) return;
    try {
        await fetch(`${API_URL}/carro-matricula/remover_curso/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({curso_id: cursoId})
        });
        loadCart();
    } catch(err) {
        console.error(err);
    }
}

async function checkout() {
    if(!token) return;
    
    try {
        const res = await fetch(`${API_URL}/matriculas/confirmar/`, {
            method: 'POST',
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        const data = await res.json();
        if(!res.ok) {
            alert(data.error || 'Error en el checkout');
            return;
        }
        
        alert('¡Pago exitoso! Bienvenido al curso.');
        loadCart();
        toggleCart();
    } catch(err) {
        console.error(err);
    }
}

// Funcionalidad de Búsqueda y Explorar
document.getElementById('search-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        loadCourses(e.target.value);
        document.getElementById('course-grid').scrollIntoView({ behavior: 'smooth' });
    }
});

document.getElementById('explore-btn').addEventListener('click', () => {
    document.getElementById('search-input').value = '';
    loadCourses();
    document.getElementById('course-grid').scrollIntoView({ behavior: 'smooth' });
});

// Mis Cursos Logic
function openMisCursosModal() {
    document.getElementById('mis-cursos-modal').classList.add('show');
    loadMisCursos();
}

function closeMisCursosModal() {
    document.getElementById('mis-cursos-modal').classList.remove('show');
}

async function loadMisCursos() {
    const list = document.getElementById('mis-cursos-list');
    list.innerHTML = '<p>Cargando tus órdenes...</p>';
    if (!token) return;
    try {
        const res = await fetch(`${API_URL}/mis-matriculas/`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        const matriculas = await res.json();
        if (matriculas.length === 0) {
            list.innerHTML = '<p>No tienes cursos registrados. ¡Explora el catálogo y agrega algunos!</p>';
            return;
        }
        let html = '';
        matriculas.forEach(m => {
            html += `<div style="border:1px solid #eee; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; background: #fafafa;">`;
            html += `<h4 style="margin-bottom:0.5rem; color: #333;">Orden #${m.id} - <span style="color: ${m.estado === 'PAGADO' ? 'green' : 'red'};">${m.estado}</span></h4>`;
            html += `<p style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">Fecha: ${new Date(m.fecha_creacion).toLocaleDateString()}</p>`;
            html += `<ul style="margin-top:0.5rem; padding-left: 1.2rem; color: #555;">`;
            m.detalles.forEach(d => {
                html += `<li>${d.curso_titulo} (Pagado: $${d.precio_congelado})</li>`;
            });
            html += `</ul></div>`;
        });
        list.innerHTML = html;
    } catch(err) {
        list.innerHTML = `<p style="color:red;">Ocurrió un error al cargar tus cursos.</p>`;
    }
}
