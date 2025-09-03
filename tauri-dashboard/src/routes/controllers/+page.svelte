<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  
  onMount(() => {
    // Immediately redirect to sessions page
    goto('/sessions', { replaceState: true });
  });
</script>

<svelte:head>
  <title>Redirecting... - Yesman Dashboard</title>
</svelte:head>

<!-- Empty page that redirects -->