/**
 * 세션 상태 관리 스토어 (FastAPI 연동)
 */

import { writable, derived, get } from 'svelte/store';
import { pythonBridge } from '$lib/utils/tauri';
import { showNotification } from './notifications';
import type { Session, SessionFilters } from '$lib/types/session';

// 세션 데이터 스토어
export const sessions = writable<Session[]>([]);
export const isLoading = writable<boolean>(false);
export const isBackgroundLoading = writable<boolean>(false); // 백그라운드 로딩 상태
export const error = writable<string | null>(null);

// 필터 상태
export const sessionFilters = writable<SessionFilters>({
  search: '',
  status: '',
  sortBy: 'session_name',
  sortOrder: 'asc',
  hasWorkspaces: false
});

// 자동 새로고침 설정
export const autoRefreshEnabled = writable<boolean>(true);
export const autoRefreshInterval = writable<number>(30000); // 30초로 증가

// 선택된 세션들
export const selectedSessions = writable<string[]>([]);

// 필터링된 세션 목록 (파생 스토어)
export const filteredSessions = derived(
  [sessions, sessionFilters],
  ([$sessions, $filters]) => {
    let filtered = [...$sessions];

    // 검색 필터
    if ($filters.search) {
      const searchLower = $filters.search.toLowerCase();
      filtered = filtered.filter(session =>
        session.session_name.toLowerCase().includes(searchLower) ||
        session.project_name?.toLowerCase().includes(searchLower) ||
        session.description?.toLowerCase().includes(searchLower)
      );
    }

    // 상태 필터
    if ($filters.status) {
      filtered = filtered.filter(session => session.status === $filters.status);
    }

    // 워크스페이스 필터
    if ($filters.hasWorkspaces) {
      filtered = filtered.filter(session =>
        !!(session.workspace_config || session.workspace_definitions || session.workspaces)
      );
    }

    // 정렬
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch ($filters.sortBy) {
        case 'session_name': // Fix: 'name' -> 'session_name'
          aValue = a.session_name;
          bValue = b.session_name;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        case 'uptime':
          aValue = a.uptime || '';
          bValue = b.uptime || '';
          break;
        case 'last_activity':
          aValue = a.last_activity_timestamp || 0;
          bValue = b.last_activity_timestamp || 0;
          break;
        default:
          aValue = a.session_name;
          bValue = b.session_name;
      }

      if (typeof aValue === 'string') {
        const comparison = aValue.localeCompare(bValue);
        return $filters.sortOrder === 'asc' ? comparison : -comparison;
      } else {
        const comparison = aValue - bValue;
        return $filters.sortOrder === 'asc' ? comparison : -comparison;
      }
    });

    return filtered;
  }
);

// 세션 통계 (파생 스토어)
export const sessionStats = derived(sessions, ($sessions) => {
  const sessionsWithWorkspaces = $sessions.filter(s => 
    !!(s.workspace_config || s.workspace_definitions || s.workspaces)
  ).length;
  
  const totalWorkspaces = $sessions.reduce((sum, s) => {
    if (s.workspace_definitions) {
      return sum + Object.keys(s.workspace_definitions).length;
    }
    if (s.workspaces) {
      return sum + Object.keys(s.workspaces).length;
    }
    return sum;
  }, 0);

  return {
    total: $sessions.length,
    running: $sessions.filter(s => s.status === 'running').length,
    stopped: $sessions.filter(s => s.status === 'stopped').length,
    sessionsWithWorkspaces,
    totalWorkspaces,
    totalWindows: $sessions.reduce((sum, s) => sum + (s.windows?.length || 0), 0),
    totalPanes: $sessions.reduce((sum, s) => sum + (s.total_panes || 0), 0)
  };
});

// 자동 새로고침 인터벌 ID
let refreshIntervalId: number | null = null;

/**
 * 세션 데이터 새로고침
 */
export async function refreshSessions(isInitial: boolean = false): Promise<void> {
  // 초기 로딩인지 백그라운드 로딩인지 구분
  if (isInitial) {
    isLoading.set(true);
  } else {
    isBackgroundLoading.set(true);
  }
  error.set(null);

  try {
		// 1) 백엔드 세션 목록 로드
		const sessionData = await pythonBridge.get_sessions();
 
		// 2) 폴백: 설정에 정의된 프로젝트를 병합하여 표시
		let configuredProjects: string[] = [];
		try {
			configuredProjects = await getAvailableProjects();
		} catch (_) {
			configuredProjects = [];
		}
 
		// 3) API 응답 가공: 우리 Session 타입으로 정규화
		const processedFromApi: Session[] = (sessionData || []).map((raw: any) => {
			const rawWindows = Array.isArray(raw.windows) ? raw.windows : [];
			const totalPanes = rawWindows.reduce((acc: number, w: any) => acc + (Array.isArray(w.panes) ? w.panes.length : 0), 0);
			const normalizedStatus: 'running' | 'stopped' = raw.status === 'running' ? 'running' : 'stopped';
			return {
				project_name: typeof raw.project_name === 'string' && raw.project_name ? raw.project_name : String(raw.session_name || ''),
				session_name: String(raw.session_name || ''),
				exists: normalizedStatus === 'running',
				status: normalizedStatus,
				windows: rawWindows,
				description: raw.description || undefined,
				uptime: undefined,
				last_activity_timestamp: undefined,
				total_panes: totalPanes,
				// Workspace configuration from API response
				workspace_config: raw.workspace_config || undefined,
				workspace_definitions: raw.workspace_definitions || undefined,
				workspaces: raw.workspaces || undefined,
			};
		});
 
		// 4) 설정 기반 플레이스홀더 생성 (API에 없는 항목 추가)
		const existingNames = new Set<string>(
			processedFromApi.flatMap((s) => [s.session_name, s.project_name].filter(Boolean) as string[]),
		);
 
		const placeholders: Session[] = configuredProjects
			.filter((name) => !existingNames.has(name))
			.map((name) => ({
				project_name: name,
				session_name: name,
				exists: false,
				status: 'stopped' as const,
				windows: [],
				description: undefined,
				uptime: undefined,
				last_activity_timestamp: undefined,
				total_panes: 0,
				// No workspace configuration for placeholders
				workspace_config: undefined,
				workspace_definitions: undefined,
				workspaces: undefined,
			}));
 
		const merged = [...processedFromApi, ...placeholders];

    // 5) 스마트 업데이트: 기존 데이터와 비교하여 변경된 경우만 업데이트
    const currentSessions = get(sessions);
    const hasChanged =
      isInitial ||
      !currentSessions ||
      currentSessions.length !== merged.length ||
      currentSessions.some((current, index) => {
        const next = merged[index];
        return (
          !next ||
          current.session_name !== next.session_name ||
          current.status !== next.status ||
          (current.windows?.length || 0) !== (next.windows?.length || 0) ||
          JSON.stringify(current.workspace_config) !== JSON.stringify(next.workspace_config) ||
          JSON.stringify(current.workspace_definitions) !== JSON.stringify(next.workspace_definitions) ||
          JSON.stringify(current.workspaces) !== JSON.stringify(next.workspaces)
        );
      });

    if (hasChanged) {
      sessions.set(merged);
    }

    if (isInitial && merged.length === 0) {
      showNotification('warning', 'No Sessions', 'No tmux sessions found.');
    }
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
    error.set(errorMessage);
    showNotification('error', 'Error', `Failed to refresh sessions: ${errorMessage}`);
    console.error('Failed to refresh sessions:', err);
  } finally {
    if (isInitial) {
      isLoading.set(false);
    } else {
      isBackgroundLoading.set(false);
    }
  }
}

/**
 * 자동 새로고침 시작
 */
export function startAutoRefresh(): void {
  stopAutoRefresh(); // 기존 인터벌 정리

  const interval = get(autoRefreshInterval);
  if (get(autoRefreshEnabled) && interval > 0) {
    refreshIntervalId = setInterval(refreshSessions, interval) as unknown as number;
    console.log('Auto-refresh started with interval:', interval);
  }
}

/**
 * 자동 새로고침 중지
 */
export function stopAutoRefresh(): void {
  if (refreshIntervalId !== null) {
    clearInterval(refreshIntervalId);
    refreshIntervalId = null;
    console.log('Auto-refresh stopped');
  }
}

/**
 * 자동 새로고침 설정 변경
 */
export function configureAutoRefresh(enabled: boolean, interval?: number): void {
  autoRefreshEnabled.set(enabled);
  if (interval !== undefined) {
    autoRefreshInterval.set(interval);
  }

  if (enabled) {
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
}

/**
 * 필터 업데이트
 */
export function updateFilters(newFilters: Partial<SessionFilters>): void {
  sessionFilters.update(current => ({ ...current, ...newFilters }));
}

/**
 * 필터 초기화
 */
export function resetFilters(): void {
  sessionFilters.set({
    search: '',
    status: '',
    controllerStatus: '',
    sortBy: 'session_name', // Fix: 'name' -> 'session_name'
    sortOrder: 'asc',
    showOnlyErrors: false
  });
}

/**
 * 세션 선택 관리
 */
export function toggleSessionSelection(sessionName: string): void {
  selectedSessions.update(current => {
    if (current.includes(sessionName)) {
      return current.filter(s => s !== sessionName);
    }
    return [...current, sessionName];
  });
}

export function selectAllSessions(): void {
  const allSessionNames = get(filteredSessions).map(s => s.session_name);
  selectedSessions.set(allSessionNames);
}

export function clearSessionSelection(): void {
  selectedSessions.set([]);
}

/**
 * 워크스페이스 유틸리티 함수들
 */
export function getSessionWorkspaces(session: Session): Record<string, any> {
  if (session.workspaces) {
    return session.workspaces;
  }
  if (session.workspace_definitions) {
    return session.workspace_definitions;
  }
  return {};
}

export function getWorkspaceAbsolutePath(session: Session, workspaceName: string): string | null {
  const workspaces = getSessionWorkspaces(session);
  if (!workspaces[workspaceName]) return null;
  
  const workspace = workspaces[workspaceName];
  const relDir = workspace.rel_dir;
  
  // If using workspace_config with base_dir
  if (session.workspace_config?.base_dir && !relDir.startsWith('/')) {
    return `${session.workspace_config.base_dir}/${relDir}`.replace(/\/+/g, '/');
  }
  
  // Otherwise return as-is (absolute path or flat workspace)
  return relDir;
}

export function hasWorkspaceConfiguration(session: Session): boolean {
  return !!(session.workspace_config || session.workspace_definitions || session.workspaces);
}

/**
 * 프로젝트 기반으로 tmux 세션을 생성합니다.
 */
export async function createTmuxSession(projectName: string): Promise<void> {
  try {
    showNotification('info', 'Creating Session', `Creating session for project: ${projectName}`);
    await pythonBridge.create_session({ project_name: projectName });
    showNotification('success', 'Session Created', `Session for ${projectName} created successfully`);
    setTimeout(refreshSessions, 1500);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Error', `Failed to create session: ${errorMessage}`);
    throw err;
  }
}

/**
 * 사용 가능한 프로젝트 목록을 가져옵니다.
 */
export async function getAvailableProjects(): Promise<string[]> {
  try {
    const response = await fetch('/api/config/projects');
    if (!response.ok) {
      throw new Error('Failed to fetch projects');
    }
    return await response.json();
  } catch (err) {
    console.error('Failed to get available projects:', err);
    return [];
  }
}

// 6. setupAllSessions 함수 구현
export async function setupAllSessions(): Promise<void> {
  try {
    showNotification('info', 'Setup Sessions', 'Setting up all sessions from configuration...');

    // Use the dedicated setup-all endpoint
    const response = await fetch('/api/sessions/setup-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (response.status === 404) {
      showNotification('warning', 'No Projects', 'No projects found in projects.yaml configuration.');
      return;
    } else if (response.status === 207) {
      // Multi-status: 일부 성공, 일부 실패
      const errorText = await response.text();
      showNotification('warning', 'Partial Success', errorText);
    } else if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to setup sessions: ${errorText}`);
    } else {
      showNotification('success', 'Setup Complete', 'All sessions have been created successfully.');
    }

    // 세션 목록 새로고침
    setTimeout(refreshSessions, 1500);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Setup Error', `Failed to setup sessions: ${errorMessage}`);
    throw err;
  }
}

export async function teardownAllSessions(): Promise<void> {
  const sessionsToTeardown = get(sessions);
  if (sessionsToTeardown.length === 0) {
    showNotification('info', 'Info', 'No sessions to teardown.');
    return;
  }

  showNotification('info', 'Teardown', `Tearing down ${sessionsToTeardown.length} sessions...`);
  try {
    // Use the dedicated teardown-all endpoint
    const response = await fetch('/api/sessions/teardown-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to teardown sessions: ${errorText}`);
    }

    showNotification('success', 'Success', 'All sessions have been torn down.');
    clearSessionSelection();
    setTimeout(refreshSessions, 1500);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Error', `Failed to teardown all sessions: ${errorMessage}`);
    throw err;
  }
}

/**
 * 워크스페이스 설정 업데이트
 */
export async function updateSessionWorkspaces(sessionName: string, workspaceConfig: any): Promise<void> {
  try {
    showNotification('info', 'Updating Workspaces', `Updating workspace configuration for ${sessionName}...`);
    
    const response = await fetch(`/api/sessions/${sessionName}/workspaces`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(workspaceConfig)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to update workspaces: ${errorText}`);
    }

    showNotification('success', 'Workspaces Updated', `Workspace configuration updated for ${sessionName}`);
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Update Failed', `Failed to update workspaces: ${errorMessage}`);
    throw err;
  }
}

/**
 * 워크스페이스 정보 가져오기
 */
export async function getWorkspaceInfo(sessionName: string): Promise<any> {
  try {
    const response = await fetch(`/api/sessions/${sessionName}/workspaces`);
    if (!response.ok) {
      throw new Error('Failed to fetch workspace info');
    }
    return await response.json();
  } catch (err) {
    console.error(`Failed to get workspace info for ${sessionName}:`, err);
    return null;
  }
}

// 9. 이벤트 리스너는 현재 아키텍처에서 불필요하므로 주석 처리
/*
export function setupEventListeners(): void {
    // ...
}
*/

// 10. 로그 관련 함수 수정
export async function viewSessionLogs(sessionName: string): Promise<void> {
    try {
        const logs = await pythonBridge.get_logs(sessionName, false, 200);
        // TODO: 받은 로그를 보여주는 UI 로직 필요 (예: 모달)
        console.log(`Logs for ${sessionName}:`, logs);
        showNotification('info', 'Logs Fetched', `Check console for logs of ${sessionName}.`);
    } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        showNotification('error', 'Error', `Failed to fetch logs: ${errorMessage}`);
        throw err;
    }
}

export async function getSessionLogs(sessionName: string): Promise<string[]> {
  try {
    const response = await pythonBridge.get_logs(sessionName, false, 500);
    if (response && (response as any).success) {
      return ((response as any).data as string[]) || [];
    }
    return [];
  } catch (err) {
    console.error(`Failed to get logs for ${sessionName}:`, err);
    return [];
  }
}

// 스토어 초기화 시 이벤트 리스너 설정 (브라우저 환경에서만)
if (typeof window !== 'undefined') {
  // setupEventListeners(); // 이벤트 리스너는 현재 아키텍처에서 불필요하므로 주석 처리
}
