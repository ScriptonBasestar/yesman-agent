<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { api, type AIProviderInfo, type AIProviderConfigRequest, type AITaskRequest } from '$lib/utils/api';
  import { pythonBridge } from '$lib/utils/tauri';

  // Provider state types
  type ProviderStatus = 'not_installed' | 'detected' | 'registered' | 'active' | 'error';
  
  interface KnownProvider {
    name: string;
    type: string;
    description: string;
    status: ProviderStatus;
    detected_path?: string;
    detected_version?: string;
    auto_detected: boolean;
    install_guide?: string;
  }

  let providers: AIProviderInfo[] = [];
  let knownProviders: KnownProvider[] = [
    {
      name: 'Claude Code',
      type: 'claude_code',
      description: 'Anthropic\'s Claude CLI for code generation',
      status: 'not_installed',
      auto_detected: false,
      install_guide: 'Install via: npm install -g @anthropic-ai/claude-cli'
    },
    {
      name: 'Ollama',
      type: 'ollama',
      description: 'Local LLM runtime for various models',
      status: 'not_installed', 
      auto_detected: false,
      install_guide: 'Download from: https://ollama.ai'
    },
    {
      name: 'OpenAI GPT',
      type: 'openai_gpt',
      description: 'OpenAI GPT models via API',
      status: 'not_installed',
      auto_detected: false,
      install_guide: 'Requires OpenAI API key'
    },
    {
      name: 'Claude API',
      type: 'claude_api',
      description: 'Anthropic Claude via direct API',
      status: 'not_installed',
      auto_detected: false,
      install_guide: 'Requires Anthropic API key'
    },
    {
      name: 'Google Gemini',
      type: 'gemini',
      description: 'Google Gemini AI models',
      status: 'not_installed',
      auto_detected: false,
      install_guide: 'Requires Google AI API key'
    },
    {
      name: 'Gemini Code',
      type: 'gemini_code',
      description: 'Google Gemini optimized for code',
      status: 'not_installed',
      auto_detected: false,
      install_guide: 'Requires Google AI API key'
    }
  ];

  let loading = true;
  let discovering = false;
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
      
      // Update known providers status based on registered providers
      updateKnownProviderStatus();
    } else {
      error = response.error || 'Failed to load AI providers';
    }
    loading = false;
  }

  function updateKnownProviderStatus() {
    knownProviders = knownProviders.map(known => {
      const registered = providers.find(p => p.provider_type === known.type);
      if (registered) {
        return {
          ...known,
          status: registered.initialized ? 'active' : 'registered'
        };
      }
      return known;
    });
  }

  async function autoDiscoverProviders() {
    discovering = true;
    error = '';

    try {
      // Check for command-line tools
      await checkCommandTools();
      
      // Check for environment variables
      await checkEnvironmentVariables();
      
      // Check for running services
      await checkRunningServices();

    } catch (err) {
      error = err instanceof Error ? err.message : 'Discovery failed';
    }
    
    discovering = false;
  }

  async function checkCommandTools() {
    const commandMappings = [
      { tool: 'claude', provider: 'claude_code' },
      { tool: 'ollama', provider: 'ollama' },
      { tool: 'gh', provider: 'openai_gpt' }, // GitHub CLI often used with Copilot
    ];

    try {
      const commands = commandMappings.map(mapping => mapping.tool);
      const results = await pythonBridge.detect_command_tools(commands);
      
      for (const result of results) {
        const mapping = commandMappings.find(m => m.tool === result.provider);
        if (mapping && result.detected) {
          updateProviderStatus(mapping.provider, 'detected', result.path || undefined, result.version || undefined);
        }
      }
    } catch (e) {
      console.log('Could not check command tools:', e);
    }
  }

  async function checkEnvironmentVariables() {
    const envMappings = [
      { env: 'OPENAI_API_KEY', provider: 'openai_gpt' },
      { env: 'ANTHROPIC_API_KEY', provider: 'claude_api' },
      { env: 'GOOGLE_API_KEY', provider: 'gemini' },
    ];

    try {
      const envVars = envMappings.map(mapping => mapping.env);
      const results = await pythonBridge.check_environment_variables(envVars);
      
      for (const result of results) {
        const mapping = envMappings.find(m => m.env === result.provider);
        if (mapping && result.detected) {
          updateProviderStatus(mapping.provider, 'detected', undefined, undefined);
        }
      }
    } catch (e) {
      console.log('Could not check environment variables:', e);
    }
  }

  async function checkRunningServices() {
    const processMappings = [
      { process: 'ollama', provider: 'ollama' },
    ];

    try {
      const processes = processMappings.map(mapping => mapping.process);
      const results = await pythonBridge.check_running_services(processes);
      
      for (const result of results) {
        const mapping = processMappings.find(m => m.process === result.provider);
        if (mapping && result.detected) {
          updateProviderStatus(mapping.provider, 'detected', 'running', undefined);
        }
      }

      // Also try direct HTTP check for Ollama API
      try {
        const response = await fetch('http://127.0.0.1:11434/api/version', {
          method: 'GET',
          signal: AbortSignal.timeout(2000) // 2 second timeout
        });
        if (response.ok) {
          const data = await response.json();
          updateProviderStatus('ollama', 'detected', 'http://127.0.0.1:11434', data.version);
        }
      } catch (e) {
        console.log('Ollama HTTP service not detected');
      }
    } catch (e) {
      console.log('Could not check running services:', e);
    }
  }

  function updateProviderStatus(providerType: string, status: ProviderStatus, path?: string, version?: string) {
    knownProviders = knownProviders.map(p => {
      if (p.type === providerType) {
        return {
          ...p,
          status,
          detected_path: path,
          detected_version: version,
          auto_detected: true
        };
      }
      return p;
    });
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

  function getProviderStatusColor(status: ProviderStatus): string {
    switch (status) {
      case 'active': return 'text-green-600';
      case 'registered': return 'text-blue-600';
      case 'detected': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      case 'not_installed': return 'text-gray-400';
      default: return 'text-gray-600';
    }
  }

  function getProviderStatusBadge(status: ProviderStatus): { class: string, text: string } {
    switch (status) {
      case 'active': 
        return { class: 'bg-green-100 text-green-800', text: 'Active' };
      case 'registered': 
        return { class: 'bg-blue-100 text-blue-800', text: 'Registered' };
      case 'detected': 
        return { class: 'bg-yellow-100 text-yellow-800', text: 'Detected' };
      case 'error': 
        return { class: 'bg-red-100 text-red-800', text: 'Error' };
      case 'not_installed': 
        return { class: 'bg-gray-100 text-gray-600', text: 'Not Installed' };
      default: 
        return { class: 'bg-gray-100 text-gray-600', text: 'Unknown' };
    }
  }

  async function registerKnownProvider(provider: KnownProvider) {
    registerConfig.provider_type = provider.type;
    registerConfig.name = provider.name;
    registerConfig.description = provider.description;
    
    if (provider.detected_path) {
      registerConfig.config = { 
        path: provider.detected_path,
        version: provider.detected_version
      };
      configJson = JSON.stringify(registerConfig.config, null, 2);
    }
    
    showRegisterForm = true;
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
        class="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded disabled:opacity-50"
        on:click={autoDiscoverProviders}
        disabled={discovering}
      >
        {discovering ? '🔍 Discovering...' : '🔍 Auto-Discover'}
      </button>
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
    <!-- Available Providers Section -->
    <div class="mb-8">
      <h2 class="text-2xl font-semibold text-gray-800 mb-4">Available AI Providers</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {#each knownProviders as provider}
          {@const statusBadge = getProviderStatusBadge(provider.status)}
          <div class="bg-white rounded-lg shadow-md border overflow-hidden {
            provider.status === 'detected' ? 'border-yellow-300' :
            provider.status === 'active' ? 'border-green-300' :
            provider.status === 'registered' ? 'border-blue-300' : 'border-gray-200'
          }">
            <div class="p-4">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center">
                  <span class="text-2xl mr-3">{getProviderIcon(provider.type)}</span>
                  <div>
                    <h3 class="text-lg font-semibold text-gray-800">{provider.name}</h3>
                    <p class="text-sm text-gray-600">{provider.description}</p>
                  </div>
                </div>
              </div>

              <div class="mb-3">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {statusBadge.class}">
                  {statusBadge.text}
                </span>
                {#if provider.auto_detected}
                  <span class="ml-2 text-xs text-blue-600">Auto-detected</span>
                {/if}
              </div>

              {#if provider.detected_path}
                <div class="mb-3 text-xs text-gray-500">
                  <strong>Path:</strong> <code class="bg-gray-100 px-1 rounded">{provider.detected_path}</code>
                  {#if provider.detected_version}
                    <br><strong>Version:</strong> {provider.detected_version}
                  {/if}
                </div>
              {/if}

              {#if provider.status === 'not_installed'}
                <div class="mb-3 text-xs text-gray-500">
                  <strong>Install:</strong> {provider.install_guide}
                </div>
              {/if}

              <div class="flex justify-between items-center">
                {#if provider.status === 'detected'}
                  <button 
                    class="bg-yellow-500 hover:bg-yellow-600 text-white text-sm px-3 py-1 rounded"
                    on:click={() => registerKnownProvider(provider)}
                  >
                    Register
                  </button>
                {:else if provider.status === 'registered' || provider.status === 'active'}
                  <button 
                    class="text-red-600 hover:text-red-800 text-sm"
                    on:click={() => unregisterProvider(provider.type)}
                  >
                    Remove
                  </button>
                {:else}
                  <span class="text-gray-400 text-sm">Not Available</span>
                {/if}
                
                {#if provider.status === 'active'}
                  <button 
                    class="bg-blue-500 hover:bg-blue-600 text-white text-sm px-3 py-1 rounded"
                    on:click={() => {
                      const registeredProvider = providers.find(p => p.provider_type === provider.type);
                      if (registeredProvider) selectProviderForTask(registeredProvider);
                    }}
                  >
                    Run Task
                  </button>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Registered Providers Section -->
    {#if providers.length > 0}
      <div class="mb-8">
        <h2 class="text-2xl font-semibold text-gray-800 mb-4">Registered Providers Details</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {#each providers as provider}
            <div class="bg-white rounded-lg shadow-md overflow-hidden border-l-4 border-blue-500">
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
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    {#if knownProviders.filter(p => p.status !== 'not_installed').length === 0}
      <div class="text-center py-12 text-gray-500">
        <div class="text-6xl mb-4">🔍</div>
        <h3 class="text-xl font-semibold mb-2">No AI Providers Detected</h3>
        <p class="mb-4">Click "Auto-Discover" to scan for installed AI tools, or manually register providers.</p>
        <button 
          class="bg-purple-500 hover:bg-purple-600 text-white px-6 py-2 rounded"
          on:click={autoDiscoverProviders}
        >
          🔍 Start Auto-Discovery
        </button>
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
          <!-- pragma: allowlist secret -->
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