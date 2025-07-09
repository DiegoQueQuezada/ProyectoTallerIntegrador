$(document).ready(function () {
    iniciarDataTables();
    iniciarEventosEstaticos();
    listarPDFs();
});

function iniciarEventosEstaticos() {

    $("#btnNuevoModal").on("click", function () {
        modalNuevoPDF();
    });

    $('#pdfModal').on('hidden.bs.modal', function () {
        $('#pdfForm')[0].reset(); // Limpia el formulario
    });

    $('#pdfModal_edit').on('hidden.bs.modal', function () {
        $('#pdfForm_edit')[0].reset(); // Limpia el formulario
    });

}
function iniciarDataTables() {
    $('#pdfTable').DataTable({
        paging: true,
        searching: true,
        ordering: true,
        language: {
            url: "//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json"
        }
    });
}
document.querySelector("#pdfModal_edit #editarPDF").addEventListener("click", function () {
    const formData = new FormData();
    const pdfId = document.getElementById("pdf_id_edit").value;
    formData.append("pdf_id", pdfId);
    formData.append("numero_caso", document.getElementById("Numerodecaso_edit").value);
    formData.append("titulo", document.getElementById("titulo_edit").value);
    formData.append("fecha", document.getElementById("fecha_edit").value);
    formData.append("tipo_documento", document.getElementById("tipoDocumento_edit").value);
    formData.append("jurisdiccion", document.getElementById("jurisdiccion_edit").value);
    const fileInput = document.getElementById("pdfFile_edit");

    if (fileInput.files.length > 0) {
        formData.append("archivo_pdf", fileInput.files[0]);
    }

    fetch("/editar-pdf/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
        },
        body: formData,
    }).then((res) => res.json()).then((data) => {

        if (data.success) {
            Swal.fire(
                "✅ Actualizado",
                "PDF editado correctamente",
                "success"
            ).then(() => {
                const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('pdfModal_edit'));
                modal.hide();
                location.reload();
            });
        } else {
            Swal.fire("❌ Error", data.error || "Ocurrió un error al editar", "error");
        }

    }).catch((error) => {

        console.error(error);
        Swal.fire("❌ Error", "Error de red", "error");
    });
});



// Variables globales para el chat
let currentPdfId = null;
let currentPdfTitle = "";
let isDragging = false;
let isResizing = false;
let offsetX, offsetY;
let originalWidth, originalHeight, originalX, originalY;
let isFullscreen = false;

function initDragAndResize() {

    const modal = document.getElementById("chatModal");
    const modalContent = document.getElementById("chatModal").querySelector(".modal-content");
    const header = document.getElementById("chatHeader");
    modal.style.display = "block";
    modalContent.style.display = "flex";
    // Arrastrar

    header.addEventListener("mousedown", startDrag);
    document.addEventListener("mousemove", drag);
    document.addEventListener("mouseup", stopDrag);

    // Redimensionar
    modal.addEventListener("mousedown", startResize);
}

// Funciones para arrastrar
function startDrag(e) {

    const header = document.getElementById("chatHeader");

    // Solo arrastrar si el click fue dentro del header

    if (!header.contains(e.target)) return;

    const modal = document.getElementById("chatModal");
    isDragging = true;
    offsetX = e.clientX - modal.getBoundingClientRect().left;
    offsetY = e.clientY - modal.getBoundingClientRect().top;
    modal.style.cursor = "grabbing";
}

function startDrag(e) {

    if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON" || e.target.tagName === "ION-ICON") {
        return;
    };

    // Solo permitir arrastrar desde el encabezado

    const header = document.getElementById("chatHeader");
    if (!header.contains(e.target)) {
        return;
    }

    const modal = document.getElementById("chatModal");
    isDragging = true;
    offsetX = e.clientX - modal.getBoundingClientRect().left;
    offsetY = e.clientY - modal.getBoundingClientRect().top;
    modal.style.cursor = "grabbing";
}

function drag(e) {
    if (!isDragging || isResizing) return;

    const modal = document.getElementById("chatModal");

    // Tamaños del modal
    const modalWidth = modal.offsetWidth;
    const modalHeight = modal.offsetHeight;

    // Tamaño de la ventana
    const maxLeft = window.innerWidth - modalWidth;
    const maxTop = window.innerHeight - modalHeight;

    // Posiciones calculadas
    let newLeft = e.clientX - offsetX;
    let newTop = e.clientY - offsetY;

    // Limitar dentro del viewport
    newLeft = Math.max(0, Math.min(newLeft, maxLeft));
    newTop = Math.max(0, Math.min(newTop, maxTop));

    // Aplicar posición
    modal.style.left = newLeft + "px";
    modal.style.top = newTop + "px";
    modal.style.transform = "none";
}


function stopDrag() {
    isDragging = false;
    const modal = document.getElementById("chatModal");
    modal.style.cursor = "default";
}

function startResize(e) {
    const modal = document.getElementById("chatModal");
    const rect = modal.getBoundingClientRect();

    if (e.clientX > rect.right - 20 && e.clientY > rect.bottom - 20) {
        e.preventDefault();
        isResizing = true;
        document.addEventListener("mousemove", resize);
        document.addEventListener("mouseup", stopResize);
    }
}

function resize(e) {
    const modal = document.getElementById("chatModal");
    const newWidth = e.clientX - modal.getBoundingClientRect().left;
    const newHeight = e.clientY - modal.getBoundingClientRect().top;

    if (newWidth > 300) modal.style.width = newWidth + "px";
    if (newHeight > 200) modal.style.height = newHeight + "px";
}

function stopResize() {
    isResizing = false;
    document.removeEventListener("mousemove", resize);
}
// Función para abrir el modal de chat
function openChatModal(pdfNumeroCaso, title) {

    currentPdfId = pdfNumeroCaso;
    currentPdfTitle = title;
    const modal = document.getElementById("chatModal");

    // Establecer tamaño inicial
    modal.style.width = "600px";
    modal.style.height = "600px";

    // Centrado si no está posicionado
    if (!modal.style.left || !modal.style.top) {
        modal.style.left = "50%";
        modal.style.top = "50%";
        modal.style.transform = "translate(-50%, -50%)";
    }

    document.getElementById("pdfTitle").textContent = title;
    modal.style.display = "block";
    document.getElementById("chatContainer").innerHTML = "";
    document.getElementById("userQuestion").focus();

    // Cargar historial si existe
    listarInteraccion(pdfNumeroCaso);
    initDragAndResize();
}


// Función para cerrar el modal de chat
function closeChatModal() {
    document.getElementById("chatModal").style.display = "none";
    currentPdfId = null;
    currentPdfTitle = "";
}

// Función para enviar pregunta
function sendQuestion() {
    const questionInput = document.getElementById("userQuestion");
    const question = questionInput.value.trim();

    if (!question || !currentPdfId) return;

    // Añadir pregunta del usuario al chat
    addMessageToChat(question, "user");
    questionInput.value = "";
    // Enviar pregunta al backend
    fetch("/consultar-pdf/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({
            pdf_id: currentPdfId,
            question: question,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            // Eliminar indicador de "escribiendo..."
            removeTypingIndicator();

            if (data.answer) {
                addMessageToChat(data.answer, "bot");
            } else {
                addMessageToChat("Lo siento, no pude obtener una respuesta.", "bot");
            }
        })
        .catch((error) => {
            removeTypingIndicator();
            addMessageToChat("Error al conectar con el servidor.", "bot");
            console.error("Error:", error);
        });
}

// Función para añadir mensajes al chat con estilo Messenger
function addMessageToChat(message, sender, skipTyping = false) {
    const chatContainer = document.getElementById("chatContainer");
    const messageDiv = document.createElement("div");

    const now = new Date();
    const timeString = now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
    });

    messageDiv.className = `chat-message ${sender}-message`;
    messageDiv.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="message-time">${timeString}</div>
    `;

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if (sender === "user" && !skipTyping) {
        showTypingIndicator();
    }
}

// Función para mostrar indicador de "escribiendo..."
function showTypingIndicator() {
    const chatContainer = document.getElementById("chatContainer");
    const typingDiv = document.createElement("div");
    typingDiv.className = "chat-message bot-message typing-indicator";
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
    const typingIndicators = document.querySelectorAll(".typing-indicator");
    typingIndicators.forEach((indicator) => {
        console.log("ELIMINADOOOOOOOOO");
        indicator.remove();
    });
}

// Función para obtener el token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
// Función para minimizar el chat
function minimizeChat() {
    const modal = document.getElementById("chatModal");

    // Restaurar a los valores originales si existen
    modal.style.width = originalWidth || "400px";
    modal.style.height = originalHeight || "500px";
    modal.style.left = originalX || "50%";
    modal.style.top = originalY || "50%";
    modal.style.transform = originalX ? "none" : "translate(-50%, -50%)";

    // Asegurarse de quitar modo fullscreen
    modal.classList.remove("fullscreen");
}


// Función para alternar pantalla completa
function toggleFullscreen() {
    const modal = $("#chatModal").get(0);
    const modalChat = $("#chatModal .modal-content").get(0);
    const computedStyle = window.getComputedStyle(modalChat);
    const width = computedStyle.width;
    const height = computedStyle.height;

    // Detectar si ya está en pantalla completa (por tamaño)
    const isCurrentlyFullscreen = width === "100vw" && height === "100vh";

    if (isCurrentlyFullscreen) {
        console.log("saliendo de  fuulscren")
        // Salir de pantalla completa
        modal.classList.remove("fullscreen");
        modal.style.width = originalWidth || "400px";
        modal.style.height = originalHeight || "500px";
        modal.style.left = originalX || "50%";
        modal.style.top = originalY || "50%";
        modal.style.transform = originalX ? "none" : "translate(-50%, -50%)";
    } else {
        console.log("entrando a fullscreen")
        // Entrar en pantalla completa
        originalWidth = modal.style.width;
        originalHeight = modal.style.height;
        originalX = modal.style.left;
        originalY = modal.style.top;
        modal.style.width = "100%";
        modal.style.height = "100%";
        modal.style.left = "0";
        modal.style.top = "0";
        modal.classList.add("fullscreen");
        modal.style.transform = "none";
    }
}

// Permitir enviar pregunta con Enter
document
    .getElementById("userQuestion")
    .addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            sendQuestion();
        }
    });


// Funciones JavaScript
function modalNuevoPDF(config) {
    let modal = new bootstrap.Modal(document.getElementById('pdfModal'));
    modal.show();

    // Validación Numerodecaso: solo letras
    $("#Numerodecaso").off().on("input", function () {
        let valor = $(this).val();
        // Elimina cualquier carácter que no sea un número
        valor = valor.replace(/\D/g, '');
        $(this).val(valor);
    });
    

    // Validación titulo: solo letras y espacios
    $("#titulo").off().on("input", function () {
        let valor = $(this).val();
        valor = valor.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, "");
        $(this).val(valor);
    });

    $("#titulo").val("");
    $("#descripcion").val("");
    $("#fecha").val("");
    $("#tipoDocumento").val("");
    $("#jurisdiccion").val("");
}

function toggleOtherDocument() {
    const tipoDocumento = document.getElementById("tipoDocumento").value;
    const otherDocumentContainer = document.getElementById(
        "otherDocumentContainer"
    );

    if (tipoDocumento === "otro") {
        otherDocumentContainer.style.display = "block";
    } else {
        otherDocumentContainer.style.display = "none";
    }
}

function guardarNuevoPDF() {
    // Mostrar el spinner
    document.getElementById("spinnerCarga").classList.remove("d-none");

    const formData = new FormData();
    formData.append("numero_caso", document.getElementById("Numerodecaso").value);
    formData.append("titulo", document.getElementById("titulo").value);
    formData.append("fecha", document.getElementById("fecha").value);

    const tipoDocumento = document.getElementById("tipoDocumento").value;
    const otherDocument = document.getElementById("otherDocument").value;
    const tipoDocumentoFinal =
        tipoDocumento === "otro" ? otherDocument : tipoDocumento;
    formData.append("tipo_documento", tipoDocumentoFinal);

    formData.append("jurisdiccion", document.getElementById("jurisdiccion").value);
    formData.append("archivo_pdf", document.getElementById("pdfFile").files[0]);

    $.ajax({
        url: "/guardar-pdf/",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        success: function (data) {
            $("#spinnerCarga").addClass("d-none");

            if (data.error) {
                Swal.fire("Error", data.error, "error");
            } else {
                Swal.fire("Exitoso", data.mensaje || "Archivo guardado correctamente", "success");
                listarPDFs();
                const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('pdfModal'));
                modal.hide();
            }
        },
        error: function (xhr) {
            $("#spinnerCarga").addClass("d-none");

            let mensajeError = "Ocurrió un error inesperado al guardar.";

            try {
                const data = xhr.responseJSON;
                if (data && data.error) {
                    mensajeError = data.error;
                }
            } catch (e) { }

            Swal.fire("Error", mensajeError, "error");
        }
    });
}


function agregarFilaATabla(titulo, fecha, nombreArchivo) {
    const tableBody = document.getElementById("tableBody");
    const newRow = document.createElement("tr");

    newRow.innerHTML = `
          <td>${titulo}</td>
          <td>${fecha}</td>
          <td>
              <button class="action-button view" onclick="viewPDF('${nombreArchivo}')">
                  <ion-icon name="eye-outline"></ion-icon>
              </button>
              <button class="action-button delete" onclick="eliminar(this)">
                  <ion-icon name="trash-outline"></ion-icon>
              </button>
          </td>
      `;

    if (tableBody.innerHTML.includes("No hay archivos")) {
        tableBody.innerHTML = "";
    }

    tableBody.appendChild(newRow);
}

function eliminarPDF(button, pdfId) {
    Swal.fire({
        title: "¿Estás seguro?",
        text: "Esta acción eliminará el PDF y sus datos permanentemente.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#3085d6",
        confirmButtonText: "Sí, eliminar",
        cancelButtonText: "Cancelar",
    }).then((result) => {
        if (result.isConfirmed) {
            fetch("/eliminar-pdf/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: JSON.stringify({ pdf_id: pdfId }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        const row = button.closest("tr");
                        row.remove();

                        const tableBody = document.getElementById("tableBody");
                        if (tableBody.children.length === 0) {
                            tableBody.innerHTML =
                                '<tr><td colspan="3">No hay archivos registrados</td></tr>';
                        }

                        Swal.fire({
                            icon: "success",
                            title: "Eliminado",
                            text: "El PDF ha sido eliminado correctamente.",
                            timer: 1500,
                            showConfirmButton: false,
                        });
                    } else {
                        Swal.fire(
                            "Error",
                            data.error || "Error desconocido al eliminar.",
                            "error"
                        );
                    }
                })
                .catch((error) => {
                    console.error("Error al eliminar:", error);
                    Swal.fire("Error", "Error en la petición al servidor.", "error");
                });
        }
    });
}

function viewPDF(filename) {
    console.log("filename", filename); // ← Esto te da la URL completa
    window.open(filename, "_blank");
}

function listarPDFs() {
    $.get("/listar-pdfs", function (data) {
        const tabla = $('#pdfTable').DataTable();

        tabla.clear(); // Limpia filas previas



        const filas = data.results.map((doc) => [
            doc.titulo,
            doc.fecha,
            `
            <div class="d-flex gap-1 justify-content-center">
                <button class="action-button view" onclick="viewPDF('${doc.pdf_url}')">
                    <ion-icon name="eye-outline"></ion-icon>
                </button>
                <button class="action-button consult" onclick="openChatModal('${doc.numero_caso}', '${doc.titulo.replace(/'/g, "\\'")}', '${doc.id}')">
                    <ion-icon name="chatbox-outline"></ion-icon>
                </button>
                <button class="action-button edit" onclick="modalEditarPDF('${doc.id}')">
                    <ion-icon name="create-outline"></ion-icon>
                </button>
                <button class="action-button delete" onclick="eliminarPDF(this, '${doc.id}')">
                    <ion-icon name="trash-outline"></ion-icon>
                </button>
            </div>
            `
        ]);

        tabla.rows.add(filas).draw(); // Agrega las filas
    }).fail(function (err) {
        console.error("Error en /listar-pdfs:", err.responseText);
    });
}


// Llama a la función al cargar la página
$(document).ready(function () {
    listarPDFs();
});


$("#pdfForm").on("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    console.log("Enviando formulario con los siguientes datos:");
    for (let [key, value] of formData.entries()) {
        console.log(key, value);
    }

    $.ajax({
        url: "/registrar-pdf",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
            console.log("Respuesta exitosa del backend:", response);
            alert(response.mensaje);
            listarPDFs(); // refresca la tabla
            $("#pdfForm")[0].reset(); // limpia el formulario
        },
        error: function (xhr) {
            console.error("Error al registrar el documento:", xhr.responseText);
            alert(
                "Error al registrar el documento: " + xhr.responseJSON?.mensaje ||
                "Error desconocido"
            );
        },
    });
});

function listarInteraccion(pdfNumeroCaso) {
    $.ajax({
        url: `/api/interacciones/${pdfNumeroCaso}/`, // Ajustá esta URL a tu ruta real
        type: "GET",
        success: function (data) {
            if (data.interacciones && data.interacciones.length > 0) {
                data.interacciones.forEach((interaccion) => {
                    addMessageToChat(interaccion.prompt, "user", true);
                    addMessageToChat(interaccion.respuesta, "bot", true);
                });
            }
        },
        error: function (xhr) {
            console.error(
                "❌ No se pudo cargar el historial del chat:",
                xhr.responseText
            );
        },
    });
}

function getCSRFToken() {
    const name = "csrftoken";
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
        const c = cookie.trim();
        if (c.startsWith(name + "=")) {
            return decodeURIComponent(c.slice(name.length + 1));
        }
    }
    return "";
}



function modalEditarPDF(pdfId) {

    $.ajax({
        url: `/api/obtener-pdf/${pdfId}/`,
        type: 'GET',
        dataType: 'json',
        success: function (data) {
            $('#pdf_id_edit').val(data.id);
            $('#Numerodecaso_edit').val(data.numero_caso);
            $('#titulo_edit').val(data.titulo);
            $('#fecha_edit').val(data.fecha);
            $('#tipoDocumento_edit').val(data.tipo_documento);
            $('#jurisdiccion_edit').val(data.jurisdiccion);

            // Validación Numerodecaso_edit: solo letras
            // $("#Numerodecaso").off().on("input", function () {
            //     let valor = $(this).val();
            //     // Elimina cualquier carácter que no sea un número
            //     valor = valor.replace(/\D/g, '');
            //     $(this).val(valor);
            // });
            
            // Validación titulo_edit: solo letras y espacios
            $("#titulo_edit").off().on("input", function () {
                let valor = $(this).val();
                valor = valor.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, "");
                $(this).val(valor);
            });

            // Mostrar el modal Bootstrap
            const modal = new bootstrap.Modal(document.getElementById('pdfModal_edit'));
            modal.show();
        },
        error: function (xhr) {
            console.error("Error al obtener PDF:", xhr);
            Swal.fire("❌ Error", xhr.responseJSON?.message || "No se pudo cargar el PDF.");
        }
    });

}
