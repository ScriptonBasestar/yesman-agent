<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { api, type AIProviderInfo, type AIProviderConfigRequest, type AITaskRequest } from '$lib/utils/api';

  let providers: AIProviderInfo[] = [];
  let loading = true;
  let error = '';
  let refreshInterval: number;
  
  // Register provider form
  let showRegisterForm = false;
  let registerConfig: AIProviderConfigRequest = {
    provider_type: 'claude_code',
    config: {},
    name: '',
    description: ''
  };
  let configJson = JSON.stringify(registerConfig.config, null, 2);
  
  // Task execution
  let showTaskForm = false;
  let selectedProvider = '';
  let taskRequest: AITaskRequest = {
    prompt: '',
    provider: '',
    model: '',
    temperature: 0.0,
    timeout: 300
  };
  let taskLoading = false;
  let taskResult: any = null;

  async function loadProviders() {
    const response = await api.getAIProviders();
    if (response.success) {
      providers = response.data || [];
      error = '';
    } else {
      error = response.error || 'Failed to load AI providers';
    }
    loading = false;
  }

  async function registerProvider() {
    try {
      loading = true;
      const response = await api.registerAIProvider(registerConfig);
      if (response.success) {
        showRegisterForm = false;
        resetRegisterForm();
        await loadProviders();
      } else {
        error = response.error || 'Failed to register provider';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    }
    loading = false;
  }

  async function unregisterProvider(providerType: string) {
    if (!confirm(`Are you sure you want to unregister ${providerType}?`)) return;
    
    try {
      loading = true;
      const response = await api.unregisterAIProvider(providerType);
      if (response.success) {
        await loadProviders();
      } else {
        error = response.error || 'Failed to unregister provider';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    }
    loading = false;
  }

  async function executeTask() {
    if (!taskRequest.prompt || !taskRequest.provider || !taskRequest.model) return;
    
    try {
      taskLoading = true;
      const response = await api.executeAITask(taskRequest);
      if (response.success) {
        taskResult = response.data;
        taskRequest.prompt = '';
      } else {
        error = response.error || 'Failed to execute task';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    }
    taskLoading = false;
  }

  async function healthCheckAll() {
    try {
      loading = true;
      const response = await api.healthCheckAllAIProviders();
      if (response.success) {
        await loadProviders(); // Refresh to see updated status
      } else {
        error = response.error || 'Failed to health check providers';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    }
    loading = false;
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'unhealthy': case 'error': return 'text-red-600';
      case 'not_configured': return 'text-gray-600';
      case 'not_initialized': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  }

  function getProviderIcon(providerType: string): string {
    switch (providerType) {
      case 'claude_code': return '🚀';
      case 'claude_api': return '🧠';
      case 'ollama': return '🦙';
      case 'openai_gpt': return '💬';
      case 'gemini': return '💎';
      case 'gemini_code': return '⚡';
      default: return '🤖';
    }
  }

  function resetRegisterForm() {
    registerConfig = {
      provider_type: 'claude_code',
      config: {},
      name: '',
      description: ''
    };
  }

  function selectProviderForTask(provider: AIProviderInfo) {
    selectedProvider = provider.provider_type;
    taskRequest.provider = provider.provider_type;
    if (provider.available_models.length > 0) {
      taskRequest.model = provider.available_models[0];
    }
    showTaskForm = true;
  }

  function renderConfigSchema(schema: any): string {
    if (!schema.properties) return 'No configuration schema available';
    
    const required = schema.required || [];
    const properties = Object.entries(schema.properties).map(([key, prop]: [string, any]) => {
      const isRequired = required.includes(key);
      const type = prop.type || 'string';
      return `${key}${isRequired ? '*' : ''}: ${type}`;
    });
    
    return properties.join(', ');
  }

  onMount(() => {
    loadProviders();
    refreshInterval = setInterval(loadProviders, 10000); // Refresh every 10 seconds
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
</script>

<div class="container mx-auto px-4 py-8">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold text-gray-800">AI Providers</h1>
    <div class="space-x-4">
      <button 
        class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
        on:click={() => showRegisterForm = true}
      >
        Register Provider
      </button>
      <button 
        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
        on:click={healthCheckAll}
        disabled={loading}
      >
        Health Check All
      </button>
      <button 
        class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
        on:click={loadProviders}
      >
        Refresh
      </button>
    </div>
  </div>

  {#if error}
    <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {error}
      <button class="ml-4 text-red-900 hover:text-red-700" on:click={() => error = ''}>✕</button>
    </div>
  {/if}

  {#if loading}
    <div class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      <p class="mt-2">Loading providers...</p>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each providers as provider}
        <div class="bg-white rounded-lg shadow-md overflow-hidden">
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center">
                <span class="text-2xl mr-3">{getProviderIcon(provider.provider_type)}</span>
                <div>
                  <h3 class="text-lg font-semibold text-gray-800">
                    {provider.provider_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </h3>
                  <p class="text-sm {getStatusColor(provider.status)}">
                    {provider.status.toUpperCase()}
                  </p>
                </div>
              </div>
              <div class="flex items-center">
                {#if provider.initialized}
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Ready
                  </span>
                {:else}
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    Not Ready
                  </span>
                {/if}
              </div>
            </div>

            <div class="mb-4">
              <div class="text-sm text-gray-600 mb-2">
                <strong>Models:</strong> {provider.available_models.length}
              </div>
              <div class="text-xs text-gray-500">
                {provider.available_models.slice(0, 3).join(', ')}
                {#if provider.available_models.length > 3}
                  <span class="text-blue-600 cursor-pointer" title={provider.available_models.join(', ')}>
                    ... +{provider.available_models.length - 3} more
                  </span>
                {/if}
              </div>
            </div>

            <div class="mb-4 text-xs text-gray-500">
              <strong>Config:</strong> {renderConfigSchema(provider.config_schema)}
            </div>

            <div class="flex justify-between items-center">
              {#if provider.initialized}
                <button 
                  class="bg-blue-500 hover:bg-blue-600 text-white text-sm px-3 py-1 rounded"
                  on:click={() => selectProviderForTask(provider)}
                >
                  Run Task
                </button>
              {:else}
                <span class="text-gray-400 text-sm">Not Available</span>
              {/if}
              
              <button 
                class="text-red-600 hover:text-red-800 text-sm"
                on:click={() => unregisterProvider(provider.provider_type)}
                disabled={!provider.initialized}
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      {/each}
    </div>

    {#if providers.length === 0}
      <div class="text-center py-12 text-gray-500">
        <div class="text-6xl mb-4">🤖</div>
        <h3 class="text-xl font-semibold mb-2">No AI Providers Configured</h3>
        <p>Register your first AI provider to get started.</p>
      </div>
    {/if}
  {/if}
</div>

<!-- Register Provider Modal -->
{#if showRegisterForm}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <h3 class="text-lg font-semibold mb-4">Register AI Provider</h3>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Provider Type</label>
          <select 
            bind:value={registerConfig.provider_type}
            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="claude_code">Claude Code</option>
            <option value="claude_api">Claude API</option>
            <option value="ollama">Ollama</option>
            <option value="openai_gpt">OpenAI GPT</option>
            <option value="gemini">Google Gemini</option>
            <option value="gemini_code">Gemini Code</option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Name (Optional)</label>
          <input 
            type="text" 
            bind:value={registerConfig.name}
            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="Friendly name"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700">Configuration (JSON)</label>
          <textarea 
            bind:value={configJson}
            on:input={(e) => {
              try {
                registerConfig.config = JSON.parse(e.target.value);
                configJson = e.target.value;
              } catch {}
            }}
            rows="8"
            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 font-mono text-xs"
            placeholder={`{"api_key": "your-key", "base_url": "https://api.example.com"}`}
          ></textarea>
          <div class="text-xs text-gray-500 mt-1">
            Example configs vary by provider. Check documentation for required fields.
          </div>
        </div>
      </div>
      
      <div class="flex justify-end space-x-3 mt-6">
        <button 
          class="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
          on:click={() => { showRegisterForm = false; resetRegisterForm(); }}
        >
          Cancel
        </button>
        <button 
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          on:click={registerProvider}
        >
          Register
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Task Execution Modal -->
{#if showTaskForm}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white max-h-[80vh] overflow-y-auto">
      <h3 class="text-lg font-semibold mb-4">Run AI Task</h3>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Provider</label>
          <input 
            type="text" 
            bind:value={taskRequest.provider}
            disabled
            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm bg-gray-50"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700">Model</label>
          <select 
            bind:value={taskRequest.model}
            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            {#each providers.find(p => p.provider_type === selectedProvider)?.available_models || [] as model}
              <option value={model}>{model}</option>
            {/each}
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Prompt</label>
          <textarea 
            bind:value={taskRequest.prompt}
            rows="6"
            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter your AI task prompt here..."
          ></textarea>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Temperature</label>
            <input 
              type="number" 
              bind:value={taskRequest.temperature}
              min="0" max="2" step="0.1"
              class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Timeout (sec)</label>
            <input 
              type="number" 
              bind:value={taskRequest.timeout}
              min="10" max="1800"
              class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {#if taskResult}
          <div class="bg-gray-50 p-4 rounded border">
            <h4 class="font-medium text-gray-900 mb-2">Result:</h4>
            <div class="text-sm">
              <div class="mb-2">
                <strong>Status:</strong> 
                <span class="px-2 py-1 rounded text-xs {
                  taskResult.status === 'completed' ? 'bg-green-100 text-green-800' :
                  taskResult.status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-blue-100 text-blue-800'
                }">
                  {taskResult.status}
                </span>
              </div>
              {#if taskResult.content}
                <div class="bg-white p-3 rounded border text-sm font-mono max-h-40 overflow-y-auto">
                  {taskResult.content}
                </div>
              {/if}
              {#if taskResult.error}
                <div class="text-red-600 text-sm mt-2">
                  <strong>Error:</strong> {taskResult.error}
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>
      
      <div class="flex justify-end space-x-3 mt-6">
        <button 
          class="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
          on:click={() => { 
            showTaskForm = false; 
            selectedProvider = '';
            taskResult = null;
            taskRequest = {
              prompt: '',
              provider: '',
              model: '',
              temperature: 0.0,
              timeout: 300
            };
          }}
        >
          Close
        </button>
        <button 
          class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          on:click={executeTask}
          disabled={taskLoading || !taskRequest.prompt}
        >
          {taskLoading ? 'Running...' : 'Run Task'}
        </button>
      </div>
    </div>
  </div>
{/if}