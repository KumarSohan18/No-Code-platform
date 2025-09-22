import { useState, useEffect } from 'react'
import WorkflowBuilder from './components/WorkflowBuilder'
import ApiService from './services/api'
import './App.css'

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  })
  const [stacks, setStacks] = useState([])
  const [currentView, setCurrentView] = useState('home') // 'home' or 'workflow'
  const [selectedStack, setSelectedStack] = useState(null)
  const [backendStatus, setBackendStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  // Check backend health and load workflows on component mount
  useEffect(() => {
    checkBackendHealth()
    loadWorkflows()
  }, [])

  const checkBackendHealth = async () => {
    try {
      const health = await ApiService.healthCheck()
      setBackendStatus({ status: 'healthy', ...health })
    } catch (error) {
      console.error('Backend health check failed:', error)
      setBackendStatus({ status: 'unhealthy', error: error.message })
    } finally {
      setLoading(false)
    }
  }

  const loadWorkflows = async () => {
    try {
      const workflows = await ApiService.getWorkflows()
      setStacks(Array.isArray(workflows) ? workflows : [])
    } catch (error) {
      console.error('Failed to load workflows:', error)
      // Keep existing stacks if API fails
      setStacks([])
    }
  }

  const handleNewStack = () => {
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setFormData({ name: '', description: '' })
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleCreate = async () => {
    console.log('handleCreate called with:', formData)
    if (formData.name.trim()) {
      try {
        console.log('Creating workflow...')
        const newStack = {
          name: formData.name.trim(),
          description: formData.description.trim(),
          nodes: [],
          edges: []
        }
        console.log('Sending data:', newStack)
        
        const createdWorkflow = await ApiService.createWorkflow(newStack)
        console.log('Created workflow:', createdWorkflow)
        setStacks(prev => Array.isArray(prev) ? [...prev, createdWorkflow] : [createdWorkflow])
        handleCloseModal()
      } catch (error) {
        console.error('Failed to create workflow:', error)
        console.error('Error details:', error.message)
        alert(`Failed to create workflow: ${error.message}`)
      }
    }
  }

  const isCreateDisabled = !formData.name.trim()

  const handleOpenStack = (stack) => {
    setSelectedStack(stack)
    setCurrentView('workflow')
  }

  const handleBackToHome = () => {
    setCurrentView('home')
    setSelectedStack(null)
  }

  const handleWorkflowUpdate = (updatedWorkflow) => {
    setSelectedStack(updatedWorkflow)
    // Also update the stacks list if needed
    setStacks(prev => {
      if (Array.isArray(prev)) {
        const existingIndex = prev.findIndex(s => s.id === updatedWorkflow.id)
        if (existingIndex >= 0) {
          const newStacks = [...prev]
          newStacks[existingIndex] = updatedWorkflow
          return newStacks
        } else {
          return [...prev, updatedWorkflow]
        }
      }
      return [updatedWorkflow]
    })
  }

  // Show workflow builder if current view is workflow
  if (currentView === 'workflow') {
    return <WorkflowBuilder onBack={handleBackToHome} stack={selectedStack || {}} onWorkflowUpdate={handleWorkflowUpdate} />
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <span className="brand-name">GenAI Stack</span>
            {backendStatus && (
              <div className={`backend-status ${backendStatus.status}`}>
                <span className="status-indicator">
                  {backendStatus.status === 'healthy' ? '🟢' : '🔴'}
                </span>
                <span className="status-text">
                  Backend {backendStatus.status}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <div className="content-header">
          <h1 className="page-title">My Stacks</h1>
          <button className="new-stack-btn" onClick={handleNewStack}>
            <span className="plus-icon">+</span>
            New Stack
          </button>
        </div>

        {loading && (
          <div className="loading-message">
            <p>Loading workflows...</p>
          </div>
        )}

        {/* Stacks Grid or Central Card */}
        {!loading && stacks.length > 0 ? (
          <div className="stacks-grid">
            {stacks.map((stack) => (
              <div key={stack.id} className="stack-card">
                <div className="stack-header">
                  <h3 className="stack-name">{stack.name}</h3>
                  <div className="stack-actions">
                    <button className="action-btn edit-btn">Edit</button>
                    <button className="action-btn delete-btn">Delete</button>
                  </div>
                </div>
                <p className="stack-description">{stack.description || 'No description'}</p>
                <div className="stack-footer">
                  <span className="stack-date">
                    Created {new Date(stack.created_at).toLocaleDateString()}
                  </span>
                  <button 
                    className="open-stack-btn"
                    onClick={() => handleOpenStack(stack)}
                  >
                    Open Stack
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : !loading ? (
          <div className="center-card">
            <h2 className="card-title">Create New Stack</h2>
            <p className="card-description">
              Start building your generative AI apps with our essential tools and frameworks
            </p>
            <button className="card-btn" onClick={handleNewStack}>
              <span className="plus-icon">+</span>
              New Stack
            </button>
          </div>
        ) : null}
      </main>

      {/* Modal */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Create New Stack</h2>
              <button className="close-btn" onClick={handleCloseModal}>
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="name" className="form-label">Name</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="form-input"
                  placeholder="Enter stack name"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="description" className="form-label">Description</label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  className="form-textarea"
                  placeholder="Enter stack description"
                  rows="4"
                />
              </div>
            </div>
            
            <div className="modal-footer">
              <button className="cancel-btn" onClick={handleCloseModal}>
                Cancel
              </button>
              <button 
                className={`create-btn ${isCreateDisabled ? 'disabled' : ''}`}
                onClick={handleCreate}
                disabled={isCreateDisabled}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
