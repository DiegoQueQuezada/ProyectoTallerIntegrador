document.getElementById('pdfForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById('submitBtn');
    const responseDiv = document.getElementById('response');
    
    // Mostrar estado de carga
    submitBtn.disabled = true;
    submitBtn.textContent = 'Procesando...';
    responseDiv.innerHTML = '<div class="loading"><div class="spinner"></div>Cargando respuesta...</div>';
    
    try {
        const formData = new FormData(e.target);
        const response = await fetch('/responder-pdf/', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }

        const data = await response.json();
        responseDiv.innerText = data.answer || 'No se recibió una respuesta válida';
    } catch (error) {
        console.error('Error:', error);
        responseDiv.innerText = 'Ocurrió un error al procesar tu solicitud. Por favor intenta nuevamente.';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Subir y preguntar';
    }
});