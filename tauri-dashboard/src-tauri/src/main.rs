#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod python_bridge;
mod events;
mod cache;
mod notifications;

use python_bridge::*;
use events::EventManager;
use notifications::*;

fn main() {
    tauri::Builder::default()
        .manage(EventManager::new())
        .invoke_handler(tauri::generate_handler![
            get_all_sessions,
            get_controller_status,
            start_controller,
            stop_controller,
            restart_claude_pane,
            get_app_config,
            save_app_config,
            get_session_logs,
            get_metrics_data,
            setup_tmux_session,
            teardown_tmux_session,
            show_notification,
            // User Experience Commands
            run_troubleshooting_diagnosis,
            get_troubleshooting_guide,
            execute_troubleshooting_fix,
            generate_documentation,
            get_setup_steps,
            run_setup_step,
            get_system_health,
            // AI Provider Detection Commands
            detect_command_tools,
            check_environment_variables,
            check_running_services
        ])
        .setup(|app| {
            // 초기 설정
            // WebKit deprecation warning 억제를 위한 환경 변수 설정
            #[cfg(target_os = "linux")]
            {
                // WebKit GTK 경고 메시지 억제
                std::env::set_var("WEBKIT_DISABLE_COMPOSITING_MODE", "1");
            }

            // Debug 모드이거나 환경변수가 설정된 경우 개발자 도구 활성화
            let enable_devtools = cfg!(debug_assertions) || std::env::var("YESMAN_DEBUG").is_ok();
            
            if enable_devtools {
                if let Some(main_window) = app.get_window("main") {
                    main_window.open_devtools();
                    println!("🔧 Developer tools enabled");
                }
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
