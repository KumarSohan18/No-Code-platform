# GenAI Stack - Complete Source Code Documentation

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Frontend Structure](#frontend-structure)
4. [Backend Structure](#backend-structure)
5. [Database Schema](#database-schema)
6. [API Documentation](#api-documentation)
7. [Service Layer](#service-layer)
8. [Component Interactions](#component-interactions)
9. [Data Flow](#data-flow)
10. [Configuration](#configuration)
11. [Deployment](#deployment)
12. [Development Guidelines](#development-guidelines)

---

## 🎯 Project Overview

**GenAI Stack** is a No-Code/Low-Code AI Workflow Builder that enables users to create intelligent workflows using drag-and-drop components. The system combines document processing, vector search, and AI language models to provide intelligent responses through a visual interface.

### Key Features
- **Visual Workflow Builder**: Drag-and-drop interface using React Flow
- **AI Integration**: Support for OpenAI GPT and Google Gemini models
- **Document Processing**: PDF, TXT, DOCX, MD file processing with vector search
- **Real-time Chat**: Interactive chat interface with workflow execution
- **Vector Search**: ChromaDB integration for semantic document search
- **Web Search**: SerpAPI integration for real-time information

---

## 🏗️ Architecture Overview

### High-Level Architecture

![Project Architecture](architecture_diagrams/project_architecture.png)
![Document workflow diagram](architecture_diagrams/doc_processing.png)
![Execution workflow](architecture_diagrams/execution.jpg)

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React.js 19, React Flow, Vite | User interface and workflow builder |
| **Backend** | FastAPI, Python 3.11, SQLAlchemy | API server and business logic |
| **Database** | PostgreSQL, ChromaDB | Relational and vector data storage |
| **AI Services** | OpenAI API, Google Gemini API | Language model integration |
| **Document Processing** | PyMuPDF, PyPDF2, python-docx | Text extraction from documents |
| **Deployment** | Docker, Docker Compose | Containerized deployment |

---

## 🎨 Frontend Structure

### Directory Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── WorkflowBuilder.jsx    # Main workflow builder
│   │   ├── WorkflowBuilder.css    # Workflow builder styles
│   │   ├── ChatInterface.jsx      # Chat interface component
│   │   └── ChatInterface.css      # Chat interface styles
│   ├── services/             # API service layer
│   │   └── api.js           # Centralized API client
│   ├── App.jsx              # Main application component
│   ├── App.css              # Global styles
│   ├── main.jsx             # Application entry point
│   └── index.css            # Base styles
├── public/                  # Static assets
├── package.json             # Dependencies and scripts
├── vite.config.js          # Vite configuration
└── env.example             # Environment variables template
```

### Key Components

#### 1. WorkflowBuilder.jsx
**Purpose**: Main component for visual workflow creation and management

**Key Features**:
- React Flow integration for drag-and-drop functionality
- Component library with 4 core node types
- Real-time validation and connection management
- Save/load workflow functionality
- Zoom and grid controls

**Component Structure**:
```javascript
// Node Types
const componentTypes = {
  input: { /* User Query Component */ },
  llm: { /* LLM Engine Component */ },
  knowledge: { /* Knowledge Base Component */ },
  output: { /* Output Component */ }
}

// Custom Node Components
const InputNode = ({ data, selected, onDelete }) => { /* ... */ }
const LLMNode = ({ data, selected, onDelete }) => { /* ... */ }
const KnowledgeNode = ({ data, selected, onDelete }) => { /* ... */ }
const OutputNode = ({ data, selected, onDelete }) => { /* ... */ }
```

**State Management**:
- `nodes`: React Flow nodes state
- `edges`: React Flow edges state
- `selectedNode`: Currently selected node
- `reactFlowInstance`: React Flow instance reference
- `zoomLevel`: Current zoom level
- `showChat`: Chat interface visibility

#### 2. ChatInterface.jsx
**Purpose**: Real-time chat interface for workflow interaction

**Key Features**:
- Session management
- Message history
- Real-time execution logs
- Error handling and loading states

**State Management**:
- `sessionId`: Current chat session ID
- `messages`: Chat message history
- `inputMessage`: Current input text
- `loading`: Loading state for API calls
- `error`: Error state management

#### 3. api.js (Service Layer)
**Purpose**: Centralized API communication layer

**Key Methods**:
```javascript
class ApiService {
  // Health endpoints
  async healthCheck()
  async detailedHealthCheck()
  
  // Workflow endpoints
  async createWorkflow(workflowData)
  async getWorkflows()
  async updateWorkflow(workflowId, workflowData)
  async validateWorkflow(workflowId)
  async deleteWorkflow(workflowId)
  
  // Chat endpoints
  async createChatSession(workflowId)
  async sendMessage(sessionId, message)
  async getChatMessages(sessionId)
  
  // Document endpoints
  async uploadDocument(file, collection)
  async processDocument(documentId, collection)
  async searchDocuments(query, collection, topK, threshold)
}
```

---

## ⚙️ Backend Structure

### Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes/          # API route handlers
│   │       ├── workflows.py     # Workflow management endpoints
│   │       ├── chat.py          # Chat interface endpoints
│   │       ├── documents.py     # Document management endpoints
│   │       └── health.py        # Health check endpoints
│   ├── core/
│   │   ├── config.py            # Application configuration
│   │   └── database.py          # Database models and connection
│   ├── schemas/
│   │   ├── workflow.py          # Workflow Pydantic models
│   │   ├── chat.py              # Chat Pydantic models
│   │   └── document.py          # Document Pydantic models
│   └── services/
│       ├── workflow_executor.py # Workflow execution engine
│       ├── llm_service.py       # LLM integration service
│       ├── vector_service.py    # Vector database service
│       └── document_service.py  # Document processing service
├── uploads/                 # File upload directory
├── chroma_db/              # ChromaDB storage
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
└── env.example            # Environment variables template
```

### Key Components

#### 1. main.py
**Purpose**: FastAPI application entry point and configuration

**Key Features**:
- Application lifecycle management
- CORS middleware configuration
- Route registration
- Service initialization

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    app.state.workflow_executor = WorkflowExecutor()
    app.state.llm_service = LLMService()
    app.state.vector_service = VectorService()
    app.state.document_service = DocumentService()
    yield
    # Shutdown
```

#### 2. Core Configuration (config.py)
**Purpose**: Centralized application configuration

**Key Settings**:
```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    
    # File Handling
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".txt", ".docx", ".md"]
    UPLOAD_DIRECTORY: str = "./uploads"
    
    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "documents"
```

#### 3. Database Models (database.py)
**Purpose**: SQLAlchemy models for data persistence

**Key Models**:
```python
class Workflow(Base):
    """Workflow model"""
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    nodes = Column(JSON, nullable=False)  # React Flow nodes
    edges = Column(JSON, nullable=False)  # React Flow edges
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatSession(Base):
    """Chat session model"""
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessage(Base):
    """Chat message model"""
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message_type = Column(String(50), nullable=False)  # 'user' or 'ai'
    content = Column(Text, nullable=False)
    meta_data = Column(JSON)  # Additional data like execution logs
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Document(Base):
    """Document model"""
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content = Column(Text)  # Extracted text content
    meta_data = Column(JSON)  # Additional metadata
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

## 🗄️ Database Schema

### PostgreSQL Tables

#### 1. workflows
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique workflow identifier |
| name | VARCHAR(255) | Workflow name |
| description | TEXT | Workflow description |
| nodes | JSON | React Flow node definitions |
| edges | JSON | React Flow edge definitions |
| is_active | BOOLEAN | Workflow activation status |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

#### 2. chat_sessions
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique session identifier |
| workflow_id | INTEGER | Foreign key to workflows |
| session_id | VARCHAR(255) | Unique session UUID |
| created_at | TIMESTAMP | Session creation time |
| updated_at | TIMESTAMP | Last activity time |

#### 3. chat_messages
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique message identifier |
| session_id | INTEGER | Foreign key to chat_sessions |
| message_type | VARCHAR(50) | 'user' or 'ai' |
| content | TEXT | Message content |
| meta_data | JSON | Execution logs and metadata |
| created_at | TIMESTAMP | Message timestamp |

#### 4. documents
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique document identifier |
| filename | VARCHAR(255) | Original filename |
| file_path | VARCHAR(500) | File storage path |
| content | TEXT | Extracted text content |
| meta_data | JSON | Document metadata |
| is_processed | BOOLEAN | Processing status |
| created_at | TIMESTAMP | Upload timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### ChromaDB Collections

#### documents
- **Purpose**: Vector storage for document embeddings
- **Structure**: 
  - Document chunks with embeddings
  - Metadata including source document ID
  - Collection-based organization
- **Operations**: Similarity search, embedding storage, index management

---

## 🔌 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
Currently, the API uses environment-based API keys for external services. Future versions will implement JWT-based authentication.

### Endpoints

#### 1. Health Endpoints

##### GET /health
**Purpose**: Basic health check
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

##### GET /health/detailed
**Purpose**: Detailed health check with database status
**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "services": {
    "openai": "available",
    "chromadb": "connected"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 2. Workflow Endpoints

##### GET /workflows
**Purpose**: List all workflows
**Response**:
```json
[
  {
    "id": 1,
    "name": "My Workflow",
    "description": "Sample workflow",
    "nodes": [...],
    "edges": [...],
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

##### POST /workflows
**Purpose**: Create a new workflow
**Request Body**:
```json
{
  "name": "New Workflow",
  "description": "Workflow description",
  "nodes": [...],
  "edges": [...]
}
```

##### GET /workflows/{id}
**Purpose**: Get specific workflow
**Response**:
```json
{
  "id": 1,
  "name": "My Workflow",
  "description": "Sample workflow",
  "nodes": [...],
  "edges": [...],
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

##### PUT /workflows/{id}
**Purpose**: Update existing workflow
**Request Body**: Same as POST /workflows

##### DELETE /workflows/{id}
**Purpose**: Delete workflow
**Response**: 204 No Content

##### POST /workflows/{id}/validate
**Purpose**: Validate workflow structure
**Response**:
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "execution_order": ["input-1", "llm-1", "output-1"]
}
```

#### 3. Chat Endpoints

##### POST /chat/sessions
**Purpose**: Create new chat session
**Request Body**:
```json
{
  "workflow_id": 1
}
```
**Response**:
```json
{
  "id": 1,
  "workflow_id": 1,
  "session_id": "uuid-string",
  "created_at": "2024-01-01T00:00:00Z"
}
```

##### POST /chat/sessions/{session_id}/messages
**Purpose**: Send message to chat session
**Request Body**:
```json
{
  "message": "Hello, how can you help me?"
}
```
**Response**:
```json
{
  "id": 1,
  "session_id": 1,
  "message_type": "ai",
  "content": "I can help you with...",
  "meta_data": {
    "execution_log": [...],
    "execution_time": 1250
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

##### GET /chat/sessions/{session_id}/messages
**Purpose**: Get chat message history
**Response**:
```json
[
  {
    "id": 1,
    "session_id": 1,
    "message_type": "user",
    "content": "Hello",
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "session_id": 1,
    "message_type": "ai",
    "content": "Hi there!",
    "created_at": "2024-01-01T00:00:01Z"
  }
]
```

#### 4. Document Endpoints

##### POST /documents/upload
**Purpose**: Upload document for processing
**Request**: Multipart form data
- `file`: Document file
- `collection`: Collection name (optional)

**Response**:
```json
{
  "id": 1,
  "filename": "document.pdf",
  "status": "uploaded",
  "message": "Document uploaded successfully"
}
```

##### POST /documents/{id}/process
**Purpose**: Process uploaded document
**Response**:
```json
{
  "id": 1,
  "status": "processed",
  "chunks_created": 15,
  "embeddings_generated": 15
}
```

##### GET /documents
**Purpose**: List documents
**Query Parameters**:
- `page`: Page number (default: 1)
- `size`: Page size (default: 10)
- `processed_only`: Filter processed documents (default: false)

##### POST /documents/search
**Purpose**: Search documents using vector similarity
**Request Body**:
```json
{
  "query": "machine learning",
  "collection": "default",
  "top_k": 5,
  "threshold": 0.7
}
```
**Response**:
```json
{
  "results": [
    {
      "id": 1,
      "content": "Machine learning is...",
      "similarity": 0.95,
      "metadata": {...}
    }
  ],
  "total_results": 5
}
```

---

## 🔧 Service Layer

### 1. WorkflowExecutor
**Purpose**: Core workflow execution engine

**Key Methods**:
```python
class WorkflowExecutor:
    async def validate_workflow(self, nodes, edges) -> WorkflowValidation
    async def execute_workflow(self, workflow_id, input_data) -> Dict[str, Any]
    def _determine_execution_order(self, nodes, edges) -> List[str]
    async def _execute_component(self, node, context) -> Dict[str, Any]
```

**Component Execution**:
- **Input Component**: Extracts user query
- **Knowledge Base Component**: Performs vector search
- **LLM Engine Component**: Generates AI response
- **Output Component**: Formats final result

### 2. LLMService
**Purpose**: Language model integration service

**Key Methods**:
```python
class LLMService:
    async def generate_response(self, query, context, model, use_web_search) -> str
    async def _call_openai(self, prompt, model) -> str
    async def _call_gemini(self, prompt, model) -> str
    async def _web_search(self, query) -> str
```

**Supported Models**:
- OpenAI: GPT-5-nano-2025-08-07
- Google: Gemini-2.5-pro

### 3. VectorService
**Purpose**: ChromaDB vector database service

**Key Methods**:
```python
class VectorService:
    async def search(self, query, collection, top_k, threshold) -> List[Dict]
    async def add_documents(self, documents, collection) -> bool
    async def create_collection(self, name) -> bool
    async def get_collections(self) -> List[str]
```

### 4. DocumentService
**Purpose**: Document processing and management

**Key Methods**:
```python
class DocumentService:
    async def upload_document(self, file, collection) -> Dict[str, Any]
    async def process_document(self, document_id, collection) -> Dict[str, Any]
    async def extract_text(self, file_path) -> str
    async def create_chunks(self, text, chunk_size) -> List[str]
```

**Supported Formats**:
- PDF (PyMuPDF, PyPDF2)
- TXT (Plain text)
- DOCX (python-docx)
- MD (Markdown)

---

## 🔄 Component Interactions

### Workflow Creation Flow

```
User Interface → React Flow → API Service → Backend Validation → Database Storage
```

1. **User drags components** from library to canvas
2. **User connects components** by drawing edges
3. **User configures components** (API keys, models, parameters)
4. **User clicks Save** → Frontend sends workflow data to API
5. **Backend validates** workflow structure and configuration
6. **Database stores** workflow definition
7. **Frontend updates** UI with saved workflow

### Workflow Execution Flow

```
User Query → Chat Interface → Workflow Executor → Component Processing → AI Response
```

1. **User types message** in chat interface
2. **Frontend sends message** to chat API endpoint
3. **Backend creates/updates** chat session
4. **Workflow Executor** processes workflow components in order
5. **Each component** processes data and passes to next component
6. **LLM Engine** generates AI response
7. **Response returned** to frontend and displayed

### Document Processing Flow

```
File Upload → Text Extraction → Chunking → Embedding → Vector Storage
```

1. **User uploads document** via file input
2. **Backend receives file** and stores in uploads directory
3. **Text extraction** using appropriate library (PyMuPDF, etc.)
4. **Text chunking** into manageable pieces
5. **Embedding generation** using OpenAI API
6. **Vector storage** in ChromaDB with metadata
7. **Database update** marking document as processed

---

## 📊 Data Flow

### 1. User Interaction Data Flow

```
User Input → Frontend State → API Call → Backend Processing → Database → Response → UI Update
```

### 2. Workflow Execution Data Flow

```
User Query → Input Component → Knowledge Base → LLM Engine → Output Component → Chat Response
```

### 3. Document Processing Data Flow

```
File Upload → Document Service → Text Extraction → Chunking → Embedding → ChromaDB → Database Update
```

### 4. Vector Search Data Flow

```
User Query → Embedding Generation → ChromaDB Search → Similarity Results → Context Building → LLM Processing
```

---

## ⚙️ Configuration

### Environment Variables

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/genai_stack

# AI Services
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here

# File Handling
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIRECTORY=./uploads
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Security
SECRET_KEY=your_secret_key_here
```

#### Frontend (.env.local)
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Docker Configuration

#### docker-compose.yml
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/genai_stack
    depends_on:
      - postgres
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/chroma_db:/app/chroma_db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1
    depends_on:
      - backend

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=genai_stack
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

---

## 🚀 Deployment

### Development Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env
# Edit .env with your API keys
python main.py
```

#### Frontend
```bash
cd frontend
npm install
cp env.example .env.local
# Edit .env.local with backend URL
npm run dev
```

### Production Deployment

#### Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Manual Deployment
1. **Backend**: Deploy FastAPI application with Gunicorn
2. **Frontend**: Build React app and serve with Nginx
3. **Database**: Set up PostgreSQL with proper configuration
4. **Vector DB**: Configure ChromaDB with persistent storage
5. **Reverse Proxy**: Configure Nginx for load balancing

---

## 📝 Development Guidelines

### Code Style

#### Python (Backend)
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Document all public methods with docstrings
- Use async/await for I/O operations
- Implement proper error handling with try/catch blocks

#### JavaScript (Frontend)
- Use ES6+ features
- Follow React best practices
- Use functional components with hooks
- Implement proper error boundaries
- Use consistent naming conventions (camelCase)


### Error Handling

#### Backend Error Handling
- Use HTTPException for API errors
- Log all errors with appropriate levels
- Return consistent error response format
- Implement graceful degradation

#### Frontend Error Handling
- Use try/catch blocks for API calls
- Implement error boundaries for React components
- Show user-friendly error messages
- Implement retry mechanisms for failed requests

### Security Considerations

1. **API Keys**: Store in environment variables, never in code
2. **File Uploads**: Validate file types and sizes
3. **CORS**: Configure appropriate origins
4. **Input Validation**: Validate all user inputs
5. **Rate Limiting**: Implement API rate limiting
6. **HTTPS**: Use SSL/TLS in production

### Performance Optimization

1. **Database**: Use connection pooling and indexing
2. **Caching**: Implement Redis caching for frequent queries
3. **Vector Search**: Optimize ChromaDB configuration
4. **Frontend**: Use React.memo and useMemo for optimization
5. **API**: Implement request/response compression

---




This documentation provides a comprehensive overview of the GenAI Stack codebase structure, helping developers understand the architecture, components, and their interactions for effective development and maintenance.
