<script lang="ts">
  import { onMount } from 'svelte';
  
  onMount(() => {
    // Redirect to sessions page since controllers are deprecated
    window.location.href = '/sessions';
  });
</script>

<svelte:head>
  <title>Controllers Deprecated - Yesman Dashboard</title>
</svelte:head>

<div class="deprecated-page p-6 text-center">
  <div class="max-w-2xl mx-auto">
    <div class="text-8xl mb-6">⚠️</div>
    <h1 class="text-3xl font-bold text-warning mb-4">Controllers Feature Deprecated</h1>
    <p class="text-base-content/70 mb-6 text-lg">
      The Controllers feature has been removed since Yesman no longer uses interactive shell mode.
    </p>
    
    <div class="bg-base-200 border border-base-content/10 rounded-lg p-6 mb-6">
      <h3 class="text-lg font-semibold mb-3">What Changed?</h3>
      <p class="text-base-content/80 text-left">
        Yesman has evolved to work directly with Claude Code without needing interactive shell controllers. 
        All automation features are now handled through the core session management system.
      </p>
    </div>

    <div class="flex justify-center gap-4">
      <button
        class="btn btn-primary"
        on:click={() => window.location.href = '/sessions'}
      >
        📋 Go to Sessions
      </button>
      
      <button
        class="btn btn-outline"
        on:click={() => window.location.href = '/'}
      >
        🏠 Dashboard Home
      </button>
    </div>

    <div class="mt-8 text-sm text-base-content/50">
      <p>This page will automatically redirect to Sessions in a moment...</p>
    </div>
  </div>
</div>

<style>
  .deprecated-page {
    @apply min-h-screen flex items-center justify-center;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  }
</style>