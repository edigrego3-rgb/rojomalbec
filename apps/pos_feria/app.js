let catalogo = typeof catalogo_data !== "undefined" ? catalogo_data : [];
let carrito = [];
let html5QrcodeScanner = null;
let currentEditId = null;
let comboSeleccionados = [];

// INICIALIZACIÓN
document.addEventListener("DOMContentLoaded", () => {
    renderCatalogo();
    renderCarrito();
    configNavigation();
});

// NAVEGACIÓN BOTTOM BAR
function configNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const views = document.querySelectorAll(".view");
    navItems.forEach(btn => {
        btn.addEventListener("click", () => {
            navItems.forEach(b => b.classList.remove("active"));
            views.forEach(v => v.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(btn.getAttribute("data-target")).classList.add("active");
        });
    });
}

// CATÁLOGO
function renderCatalogo() {
    const list = document.getElementById("catalogo-list");
    list.innerHTML = "";
    catalogo.forEach(p => {
        const div = document.createElement("div");
        div.className = "cart-card";
        div.innerHTML = `
            <div class="cart-card-info">
                <div class="cart-card-title">${p.Nombre}</div>
                <div style="color:#aaa; font-size:0.9rem;">$ ${p.Precio_Venta}</div>
            </div>
            <button class="action-btn outline" style="padding:8px; flex:none; width:80px;" onclick="addFromCatalog('${p.Codigo}')">Vender</button>
        `;
        list.appendChild(div);
    });
}

function addFromCatalog(codigo) {
    const p = catalogo.find(x => x.Codigo === codigo);
    if(p) {
        agregarAlCarrito(p);
        document.querySelector('[data-target="view-vender"]').click(); // Ir a vender
    }
}

document.getElementById('btn-manual').addEventListener('click', () => {
    document.querySelector('[data-target="view-catalogo"]').click();
});

// CARRITO
function agregarAlCarrito(prod, isCombo = false, comboItems = []) {
    // Si ya existe y no es combo, sumar cantidad
    let existente = carrito.find(x => x.codigo === prod.Codigo && !x.esCombo);
    if(existente && !isCombo) {
        existente.cantidad += 1;
    } else {
        carrito.push({
            id: Date.now() + Math.random(),
            codigo: prod.Codigo || "COMBO",
            nombre: prod.Nombre,
            costoUnitario: parseFloat(prod.Precio_Mayorista),
            precioFinal: parseFloat(prod.Precio_Venta),
            cantidad: 1,
            esCombo: isCombo,
            comboItems: comboItems
        });
    }
    renderCarrito();
}

function cambiarCantidad(id, delta) {
    let item = carrito.find(x => x.id === id);
    if(item) {
        item.cantidad += delta;
        if(item.cantidad <= 0) {
            carrito = carrito.filter(x => x.id !== id);
        }
        renderCarrito();
    }
}

function renderCarrito() {
    const list = document.getElementById("cart-list");
    const empty = document.getElementById("empty-cart");
    list.innerHTML = "";
    
    if(carrito.length === 0) {
        empty.style.display = "block";
    } else {
        empty.style.display = "none";
        carrito.forEach(item => {
            const card = document.createElement("li");
            card.className = "cart-card";
            
            let extra = item.esCombo ? `<div style="font-size:0.75rem; color:#aaa;">${item.comboItems.join(", ")}</div>` : '';
            
            card.innerHTML = `
                <div class="cart-card-info">
                    <div class="cart-card-title">${item.nombre}</div>
                    ${extra}
                    <div class="cart-card-price" onclick="abrirModalPrecio(${item.id})">$ ${item.precioFinal}</div>
                </div>
                <div class="cart-card-qty">
                    <button class="qty-btn" onclick="cambiarCantidad(${item.id}, -1)">-</button>
                    <span style="font-size:1.2rem; font-weight:bold;">${item.cantidad}</span>
                    <button class="qty-btn" onclick="cambiarCantidad(${item.id}, 1)">+</button>
                </div>
            `;
            list.appendChild(card);
        });
    }
    calcularTotal();
}

function calcularTotal() {
    let total = carrito.reduce((sum, item) => sum + (item.precioFinal * item.cantidad), 0);
    document.getElementById("tot-vendido").innerText = "$ " + total.toLocaleString();
}

// MODAL PRECIO (DESCUENTOS)
function abrirModalPrecio(id) {
    const item = carrito.find(x => x.id === id);
    if(!item) return;
    currentEditId = id;
    document.getElementById("modal-prod-name").innerText = item.nombre;
    document.getElementById("input-nuevo-precio").value = item.precioFinal;
    document.getElementById("modal-precio").style.display = "flex";
}
document.getElementById("btn-cancel-precio").addEventListener("click", () => document.getElementById("modal-precio").style.display = "none");
document.getElementById("btn-save-precio").addEventListener("click", () => {
    let item = carrito.find(x => x.id === currentEditId);
    let nPrecio = parseFloat(document.getElementById("input-nuevo-precio").value);
    if(item && !isNaN(nPrecio)) {
        item.precioFinal = nPrecio;
        renderCarrito();
    }
    document.getElementById("modal-precio").style.display = "none";
});

// ARMADOR DE COMBOS INTELIGENTE
document.getElementById("btn-crear-combo").addEventListener("click", () => {
    comboSeleccionados = [];
    renderComboList();
    actualizarCifrasCombo();
    document.getElementById("combo-precio-final").value = "";
    document.getElementById("modal-combo").style.display = "flex";
});
document.getElementById("btn-cancel-combo").addEventListener("click", () => document.getElementById("modal-combo").style.display = "none");

function renderComboList() {
    const clist = document.getElementById("combo-catalog-list");
    clist.innerHTML = "";
    catalogo.forEach(p => {
        let cnt = comboSeleccionados.filter(x => x.Codigo === p.Codigo).length;
        let cdiv = document.createElement("div");
        cdiv.className = "combo-sel-item";
        cdiv.innerHTML = `
            <span>${p.Nombre} ${cnt > 0 ? '<strong style="color:#d4af37;">(x'+cnt+')</strong>' : ''}</span>
            <button class="combo-sel-btn" onclick="addToCombo('${p.Codigo}')">Sumar</button>
        `;
        clist.appendChild(cdiv);
    });
}
window.addToCombo = function(codigo) { // global for onclick
    const p = catalogo.find(x => x.Codigo === codigo);
    if(p) {
        comboSeleccionados.push(p);
        renderComboList();
        actualizarCifrasCombo();
    }
};

function actualizarCifrasCombo() {
    let tCosto = comboSeleccionados.reduce((s, p) => s + parseFloat(p.Precio_Mayorista), 0);
    let tNormal = comboSeleccionados.reduce((s, p) => s + parseFloat(p.Precio_Venta), 0);
    document.getElementById("combo-costo").innerText = tCosto.toLocaleString();
    document.getElementById("combo-normal").innerText = tNormal.toLocaleString();
    
    // Auto-llenar sugerencia
    if(document.getElementById("combo-precio-final").value === "" || document.getElementById("combo-precio-final").value === "0") {
        document.getElementById("combo-precio-final").value = tNormal;
    }
}

document.getElementById("btn-save-combo").addEventListener("click", () => {
    if(comboSeleccionados.length === 0) return alert("Elegí al menos un producto");
    let pFinal = parseFloat(document.getElementById("combo-precio-final").value);
    if(isNaN(pFinal)) return alert("Poné un precio válido");
    
    let tCosto = comboSeleccionados.reduce((s, p) => s + parseFloat(p.Precio_Mayorista), 0);
    let nombres = comboSeleccionados.map(p => p.Nombre);
    
    let prodVirtual = {
        Nombre: "🎁 Combo Armado",
        Precio_Mayorista: tCosto,
        Precio_Venta: pFinal
    };
    agregarAlCarrito(prodVirtual, true, nombres);
    document.getElementById("modal-combo").style.display = "none";
});

// ESCANER FAB
document.getElementById("fab-scan").addEventListener("click", () => {
    const readerDiv = document.getElementById("reader");
    if(readerDiv.style.display === "block") {
        readerDiv.style.display = "none";
        if(html5QrcodeScanner) { html5QrcodeScanner.clear(); html5QrcodeScanner = null; }
        return;
    }
    
    readerDiv.style.display = "block";
    html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: {width: 250, height: 250} }, false);
    html5QrcodeScanner.render(
        (text) => {
            const p = catalogo.find(x => x.Codigo === text);
            if(p) {
                agregarAlCarrito(p);
                alert("Agregado: " + p.Nombre);
            } else {
                alert("Código no reconocido: " + text);
            }
        }, 
        (err) => {}
    );
});

// CIERRE DE CAJA TICKET
document.getElementById("btn-calcular-cierre").addEventListener("click", () => {
    if(carrito.length === 0) return alert("No hay ventas hoy.");
    
    const isSocio = document.getElementById("chk-socio").checked;
    const gEdu = parseFloat(document.getElementById("gastos-edu").value) || 0;
    const gAlb = parseFloat(document.getElementById("gastos-alb").value) || 0;
    
    let tVentas = 0;
    let tCostos = 0;
    
    // Agrupar para ticket
    let resumenStock = {};
    
    carrito.forEach(i => {
        let q = i.cantidad;
        tVentas += (i.precioFinal * q);
        tCostos += (i.costoUnitario * q);
        
        if(i.esCombo) {
            i.comboItems.forEach(ci => {
                resumenStock[ci] = (resumenStock[ci] || 0) + q;
            });
        } else {
            resumenStock[i.nombre] = (resumenStock[i.nombre] || 0) + q;
        }
    });
    
    let neta = tVentas - tCostos - gEdu - gAlb;
    if(neta < 0) neta = 0;
    
    let eduFinal = isSocio ? (tCostos + gEdu + (neta/2)) : tVentas;
    let albFinal = isSocio ? (gAlb + (neta/2)) : 0;
    
    document.getElementById("rep-caja").innerText = "$ " + tVentas.toLocaleString();
    document.getElementById("rep-costos").innerText = "$ " + tCostos.toLocaleString();
    document.getElementById("rep-gastos").innerText = "$ " + (gEdu + gAlb).toLocaleString();
    document.getElementById("rep-neta").innerText = "$ " + neta.toLocaleString();
    
    document.getElementById("rep-edu").innerText = "$ " + eduFinal.toLocaleString();
    
    if(isSocio) {
        document.getElementById("rep-socio-box").style.display = "flex";
        document.getElementById("rep-alb").innerText = "$ " + albFinal.toLocaleString();
    } else {
        document.getElementById("rep-socio-box").style.display = "none";
    }
    
    // Lista stock
    const ulStock = document.getElementById("lista-vendidos");
    ulStock.innerHTML = "";
    for(const [nombre, cant] of Object.entries(resumenStock)) {
        ulStock.innerHTML += `<li><span>${nombre}</span> <strong>x${cant}</strong></li>`;
    }
    
    document.getElementById("reporte-final").style.display = "block";
});

// WHATSAPP
document.getElementById("btn-whatsapp").addEventListener("click", () => {
    let tVentas = document.getElementById("rep-caja").innerText;
    let tEdu = document.getElementById("rep-edu").innerText;
    let tAlb = document.getElementById("rep-alb").innerText;
    let isSocio = document.getElementById("chk-socio").checked;
    
    let msj = `*CIERRE FERIA ROJO MALBEC* %0A`;
    msj += `Recaudación: ${tVentas}%0A`;
    msj += `Eduardo: ${tEdu}%0A`;
    if(isSocio) msj += `Acompañante: ${tAlb}%0A%0A`;
    
    msj += `*Unidades Vendidas:*%0A`;
    const lis = document.querySelectorAll("#lista-vendidos li");
    lis.forEach(li => {
        msj += `- ${li.innerText.replace('\n', ' ')}%0A`;
    });
    
    window.open(`https://wa.me/?text=${msj}`, '_blank');
});

document.getElementById("btn-nuevo-dia").addEventListener("click", () => {
    if(confirm("¿Seguro querés vaciar todo y arrancar de cero?")) {
        carrito = [];
        renderCarrito();
        document.getElementById("reporte-final").style.display = "none";
        document.getElementById("gastos-edu").value = "0";
        document.getElementById("gastos-alb").value = "0";
        document.querySelector('[data-target="view-vender"]').click();
    }
});