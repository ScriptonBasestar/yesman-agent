<script lang="ts">
  import { onMount } from 'svelte';
  import { sessions, filteredSessions, refreshSessions, getSessionWorkspaces, hasWorkspaceConfiguration } from '$lib/stores/sessions';
  import { showNotification } from '$lib/stores/notifications';

  // 워크스페이스 데이터
  let workspaceData: Array<{
    sessionName: string;
    workspaces: Record<string, any>;
    totalWorkspaces: number;
    hasConfig: boolean;
  }> = [];

  // 필터 및 정렬
  let searchTerm = '';
  let sortBy: 'session' | 'workspaces' | 'paths' = 'session';
  let showOnlyConfigured = false;

  // 모달 상태
  let showDetailsModal = false;
  let selectedSession: any = null;

  onMount(() => {
    refreshSessions();
  });

  // 워크스페이스 데이터 계산
  $: {
    workspaceData = $sessions.map(session => {
      const workspaces = getSessionWorkspaces(session);
      return {
        sessionName: session.session_name,
        projectName: session.project_name,
        status: session.status,
        workspaces,
        totalWorkspaces: Object.keys(workspaces).length,
        hasConfig: hasWorkspaceConfiguration(session),
        session
      };
    });
  }

  // 필터링된 데이터
  $: filteredData = workspaceData.filter(item => {
    const matchesSearch = !searchTerm || 
      item.sessionName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.projectName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      Object.keys(item.workspaces).some(ws => ws.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesFilter = !showOnlyConfigured || item.hasConfig;

    return matchesSearch && matchesFilter;
  }).sort((a, b) => {
    switch (sortBy) {
      case 'workspaces':
        return b.totalWorkspaces - a.totalWorkspaces;
      case 'paths':
        const aPaths = Object.values(a.workspaces).reduce((sum: number, ws: any) => sum + (ws.allowed_paths?.length || 0), 0);
        const bPaths = Object.values(b.workspaces).reduce((sum: number, ws: any) => sum + (ws.allowed_paths?.length || 0), 0);
        return bPaths - aPaths;
      default:
        return a.sessionName.localeCompare(b.sessionName);
    }
  });

  // 통계 계산
  $: stats = {
    total: workspaceData.length,
    withWorkspaces: workspaceData.filter(item => item.hasConfig).length,
    totalWorkspaces: workspaceData.reduce((sum, item) => sum + item.totalWorkspaces, 0),
    runningWithWorkspaces: workspaceData.filter(item => item.status === 'running' && item.hasConfig).length
  };

  function viewDetails(item: any) {
    selectedSession = item;
    showDetailsModal = true;
  }

  function getWorkspaceType(session: any): string {
    if (session.workspace_config && session.workspace_definitions) {
      return 'Hierarchical (base_dir + definitions)';
    }
    if (session.workspaces) {
      return 'Flat (direct paths)';
    }
    return 'None';
  }

  function getTotalAllowedPaths(workspaces: Record<string, any>): number {
    return Object.values(workspaces).reduce((sum: number, ws: any) => sum + (ws.allowed_paths?.length || 0), 0);
  }
</script>

<svelte:head>
  <title>Workspaces - Yesman Dashboard</title>
</svelte:head>

<div class="workspaces-page p-6 space-y-6">
  <!-- 페이지 헤더 -->
  <div class="page-header">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-3xl font-bold text-base-content flex items-center gap-3">
          🗂️ Workspaces
        </h1>
        <p class="text-base-content/70 mt-2">
          Manage secure development environments and directory access controls
        </p>
      </div>

      <div class="header-actions flex gap-3">
        <button
          class="btn btn-outline btn-sm"
          on:click={() => refreshSessions()}
        >
          🔄 Refresh
        </button>
      </div>
    </div>
  </div>

  <!-- 통계 -->
  <div class="stats-section">
    <div class="stats stats-horizontal shadow">
      <div class="stat">
        <div class="stat-title">Total Sessions</div>
        <div class="stat-value text-primary">{stats.total}</div>
        <div class="stat-desc">All configured sessions</div>
      </div>

      <div class="stat">
        <div class="stat-title">With Workspaces</div>
        <div class="stat-value text-success">{stats.withWorkspaces}</div>
        <div class="stat-desc">{stats.runningWithWorkspaces} running</div>
      </div>

      <div class="stat">
        <div class="stat-title">Total Workspaces</div>
        <div class="stat-value text-info">{stats.totalWorkspaces}</div>
        <div class="stat-desc">Across all sessions</div>
      </div>
    </div>
  </div>

  <!-- 필터 및 검색 -->
  <div class="filters-section bg-base-200 p-4 rounded-lg">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <!-- 검색 -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">Search</span>
        </label>
        <input
          type="text"
          placeholder="Session or workspace name..."
          class="input input-bordered input-sm"
          bind:value={searchTerm}
        />
      </div>

      <!-- 정렬 -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">Sort by</span>
        </label>
        <select class="select select-bordered select-sm" bind:value={sortBy}>
          <option value="session">Session Name</option>
          <option value="workspaces">Workspace Count</option>
          <option value="paths">Total Paths</option>
        </select>
      </div>

      <!-- 필터 -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">Filter</span>
        </label>
        <label class="label cursor-pointer">
          <input
            type="checkbox"
            class="checkbox checkbox-sm"
            bind:checked={showOnlyConfigured}
          />
          <span class="label-text">Only with workspaces</span>
        </label>
      </div>

      <!-- 결과 개수 -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">Results</span>
        </label>
        <div class="text-sm text-base-content/70 mt-2">
          {filteredData.length} of {workspaceData.length} sessions
        </div>
      </div>
    </div>
  </div>

  <!-- 워크스페이스 목록 -->
  <div class="workspaces-list space-y-4">
    {#if filteredData.length === 0}
      <div class="no-workspaces text-center py-20">
        <div class="text-8xl mb-6">🗂️</div>
        <h3 class="text-2xl font-semibold mb-4">No workspaces found</h3>
        <p class="text-base-content/70 mb-6 max-w-md mx-auto">
          {#if searchTerm || showOnlyConfigured}
            Try adjusting your filters to see more results.
          {:else}
            Configure workspaces for your sessions to define secure development environments.
          {/if}
        </p>
      </div>
    {:else}
      {#each filteredData as item (item.sessionName)}
        <div class="workspace-card card bg-base-100 shadow border border-base-content/10">
          <div class="card-body p-6">
            <!-- 카드 헤더 -->
            <div class="flex items-start justify-between mb-4">
              <div class="workspace-info flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <h3 class="card-title text-lg font-semibold">{item.sessionName}</h3>
                  <div class="badge {item.status === 'running' ? 'badge-success' : 'badge-error'} badge-sm">
                    {item.status === 'running' ? '🟢' : '🔴'} {item.status}
                  </div>
                  {#if item.hasConfig}
                    <div class="badge badge-primary badge-sm">
                      🗂️ {item.totalWorkspaces} workspace{item.totalWorkspaces !== 1 ? 's' : ''}
                    </div>
                  {:else}
                    <div class="badge badge-warning badge-sm">⚠️ No config</div>
                  {/if}
                </div>

                {#if item.projectName && item.projectName !== item.sessionName}
                  <p class="text-sm text-base-content/70">
                    Project: <span class="font-medium">{item.projectName}</span>
                  </p>
                {/if}

                <div class="text-sm text-base-content/60 mt-1">
                  Type: {getWorkspaceType(item.session)}
                </div>
              </div>

              <div class="workspace-actions flex gap-2">
                <button
                  class="btn btn-outline btn-sm"
                  on:click={() => viewDetails(item)}
                >
                  👁️ Details
                </button>
                {#if item.hasConfig}
                  <button
                    class="btn btn-primary btn-sm"
                    on:click={() => {
                      // Navigate to sessions page for editing
                      window.location.href = '/sessions';
                    }}
                  >
                    ⚙️ Manage
                  </button>
                {/if}
              </div>
            </div>

            <!-- 워크스페이스 요약 -->
            {#if item.hasConfig && Object.keys(item.workspaces).length > 0}
              <div class="workspaces-summary">
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {#each Object.entries(item.workspaces) as [name, config]}
                    <div class="workspace-item bg-base-200 p-3 rounded border border-base-content/5">
                      <div class="flex items-center justify-between mb-2">
                        <span class="font-medium text-sm text-primary">📁 {name}</span>
                        <span class="badge badge-outline badge-xs">
                          {config.allowed_paths?.length || 0} paths
                        </span>
                      </div>
                      <div class="text-xs text-base-content/60 font-mono truncate">
                        {config.rel_dir}
                      </div>
                      {#if config.description}
                        <div class="text-xs text-base-content/50 mt-1 truncate">
                          {config.description}
                        </div>
                      {/if}
                    </div>
                  {/each}
                </div>
              </div>
            {:else if !item.hasConfig}
              <div class="no-config-warning bg-warning/10 border border-warning/20 p-3 rounded">
                <div class="flex items-center gap-2">
                  <span class="text-warning">⚠️</span>
                  <div>
                    <div class="text-sm font-medium text-warning">No Workspace Configuration</div>
                    <div class="text-xs text-base-content/60">
                      This session doesn't have workspace security controls configured.
                    </div>
                  </div>
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/each}
    {/if}
  </div>
</div>

<!-- 상세 정보 모달 -->
{#if showDetailsModal && selectedSession}
  <div class="modal modal-open">
    <div class="modal-box max-w-4xl">
      <h3 class="font-bold text-lg mb-4">
        Workspace Details - {selectedSession.sessionName}
      </h3>

      {#if selectedSession.hasConfig}
        <div class="space-y-4">
          <!-- 기본 정보 -->
          <div class="bg-base-200 p-4 rounded">
            <h4 class="font-semibold mb-2">Configuration Type</h4>
            <p class="text-sm">{getWorkspaceType(selectedSession.session)}</p>
            
            {#if selectedSession.session.workspace_config?.base_dir}
              <div class="mt-2">
                <span class="text-sm font-medium">Base Directory:</span>
                <code class="text-sm bg-base-300 px-2 py-1 rounded ml-2">
                  {selectedSession.session.workspace_config.base_dir}
                </code>
              </div>
            {/if}
          </div>

          <!-- 워크스페이스 목록 -->
          <div class="space-y-3">
            <h4 class="font-semibold">Workspaces ({Object.keys(selectedSession.workspaces).length})</h4>
            {#each Object.entries(selectedSession.workspaces) as [name, config]}
              <div class="workspace-detail bg-base-200 p-4 rounded border-l-4 border-primary">
                <div class="flex items-start justify-between mb-2">
                  <h5 class="font-medium text-primary">📁 {name}</h5>
                  <span class="badge badge-primary badge-sm">
                    {config.allowed_paths?.length || 0} paths
                  </span>
                </div>

                {#if config.description}
                  <p class="text-sm text-base-content/70 mb-2">{config.description}</p>
                {/if}

                <div class="text-sm">
                  <div class="mb-2">
                    <span class="font-medium">Directory:</span>
                    <code class="bg-base-300 px-2 py-1 rounded ml-2">{config.rel_dir}</code>
                  </div>

                  {#if config.allowed_paths && config.allowed_paths.length > 0}
                    <div>
                      <span class="font-medium">Allowed paths:</span>
                      <div class="flex flex-wrap gap-1 mt-1">
                        {#each config.allowed_paths as path}
                          <span class="badge badge-outline badge-xs font-mono">{path}</span>
                        {/each}
                      </div>
                    </div>
                  {/if}
                </div>
              </div>
            {/each}
          </div>

          <!-- JSON 구성 -->
          <div class="collapse collapse-arrow bg-base-200">
            <input type="checkbox" />
            <div class="collapse-title text-sm font-medium">
              📄 Raw Configuration
            </div>
            <div class="collapse-content">
              <pre class="text-xs bg-base-300 p-4 rounded overflow-auto">{JSON.stringify({
                workspace_config: selectedSession.session.workspace_config,
                workspace_definitions: selectedSession.session.workspace_definitions,
                workspaces: selectedSession.session.workspaces
              }, null, 2)}</pre>
            </div>
          </div>
        </div>
      {:else}
        <div class="text-center py-8">
          <div class="text-6xl mb-4">⚠️</div>
          <h4 class="text-lg font-semibold mb-2">No Workspace Configuration</h4>
          <p class="text-base-content/70 mb-4">
            This session doesn't have any workspace security controls configured.
          </p>
          <button
            class="btn btn-primary btn-sm"
            on:click={() => {
              showDetailsModal = false;
              window.location.href = '/sessions';
            }}
          >
            Configure Workspaces
          </button>
        </div>
      {/if}

      <div class="modal-action">
        <button
          class="btn btn-ghost"
          on:click={() => {
            showDetailsModal = false;
            selectedSession = null;
          }}
        >
          Close
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .workspaces-page {
    @apply max-w-7xl mx-auto;
  }

  .workspace-card {
    @apply transition-all duration-200;
  }

  .workspace-card:hover {
    @apply border-primary/20 shadow-lg;
  }

  .workspace-item {
    @apply transition-colors;
  }

  .workspace-item:hover {
    @apply bg-base-300;
  }

  .no-workspaces {
    @apply min-h-[400px];
  }
</style>