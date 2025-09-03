<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { sessionFilters, updateFilters, resetFilters } from '$lib/stores/sessions';

  const dispatch = createEventDispatcher();

  // 필터 옵션들
  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'active', label: 'Active' },
    { value: 'inactive', label: 'Inactive' },
    { value: 'unknown', label: 'Unknown' }
  ];


  const sortOptions = [
    { value: 'name', label: 'Name' },
    { value: 'status', label: 'Status' },
    { value: 'uptime', label: 'Uptime' },
    { value: 'last_activity', label: 'Last Activity' }
  ];

  // 필터 변경 핸들러
  function handleSearchChange(event: Event) {
    const target = event.target as HTMLInputElement;
    updateFilters({ search: target.value });
  }

  function handleStatusChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    updateFilters({ status: target.value });
  }


  function handleSortChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    updateFilters({ sortBy: target.value });
  }

  function handleSortOrderToggle() {
    updateFilters({
      sortOrder: $sessionFilters.sortOrder === 'asc' ? 'desc' : 'asc'
    });
  }

  function handleShowOnlyErrorsToggle() {
    updateFilters({
      showOnlyErrors: !$sessionFilters.showOnlyErrors
    });
  }

  function handleReset() {
    resetFilters();
    dispatch('filtersReset');
  }

  // 활성 필터 수 계산
  $: activeFilterCount = [
    $sessionFilters.search,
    $sessionFilters.status,
    $sessionFilters.showOnlyErrors
  ].filter(Boolean).length;
</script>

<div class="session-filters bg-base-200 p-4 rounded-lg border border-base-content/10">
  <div class="filters-header flex items-center justify-between mb-4">
    <h3 class="text-sm font-semibold text-base-content/80 flex items-center gap-2">
      🔍 Filters
      {#if activeFilterCount > 0}
        <span class="badge badge-primary badge-sm">{activeFilterCount}</span>
      {/if}
    </h3>

    {#if activeFilterCount > 0}
      <button
        class="btn btn-ghost btn-xs"
        on:click={handleReset}
        title="Clear all filters"
      >
        🗑️ Clear
      </button>
    {/if}
  </div>

  <div class="filters-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <!-- 검색 필터 -->
    <div class="filter-item">
      <label class="label" for="search-input">
        <span class="label-text text-xs font-medium">Search</span>
      </label>
      <div class="input-group">
        <input
          id="search-input"
          type="text"
          placeholder="Session name..."
          class="input input-sm input-bordered w-full"
          value={$sessionFilters.search}
          on:input={handleSearchChange}
        />
        <span class="input-group-text">🔍</span>
      </div>
    </div>

    <!-- 세션 상태 필터 -->
    <div class="filter-item">
      <label class="label" for="status-select">
        <span class="label-text text-xs font-medium">Status</span>
      </label>
      <select
        id="status-select"
        class="select select-sm select-bordered w-full"
        value={$sessionFilters.status}
        on:change={handleStatusChange}
      >
        {#each statusOptions as option}
          <option value={option.value}>{option.label}</option>
        {/each}
      </select>
    </div>


    <!-- 정렬 기준 -->
    <div class="filter-item">
      <label class="label" for="sort-select">
        <span class="label-text text-xs font-medium">Sort by</span>
      </label>
      <select
        id="sort-select"
        class="select select-sm select-bordered w-full"
        value={$sessionFilters.sortBy}
        on:change={handleSortChange}
      >
        {#each sortOptions as option}
          <option value={option.value}>{option.label}</option>
        {/each}
      </select>
    </div>

    <!-- 정렬 순서 -->
    <div class="filter-item">
      <div class="mb-2">
        <span class="label-text text-xs font-medium">Order</span>
      </div>
      <button
        class="btn btn-sm btn-outline w-full"
        on:click={handleSortOrderToggle}
        title="Toggle sort order"
      >
        {#if $sessionFilters.sortOrder === 'asc'}
          ⬆️ Ascending
        {:else}
          ⬇️ Descending
        {/if}
      </button>
    </div>

    <!-- 토글 옵션들 -->
    <div class="filter-item">
      <div class="mb-2">
        <span class="label-text text-xs font-medium">Options</span>
      </div>
      <div class="form-control">
        <label class="label cursor-pointer" for="errors-only-toggle">
          <span class="label-text text-xs">Errors only</span>
          <input
            id="errors-only-toggle"
            type="checkbox"
            class="toggle toggle-sm toggle-error"
            checked={$sessionFilters.showOnlyErrors}
            on:change={handleShowOnlyErrorsToggle}
          />
        </label>
      </div>
    </div>
  </div>

  <!-- 빠른 필터 버튼들 -->
  <div class="quick-filters mt-4 pt-4 border-t border-base-content/10">
    <div class="flex flex-wrap gap-2">
      <span class="text-xs font-medium text-base-content/60 mr-2">Quick filters:</span>

      <button
        class="btn btn-xs btn-outline"
        class:btn-active={$sessionFilters.status === 'active'}
        on:click={() => updateFilters({ status: $sessionFilters.status === 'active' ? '' : 'active' })}
      >
        🟢 Active Sessions
      </button>

      <button
        class="btn btn-xs btn-outline btn-error"
        class:btn-active={$sessionFilters.showOnlyErrors}
        on:click={handleShowOnlyErrorsToggle}
      >
        ❌ With Errors
      </button>
    </div>
  </div>

  <!-- 결과 요약 -->
  <div class="results-summary mt-3 text-xs text-base-content/60">
    <div class="flex items-center justify-between">
      <span>
        {#if activeFilterCount > 0}
          Filtered results • {activeFilterCount} active filter{activeFilterCount > 1 ? 's' : ''}
        {:else}
          All sessions
        {/if}
      </span>

      <span>
        Sort: {$sessionFilters.sortBy} ({$sessionFilters.sortOrder})
      </span>
    </div>
  </div>
</div>

<style>
  .filter-item {
    @apply min-w-0;
  }

  .input-group {
    @apply relative;
  }

  .input-group-text {
    @apply absolute right-3 top-1/2 transform -translate-y-1/2 text-base-content/50 pointer-events-none;
  }

  .quick-filters {
    @apply flex-wrap;
  }

  .btn-xs {
    @apply text-xs;
  }

  @media (max-width: 768px) {
    .filters-grid {
      @apply grid-cols-1;
    }

    .quick-filters .btn {
      @apply text-xs;
    }
  }
</style>
