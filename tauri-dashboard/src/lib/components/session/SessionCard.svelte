<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { Session } from '$lib/types/session';
  import { getSessionWorkspaces, hasWorkspaceConfiguration } from '$lib/stores/sessions';

  export let session: Session;

  const dispatch = createEventDispatcher();

  // 상태별 스타일 정의
  const statusStyles = {
    running: {
      badge: 'badge-success',
      icon: '🟢',
      bg: 'bg-success/10'
    },
    stopped: {
      badge: 'badge-error',
      icon: '🔴',
      bg: 'bg-error/10'
    },
    unknown: {
      badge: 'badge-warning',
      icon: '🟡',
      bg: 'bg-warning/10'
    }
  };

  // 세션 상태 계산
  $: sessionStyle = statusStyles[session.status as keyof typeof statusStyles] || statusStyles.unknown;

  // 세션이 실행 중인지 확인
  $: isSessionRunning = session.status === 'running';

  // Claude Code가 실행되고 있는지 확인
  $: hasClaudeRunning = session.windows && session.windows.some(w =>
    w.panes && w.panes.some(p => p.is_claude || p.command === 'claude')
  );

  // 워크스페이스 정보 계산
  $: workspaces = getSessionWorkspaces(session);
  $: workspaceNames = Object.keys(workspaces);
  $: hasWorkspaces = hasWorkspaceConfiguration(session);

  // 시간 포맷팅
  function formatUptime(uptime: string | null): string {
    if (!uptime) return 'N/A';
    return uptime;
  }

  function formatLastActivity(timestamp: number | null): string {
    if (!timestamp) return 'No activity';

    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  }

  // 이벤트 핸들러

  function handleViewLogs() {
    dispatch('viewLogs', { session: session.session_name });
  }

  function handleAttachSession() {
    dispatch('attachSession', { session: session.session_name });
  }

  function handleViewDetails() {
    dispatch('viewDetails', { session: session.session_name });
  }


  function handleStartSession() {
    console.log('SessionCard: handleStartSession called for', session.session_name);
    dispatch('startSession', { session: session.session_name });
    console.log('SessionCard: startSession event dispatched');
  }

  function handleStopSession() {
    dispatch('stopSession', { session: session.session_name });
  }

  function handleManageWorkspaces() {
    dispatch('manageWorkspaces', { session: session.session_name });
  }

  function handleViewWorkspaceDefinitions() {
    // 워크스페이스 정의 보기 - workspaces 페이지로 이동
    window.location.href = `/workspaces?session=${session.session_name}`;
  }
</script>

<div class="session-card card bg-base-100 shadow-lg border border-base-content/10 hover:shadow-xl transition-shadow">
  <div class="card-body p-6">
    <!-- 카드 헤더 -->
    <div class="card-header flex items-start justify-between mb-4">
      <div class="session-info flex-1">
        <div class="flex items-center gap-3 mb-2">
          <h3 class="card-title text-lg font-semibold">{session.session_name}</h3>
          <div class="badge {sessionStyle.badge} badge-sm">
            {sessionStyle.icon} {session.status}
          </div>
        </div>

        {#if session.project_name && session.project_name !== session.session_name}
          <p class="text-sm text-base-content/70">
            Project: <span class="font-medium">{session.project_name}</span>
          </p>
        {/if}

        {#if session.description}
          <p class="text-sm text-base-content/60 mt-1">{session.description}</p>
        {/if}
      </div>

      <div class="session-actions flex gap-2">
        <button
          class="btn btn-ghost btn-sm"
          on:click={handleViewDetails}
          title="View details"
        >
          📊
        </button>

        <div class="dropdown dropdown-end">
          <button class="btn btn-ghost btn-sm">⋮</button>
          <ul class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
            <li><button on:click={handleAttachSession}>🔗 Attach to Session</button></li>
            <li><button on:click={handleViewLogs}>📋 View Logs</button></li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 세션 통계 -->
    <div class="session-stats grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-4">
      <div class="stat-item bg-base-200 p-3 rounded-lg cursor-pointer hover:bg-base-300 transition-colors {workspaceNames.length === 0 ? 'border border-dashed border-base-content/30' : ''}" 
           on:click={handleViewWorkspaceDefinitions}
           on:keydown={(e) => e.key === 'Enter' && handleViewWorkspaceDefinitions()}
           tabindex="0"
           title="Click to view workspace definitions">
        <div class="stat-title text-xs text-base-content/60">Workspace Definitions</div>
        <div class="stat-value text-lg font-bold {workspaceNames.length === 0 ? 'text-base-content/50' : ''}">{workspaceNames.length}</div>
        <div class="text-xs {workspaceNames.length === 0 ? 'text-warning' : 'text-primary'} mt-1">
          {workspaceNames.length === 0 ? '⚠️ Configure' : '👁️ View'}
        </div>
      </div>

      <div class="stat-item bg-base-200 p-3 rounded-lg">
        <div class="stat-title text-xs text-base-content/60">Windows</div>
        <div class="stat-value text-lg font-bold">{session.windows?.length || 0}</div>
      </div>

      <div class="stat-item bg-base-200 p-3 rounded-lg">
        <div class="stat-title text-xs text-base-content/60">Panes</div>
        <div class="stat-value text-lg font-bold">{session.total_panes || 0}</div>
      </div>

      <div class="stat-item bg-base-200 p-3 rounded-lg">
        <div class="stat-title text-xs text-base-content/60">Workspaces</div>
        <div class="stat-value text-lg font-bold">{workspaceNames.length}</div>
      </div>

      <div class="stat-item bg-base-200 p-3 rounded-lg">
        <div class="stat-title text-xs text-base-content/60">Last Activity</div>
        <div class="stat-value text-sm">{formatLastActivity(session.last_activity_timestamp)}</div>
      </div>
    </div>

    <!-- 워크스페이스 정보 -->
    {#if hasWorkspaces}
      <div class="workspace-info bg-primary/10 border border-primary/20 p-3 rounded-lg mb-4">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <span class="text-primary">🗂️</span>
            <div>
              <div class="text-sm font-medium text-primary">
                Workspace Configuration Active
              </div>
              <div class="text-xs text-base-content/60">
                {workspaceNames.length} workspace{workspaceNames.length !== 1 ? 's' : ''} configured
                {#if workspaceNames.length > 0}
                  : {workspaceNames.join(', ')}
                {/if}
              </div>
              {#if session.workspace_config?.base_dir}
                <div class="text-xs text-base-content/50 font-mono">
                  Base: {session.workspace_config.base_dir}
                </div>
              {/if}
            </div>
          </div>
          <button
            class="btn btn-primary btn-sm"
            on:click={handleManageWorkspaces}
            title="Manage workspaces"
          >
            ⚙️ Manage
          </button>
        </div>
      </div>
    {:else}
      <div class="workspace-info bg-warning/10 border border-warning/20 p-3 rounded-lg mb-4">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <span class="text-warning">⚠️</span>
            <div>
              <div class="text-sm font-medium text-warning">No Workspace Configuration</div>
              <div class="text-xs text-base-content/60">
                Configure workspaces to define secure development environments
              </div>
            </div>
          </div>
          <button
            class="btn btn-outline btn-warning btn-sm"
            on:click={handleManageWorkspaces}
            title="Configure workspaces"
          >
            🗂️ Configure
          </button>
        </div>
      </div>
    {/if}

    <!-- 세션 액션 -->
    <div class="session-actions">
      <!-- 세션 상태 경고 -->
      {#if !isSessionRunning}
        <div class="session-warning bg-warning/10 border border-warning/20 p-3 rounded-lg mb-3">
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <span class="text-warning">⚠️</span>
              <div>
                <div class="text-sm font-medium text-warning">Session Not Running</div>
                <div class="text-xs text-base-content/60">
                  Start the tmux session to begin working
                </div>
              </div>
            </div>
            <button
              class="btn btn-warning btn-sm"
              on:click={handleStartSession}
              title="Start tmux session"
            >
              ▶️ Start Session
            </button>
          </div>
        </div>
      {/if}

      <!-- 세션 액션 버튼 -->
      <div class="actions flex gap-2">
        {#if !isSessionRunning}
          <button
            class="btn btn-success btn-sm flex-1"
            on:click={handleStartSession}
            title="Start tmux session"
          >
            ▶️ Start Session
          </button>
        {:else}
          <button
            class="btn btn-error btn-outline btn-sm"
            on:click={handleStopSession}
          title={isSessionRunning ? 'Stop tmux session' : 'Session is not running'}
        >
          ⏹️ Stop
        </button>

        <button
          class="btn btn-ghost btn-sm"
          on:click={handleViewLogs}
        >
          📋 Logs
        </button>
        {/if}
      </div>
    </div>

    <!-- 윈도우 목록 (접기/펼치기) -->
    {#if session.windows && session.windows.length > 0}
      <div class="windows-section mt-4">
        <div class="collapse collapse-arrow bg-base-200">
          <input type="checkbox" />
          <div class="collapse-title text-sm font-medium">
            📋 Windows ({session.windows.length})
          </div>
          <div class="collapse-content">
            <div class="space-y-1">
              {#each session.windows as window}
                <div class="window-item bg-base-100 p-2 rounded border border-base-content/5">
                  <div class="flex items-start gap-2">
                    <span class="text-base text-base-content/60 mt-0.5">🗂️</span>
                    <div class="flex-1">
                      <div class="flex items-center justify-between">
                        <span class="text-sm font-medium">{window.name}</span>
                        <div class="flex items-center gap-2 text-xs text-base-content/60">
                          <span>{window.panes?.length || 0} panes</span>
                          {#if window.active}
                            <span class="badge badge-primary badge-xs">active</span>
                          {/if}
                        </div>
                      </div>
                      {#if window.layout}
                        <div class="text-xs text-base-content/50 mt-1">Layout: {window.layout}</div>
                      {/if}
                      
                      <!-- Panes as sub-tree -->
                      {#if window.panes && window.panes.length > 0}
                        <div class="mt-2 ml-6 space-y-1">
                          {#each window.panes as pane}
                            <div class="flex items-start gap-2 text-xs">
                              <span class="text-sm text-base-content/50 mt-0.5">
                                {pane.is_claude ? '🤖' : '📄'}
                              </span>
                              <div class="flex-1">
                                <div class="flex items-center justify-between">
                                  <span class="font-mono text-base-content/80">
                                    {pane.command || 'shell'}
                                  </span>
                                  <div class="flex items-center gap-1">
                                    {#if pane.is_claude}
                                      <span class="badge badge-info badge-xs">claude</span>
                                    {/if}
                                    {#if pane.active}
                                      <span class="badge badge-success badge-xs">active</span>
                                    {/if}
                                  </div>
                                </div>
                                {#if pane.current_path}
                                  <div class="text-base-content/50 font-mono flex items-center gap-1">
                                    <span>📁</span>
                                    <span>{pane.current_path}</span>
                                  </div>
                                {/if}
                              </div>
                            </div>
                          {/each}
                        </div>
                      {/if}
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
    {/if}

    <!-- 워크스페이스 상세 (접기/펼치기) -->
    {#if hasWorkspaces && workspaceNames.length > 0}
      <div class="workspaces-section mt-4">
        <div class="collapse collapse-arrow bg-primary/5">
          <input type="checkbox" />
          <div class="collapse-title text-sm font-medium text-primary">
            🗂️ Workspaces ({workspaceNames.length})
          </div>
          <div class="collapse-content">
            <div class="space-y-2">
              {#each workspaceNames as workspaceName}
                {@const workspace = workspaces[workspaceName]}
                <div class="workspace-item bg-base-100 p-3 rounded border border-primary/20">
                  <div class="flex items-start gap-2">
                    <span class="text-base text-primary mt-0.5">📁</span>
                    <div class="flex-1">
                      <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-medium text-primary">{workspaceName}</span>
                        <span class="badge badge-primary badge-xs">
                          {workspace.allowed_paths?.length || 0} paths
                        </span>
                      </div>
                      
                      {#if workspace.description}
                        <div class="text-xs text-base-content/70 mb-2">
                          {workspace.description}
                        </div>
                      {/if}

                      <div class="text-xs font-mono text-base-content/60 mb-2">
                        <span class="text-base-content/50">📂 Directory:</span>
                        <span class="bg-base-200 px-1 rounded">{workspace.rel_dir}</span>
                      </div>

                      {#if workspace.allowed_paths && workspace.allowed_paths.length > 0}
                        <div class="allowed-paths">
                          <div class="text-xs text-base-content/50 mb-1">Allowed paths:</div>
                          <div class="flex flex-wrap gap-1">
                            {#each workspace.allowed_paths as path}
                              <span class="badge badge-outline badge-xs font-mono">{path}</span>
                            {/each}
                          </div>
                        </div>
                      {/if}
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .session-card {
    @apply transition-all duration-200;
  }

  .session-card:hover {
    @apply border-primary/20;
  }

  .stat-item {
    @apply text-center border border-base-content/5;
  }

  .stat-title {
    @apply block mb-1;
  }

  .stat-value {
    @apply block;
  }


  .window-item {
    @apply hover:bg-base-200 transition-colors;
  }
</style>
