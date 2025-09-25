import React, { useState, useCallback, useRef, useMemo, useEffect } from 'react'
import ReactFlow, {
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  ReactFlowProvider,
  Handle,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import ApiService from '../services/api'
import ChatInterface from './ChatInterface'
import './WorkflowBuilder.css'

// Component definitions
const componentTypes = {
  input: {
    id: 'input',
    type: 'input',
    label: 'Input',
    icon: '→',
    description: 'User Query Component',
    defaultData: {
      label: 'User Query',
      placeholder: 'Enter your query...',
      required: true
    }
  },
  llm: {
    id: 'llm',
    type: 'llm',
    label: 'LLM Engine',
    icon: '✨',
    description: 'LLM Engine Component',
    defaultData: {
      label: 'LLM Engine',
      model: 'gpt-5-nano-2025-08-07',
      maxTokens: 1000,
      apiKey: '',
      useDefaultKey: true,
      use_web_search: false
    }
  },
  knowledge: {
    id: 'knowledge',
    type: 'knowledge',
    label: 'Knowledge Base',
    icon: '📚',
    description: 'Knowledge Base Component',
    defaultData: {
      label: 'Knowledge Base',
      collection: 'default',
      topK: 5,
      threshold: 0.7,
      uploadedFiles: [],
      embeddingModel: 'text-embedding-ada-002'
    }
  },
  output: {
    id: 'output',
    type: 'output',
    label: 'Output',
    icon: '→',
    description: 'Output Component',
    defaultData: {
      label: 'Output',
      format: 'text',
      streaming: true
    }
  }
}

// Custom node components
const InputNode = ({ data, selected, onDelete }) => (
  <div className={`custom-node input-node ${selected ? 'selected' : ''}`}>
    <div className="node-header">
      <span className="node-icon">⚙️</span>
      <span className="node-label">{data.label}</span>
      {selected && (
        <button 
          className="node-delete-btn"
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          title="Delete Component"
        >
          ×
        </button>
      )}
    </div>
    <div className="node-description">
      Enter point for querys
    </div>
    <div className="node-content">
      <div className="input-field">
        <label>User Query</label>
        <input 
          type="text" 
          placeholder="Write your query here" 
          className="node-input"
          readOnly
        />
      </div>
    </div>
    
    {/* React Flow Handles for all edges */}
    <Handle
      type="source"
      position={Position.Top}
      id="query-top"
      style={{ background: '#f59e0b', width: 16, height: 16 }}
    />
    <Handle
      type="source"
      position={Position.Right}
      id="query-right"
      style={{ background: '#f59e0b', width: 16, height: 16 }}
    />
    <Handle
      type="source"
      position={Position.Bottom}
      id="query-bottom"
      style={{ background: '#f59e0b', width: 16, height: 16 }}
    />
    <Handle
      type="source"
      position={Position.Left}
      id="query-left"
      style={{ background: '#f59e0b', width: 16, height: 16 }}
    />
  </div>
)

const LLMNode = ({ data, selected, onDelete, onDataChange }) => (
  <div className={`custom-node llm-node ${selected ? 'selected' : ''}`}>
    <div className="node-header">
      <span className="node-icon">⚙️</span>
      <span className="node-label">{data.label}</span>
      {selected && (
        <button 
          className="node-delete-btn"
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          title="Delete Component"
        >
          ×
        </button>
      )}
    </div>
    <div className="node-description">
      Run a query with OpenAI LLM
    </div>
    <div className="node-content">
      <div className="config-row">
        <label>Model</label>
        <select className="config-select">
          <option>GPT-5-nano</option>
          <option>Gemini-2.5-pro</option>
        </select>
      </div>
      <div className="config-row">
        <label>API Key</label>
        <div className="api-key-field">
          <input type="password" placeholder="Enter API key or use default" />
          <span className="eye-icon">👁️</span>
        </div>
      </div>
      <div className="config-row">
        <label>SERP API Key</label>
        <div className="api-key-field">
          <input type="password" placeholder="Enter SERP API key or use default" />
          <span className="eye-icon">👁️</span>
        </div>
      </div>
      <div className="config-row">
        <label>Prompt</label>
        <textarea 
          className="prompt-textarea"
          value="You are a helpful PDF assistant. Use web search if the PDF lacks context"
          readOnly
        />
      </div>
      <div className="config-row">
        <label>WebSearch Tool</label>
        <div 
          className={`toggle-switch ${data.use_web_search ? 'active' : ''}`}
          onClick={() => onDataChange && onDataChange({ use_web_search: !data.use_web_search })}
        >
          <div className="toggle-slider"></div>
        </div>
      </div>
      <div className="config-row">
        <label>SERF API</label>
        <div className="api-key-field">
          <input type="password" value="************" readOnly />
          <span className="eye-icon">👁️</span>
        </div>
      </div>
    </div>
    
    {/* React Flow Handles for all edges */}
    <Handle
      type="target"
      position={Position.Top}
      id="llm-top"
      style={{ background: '#8b5cf6', width: 16, height: 16 }}
    />
    <Handle
      type="target"
      position={Position.Right}
      id="llm-right"
      style={{ background: '#8b5cf6', width: 16, height: 16 }}
    />
    <Handle
      type="target"
      position={Position.Bottom}
      id="llm-bottom"
      style={{ background: '#8b5cf6', width: 16, height: 16 }}
    />
    <Handle
      type="target"
      position={Position.Left}
      id="llm-left"
      style={{ background: '#8b5cf6', width: 16, height: 16 }}
    />
    
    {/* Output handles */}
    <Handle
      type="source"
      position={Position.Top}
      id="output-top"
      style={{ background: '#8b5cf6', width: 16, height: 16 }}
    />
    <Handle
      type="source"
      position={Position.Right}
      id="output-right"
      style={{ background: '#8b5cf6', width: 16, height: 16 }}
    />
    <Handle
      type="source"
      position={Position.Bottom}
      id="output-bottom"
      style={{ background: '#8b5cf6', width: 16, height: 16 }}
    />
    <Handle
      type="source"
      position={Position.Left}
      id="output-left"
      style={{ background: '#8b5cf6', width: 16, height: 16 }}
    />
  </div>
)

const KnowledgeNode = ({ data, selected, onDelete }) => {
  const [uploading, setUploading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState(data.uploadedFiles || [])
  const fileInputRef = useRef(null)
  
  console.log('KnowledgeNode rendered with data:', data)

  const handleFileUpload = async (event) => {
    console.log('handleFileUpload called with event:', event);
    const files = event.target.files
    console.log('Files from event:', files);
    if (!files || files.length === 0) {
      console.log('No files selected, returning');
      return;
    }

    console.log('Starting file upload:', files.length, 'files')
    setUploading(true)
    try {
      for (const file of files) {
        console.log('Uploading file:', file.name, 'to collection:', data.collection || 'default')
        const result = await ApiService.uploadDocument(file, data.collection || 'default')
        console.log('Upload result:', result)
        
        setUploadedFiles(prev => [...prev, {
          id: result.id,
          filename: result.filename,
          status: 'uploaded'
        }])
        
        console.log('Processing document:', result.id)
        // Process the document after upload
        const processResult = await ApiService.processDocument(result.id, data.collection || 'default')
        console.log('Process result:', processResult)
        
        setUploadedFiles(prev => prev.map(f => 
          f.id === result.id ? { ...f, status: 'processed' } : f
        ))
        console.log('Document processed successfully:', result.filename)
      }
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed: ' + error.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className={`custom-node knowledge-node ${selected ? 'selected' : ''}`}>
      <div className="node-header">
        <span className="node-icon">⚙️</span>
        <span className="node-label">{data.label}</span>
        {selected && (
          <button 
            className="node-delete-btn"
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
            title="Delete Component"
          >
            ×
          </button>
        )}
      </div>
      <div className="node-description">
        Let LLM search info in your file
      </div>
      <div className="node-content">
        <div className="config-row">
          <label>Upload Documents</label>
          
          
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.txt,.doc,.docx,.md"
            onChange={(e) => {
              console.log('REF-BASED File input changed:', e.target.files);
              if (e.target.files.length > 0) {
                console.log('REF-BASED File selected:', e.target.files[0]);
                handleFileUpload(e);
              }
            }}
            onClick={(e) => e.stopPropagation()}
            onMouseDown={(e) => e.stopPropagation()}
            style={{ display: 'block', margin: '10px 0' }}
          />
          <button 
            className="upload-btn"
            onClick={(e) => {
              e.stopPropagation();
              console.log('Upload button clicked, opening file dialog');
              if (fileInputRef.current) {
                console.log('Using ref to click file input');
                fileInputRef.current.click();
              } else {
                console.error('File input ref not found!');
              }
            }}
            disabled={uploading}
          >
            <span className="upload-icon">📁</span>
            {uploading ? 'Uploading...' : 'Upload Documents'}
          </button>
          <div className="uploaded-files">
            <small>Uploaded: {uploadedFiles.length} files</small>
            {uploadedFiles.length > 0 && (
              <div className="file-list">
                {uploadedFiles.map(file => (
                  <div key={file.id} className="file-item">
                    <span className="file-name">{file.filename}</span>
                    <span className={`file-status ${file.status}`}>
                      {file.status === 'uploaded' ? '⏳' : '✅'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="config-row">
          <label>Embedding Model</label>
          <select className="config-select">
            <option>text-embedding-ada-002</option>
          </select>
        </div>
        <div className="config-row">
          <label>Collection: {data.collection || 'default'}</label>
          <div className="collection-info">
            <small>Documents will be processed and stored in vector database</small>
          </div>
        </div>
      </div>
    
      {/* React Flow Handles for all edges */}
      <Handle
        type="target"
        position={Position.Top}
        id="kb-top"
        style={{ background: '#8b5cf6', width: 16, height: 16 }}
      />
      <Handle
        type="target"
        position={Position.Right}
        id="kb-right"
        style={{ background: '#8b5cf6', width: 16, height: 16 }}
      />
      <Handle
        type="target"
        position={Position.Bottom}
        id="kb-bottom"
        style={{ background: '#8b5cf6', width: 16, height: 16 }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="kb-left"
        style={{ background: '#8b5cf6', width: 16, height: 16 }}
      />
    </div>
  )
}

const OutputNode = ({ data, selected, onDelete }) => (
  <div className={`custom-node output-node ${selected ? 'selected' : ''}`}>
    <div className="node-header">
      <span className="node-icon">⚙️</span>
      <span className="node-label">{data.label}</span>
      {selected && (
        <button 
          className="node-delete-btn"
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          title="Delete Component"
        >
          ×
        </button>
      )}
    </div>
    <div className="node-description">
      Output of the result nodes as text
    </div>
    <div className="node-content">
      <div className="input-field">
        <label>Output Text</label>
        <textarea 
          className="output-textarea"
          placeholder="Output will be generated based on query"
          readOnly
        />
      </div>
    </div>
    
    {/* React Flow Handles for all edges */}
    <Handle
      type="target"
      position={Position.Top}
      id="output-top"
      style={{ background: '#10b981', width: 16, height: 16 }}
    />
    <Handle
      type="target"
      position={Position.Right}
      id="output-right"
      style={{ background: '#10b981', width: 16, height: 16 }}
    />
    <Handle
      type="target"
      position={Position.Bottom}
      id="output-bottom"
      style={{ background: '#10b981', width: 16, height: 16 }}
    />
    <Handle
      type="target"
      position={Position.Left}
      id="output-left"
      style={{ background: '#10b981', width: 16, height: 16 }}
    />
  </div>
)

function WorkflowBuilder({ onBack, stack, onWorkflowUpdate }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const [zoomLevel, setZoomLevel] = useState(100)
  const [snapToGrid, setSnapToGrid] = useState(true)
  const [showChat, setShowChat] = useState(false)
  const [chatWorkflowId, setChatWorkflowId] = useState(null)
  const reactFlowWrapper = useRef(null)

  // Load workflow data when component mounts
  useEffect(() => {
    if (stack?.nodes && stack?.edges) {
      setNodes(stack.nodes)
      setEdges(stack.edges)
    }
  }, [stack, setNodes, setEdges])

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const onDragOver = useCallback((event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event) => {
      event.preventDefault()

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect()
      const type = event.dataTransfer.getData('application/reactflow')

      if (typeof type === 'undefined' || !type) {
        return
      }

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      })

      const newNode = {
        id: `${type}-${Date.now()}`,
        type,
        position,
        data: { ...componentTypes[type].defaultData },
      }

      setNodes((nds) => nds.concat(newNode))
    },
    [reactFlowInstance, setNodes]
  )

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const onDeleteNode = useCallback(() => {
    console.log('Delete button clicked, selectedNode:', selectedNode)
    if (selectedNode) {
      console.log('Deleting node:', selectedNode.id)
      setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id))
      setEdges((eds) => eds.filter((edge) => 
        edge.source !== selectedNode.id && edge.target !== selectedNode.id
      ))
      setSelectedNode(null)
    }
  }, [selectedNode, setNodes, setEdges])

  const updateNodeData = useCallback((nodeId, newData) => {
    setNodes((nds) => 
      nds.map((node) => 
        node.id === nodeId 
          ? { ...node, data: { ...node.data, ...newData } }
          : node
      )
    )
  }, [setNodes])

  // Create node types with delete functionality
  const nodeTypes = useMemo(() => ({
    input: (props) => <InputNode {...props} onDelete={onDeleteNode} />,
    llm: (props) => <LLMNode {...props} onDelete={onDeleteNode} onDataChange={(newData) => updateNodeData(props.id, newData)} />,
    knowledge: (props) => <KnowledgeNode {...props} onDelete={onDeleteNode} />,
    output: (props) => <OutputNode {...props} onDelete={onDeleteNode} />,
  }), [onDeleteNode, updateNodeData])

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
    
    // Create a custom drag image to replace the black box
    const dragImage = document.createElement('div')
    dragImage.style.cssText = `
      position: absolute;
      top: -1000px;
      left: -1000px;
      width: 200px;
      height: 100px;
      background: white;
      border: 2px solid #10b981;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 500;
      color: #10b981;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      z-index: 1000;
    `
    dragImage.textContent = componentTypes[nodeType].label
    
    document.body.appendChild(dragImage)
    event.dataTransfer.setDragImage(dragImage, 100, 50)
    
    // Clean up the drag image after a short delay
    setTimeout(() => {
      if (document.body.contains(dragImage)) {
        document.body.removeChild(dragImage)
      }
    }, 0)
  }

  const handleSave = async () => {
    console.log('Saving workflow:', { stack, nodes, edges })
    
    if (!stack) {
      alert('No workflow selected to save')
      return
    }

    try {
      const workflowData = {
        name: stack.name || 'Untitled Workflow',
        description: stack.description || '',
        nodes: nodes,
        edges: edges
      }
      
      let savedWorkflow
      if (stack.id) {
        // Update existing workflow
        savedWorkflow = await ApiService.updateWorkflow(stack.id, workflowData)
        console.log('Updated existing workflow:', savedWorkflow)
      } else {
        // Create new workflow
        savedWorkflow = await ApiService.createWorkflow(workflowData)
        console.log('Created new workflow:', savedWorkflow)
        
        // Update the stack with the new ID
        if (savedWorkflow.id && onWorkflowUpdate) {
          // Update the parent component with the new workflow ID
          onWorkflowUpdate(savedWorkflow)
          console.log('New workflow created with ID:', savedWorkflow.id)
        }
      }
      
      alert('Workflow saved successfully!')
    } catch (error) {
      console.error('Failed to save workflow:', error)
      alert('Failed to save workflow: ' + error.message)
    }
  }

  const handleValidateWorkflow = async () => {
    console.log('Validating workflow:', { stack, nodes, edges })
    
    // Check if workflow has any components
    if (nodes.length === 0) {
      alert('❌ Workflow validation failed: No components added to the workflow')
      return
    }

    try {
      let workflowId = stack?.id
      
      // If no ID, save the workflow first
      if (!workflowId) {
        const workflowData = {
          name: stack?.name || 'Untitled Workflow',
          description: stack?.description || '',
          nodes: nodes,
          edges: edges
        }
        
        const savedWorkflow = await ApiService.createWorkflow(workflowData)
        workflowId = savedWorkflow.id
        
        // Update parent component
        if (onWorkflowUpdate) {
          onWorkflowUpdate(savedWorkflow)
        }
      }

      const validation = await ApiService.validateWorkflow(workflowId)
      if (validation.is_valid) {
        alert('✅ Workflow is valid and ready to execute!')
      } else {
        alert('❌ Workflow validation failed:\n' + validation.errors.join('\n'))
      }
    } catch (error) {
      console.error('Failed to validate workflow:', error)
      alert('Failed to validate workflow: ' + error.message)
    }
  }

  const handleBuildStack = async () => {
    console.log('Building stack:', { stack, nodes, edges })
    
    // Check if workflow has any components
    if (nodes.length === 0) {
      alert('❌ Cannot build stack - No components added to the workflow')
      return
    }

    try {
      let workflowId = stack?.id
      
      // If no ID, save the workflow first
      if (!workflowId) {
        const workflowData = {
          name: stack?.name || 'Untitled Workflow',
          description: stack?.description || '',
          nodes: nodes,
          edges: edges
        }
        
        const savedWorkflow = await ApiService.createWorkflow(workflowData)
        workflowId = savedWorkflow.id
        
        // Update parent component
        if (onWorkflowUpdate) {
          onWorkflowUpdate(savedWorkflow)
        }
      }

      // First validate the workflow
      const validation = await ApiService.validateWorkflow(workflowId)
      if (!validation.is_valid) {
        alert('❌ Cannot build stack - workflow validation failed:\n' + validation.errors.join('\n'))
        return
      }

      // If validation passes, mark workflow as active/ready
      const workflowData = {
        name: stack?.name || 'Untitled Workflow',
        description: stack?.description || '',
        nodes: nodes,
        edges: edges,
        is_active: true
      }
      
      await ApiService.updateWorkflow(workflowId, workflowData)
      alert('✅ Stack built successfully! Workflow is now ready for execution.')
    } catch (error) {
      console.error('Failed to build stack:', error)
      alert('Failed to build stack: ' + error.message)
    }
  }


  const handleChat = async () => {
    console.log('Opening chat for workflow:', { stack, nodes, edges })
    
    // Check if workflow has any components
    if (nodes.length === 0) {
      alert('❌ Cannot start chat - No components added to the workflow')
      return
    }

    try {
      let workflowId = stack?.id
      
      // If no ID, save the workflow first
      if (!workflowId) {
        const workflowData = {
          name: stack?.name || 'Untitled Workflow',
          description: stack?.description || '',
          nodes: nodes,
          edges: edges
        }
        
        const savedWorkflow = await ApiService.createWorkflow(workflowData)
        workflowId = savedWorkflow.id
        
        // Update parent component with the new workflow data
        if (onWorkflowUpdate) {
          onWorkflowUpdate(savedWorkflow)
        }
        
        // Update the workflowId for the chat session
        workflowId = savedWorkflow.id
      }

      // Set the workflow ID for chat and open chat
      setChatWorkflowId(workflowId)
      setShowChat(true)
    } catch (error) {
      console.error('Failed to prepare workflow for chat:', error)
      alert('Failed to prepare workflow for chat: ' + error.message)
    }
  }

  const handleZoomIn = () => {
    if (reactFlowInstance) {
      reactFlowInstance.zoomIn()
      setZoomLevel(Math.round(reactFlowInstance.getZoom() * 100))
    }
  }

  const handleZoomOut = () => {
    if (reactFlowInstance) {
      reactFlowInstance.zoomOut()
      setZoomLevel(Math.round(reactFlowInstance.getZoom() * 100))
    }
  }

  const handleFitView = () => {
    if (reactFlowInstance) {
      reactFlowInstance.fitView()
      setZoomLevel(Math.round(reactFlowInstance.getZoom() * 100))
    }
  }

  const handleZoomChange = (event) => {
    const newZoom = parseInt(event.target.value)
    if (reactFlowInstance) {
      reactFlowInstance.setZoom(newZoom / 100)
      setZoomLevel(newZoom)
    }
  }

  const toggleSnapToGrid = () => {
    setSnapToGrid(!snapToGrid)
  }

  return (
    <div className="workflow-builder">
      {/* Header */}
      <header className="workflow-header">
        <div className="header-content">
          <div className="logo-section">
            <button className="back-btn" onClick={onBack}>
              ←
            </button>
            <span className="brand-name">
              {stack ? stack.name : 'GenAI Stack'}
            </span>
          </div>
          <div className="header-actions">
            <button className="validate-btn" onClick={handleValidateWorkflow}>
              <span className="validate-icon">✅</span>
              Validate
            </button>
            <button className="save-btn" onClick={handleSave}>
              <span className="save-icon">💾</span>
              Save
            </button>
          </div>
        </div>
      </header>

      <div className="workflow-content">
        {/* Left Sidebar - Components */}
        <div className="components-panel">
          <div className="panel-header">
            <h3 className="panel-title">
              <span className="title-icon">📄</span>
              Chat With AI
            </h3>
          </div>
          
          <div className="components-section">
            <h4 className="section-title">Components</h4>
            <div className="components-list">
              {Object.values(componentTypes).map((component) => (
                <div
                  key={component.id}
                  className="component-item"
                  draggable
                  onDragStart={(event) => onDragStart(event, component.id)}
                >
                  <div className="component-icon">{component.icon}</div>
                  <div className="component-info">
                    <span className="component-label">{component.label}</span>
                    <span className="component-description">{component.description}</span>
                  </div>
                  <div className="drag-handle">⋮⋮</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Canvas */}
        <div className="canvas-container">
          <div className="reactflow-wrapper" ref={reactFlowWrapper}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onInit={setReactFlowInstance}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              onMove={(event, viewport) => setZoomLevel(Math.round(viewport.zoom * 100))}
              nodeTypes={nodeTypes}
              fitView
              snapToGrid={snapToGrid}
              snapGrid={[20, 20]}
              attributionPosition="bottom-left"
            >
              <Background variant="dots" gap={20} size={1} />
              
              {/* Welcome message for empty workflows */}
              {nodes.length === 0 && (
                <div className="welcome-overlay">
                  <div className="welcome-content">
                    <h3>Welcome to {stack?.name || 'Your Workflow'}</h3>
                    <p>Start building your AI workflow by dragging components from the left panel onto the canvas.</p>
                    <div className="welcome-steps">
                      <div className="step">
                        <span className="step-number">1</span>
                        <span>Drag an Input component to start</span>
                      </div>
                      <div className="step">
                        <span className="step-number">2</span>
                        <span>Add an LLM component for AI processing</span>
                      </div>
                      <div className="step">
                        <span className="step-number">3</span>
                        <span>Connect an Output component to finish</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </ReactFlow>
          </div>

          {/* Bottom Controls */}
          <div className="bottom-controls">
            <div className="zoom-controls">
              <button className="zoom-btn" onClick={handleZoomIn}>+</button>
              <button className="zoom-btn" onClick={handleZoomOut}>-</button>
              <button className="fit-btn" onClick={handleFitView}>⊞</button>
              <select 
                className="zoom-select" 
                value={zoomLevel} 
                onChange={handleZoomChange}
              >
                <option value={25}>25%</option>
                <option value={50}>50%</option>
                <option value={75}>75%</option>
                <option value={100}>100%</option>
                <option value={125}>125%</option>
                <option value={150}>150%</option>
                <option value={200}>200%</option>
              </select>
              <button 
                className={`snap-btn ${snapToGrid ? 'active' : ''}`}
                onClick={toggleSnapToGrid}
                title="Toggle Snap to Grid"
              >
                ⊞
              </button>
            </div>
          </div>

          {/* Floating Action Buttons */}
          <div className="floating-actions">
            <button className="action-btn build-btn" onClick={handleBuildStack}>
              🔨
            </button>
            <button className="action-btn chat-btn" onClick={handleChat}>
              💬
            </button>
          </div>
        </div>

      </div>

      {/* Chat Interface Modal */}
      {showChat && (
        <div className="chat-overlay" onClick={() => setShowChat(false)}>
          <div onClick={(e) => e.stopPropagation()}>
            <ChatInterface 
              workflowId={chatWorkflowId} 
              onClose={() => {
                setShowChat(false)
                setChatWorkflowId(null)
              }} 
            />
            {/* Debug info */}
            <div style={{ position: 'absolute', top: '10px', right: '10px', background: 'white', padding: '10px', border: '1px solid #ccc' }}>
              Debug: chatWorkflowId = {chatWorkflowId || 'undefined'}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function WorkflowBuilderWrapper() {
  return (
    <ReactFlowProvider>
      <WorkflowBuilder />
    </ReactFlowProvider>
  )
}
