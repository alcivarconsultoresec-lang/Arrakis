/**
 * Ω JARBIS Enterprise - ChatInterface Component
 * Interfaz de chat principal con soporte para voz, fotos y rich cards
 */

import { api } from '../services/api.js';

// ============================================================================
// ESTILOS CSS (inline para simplicidad)
// ============================================================================

const styles = `
  .chat-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 600px;
    margin: 0 auto;
    background: #1a1a2e;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  .chat-header {
    padding: 16px;
    background: #0f3460;
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }

  .chat-header h1 {
    font-size: 1.2rem;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .status-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #4ade80;
    animation: pulse 2s infinite;
  }

  .status-indicator.offline {
    background: #f87171;
    animation: none;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .message {
    max-width: 85%;
    padding: 12px 16px;
    border-radius: 16px;
    line-height: 1.5;
    animation: fadeIn 0.3s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .message.user {
    align-self: flex-end;
    background: #0f3460;
    color: white;
    border-bottom-right-radius: 4px;
  }

  .message.assistant {
    align-self: flex-start;
    background: #2d2d44;
    color: #e0e0e0;
    border-bottom-left-radius: 4px;
  }

  .message.system {
    align-self: center;
    background: transparent;
    color: #888;
    font-size: 0.85rem;
    text-align: center;
    border: 1px solid #444;
  }

  /* Rich Cards */
  .rich-card {
    background: #1e1e32;
    border-radius: 12px;
    padding: 12px;
    margin-top: 8px;
    border: 1px solid #333;
  }

  .rich-card-title {
    font-weight: 600;
    color: #fff;
    margin-bottom: 8px;
  }

  .rich-card-content {
    color: #ccc;
    font-size: 0.9rem;
  }

  .rich-card-actions {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    flex-wrap: wrap;
  }

  .card-button {
    background: #0f3460;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.85rem;
    transition: background 0.2s;
  }

  .card-button:hover {
    background: #1a4a7a;
  }

  .card-button.secondary {
    background: transparent;
    border: 1px solid #0f3460;
  }

  /* Input Area */
  .chat-input-area {
    padding: 12px;
    background: #2d2d44;
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .chat-input {
    flex: 1;
    background: #1a1a2e;
    border: 1px solid #444;
    border-radius: 24px;
    padding: 12px 16px;
    color: white;
    font-size: 1rem;
    outline: none;
    transition: border-color 0.2s;
  }

  .chat-input:focus {
    border-color: #0f3460;
  }

  .chat-input::placeholder {
    color: #666;
  }

  .input-button {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: none;
    background: #0f3460;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
  }

  .input-button:hover {
    background: #1a4a7a;
  }

  .input-button.recording {
    background: #dc2626;
    animation: pulse 1s infinite;
  }

  .input-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Offline indicator */
  .offline-banner {
    background: #dc2626;
    color: white;
    text-align: center;
    padding: 8px;
    font-size: 0.85rem;
    display: none;
  }

  .offline-banner.visible {
    display: block;
  }

  /* Loading indicator */
  .typing-indicator {
    display: flex;
    gap: 4px;
    padding: 12px 16px;
  }

  .typing-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #666;
    animation: typing 1.4s infinite;
  }

  .typing-dot:nth-child(2) { animation-delay: 0.2s; }
  .typing-dot:nth-child(3) { animation-delay: 0.4s; }

  @keyframes typing {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-8px); }
  }

  /* Photo preview */
  .photo-preview {
    position: relative;
    max-width: 200px;
    margin: 8px 0;
  }

  .photo-preview img {
    width: 100%;
    border-radius: 8px;
  }

  .photo-preview-remove {
    position: absolute;
    top: -8px;
    right: -8px;
    background: #dc2626;
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    font-size: 1rem;
  }

  /* Quick suggestions */
  .quick-suggestions {
    display: flex;
    gap: 8px;
    padding: 8px 16px;
    overflow-x: auto;
    background: #2d2d44;
  }

  .suggestion-chip {
    background: #1a1a2e;
    border: 1px solid #444;
    color: #ccc;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 0.85rem;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
  }

  .suggestion-chip:hover {
    background: #0f3460;
    border-color: #0f3460;
  }
`;

// ============================================================================
// COMPONENTE CHATINTERFACE
// ============================================================================

export class ChatInterface {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      throw new Error(`Container #${containerId} not found`);
    }

    this.options = {
      placeholder: 'Escribe tu mensaje...',
      voiceEnabled: true,
      photoEnabled: true,
      quickSuggestions: [
        '¿Qué hay en stock bajo?',
        'Recomienda una receta',
        'Registrar venta del día',
        'Ver reporte financiero',
      ],
      ...options,
    };

    this.messages = [];
    this.isRecording = false;
    this.photoFile = null;
    this.recognition = null;

    this.init();
  }

  // ============================================================================
  // INICIALIZACIÓN
  // ============================================================================

  init() {
    this.render();
    this.setupEventListeners();
    this.setupVoiceRecognition();
    this.checkConnection();
    this.loadChatHistory();

    // Escuchar cambios de conexión
    window.addEventListener('online', () => this.updateConnectionStatus());
    window.addEventListener('offline', () => this.updateConnectionStatus());
  }

  render() {
    this.container.innerHTML = `
      <style>${styles}</style>
      <div class="chat-container">
        <div class="offline-banner" id="offlineBanner">
          ⚠️ Sin conexión - Los mensajes se enviarán cuando recuperes la conexión
        </div>
        
        <header class="chat-header">
          <h1>
            <span class="status-indicator" id="statusIndicator"></span>
            Ω JARBIS
          </h1>
          <button class="input-button" id="menuButton" title="Menú">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/>
            </svg>
          </button>
        </header>

        <div class="quick-suggestions" id="quickSuggestions"></div>

        <div class="chat-messages" id="chatMessages">
          <!-- Messages will be inserted here -->
        </div>

        <div class="chat-input-area">
          ${this.options.photoEnabled ? `
            <button class="input-button" id="photoButton" title="Agregar foto">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
              </svg>
            </button>
            <input type="file" id="photoInput" accept="image/*" capture="environment" style="display:none;">
          ` : ''}
          
          <input 
            type="text" 
            class="chat-input" 
            id="chatInput" 
            placeholder="${this.options.placeholder}"
            autocomplete="off"
          >
          
          ${this.options.voiceEnabled ? `
            <button class="input-button" id="voiceButton" title="Entrada de voz">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </button>
          ` : ''}
          
          <button class="input-button" id="sendButton" title="Enviar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
        
        <div id="photoPreviewContainer"></div>
      </div>
    `;

    this.renderQuickSuggestions();
  }

  renderQuickSuggestions() {
    const container = document.getElementById('quickSuggestions');
    if (!container) return;

    container.innerHTML = this.options.quickSuggestions
      .map((suggestion) => `<span class="suggestion-chip">${suggestion}</span>`)
      .join('');
  }

  // ============================================================================
  // EVENT LISTENERS
  // ============================================================================

  setupEventListeners() {
    const input = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const voiceButton = document.getElementById('voiceButton');
    const photoButton = document.getElementById('photoButton');
    const photoInput = document.getElementById('photoInput');
    const menuButton = document.getElementById('menuButton');

    // Send message on button click
    sendButton?.addEventListener('click', () => this.sendMessage());

    // Send message on Enter key
    input?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Voice input
    voiceButton?.addEventListener('click', () => this.toggleVoiceRecording());

    // Photo input
    photoButton?.addEventListener('click', () => photoInput?.click());
    photoInput?.addEventListener('change', (e) => this.handlePhotoSelect(e));

    // Quick suggestions
    document.querySelectorAll('.suggestion-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        input.value = chip.textContent;
        this.sendMessage();
      });
    });

    // Menu button
    menuButton?.addEventListener('click', () => this.showMenu());
  }

  // ============================================================================
  // VOICE RECOGNITION
  // ============================================================================

  setupVoiceRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      console.warn('Voice recognition not supported');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = 'es-MX';

    this.recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join('');
      
      document.getElementById('chatInput').value = transcript;
    };

    this.recognition.onend = () => {
      this.isRecording = false;
      document.getElementById('voiceButton')?.classList.remove('recording');
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      this.isRecording = false;
      document.getElementById('voiceButton')?.classList.remove('recording');
    };
  }

  toggleVoiceRecording() {
    if (!this.recognition) return;

    if (this.isRecording) {
      this.recognition.stop();
    } else {
      this.recognition.start();
      this.isRecording = true;
      document.getElementById('voiceButton')?.classList.add('recording');
    }
  }

  // ============================================================================
  // PHOTO HANDLING
  // ============================================================================

  handlePhotoSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    this.photoFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
      const container = document.getElementById('photoPreviewContainer');
      if (container) {
        container.innerHTML = `
          <div class="photo-preview">
            <img src="${e.target.result}" alt="Preview">
            <button class="photo-preview-remove" onclick="document.getElementById('photoPreviewContainer').innerHTML=''">×</button>
          </div>
        `;
      }
    };
    reader.readAsDataURL(file);
  }

  // ============================================================================
  // MESSAGE HANDLING
  // ============================================================================

  async sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message && !this.photoFile) return;

    // Add user message
    this.addMessage(message, 'user', this.photoFile ? { photo: this.photoFile.name } : null);
    input.value = '';

    // Show typing indicator
    this.showTypingIndicator();

    try {
      // Prepare request
      const requestData = { message };
      
      if (this.photoFile) {
        // In production: upload photo and include URL
        requestData.photo_url = 'pending_upload';
      }

      // Send to API
      const response = await api.sendMessage(requestData);
      
      // Remove typing indicator
      this.hideTypingIndicator();

      // Add assistant response
      this.addMessage(response.response || response.message, 'assistant', response.data);

      // Render rich cards if present
      if (response.cards) {
        response.cards.forEach((card) => this.renderRichCard(card));
      }
    } catch (error) {
      this.hideTypingIndicator();
      this.addMessage(`Error: ${error.message}`, 'system');
    }

    this.photoFile = null;
    document.getElementById('photoPreviewContainer').innerHTML = '';
  }

  addMessage(text, type, metadata = null) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = text;

    if (metadata?.photo) {
      const photoNote = document.createElement('div');
      photoNote.style.fontSize = '0.8rem';
      photoNote.style.opacity = '0.7';
      photoNote.style.marginTop = '4px';
      photoNote.textContent = `📷 ${metadata.photo}`;
      messageDiv.appendChild(photoNote);
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Store message
    this.messages.push({ text, type, metadata, timestamp: new Date().toISOString() });
    
    // Cache for offline
    this.cacheMessages();
  }

  showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;

    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = `
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    `;

    messagesContainer.appendChild(indicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
      indicator.remove();
    }
  }

  // ============================================================================
  // RICH CARDS
  // ============================================================================

  renderRichCard(card) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;

    const cardDiv = document.createElement('div');
    cardDiv.className = 'rich-card';
    
    let html = '';
    
    if (card.title) {
      html += `<div class="rich-card-title">${card.title}</div>`;
    }
    
    if (card.content) {
      html += `<div class="rich-card-content">${card.content}</div>`;
    }
    
    if (card.actions && card.actions.length > 0) {
      html += '<div class="rich-card-actions">';
      card.actions.forEach((action) => {
        const className = action.primary ? '' : 'secondary';
        html += `<button class="card-button ${className}" data-action="${action.type}" data-payload='${JSON.stringify(action.payload)}'>${action.label}</button>`;
      });
      html += '</div>';
    }

    cardDiv.innerHTML = html;
    messagesContainer.appendChild(cardDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Setup action handlers
    cardDiv.querySelectorAll('.card-button').forEach((button) => {
      button.addEventListener('click', () => {
        const action = button.dataset.action;
        const payload = JSON.parse(button.dataset.payload);
        this.handleCardAction(action, payload);
      });
    });
  }

  handleCardAction(action, payload) {
    console.log('Card action:', action, payload);
    
    switch (action) {
      case 'view_recipe':
        this.addMessage(`Mostrando receta: ${payload.name}`, 'system');
        break;
      case 'approve_recommendation':
        this.addMessage('✅ Recomendación aprobada', 'system');
        api.logMovement({ type: 'approval', ...payload });
        break;
      case 'reject_recommendation':
        this.addMessage('❌ Recomendación rechazada', 'system');
        break;
      case 'create_order':
        this.addMessage('📦 Creando orden de compra...', 'system');
        api.createPurchaseOrder(payload);
        break;
      default:
        console.warn('Unknown action:', action);
    }
  }

  // ============================================================================
  // CONNECTION STATUS
  // ============================================================================

  async checkConnection() {
    const isOnline = await api.checkConnection();
    this.updateConnectionStatus(isOnline);
  }

  updateConnectionStatus(forceOnline = null) {
    const isOnline = forceOnline !== null ? forceOnline : navigator.onLine;
    const banner = document.getElementById('offlineBanner');
    const indicator = document.getElementById('statusIndicator');

    if (banner) {
      banner.classList.toggle('visible', !isOnline);
    }

    if (indicator) {
      indicator.classList.toggle('offline', !isOnline);
    }
  }

  // ============================================================================
  // CACHE & HISTORY
  // ============================================================================

  async loadChatHistory() {
    try {
      // Try to load from cache first (works offline)
      const cached = localStorage.getItem('jarbis_chat_history');
      if (cached) {
        this.messages = JSON.parse(cached);
        this.messages.forEach((msg) => {
          this.addMessage(msg.text, msg.type, msg.metadata);
        });
      }

      // Then try to fetch from server
      const history = await api.getChatHistory(20);
      if (history && history.messages) {
        // Clear and reload with fresh data
        document.getElementById('chatMessages').innerHTML = '';
        this.messages = [];
        history.messages.forEach((msg) => {
          this.addMessage(msg.text, msg.type, msg.metadata);
        });
      }
    } catch (error) {
      console.log('Using cached history (offline mode)');
    }
  }

  cacheMessages() {
    // Keep only last 10 conversations
    const recentMessages = this.messages.slice(-50);
    localStorage.setItem('jarbis_chat_history', JSON.stringify(recentMessages));
  }

  // ============================================================================
  // MENU
  // ============================================================================

  showMenu() {
    const menuItems = [
      { label: '📊 Dashboard Financiero', action: 'financial' },
      { label: '📦 Inventario', action: 'inventory' },
      { label: '🍳 Recetas', action: 'recipes' },
      { label: '🎉 Eventos', action: 'events' },
      { label: '⚙️ Configuración', action: 'settings' },
      { label: '🚪 Cerrar sesión', action: 'logout' },
    ];

    // Simple alert menu (en producción: usar modal custom)
    const selection = prompt(
      'Selecciona una opción:\n' + menuItems.map((item, i) => `${i + 1}. ${item.label}`).join('\n')
    );

    if (selection) {
      const index = parseInt(selection) - 1;
      if (index >= 0 && index < menuItems.length) {
        this.handleMenuAction(menuItems[index].action);
      }
    }
  }

  handleMenuAction(action) {
    switch (action) {
      case 'financial':
        this.addMessage('Abriendo dashboard financiero...', 'system');
        window.location.href = '/financial';
        break;
      case 'inventory':
        this.addMessage('Mostrando inventario...', 'system');
        window.location.href = '/inventory';
        break;
      case 'recipes':
        this.addMessage('Mostrando recetas...', 'system');
        window.location.href = '/recipes';
        break;
      case 'events':
        this.addMessage('Gestión de eventos...', 'system');
        window.location.href = '/events';
        break;
      case 'settings':
        this.addMessage('Abriendo configuración...', 'system');
        window.location.href = '/settings';
        break;
      case 'logout':
        api.logout();
        window.location.href = '/login';
        break;
      default:
        console.warn('Unknown menu action:', action);
    }
  }
}

export default ChatInterface;
