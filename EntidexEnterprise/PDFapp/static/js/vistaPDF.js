document.querySelector('#pdfModal_edit #editarPDF').addEventListener('click', function () {
    const form = document.getElementById('pdfForm');
    const formData = new FormData();

    const pdfId = document.getElementById('pdf_id_edit').value;
    formData.append('pdf_id', pdfId);
    formData.append('numero_caso', document.getElementById('Numerodecaso_edit').value);
    formData.append('titulo', document.getElementById('titulo_edit').value);
    formData.append('fecha', document.getElementById('fecha_edit').value);
    formData.append('tipo_documento', document.getElementById('tipoDocumento_edit').value);
    formData.append('jurisdiccion', document.getElementById('jurisdiccion_edit').value);

    const fileInput = document.getElementById('pdfFile_edit');
    if (fileInput.files.length > 0) {
        formData.append('archivo_pdf', fileInput.files[0]);
    }

    fetch('/editar-pdf/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
        },
        body: formData,
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                Swal.fire("✅ Actualizado", "PDF editado correctamente", "success").then(() => {
                    closeModal(); // ocultar modal
                    location.reload(); // o refrescar lista
                });
            } else {
                Swal.fire("❌ Error", data.error || "Ocurrió un error al editar", "error");
            }
        })
        .catch(error => {
            console.error(error);
            Swal.fire("❌ Error", "Error de red", "error");
        });
});

// Espera a que jQuery esté completamente cargado
document.addEventListener('DOMContentLoaded', function () {
    $(document).ready(function () {
        cargarTablaPDFs();
    });
});
// Variables globales para el chat
let currentPdfId = null;
let currentPdfTitle = '';
let isDragging = false;
let isResizing = false;
let offsetX, offsetY;
let originalWidth, originalHeight, originalX, originalY;
let isFullscreen = false;

function initDragAndResize() {
    const modal = document.getElementById('chatModal');
    const modalContent = document.getElementById('chatModal').querySelector(".modal-content");
    const header = document.getElementById('chatHeader');
    modal.style.display = "block";
    modalContent.style.display = "flex";
    // Arrastrar
    header.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);

    // Redimensionar
    modal.addEventListener('mousedown', startResize);
}

// Funciones para arrastrar
function startDrag(e) {
    const header = document.getElementById('chatHeader');

    // Solo arrastrar si el click fue dentro del header
    if (!header.contains(e.target)) return;

    const modal = document.getElementById('chatModal');
    isDragging = true;
    offsetX = e.clientX - modal.getBoundingClientRect().left;
    console.log("X", offsetX);
    offsetY = e.clientY - modal.getBoundingClientRect().top;
    console.log("Y", offsetY);
    modal.style.cursor = 'grabbing';
}


function startDrag(e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON' || e.target.tagName === 'ION-ICON') return;

    // Solo permitir arrastrar desde el encabezado
    const header = document.getElementById('chatHeader');
    if (!header.contains(e.target)) return;

    const modal = document.getElementById('chatModal');
    isDragging = true;
    offsetX = e.clientX - modal.getBoundingClientRect().left;
    offsetY = e.clientY - modal.getBoundingClientRect().top;
    modal.style.cursor = 'grabbing';
}

function drag(e) {
    if (!isDragging || isResizing) return;

    const modal = document.getElementById('chatModal');
    modal.style.left = (e.clientX - offsetX) + 'px';
    modal.style.top = (e.clientY - offsetY) + 'px';
    modal.style.transform = 'none';
}

function stopDrag() {
    isDragging = false;
    const modal = document.getElementById('chatModal');
    modal.style.cursor = 'default';
}

function startResize(e) {
    const modal = document.getElementById('chatModal');
    const rect = modal.getBoundingClientRect();

    if (e.clientX > rect.right - 20 && e.clientY > rect.bottom - 20) {
        e.preventDefault();
        isResizing = true;
        document.addEventListener('mousemove', resize);
        document.addEventListener('mouseup', stopResize);
    }
}

function resize(e) {
    const modal = document.getElementById('chatModal');
    const newWidth = e.clientX - modal.getBoundingClientRect().left;
    const newHeight = e.clientY - modal.getBoundingClientRect().top;

    if (newWidth > 300) modal.style.width = newWidth + 'px';
    if (newHeight > 200) modal.style.height = newHeight + 'px';
}

function stopResize() {
    isResizing = false;
    document.removeEventListener('mousemove', resize);
}
// Función para abrir el modal de chat
function openChatModal(pdfNumeroCaso, title, pdfId) {
    currentPdfId = pdfNumeroCaso;
    currentPdfTitle = title;
    const modal = document.getElementById('chatModal');

    if (!modal.style.left || !modal.style.top) {
        modal.style.left = '50%';
        modal.style.top = '50%';
        modal.style.transform = 'translate(-50%, -50%)';
    }

    document.getElementById('pdfTitle').textContent = title;
    modal.style.display = 'block';
    document.getElementById('chatContainer').innerHTML = '';
    document.getElementById('userQuestion').focus();

    // Cargar historial si existe
    loadChatHistory(pdfNumeroCaso);

    initDragAndResize();
}


// Función para cerrar el modal de chat
function closeChatModal() {
    document.getElementById('chatModal').style.display = 'none';
    currentPdfId = null;
    currentPdfTitle = '';
}

// Función para enviar pregunta
function sendQuestion() {
    const questionInput = document.getElementById('userQuestion');
    const question = questionInput.value.trim();

    if (!question || !currentPdfId) return;

    // Añadir pregunta del usuario al chat
    addMessageToChat(question, 'user');
    questionInput.value = '';

    // Mostrar indicador de "escribiendo..."
    const typingIndicator = showTypingIndicator();

    // Enviar pregunta al backend
    fetch('/consultar-pdf/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            pdf_id: currentPdfId,
            question: question
        })
    })
        .then(response => response.json())
        .then(data => {
            // Eliminar indicador de "escribiendo..."
            removeTypingIndicator();

            if (data.answer) {
                addMessageToChat(data.answer, 'bot');
            } else {
                addMessageToChat("Lo siento, no pude obtener una respuesta.", 'bot');
            }
        })
        .catch(error => {
            removeTypingIndicator();
            addMessageToChat("Error al conectar con el servidor.", 'bot');
            console.error('Error:', error);
        });
}

// Función para añadir mensajes al chat con estilo Messenger
function addMessageToChat(message, sender, skipTyping = false) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');

    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    messageDiv.className = `chat-message ${sender}-message`;
    messageDiv.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="message-time">${timeString}</div>
    `;

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if (sender === 'user' && !skipTyping) {
        showTypingIndicator();
    }
}


// Función para mostrar indicador de "escribiendo..."
function showTypingIndicator() {
    const chatContainer = document.getElementById('chatContainer');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot-message typing-indicator';
    typingDiv.innerHTML = `
      <div class="message-content">
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
      </div>
  `;
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return typingDiv;
}

// Función para eliminar el indicador de "escribiendo..."
function removeTypingIndicator() {
    const typingIndicators = document.querySelectorAll('.typing-indicator');
    typingIndicators.forEach(indicator => {
        console.log("ELIMINADOOOOOOOOO");
        indicator.remove();
    });
}


// Función para obtener el token CSRF
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
// Función para minimizar el chat
function minimizeChat() {
    const modal = document.getElementById('chatModal');
    if (modal.style.height === '40px') {
        // Restaurar tamaño
        modal.style.height = originalHeight || '500px';
        modal.style.width = originalWidth || '400px';
        document.querySelector('.chat-container').style.display = 'flex';
        document.querySelector('.chat-input-container').style.display = 'block';
    } else {
        // Guardar tamaño actual y minimizar
        originalHeight = modal.style.height;
        originalWidth = modal.style.width;
        modal.style.height = '40px';
        modal.style.width = '300px';
        document.querySelector('.chat-container').style.display = 'none';
        document.querySelector('.chat-input-container').style.display = 'none';
    }
}

// Función para alternar pantalla completa
function toggleFullscreen() {
    const modal = document.getElementById('chatModal');
    if (isFullscreen) {
        // Salir de pantalla completa
        modal.classList.remove('fullscreen');
        modal.style.width = originalWidth || '400px';
        modal.style.height = originalHeight || '500px';
        modal.style.left = originalX || '50%';
        modal.style.top = originalY || '50%';
        modal.style.transform = originalX ? 'none' : 'translate(-50%, -50%)';
    } else {
        // Entrar en pantalla completa
        originalWidth = modal.style.width;
        originalHeight = modal.style.height;
        originalX = modal.style.left;
        originalY = modal.style.top;
        modal.classList.add('fullscreen');
        modal.style.transform = 'none';
    }
    isFullscreen = !isFullscreen;
}
// Permitir enviar pregunta con Enter
document.getElementById('userQuestion').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendQuestion();
    }
});
// Funciones JavaScript
function openModal() {
    document.getElementById('pdfModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('pdfModal_edit').style.display = 'none';
    document.getElementById('pdfModal').style.display = 'none';
    document.getElementById('pdfForm').reset();
    document.getElementById('otherDocumentContainer').style.display = 'none';
}

function toggleOtherDocument() {
    const tipoDocumento = document.getElementById('tipoDocumento').value;
    const otherDocumentContainer = document.getElementById('otherDocumentContainer');

    if (tipoDocumento === 'otro') {
        otherDocumentContainer.style.display = 'block';
    } else {
        otherDocumentContainer.style.display = 'none';
    }
}

function savePDF() {
    const formData = new FormData();
    formData.append('numero_caso', document.getElementById('Numerodecaso').value);
    formData.append('titulo', document.getElementById('titulo').value);
    formData.append('fecha', document.getElementById('fecha').value);

    const tipoDocumento = document.getElementById('tipoDocumento').value;
    const otherDocument = document.getElementById('otherDocument').value;
    const tipoDocumentoFinal = tipoDocumento === 'otro' ? otherDocument : tipoDocumento;
    formData.append('tipo_documento', tipoDocumentoFinal);

    formData.append('jurisdiccion', document.getElementById('jurisdiccion').value);
    formData.append('archivo_pdf', document.getElementById('pdfFile').files[0]);

    fetch('/guardar-pdf/', {
        method: 'POST',
        body: formData,
        headers: {
            //'X-CSRFToken': getCookie('csrftoken')  // Si quieres manejar CSRF, aunque @csrf_exempt lo omite.
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert("Error: " + data.error);
            } else {
                Swal.fire("Exitoso", "Archivo correctamente guardado", "success");
                cargarTablaPDFs();
                closeModal();
            }
        })
        .catch(error => {
            alert("Error en la petición: " + error);
        });
}

function agregarFilaATabla(titulo, fecha, nombreArchivo) {
    const tableBody = document.getElementById('tableBody');
    const newRow = document.createElement('tr');

    newRow.innerHTML = `
          <td>${titulo}</td>
          <td>${fecha}</td>
          <td>
              <button class="action-button view" onclick="viewPDF('${nombreArchivo}')">
                  <ion-icon name="eye-outline"></ion-icon>
              </button>
              <button class="action-button delete" onclick="deletePDF(this)">
                  <ion-icon name="trash-outline"></ion-icon>
              </button>
          </td>
      `;

    if (tableBody.innerHTML.includes('No hay archivos')) {
        tableBody.innerHTML = '';
    }

    tableBody.appendChild(newRow);
}


function deletePDF(button, pdfId) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Esta acción eliminará el PDF y sus datos permanentemente.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/eliminar-pdf/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({ pdf_id: pdfId }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const row = button.closest('tr');
                        row.remove();

                        const tableBody = document.getElementById('tableBody');
                        if (tableBody.children.length === 0) {
                            tableBody.innerHTML = '<tr><td colspan="3">No hay archivos registrados</td></tr>';
                        }

                        Swal.fire({
                            icon: 'success',
                            title: 'Eliminado',
                            text: 'El PDF ha sido eliminado correctamente.',
                            timer: 1500,
                            showConfirmButton: false
                        });
                    } else {
                        Swal.fire('Error', data.error || 'Error desconocido al eliminar.', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error al eliminar:', error);
                    Swal.fire('Error', 'Error en la petición al servidor.', 'error');
                });
        }
    });
}



function viewPDF(filename) {
    console.log("filename", filename); // ← Esto te da la URL completa
    window.open(filename, '_blank');
}

function cargarTablaPDFs() {
    $.get('/listar-pdfs', function (data) {
        const tbody = $('#tableBody');
        tbody.empty();

        if (data.results.length === 0) {
            tbody.append('<tr><td colspan="3">No hay archivos registrados</td></tr>');
            return;
        }

        data.results.forEach(function (doc) {
            const fila = `
              <tr>
                  <td>${doc.titulo}</td>
                  <td>${doc.fecha}</td>
                  <td class="actions-cell">
                      <button class="action-button view" onclick="viewPDF('${doc.pdf_url}')">
                        <ion-icon name="eye-outline"></ion-icon>
                      </button>
                      <button class="action-button consult" onclick="openChatModal('${doc.numero_caso}', '${doc.titulo.replace(/'/g, "\\'")}','${doc.id}')">
                        <ion-icon name="chatbox-outline"></ion-icon>
                      </button>
                      <button class="action-button edit" onclick="editPDF('${doc.id}')">
                        <ion-icon name="create-outline"></ion-icon>
                      </button>
                      <button class="action-button delete" onclick="deletePDF(this, '${doc.id}')">
                        <ion-icon name="trash-outline"></ion-icon>
                      </button>
                  </td>
              </tr>
          `;
            //   deletePDF
            tbody.append(fila);
        });
    }).fail(function (err) {
        console.error("Error en /listar-pdfs:", err.responseText);
    });
}

// Llama a la función al cargar la página
$(document).ready(function () {
    cargarTablaPDFs();
});

// Búsqueda en tiempo real
document.getElementById('searchInput').addEventListener('input', function () {
    const searchTerm = this.value.toLowerCase();
    const rows = document.querySelectorAll('#tableBody tr');

    rows.forEach(row => {
        const title = row.cells[0].textContent.toLowerCase();
        row.style.display = title.includes(searchTerm) ? '' : 'none';
    });
});
$('#pdfForm').on('submit', function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    console.log("Enviando formulario con los siguientes datos:");
    for (let [key, value] of formData.entries()) {
        console.log(key, value);
    }

    $.ajax({
        url: '/registrar-pdf',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
            console.log("Respuesta exitosa del backend:", response);
            alert(response.mensaje);
            cargarTablaPDFs(); // refresca la tabla
            $('#pdfForm')[0].reset(); // limpia el formulario
        },
        error: function (xhr) {
            console.error("Error al registrar el documento:", xhr.responseText);
            alert("Error al registrar el documento: " + xhr.responseJSON?.mensaje || 'Error desconocido');
        }
    });
});

function loadChatHistory(pdfNumeroCaso) {
    $.ajax({
        url: `/api/interacciones/${pdfNumeroCaso}/`,  // Ajustá esta URL a tu ruta real
        type: 'GET',
        success: function (data) {
            if (data.interacciones && data.interacciones.length > 0) {
                data.interacciones.forEach(interaccion => {
                    addMessageToChat(interaccion.prompt, 'user', true);
                    addMessageToChat(interaccion.respuesta, 'bot', true);
                });
            }
        },
        error: function (xhr) {
            console.error("❌ No se pudo cargar el historial del chat:", xhr.responseText);
        }
    });
}

function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const c = cookie.trim();
        if (c.startsWith(name + '=')) {
            return decodeURIComponent(c.slice(name.length + 1));
        }
    }
    return '';
}

function editPDF(pdfId) {
    fetch(`/api/obtener-pdf/${pdfId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error("No se pudo obtener el PDF");
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('pdf_id_edit').value = data.id;
            document.getElementById('Numerodecaso_edit').value = data.numero_caso;
            document.getElementById('titulo_edit').value = data.titulo;
            document.getElementById('fecha_edit').value = data.fecha;
            document.getElementById('tipoDocumento_edit').value = data.tipo_documento;
            document.getElementById('jurisdiccion_edit').value = data.jurisdiccion;

            // Mostrar el modal
            document.getElementById('pdfModal_edit').style.display = 'block';
        })
        .catch(error => {
            console.error("Error al obtener PDF:", error);
            Swal.fire("❌ Error", error.message || "No se pudo cargar el PDF.");
        });
}
