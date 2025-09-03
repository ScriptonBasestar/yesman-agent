<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { api, type AgentInfo, type AgentConfigRequest, type TaskRequest } from '$lib/utils/api';

  let agents: AgentInfo[] = [];
  let loading = true;
  let error = '';
  let refreshInterval: number;
  
  // Create agent form
  let showCreateForm = false;
  let createConfig: AgentConfigRequest = {
    workspace_path: '/tmp/yesman-agent-workspace',
    model: 'claude-3-5-sonnet-20241022',
    allowed_tools: ['Read', 'Edit', 'Write', 'Bash'],
    timeout: 300,
    max_tokens: 4000,
    temperature: 0.0
  };

  // Task execution
  let selectedAgent = '';
  let taskPrompt = '';
  let showTaskForm = false;
  let taskLoading = false;

  async function loadAgents() {
    const response = await api.getAgents();
    if (response.success) {
      agents = response.data || [];
      error = '';
    } else {
      error = response.error || 'Failed to load agents';
    }
    loading = false;
  }

  async function createAgent() {
    try {
      loading = true;
      const response = await api.createAgent(createConfig);
      if (response.success) {
        showCreateForm = false;
        await loadAgents();
      } else {
        error = response.error || 'Failed to create agent';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    }
    loading = false;
  }

  async function runTask() {
    if (!selectedAgent || !taskPrompt) return;
    
    try {
      taskLoading = true;
      const taskRequest: TaskRequest = {
        prompt: taskPrompt,
        timeout: 60
      };
      
      const response = await api.runTask(selectedAgent, taskRequest);
      if (response.success) {
        taskPrompt = '';
        showTaskForm = false;
        // Refresh agents to see updated status
        await loadAgents();
      } else {
        error = response.error || 'Failed to run task';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    }
    taskLoading = false;
  }

  async function disposeAgent(agentId: string) {
    if (!confirm('Are you sure you want to dispose this agent?')) return;
    
    try {
      loading = true;
      const response = await api.disposeAgent(agentId);
      if (response.success) {
        await loadAgents();
      } else {
        error = response.error || 'Failed to dispose agent';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    }
    loading = false;
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'running': return 'text-blue-600';
      case 'idle': return 'text-green-600';
      case 'created': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      case 'disposed': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  }

  function formatTimestamp(timestamp: string | null): string {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleString();
  }

  onMount(() => {
    loadAgents();
    // Auto-refresh every 5 seconds
    refreshInterval = setInterval(loadAgents, 5000);
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
</script>

<div class="container mx-auto px-4 py-8">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold text-gray-800">Headless Agents</h1>
    <div class="space-x-4">
      <button 
        class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
        on:click={() => showCreateForm = true}
      >
        Create Agent
      </button>
      <button 
        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
        on:click={loadAgents}
      >
        Refresh
      </button>
    </div>
  </div>

  {#if error}
    <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {error}
    </div>
  {/if}

  {#if loading}
    <div class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      <p class="mt-2">Loading agents...</p>
    </div>
  {:else}
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold">Active Agents ({agents.length})</h2>
      </div>
      
      {#if agents.length === 0}
        <div class="px-6 py-8 text-center text-gray-500">
          No agents found. Create your first agent to get started.
        </div>
      {:else}
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Agent ID
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Workspace
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Activity
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              {#each agents as agent}
                <tr>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                    {agent.agent_id.slice(0, 8)}...
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                      {agent.status === 'running' ? 'bg-blue-100 text-blue-800' : 
                       agent.status === 'idle' ? 'bg-green-100 text-green-800' :
                       agent.status === 'created' ? 'bg-yellow-100 text-yellow-800' :
                       agent.status === 'error' ? 'bg-red-100 text-red-800' : 
                       'bg-gray-100 text-gray-800'}">
                      {agent.status.toUpperCase()}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {agent.model}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {agent.workspace_path.split('/').pop()}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatTimestamp(agent.last_activity)}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button 
                      class="text-blue-600 hover:text-blue-900"
                      on:click={() => { selectedAgent = agent.agent_id; showTaskForm = true; }}
                    >
                      Run Task
                    </button>
                    <button 
                      class="text-red-600 hover:text-red-900"
                      on:click={() => disposeAgent(agent.agent_id)}
                    >
                      Dispose
                    </button>
                  </td>
                </tr>
                {#if agent.error_message}
                  <tr class="bg-red-50">
                    <td colspan="6" class="px-6 py-2 text-sm text-red-700">
                      <strong>Error:</strong> {agent.error_message}
                    </td>
                  </tr>
                {/if}
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
  {/if}
</div>

<!-- Create Agent Modal -->
{#if showCreateForm}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <h3 class="text-lg font-semibold mb-4">Create New Agent</h3>
      
      <div class="space-y-4">
        <div>
          <label for="workspace_path" class="block text-sm font-medium text-gray-700">Workspace Path</label>
          <input 
            id="workspace_path"
            type="text" 
            bind:value={createConfig.workspace_path}
            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div>
          <label for="model" class="block text-sm font-medium text-gray-700">Model</label>
          <select 
            id="model"
            bind:value={createConfig.model}
            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
            <option value="claude-3-opus-20240229">Claude 3 Opus</option>
            <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
          </select>
        </div>
        
        <div>
          <label for="timeout" class="block text-sm font-medium text-gray-700">Timeout (seconds)</label>
          <input 
            id="timeout"
            type="number" 
            bind:value={createConfig.timeout}
            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
      
      <div class="flex justify-end space-x-3 mt-6">
        <button 
          class="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
          on:click={() => showCreateForm = false}
        >
          Cancel
        </button>
        <button 
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          on:click={createAgent}
        >
          Create
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Task Execution Modal -->
{#if showTaskForm}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <h3 class="text-lg font-semibold mb-4">Run Task</h3>
      
      <div class="space-y-4">
        <div>
          <label for="task_prompt" class="block text-sm font-medium text-gray-700">Task Prompt</label>
          <textarea 
            id="task_prompt"
            bind:value={taskPrompt}
            rows="4"
            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter your task description here..."
          ></textarea>
        </div>
      </div>
      
      <div class="flex justify-end space-x-3 mt-6">
        <button 
          class="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
          on:click={() => { showTaskForm = false; selectedAgent = ''; taskPrompt = ''; }}
        >
          Cancel
        </button>
        <button 
          class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          on:click={runTask}
          disabled={taskLoading || !taskPrompt}
        >
          {taskLoading ? 'Running...' : 'Run Task'}
        </button>
      </div>
    </div>
  </div>
{/if}