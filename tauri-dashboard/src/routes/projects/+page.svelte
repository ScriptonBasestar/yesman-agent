<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  
  // 기존 Sessions 컴포넌트들 import
  import SessionCard from '$lib/components/session/SessionCard.svelte';
  import SessionFilters from '$lib/components/session/SessionFilters.svelte';
  
  // Sessions store
  import {
    filteredSessions,
    sessionStats,
    isLoading,
    error,
    refreshSessions,
    viewSessionLogs,
    createTmuxSession,
    getAvailableProjects,
    updateSessionWorkspaces,
    getWorkspaceInfo,
    getSessionWorkspaces,
    hasWorkspaceConfiguration,
    sessions
  } from '$lib/stores/sessions';
  import { showNotification } from '$lib/stores/notifications';
  import { api } from '$lib/utils/api';

  // 탭 상태 관리
  let activeTab: 'sessions' | 'workspaces' = 'sessions';

  // URL 파라미터로 탭 상태 관리
  $: {
    const tab = $page.url.searchParams.get('tab');
    if (tab === 'workspaces') {
      activeTab = 'workspaces';
    } else {
      activeTab = 'sessions';
    }
  }

  // 탭 변경 함수
  function switchTab(tab: 'sessions' | 'workspaces') {
    const url = new URL($page.url);
    if (tab === 'workspaces') {
      url.searchParams.set('tab', 'workspaces');
    } else {
      url.searchParams.delete('tab');
    }
    window.history.replaceState({}, '', url);
    activeTab = tab;
  }

  // Sessions 관련 상태 (기존 sessions/+page.svelte에서 복사)
  let showCreateModal = false;
  let availableProjects: string[] = [];
  let selectedProject = '';
  let isCreatingSession = false;

  // 워크스페이스 관리 모달 상태
  let showWorkspaceModal = false;
  let selectedSessionForWorkspace = '';
  let workspaceConfig = {};
  let workspaceConfigJson = '';

  // Workspaces 관련 상태
  let workspaceData: Array<{
    sessionName: string;
    workspaces: Record<string, any>;
    totalWorkspaces: number;
    hasConfig: boolean;
  }> = [];

  let searchTerm = '';
  let sortBy: 'session' | 'workspaces' | 'paths' = 'session';
  let showOnlyConfigured = false;
  let showDetailsModal = false;
  let selectedSession: any = null;

  onMount(async () => {
    refreshSessions();
    try {
      availableProjects = await getAvailableProjects();
    } catch (error) {
      console.error('Failed to load available projects:', error);
    }
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

  // 워크스페이스 필터링
  $: filteredWorkspaceData = workspaceData.filter(item => {
    const matchesSearch = !searchTerm || 
      item.sessionName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.projectName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      Object.keys(item.workspaces).some(ws => ws.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesFilter = !showOnlyConfigured || item.hasConfig;
    return matchesSearch && matchesFilter;
  });

  // 워크스페이스 관리 이벤트 핸들러
  async function handleManageWorkspaces(event: CustomEvent) {
    const { session } = event.detail;
    selectedSessionForWorkspace = session;
    
    try {
      const workspaceInfo = await getWorkspaceInfo(session);
      workspaceConfig = workspaceInfo || {};
      workspaceConfigJson = JSON.stringify(workspaceConfig, null, 2);
      showWorkspaceModal = true;
    } catch (error) {
      console.error('Failed to load workspace info:', error);
      showNotification('워크스페이스 정보를 불러오는데 실패했습니다.', 'error');
    }
  }

  // 세션 생성 핸들러
  async function handleCreateSession() {
    if (!selectedProject.trim()) {
      showNotification('프로젝트를 선택해주세요.', 'error');
      return;
    }

    isCreatingSession = true;
    try {
      await createTmuxSession(selectedProject.trim());
      showNotification(`세션 "${selectedProject}"가 생성되었습니다.`, 'success');
      showCreateModal = false;
      selectedProject = '';
      refreshSessions();
    } catch (error) {
      console.error('Session creation failed:', error);
      showNotification('세션 생성에 실패했습니다.', 'error');
    } finally {
      isCreatingSession = false;
    }
  }

  // 워크스페이스 저장 핸들러
  async function handleSaveWorkspace() {
    try {
      const parsedConfig = JSON.parse(workspaceConfigJson);
      await updateSessionWorkspaces(selectedSessionForWorkspace, parsedConfig);
      showNotification('워크스페이스 설정이 저장되었습니다.', 'success');
      showWorkspaceModal = false;
      refreshSessions();
    } catch (error) {
      console.error('Failed to save workspace config:', error);
      if (error instanceof SyntaxError) {
        showNotification('JSON 형식이 올바르지 않습니다.', 'error');
      } else {
        showNotification('워크스페이스 설정 저장에 실패했습니다.', 'error');
      }
    }
  }

  // 세션 시작 핸들러
  async function handleStartSession(event: CustomEvent) {
    const { session } = event.detail;
    try {
      const { setupSession } = await import('$lib/stores/sessions');
      await setupSession(session);
    } catch (error) {
      console.error('Failed to start session:', error);
    }
  }
</script>

<svelte:head>
  <title>Projects - Yesman Dashboard</title>
</svelte:head>

<!-- 페이지 헤더 -->
<div class="page-header bg-base-100 border-b border-base-300">
  <div class="container mx-auto px-6 py-4">
    <div class="flex justify-between items-start">
      <div class="space-y-1">
        <div class="flex items-center gap-3">
          <span class="text-2xl">🖥️</span>
          <h1 class="text-2xl font-bold text-base-content">Projects</h1>
        </div>
        <p class="text-base-content/70 text-sm">
          {#if activeTab === 'sessions'}
            Manage your project sessions and tmux environments
          {:else}
            Configure development environments and workspace access
          {/if}
        </p>
      </div>
      
      <div class="flex items-center gap-2">
        <!-- 새로고침 버튼 -->
        <button 
          class="btn btn-ghost btn-sm" 
          on:click={() => refreshSessions()}
          disabled={$isLoading}
        >
          <span class="text-lg">🔄</span>
          Refresh
        </button>
        
        <!-- 새 프로젝트 버튼 -->
        {#if activeTab === 'sessions'}
          <button 
            class="btn btn-primary btn-sm" 
            on:click={() => showCreateModal = true}
          >
            <span class="text-lg">➕</span>
            New Project
          </button>
        {/if}
      </div>
    </div>
  </div>
</div>

<!-- 탭 네비게이션 -->
<div class="bg-base-100 border-b border-base-300">
  <div class="container mx-auto px-6">
    <div role="tablist" class="tabs tabs-bordered">
      <button 
        role="tab" 
        class="tab {activeTab === 'sessions' ? 'tab-active' : ''}" 
        on:click={() => switchTab('sessions')}
      >
        <span class="text-lg mr-2">📋</span>
        Sessions
        <div class="badge badge-neutral badge-sm ml-2">{$sessionStats.total}</div>
      </button>
      <button 
        role="tab" 
        class="tab {activeTab === 'workspaces' ? 'tab-active' : ''}" 
        on:click={() => switchTab('workspaces')}
      >
        <span class="text-lg mr-2">🗂️</span>
        Workspaces
        <div class="badge badge-neutral badge-sm ml-2">{workspaceData.filter(w => w.hasConfig).length}</div>
      </button>
    </div>
  </div>
</div>

<!-- 탭 콘텐츠 -->
<main class="container mx-auto p-6">
  {#if activeTab === 'sessions'}
    <!-- Sessions 탭 콘텐츠 -->
    <div class="space-y-6">
      <!-- 통계 카드 -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="stat bg-base-200 rounded-lg p-4">
          <div class="stat-title text-base-content/60">Total Sessions</div>
          <div class="stat-value text-2xl text-base-content">{$sessionStats.total}</div>
          <div class="stat-desc text-base-content/50">All configured sessions</div>
        </div>
        <div class="stat bg-base-200 rounded-lg p-4">
          <div class="stat-title text-base-content/60">Running</div>
          <div class="stat-value text-2xl text-success">{$sessionStats.running}</div>
          <div class="stat-desc text-base-content/50">Active sessions</div>
        </div>
        <div class="stat bg-base-200 rounded-lg p-4">
          <div class="stat-title text-base-content/60">With Workspaces</div>
          <div class="stat-value text-2xl text-info">{$sessionStats.withWorkspaces}</div>
          <div class="stat-desc text-base-content/50">Configured environments</div>
        </div>
        <div class="stat bg-base-200 rounded-lg p-4">
          <div class="stat-title text-base-content/60">Claude Active</div>
          <div class="stat-value text-2xl text-warning">{$sessionStats.claudeActive}</div>
          <div class="stat-desc text-base-content/50">AI-powered sessions</div>
        </div>
      </div>

      <!-- 필터 -->
      <SessionFilters />

      <!-- 세션 목록 -->
      {#if $isLoading}
        <div class="flex justify-center items-center py-12">
          <div class="loading loading-spinner loading-lg text-primary"></div>
        </div>
      {:else if $error}
        <div class="alert alert-error">
          <span class="text-lg">⚠️</span>
          <div>
            <h3 class="font-bold">Error loading sessions</h3>
            <div class="text-xs">{$error}</div>
          </div>
          <button class="btn btn-outline btn-sm" on:click={() => refreshSessions()}>
            Retry
          </button>
        </div>
      {:else if $filteredSessions.length === 0}
        <div class="text-center py-12">
          <div class="text-6xl mb-4">🖥️</div>
          <h3 class="text-xl font-semibold mb-2 text-base-content">No projects found</h3>
          <p class="text-base-content/70 mb-4">You don't have any projects yet. Create your first project to get started.</p>
          <div class="space-x-2">
            <button class="btn btn-primary" on:click={() => showCreateModal = true}>
              <span class="text-lg">➕</span>
              Create First Project
            </button>
            <button class="btn btn-outline" on:click={() => refreshSessions()}>
              <span class="text-lg">🔄</span>
              Refresh
            </button>
          </div>
        </div>
      {:else}
        <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {#each $filteredSessions as session (session.session_name)}
            <SessionCard 
              {session} 
              on:viewLogs={viewSessionLogs} 
              on:manageWorkspaces={handleManageWorkspaces}
              on:startSession={handleStartSession}
            />
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <!-- Workspaces 탭 콘텐츠 -->
    <div class="space-y-6">
      <!-- 워크스페이스 통계 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="stat bg-base-200 rounded-lg p-4">
          <div class="stat-title text-base-content/60">Total Sessions</div>
          <div class="stat-value text-2xl text-base-content">{workspaceData.length}</div>
          <div class="stat-desc text-base-content/50">All configured sessions</div>
        </div>
        <div class="stat bg-base-200 rounded-lg p-4">
          <div class="stat-title text-base-content/60">With Workspaces</div>
          <div class="stat-value text-2xl text-info">{workspaceData.filter(w => w.hasConfig).length}</div>
          <div class="stat-desc text-base-content/50">{workspaceData.filter(w => w.hasConfig && w.session?.status === 'running').length} running</div>
        </div>
        <div class="stat bg-base-200 rounded-lg p-4">
          <div class="stat-title text-base-content/60">Total Workspaces</div>
          <div class="stat-value text-2xl text-success">{workspaceData.reduce((sum, w) => sum + w.totalWorkspaces, 0)}</div>
          <div class="stat-desc text-base-content/50">Across all sessions</div>
        </div>
      </div>

      <!-- 워크스페이스 필터 -->
      <div class="bg-base-200 p-4 rounded-lg space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
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
          <div class="form-control">
            <label class="label">
              <span class="label-text">Filter</span>
            </label>
            <label class="label cursor-pointer">
              <input type="checkbox" class="checkbox checkbox-sm" bind:checked={showOnlyConfigured} />
              <span class="label-text">Only with workspaces</span>
            </label>
          </div>
          <div class="form-control">
            <label class="label">
              <span class="label-text">Results</span>
            </label>
            <div class="text-sm text-base-content/70">{filteredWorkspaceData.length} of {workspaceData.length} sessions</div>
          </div>
        </div>
      </div>

      <!-- 워크스페이스 목록 -->
      {#if $isLoading}
        <div class="flex justify-center items-center py-12">
          <div class="loading loading-spinner loading-lg text-primary"></div>
        </div>
      {:else if filteredWorkspaceData.length === 0}
        <div class="text-center py-12">
          <div class="text-6xl mb-4">🗂️</div>
          <h3 class="text-xl font-semibold mb-2 text-base-content">No workspaces found</h3>
          <p class="text-base-content/70 mb-4">Configure workspaces for your sessions to define secure development environments.</p>
        </div>
      {:else}
        <div class="space-y-4">
          {#each filteredWorkspaceData as item (item.sessionName)}
            <div class="card bg-base-100 border border-base-300">
              <div class="card-body p-4">
                <div class="flex justify-between items-start">
                  <div>
                    <h3 class="font-semibold text-base-content">
                      {item.sessionName}
                      {#if item.projectName && item.projectName !== item.sessionName}
                        <span class="text-sm text-base-content/70">({item.projectName})</span>
                      {/if}
                    </h3>
                    <div class="flex items-center gap-4 text-sm text-base-content/60 mt-1">
                      <span class="badge badge-{item.session?.status === 'running' ? 'success' : 'ghost'} badge-sm">
                        {item.session?.status || 'unknown'}
                      </span>
                      <span>{item.totalWorkspaces} workspaces</span>
                      <span>{item.hasConfig ? 'Configured' : 'Not configured'}</span>
                    </div>
                  </div>
                  <div class="flex gap-2">
                    <button 
                      class="btn btn-ghost btn-sm" 
                      on:click={() => { selectedSession = item.session; showDetailsModal = true; }}
                      disabled={!item.hasConfig}
                    >
                      View
                    </button>
                    <button 
                      class="btn btn-primary btn-sm" 
                      on:click={() => handleManageWorkspaces({ detail: { session: item.sessionName } })}
                    >
                      Configure
                    </button>
                  </div>
                </div>
                {#if item.hasConfig && Object.keys(item.workspaces).length > 0}
                  <div class="mt-3">
                    <div class="text-sm text-base-content/70 mb-2">Workspaces:</div>
                    <div class="flex flex-wrap gap-1">
                      {#each Object.keys(item.workspaces) as workspace}
                        <span class="badge badge-outline badge-sm">{workspace}</span>
                      {/each}
                    </div>
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</main>

<!-- 세션 생성 모달 -->
{#if showCreateModal}
  <div class="modal modal-open">
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-4">Create New Project</h3>
      
      <div class="form-control">
        <label class="label">
          <span class="label-text">Project Name</span>
        </label>
        <input 
          type="text" 
          placeholder="Enter project name..." 
          class="input input-bordered" 
          bind:value={selectedProject}
          disabled={isCreatingSession}
        />
        <label class="label">
          <span class="label-text-alt">This will create a new tmux session</span>
        </label>
      </div>

      {#if availableProjects.length > 0}
        <div class="form-control mt-4">
          <label class="label">
            <span class="label-text">Available Templates</span>
          </label>
          <select 
            class="select select-bordered" 
            bind:value={selectedProject}
            disabled={isCreatingSession}
          >
            <option value="">Select a template...</option>
            {#each availableProjects as project}
              <option value={project}>{project}</option>
            {/each}
          </select>
        </div>
      {/if}

      <div class="modal-action">
        <button 
          class="btn btn-ghost" 
          on:click={() => { showCreateModal = false; selectedProject = ''; }}
          disabled={isCreatingSession}
        >
          Cancel
        </button>
        <button 
          class="btn btn-primary" 
          on:click={handleCreateSession}
          disabled={!selectedProject.trim() || isCreatingSession}
        >
          {#if isCreatingSession}
            <span class="loading loading-spinner loading-sm"></span>
          {/if}
          Create Project
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- 워크스페이스 관리 모달 -->
{#if showWorkspaceModal}
  <div class="modal modal-open">
    <div class="modal-box max-w-4xl">
      <h3 class="font-bold text-lg mb-4">
        Manage Workspaces: {selectedSessionForWorkspace}
      </h3>
      
      <div class="form-control">
        <label class="label">
          <span class="label-text">Workspace Configuration (JSON)</span>
          <span class="label-text-alt">
            <a href="#" class="link link-primary text-xs">View Documentation</a>
          </span>
        </label>
        <textarea 
          class="textarea textarea-bordered font-mono text-sm h-64" 
          placeholder="Enter workspace configuration as JSON..."
          bind:value={workspaceConfigJson}
        ></textarea>
        <label class="label">
          <span class="label-text-alt">Configure development environments and directory access</span>
        </label>
      </div>

      <div class="modal-action">
        <button 
          class="btn btn-ghost" 
          on:click={() => { showWorkspaceModal = false; workspaceConfigJson = ''; }}
        >
          Cancel
        </button>
        <button 
          class="btn btn-primary" 
          on:click={handleSaveWorkspace}
        >
          Save Configuration
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- 워크스페이스 상세 모달 -->
{#if showDetailsModal && selectedSession}
  <div class="modal modal-open">
    <div class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        Workspace Details: {selectedSession.session_name}
      </h3>
      
      <div class="space-y-4">
        <div>
          <div class="text-sm font-medium text-base-content/70">Session Status</div>
          <div class="badge badge-{selectedSession.status === 'running' ? 'success' : 'ghost'} badge-lg">
            {selectedSession.status}
          </div>
        </div>

        <div>
          <div class="text-sm font-medium text-base-content/70 mb-2">Workspaces</div>
          {#each Object.entries(getSessionWorkspaces(selectedSession)) as [name, config]}
            <div class="bg-base-200 p-3 rounded-lg mb-2">
              <div class="font-medium">{name}</div>
              <pre class="text-xs text-base-content/70 mt-1 overflow-x-auto">{JSON.stringify(config, null, 2)}</pre>
            </div>
          {/each}
        </div>
      </div>

      <div class="modal-action">
        <button 
          class="btn btn-ghost" 
          on:click={() => { showDetailsModal = false; selectedSession = null; }}
        >
          Close
        </button>
      </div>
    </div>
  </div>
{/if}