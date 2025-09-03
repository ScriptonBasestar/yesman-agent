<script lang="ts">
  import { page } from '$app/stores';
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  // 외부 참조용 (실제로는 $page.url.pathname 사용)
  export const currentRoute: string | null = null; // 현재 라우트 ID (외부 참조용)
  // 사이드바 축소 상태 (bind로 연결됨)
  export let isMinimized: boolean = false;

  // 네비게이션 메뉴 아이템
  const navItems = [
    {
      path: '/',
      icon: '🏠',
      label: 'Dashboard',
      description: 'Main overview'
    },
    {
      path: '/sessions',
      icon: '🖥️',
      label: 'Sessions',
      description: 'Tmux sessions'
    },
    {
      path: '/agents',
      icon: '🧠',
      label: 'Agents',
      description: 'Headless agents'
    },
    {
      path: '/ai-providers',
      icon: '🤖',
      label: 'AI Providers',
      description: 'Multi-AI support'
    },
    {
      path: '/workspaces',
      icon: '🗂️',
      label: 'Workspaces',
      description: 'Development environments'
    },
    {
      path: '/logs',
      icon: '📋',
      label: 'Logs',
      description: 'Activity logs'
    },
    {
      path: '/settings',
      icon: '⚙️',
      label: 'Settings',
      description: 'Configuration'
    }
  ];

  // 빠른 액션 버튼들
  const quickActions = [
    {
      action: 'refresh',
      icon: '🔄',
      label: 'Refresh All',
      variant: 'btn-outline'
    },
    {
      action: 'setup',
      icon: '⚡',
      label: 'Setup All Sessions',
      variant: 'btn-primary'
    },
    {
      action: 'teardown',
      icon: '🛑',
      label: 'Teardown All Sessions',
      variant: 'btn-error btn-outline'
    }
  ];

  function handleQuickAction(action: string) {
    dispatch('quickAction', { action });
  }

  // 현재 경로 확인
  $: currentPath = $page.url.pathname;
  
  // 최소화 토글 함수
  function toggleMinimized() {
    isMinimized = !isMinimized;
  }
</script>

<aside class="sidebar bg-base-200 w-64 min-h-screen p-4 space-y-6">
  <!-- 로고 및 타이틀 -->
  <div class="sidebar-header">
    <div class="flex items-center gap-3 mb-2">
      <div class="avatar placeholder">
        <div class="bg-primary text-primary-content rounded-full w-10">
          <span class="text-xl">🚀</span>
        </div>
      </div>
      {#if !isMinimized}
        <div class="flex-1">
          <h1 class="text-lg font-bold text-base-content">Yesman</h1>
          <p class="text-xs text-base-content/60">Claude Dashboard</p>
        </div>
      {/if}
      <button 
        class="btn btn-ghost btn-sm" 
        on:click={toggleMinimized}
        title={isMinimized ? 'Expand sidebar' : 'Minimize sidebar'}
      >
        {isMinimized ? '→' : '←'}
      </button>
    </div>
  </div>

  <!-- 네비게이션 메뉴 -->
  <nav class="navigation">
    {#if !isMinimized}
      <h2 class="text-xs font-semibold text-base-content/60 uppercase tracking-wider mb-3">
        Navigation
      </h2>
    {/if}

    <ul class="menu menu-vertical space-y-1">
      {#each navItems as item}
        <li>
          <a
            href={item.path}
            class="menu-item flex items-center gap-3 p-3 rounded-lg transition-colors"
            class:active={currentPath === item.path}
            title={isMinimized ? item.label : ''}
          >
            <span class="text-xl">{item.icon}</span>
            {#if !isMinimized}
              <div class="flex-1">
                <div class="font-medium text-sm">{item.label}</div>
                <div class="text-xs text-base-content/60">{item.description}</div>
              </div>
            {/if}
          </a>
        </li>
      {/each}
    </ul>
  </nav>

  <!-- 빠른 액션 -->
  {#if !isMinimized}
    <div class="quick-actions">
      <h2 class="text-xs font-semibold text-base-content/60 uppercase tracking-wider mb-3">
        Quick Actions
      </h2>

      <div class="space-y-2">
        {#each quickActions as action}
          <button
            class="btn {action.variant} btn-sm w-full justify-start gap-2"
            on:click={() => handleQuickAction(action.action)}
          >
            <span>{action.icon}</span>
            <span class="text-xs">{action.label}</span>
          </button>
        {/each}
      </div>
    </div>
  {/if}

  <!-- 상태 정보 -->
  {#if !isMinimized}
    <div class="status-info">
      <h2 class="text-xs font-semibold text-base-content/60 uppercase tracking-wider mb-3">
        System Status
      </h2>

      <div class="space-y-2">
        <div class="stat-item bg-base-100 p-2 rounded-lg">
          <div class="flex justify-between items-center">
            <span class="text-xs text-base-content/70">Uptime</span>
            <span class="text-xs font-mono text-base-content">2h 34m</span>
          </div>
        </div>

        <div class="stat-item bg-base-100 p-2 rounded-lg">
          <div class="flex justify-between items-center">
            <span class="text-xs text-base-content/70">Memory</span>
            <span class="text-xs font-mono text-base-content">142MB</span>
          </div>
        </div>

        <div class="stat-item bg-base-100 p-2 rounded-lg">
          <div class="flex justify-between items-center">
            <span class="text-xs text-base-content/70">Sessions</span>
            <span class="text-xs font-mono text-base-content badge badge-primary badge-sm">3</span>
          </div>
        </div>
      </div>
    </div>
  {/if}

  <!-- 하단 정보 -->
  {#if !isMinimized}
    <div class="sidebar-footer mt-auto pt-4 border-t border-base-content/10">
      <div class="text-center">
        <p class="text-xs text-base-content/50">
          v1.0.0 • Tauri + Svelte
        </p>
        <p class="text-xs text-base-content/30 mt-1">
          Built with ❤️
        </p>
      </div>
    </div>
  {/if}
</aside>

<style>
  .sidebar {
    @apply flex flex-col;
  }

  .menu-item {
    @apply hover:bg-base-300;
  }

  .menu-item.active {
    @apply bg-primary text-primary-content;
  }

  .menu-item.active .text-base-content\/60 {
    @apply text-primary-content/70;
  }

  .stat-item {
    @apply border border-base-content/5;
  }

  .sidebar-footer {
    @apply mt-auto;
  }
</style>
